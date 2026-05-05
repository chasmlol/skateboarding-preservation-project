import argparse
import json
import socket
import ssl
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ROOT_CA = ROOT / "local_gos_root_ca.pem"
CERT = ROOT / "local_127_cert.pem"
KEY = ROOT / "local_127_key.pem"
LISTEN_HOST = "127.0.0.1"
FORCE_TLS12 = False
CERT_PATH = CERT
KEY_PATH = KEY
PORT443_CERT_PATH = None
PORT443_KEY_PATH = None
BLAZE_MODE = "echo16"
KEEP_BLAZE_OPEN = False
LOCAL_BLAZE_ID = 100000001
LOCAL_ACCOUNT_ID = 100000002
LOCAL_PERSONA_ID = 100000003
USERSESSIONS_COMPONENT = 0x7802
HTTP_METHODS = (b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ")


class Logger:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.path.write_text("", encoding="utf-8")

    def write(self, event, **fields):
        row = {"t": round(time.time(), 3), "event": event, **fields}
        with self.lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


def serve_port(port, logger, stop):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    if FORCE_TLS12:
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.set_alpn_protocols(["http/1.1", "h2"])
    if port == 443 and PORT443_CERT_PATH and PORT443_KEY_PATH:
        context.load_cert_chain(PORT443_CERT_PATH, PORT443_KEY_PATH)
    else:
        context.load_cert_chain(CERT_PATH, KEY_PATH)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LISTEN_HOST, port))
        server.listen(8)
        server.settimeout(0.5)
        logger.write("listen", host=LISTEN_HOST, port=port)
        while not stop.is_set():
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle_conn, args=(context, conn, addr, port, logger), daemon=True).start()


def handle_conn(context, conn, addr, port, logger):
    peer = f"{addr[0]}:{addr[1]}"
    logger.write("accept", port=port, addr=peer)
    try:
        conn.settimeout(2.0)
        try:
            peek = conn.recv(4096, socket.MSG_PEEK)
            logger.write("peek", port=port, addr=peer, len=len(peek), data_hex=peek[:512].hex(), **parse_client_hello(peek))
        except Exception as exc:
            logger.write("peek_error", port=port, addr=peer, error=repr(exc))
        with context.wrap_socket(conn, server_side=True) as tls:
            logger.write(
                "tls",
                port=port,
                addr=peer,
                cipher=tls.cipher(),
                version=tls.version(),
                alpn=tls.selected_alpn_protocol(),
            )
            tls.settimeout(2.0)
            if port == 44325:
                handle_blaze_conn(tls, port, peer, logger)
                return
            try:
                data = recv_request(tls)
            except socket.timeout:
                data = b""
            logger.write(
                "app_data",
                port=port,
                addr=peer,
                len=len(data),
                data_hex=data[:2048].hex(),
                data_text=data[:2048].decode("utf-8", "replace"),
            )
            if data:
                response = response_for(port, data)
                logger.write(
                    "send",
                    port=port,
                    addr=peer,
                    len=len(response),
                    data_hex=response[:2048].hex(),
                    data_text=response[:2048].decode("utf-8", "replace"),
                )
                tls.sendall(response)
    except Exception as exc:
        logger.write("error", port=port, addr=peer, error=repr(exc))
    finally:
        try:
            conn.close()
        except OSError:
            pass


def handle_blaze_conn(tls, port, peer, logger):
    sent_notifications = False
    while True:
        try:
            data = tls.recv(65535)
        except socket.timeout:
            logger.write("blaze_timeout", port=port, addr=peer)
            if KEEP_BLAZE_OPEN:
                continue
            return
        if not data:
            logger.write("blaze_disconnect", port=port, addr=peer)
            return
        logger.write(
            "app_data",
            port=port,
            addr=peer,
            len=len(data),
            data_hex=data[:4096].hex(),
            data_text=data[:4096].decode("utf-8", "replace"),
        )
        if data.startswith(HTTP_METHODS):
            response = response_for(port, data)
            logger.write(
                "http_send",
                port=port,
                addr=peer,
                len=len(response),
                data_hex=response[:4096].hex(),
                data_text=response[:4096].decode("utf-8", "replace"),
            )
            tls.sendall(response)
            return
        if len(data) >= 16:
            logger.write("blaze_request", port=port, addr=peer, **fire2_packet_info(data))
        response = response_for(port, data)
        logger.write(
            "send",
            port=port,
            addr=peer,
            len=len(response),
            data_hex=response[:4096].hex(),
            data_text=response[:4096].decode("utf-8", "replace"),
        )
        tls.sendall(response)
        if (
            not sent_notifications
            and len(data) >= 16
            and BLAZE_MODE.startswith("fire2_auto")
            and "notify" in BLAZE_MODE
        ):
            info = fire2_packet_info(data)
            if info["component"] == 9 and info["command"] == 1:
                sent_notifications = True
                for notice_name, notice in blaze_notifications_for_mode():
                    try:
                        logger.write(
                            "notify_send",
                            port=port,
                            addr=peer,
                            name=notice_name,
                            len=len(notice),
                            data_hex=notice[:4096].hex(),
                        )
                        tls.sendall(notice)
                        time.sleep(0.05)
                    except OSError as exc:
                        logger.write("notify_error", port=port, addr=peer, name=notice_name, error=repr(exc))
                        return


def recv_request(tls):
    data = bytearray()
    deadline = time.time() + 2.0
    while time.time() < deadline and len(data) < 65536:
        chunk = tls.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
        header_end = data.find(b"\r\n\r\n")
        if header_end >= 0:
            headers = data[:header_end].decode("iso-8859-1", "replace")
            content_length = 0
            for line in headers.split("\r\n")[1:]:
                name, sep, value = line.partition(":")
                if sep and name.strip().lower() == "content-length":
                    try:
                        content_length = int(value.strip())
                    except ValueError:
                        content_length = 0
            if len(data) >= header_end + 4 + content_length:
                break
        elif len(data) >= 4 and not data.startswith((b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ")):
            break
    return bytes(data)


def response_for(port, data):
    if b"/redirector/getServerInstance" in data:
        return redirector_response()
    if b"/redirector/findCACertificates" in data or b"/redirector/getCACertificates" in data:
        return ca_certificates_response()
    if port == 44325 and len(data) >= 16:
        return blaze_response(data)
    return b"\x00\x00\x00\x00"


def blaze_response(data):
    header = bytearray(data[:16])
    header[0:4] = b"\x00\x00\x00\x00"
    if BLAZE_MODE.startswith("fire2_auto"):
        component = int.from_bytes(data[6:8], "big")
        command = int.from_bytes(data[8:10], "big")
        if component == 9 and command == 1:
            if BLAZE_MODE == "fire2_auto_empty_fetch":
                payload = b""
            elif BLAZE_MODE == "fire2_auto_fetch_noterm":
                payload = fetch_config_payload(terminator=False)
            elif BLAZE_MODE == "fire2_auto_fetch_string":
                payload = fetch_config_string_payload()
            elif "full_config" in BLAZE_MODE:
                payload = fetch_config_payload(full=True)
            else:
                payload = fetch_config_payload()
        elif component == 9 and command == 7:
            payload = preauth_payload(full=("preauth_full" in BLAZE_MODE))
        elif component == 1 and command in (10, 11, 60, 230, 290, 310):
            payload = login_response_payload()
        else:
            payload = b""
        return fire2_response_packet(data, payload)
    if BLAZE_MODE == "echo16":
        return bytes(header)
    if BLAZE_MODE == "type1":
        header[10:12] = b"\x00\x01"
        return bytes(header)
    if BLAZE_MODE == "type1000":
        header[10:12] = b"\x10\x00"
        return bytes(header)
    if BLAZE_MODE == "type2000":
        header[10:12] = b"\x20\x00"
        return bytes(header)
    if BLAZE_MODE == "id80000000":
        msg_id = int.from_bytes(header[12:16], "little") | 0x80000000
        header[12:16] = msg_id.to_bytes(4, "little")
        return bytes(header)
    if BLAZE_MODE == "fire2_response":
        header[4:6] = b"\x10\x00"
        return bytes(header)
    if BLAZE_MODE == "fire2_notify":
        header[4:6] = b"\x20\x00"
        return bytes(header)
    if BLAZE_MODE == "fire2_error":
        header[4:6] = b"\x30\x00"
        return bytes(header)
    if BLAZE_MODE == "fire2_response_le":
        header[4:6] = b"\x00\x10"
        return bytes(header)
    if BLAZE_MODE == "fire2_response_id80000000":
        header[4:6] = b"\x10\x00"
        msg_id = int.from_bytes(header[12:16], "little") | 0x80000000
        header[12:16] = msg_id.to_bytes(4, "little")
        return bytes(header)
    if BLAZE_MODE in (
        "fire2_preauth_min_header",
        "fire2_preauth_full_header",
        "fire2_preauth_full_header_type3",
    ):
        payload = preauth_payload(full=("full" in BLAZE_MODE))
        header[0:4] = len(payload).to_bytes(4, "big")
        header[4:6] = b"\x00\x00"
        header[6:10] = data[6:10]
        header[10:13] = data[10:13]
        response_type = 3 if BLAZE_MODE.endswith("_type3") else 1
        header[13] = ((response_type & 0x7) << 5) | (data[13] & 0x1F)
        header[14:16] = data[14:16]
        return bytes(header) + payload
    if BLAZE_MODE in (
        "fire2_preauth_min",
        "fire2_preauth_full",
        "fire2_preauth_full_le",
        "fire2_preauth_min_len24",
        "fire2_preauth_full_len24",
        "fire2_preauth_full_len24_le",
    ):
        payload = preauth_payload(full=("full" in BLAZE_MODE))
        if "len24" in BLAZE_MODE:
            header[0:3] = len(payload).to_bytes(3, "big")
            header[3] = 0
        else:
            header[0:4] = len(payload).to_bytes(4, "big")
        header[4:6] = b"\x00\x10" if BLAZE_MODE.endswith("_le") else b"\x10\x00"
        return bytes(header) + payload
    return bytes(header)


def fire2_response_packet(request, payload, response_type=1):
    header = bytearray(request[:16])
    header[0:4] = len(payload).to_bytes(4, "big")
    header[4:6] = b"\x00\x00"
    header[6:10] = request[6:10]
    header[10:13] = request[10:13]
    header[13] = ((response_type & 0x7) << 5) | (request[13] & 0x1F)
    header[14:16] = request[14:16]
    return bytes(header) + payload


def fire2_notification_packet(component, command, payload, msg_id=0, user_index=0):
    header = bytearray(16)
    header[0:4] = len(payload).to_bytes(4, "big")
    header[4:6] = b"\x00\x00"
    header[6:8] = int(component).to_bytes(2, "big")
    header[8:10] = int(command).to_bytes(2, "big")
    header[10:13] = int(msg_id).to_bytes(3, "big")
    header[13] = (2 << 5) | (user_index & 0x1F)
    return bytes(header) + payload


def fire2_packet_info(data):
    return {
        "payload_len": int.from_bytes(data[0:4], "big"),
        "metadata_len": int.from_bytes(data[4:6], "big"),
        "component": int.from_bytes(data[6:8], "big"),
        "command": int.from_bytes(data[8:10], "big"),
        "msg_id": int.from_bytes(data[10:13], "big"),
        "msg_type": data[13] >> 5,
        "user_index": data[13] & 0x1F,
    }


TDF_VARINT = 0
TDF_STRING = 1
TDF_BLOB = 2
TDF_GROUP = 3
TDF_LIST = 4
TDF_MAP = 5


def tdf_varint(value):
    value = int(value)
    if value < 64:
        return bytes([value])
    out = bytearray()
    out.append((value & 0x3F) | 0x80)
    value >>= 6
    while value >= 128:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def tdf_tag(name, value_type):
    raw = name.encode("ascii")
    out = [0, 0, 0, value_type]
    if len(raw) > 0:
        out[0] |= (raw[0] & 0x40) << 1
        out[0] |= (raw[0] & 0x10) << 2
        out[0] |= (raw[0] & 0x0F) << 2
    if len(raw) > 1:
        out[0] |= (raw[1] & 0x40) >> 5
        out[0] |= (raw[1] & 0x10) >> 4
        out[1] |= (raw[1] & 0x0F) << 4
    if len(raw) > 2:
        out[1] |= (raw[2] & 0x40) >> 3
        out[1] |= (raw[2] & 0x10) >> 2
        out[1] |= (raw[2] & 0x0C) >> 2
        out[2] |= (raw[2] & 0x03) << 6
    if len(raw) > 3:
        out[2] |= (raw[3] & 0x40) >> 1
        out[2] |= raw[3] & 0x1F
    return bytes(out)


def tdf_string(name, value):
    raw = value.encode("utf-8") + b"\x00"
    return tdf_tag(name, TDF_STRING) + tdf_varint(len(raw)) + raw


def tdf_int(name, value):
    return tdf_tag(name, TDF_VARINT) + tdf_varint(value)


def tdf_raw_tag(tag24, value_type):
    return int(tag24).to_bytes(3, "big") + bytes([value_type])


def tdf_raw_string(tag24, value):
    raw = value.encode("utf-8") + b"\x00"
    return tdf_raw_tag(tag24, TDF_STRING) + tdf_varint(len(raw)) + raw


def tdf_raw_int(tag24, value):
    return tdf_raw_tag(tag24, TDF_VARINT) + tdf_varint(value)


def tdf_group(name, payload):
    return tdf_tag(name, TDF_GROUP) + payload + b"\x00"


def tdf_raw_group(tag24, payload):
    return tdf_raw_tag(tag24, TDF_GROUP) + payload + b"\x00"


def tdf_list_varint(name, values):
    payload = bytearray()
    payload += tdf_tag(name, TDF_LIST)
    payload.append(TDF_VARINT)
    payload += tdf_varint(len(values))
    for value in values:
        payload += tdf_varint(value)
    return bytes(payload)


def tdf_map_str_str(name, entries):
    payload = bytearray()
    payload += tdf_tag(name, TDF_MAP)
    payload.append(TDF_STRING)
    payload.append(TDF_STRING)
    payload += tdf_varint(len(entries))
    for key, value in entries.items():
        key_raw = key.encode("utf-8") + b"\x00"
        value_raw = value.encode("utf-8") + b"\x00"
        payload += tdf_varint(len(key_raw)) + key_raw
        payload += tdf_varint(len(value_raw)) + value_raw
    return bytes(payload)


def blaze_config_entries(full=False):
    grpc_endpoint = "http://127.0.0.1:50051"
    http_endpoint = "http://127.0.0.1"
    config = {
        "eadp.authentication.useJwtToken": "false",
        "eadp.instrumentation.enabled": "false",
        "eadp.auth.account": http_endpoint,
        "eadp.identity": http_endpoint,
        "eadp.identity.proxy": f"{http_endpoint}/proxy",
        "AmpSettings.Endpoint": grpc_endpoint,
        "AmpSettings.Environment": "prod",
        "AmpSettings.Namespace": "dingo",
        "AmpSettings.DataLineage": "default",
        "DingoOnline.BlazeServiceNameOverride": "dingo-1-$platform$",
        "DingoOnline.BlazeLoginWithJwt": "false",
        "DingoOnline.ClientAutoLoginEnabled": "true",
        "DingoOnline.CdnBaseUrl": f"{http_endpoint}/cdn/production",
        "DingoOnline.Events.Enabled": "true",
        "DingoOnline.ProfileLoadoutId": "profile8",
        "DingoOnline.Skatepass.Enabled": "true",
        "OnlineBackend.BlazeLoginWithJwt": "false",
    }
    if full:
        service_keys = [
            "eadp.nexus.connect.grpc.v1",
            "eadp.eaid.grpc.model",
            "eadp.identity.v2",
            "eadp.eaid.grpc.model.v1",
            "eadp.candi.offer.service",
            "eadp.candi.offer.v2.service",
            "eadp.candi.catalog.service",
            "eadp.candi.catalog.v2.service",
            "eadp.candi.entitlement.v2.service",
            "eadp.candi.drm.service",
            "eadp.candi.valuetransfer.service",
            "eadp.candi.valuetransfer.v2.service",
            "eadp.playercard.v1",
            "amp.services.login.v1",
            "amp.services.inventory",
            "amp.services.server_discovery",
            "amp.services.gamestore.v1",
            "amp.services.data.game.v1",
            "amp.services.date",
            "amp.services.game.tasks.v1",
            "dingo.services.profile.game.v1",
            "dingo.services.ownable.game.v1",
            "dingo.services.save.game.v1",
            "dingo.services.progression.game.v1",
            "dingo.services.unlocks.game.v1",
            "dingo.services.store.game.v1",
            "dingo.services.mail.game.v1",
            "dingo.services.stats.game.v1",
            "dingo.services.storage.v1",
        ]
        config.update({key: grpc_endpoint for key in service_keys})
        config.update(
            {
                "eadp.director": http_endpoint,
                "eadp.networkReachability.primaryEndpoint": "127.0.0.1",
                "eadp.networkReachability.secondaryEndpoint": "127.0.0.1",
                "eadp.stats": grpc_endpoint,
                "eadp.leaderboards": grpc_endpoint,
                "eadp.leaderboards.v2": grpc_endpoint,
                "eadp.pushnotification": grpc_endpoint,
                "eadp.realtimemessaging": grpc_endpoint,
                "eadp.friends.v1": grpc_endpoint,
                "eadp.social.privacy.v1": grpc_endpoint,
            }
        )
    return config


def fetch_config_payload(terminator=True, full=False):
    payload = tdf_map_str_str("CONF", blaze_config_entries(full=full))
    if terminator:
        payload += b"\x00"
    return payload


def fetch_config_string_payload():
    return tdf_string("CONF", json.dumps(blaze_config_entries(), separators=(",", ":"))) + b"\x00"


def preauth_payload(full=False):
    payload = bytearray()
    payload += tdf_string("ASRC", "local")
    payload += tdf_list_varint("CIDS", [1, 4, 5, 7, 9, 28, USERSESSIONS_COMPONENT])
    payload += tdf_string("CLID", "skate-local-client")
    if full:
        payload += tdf_map_str_str(
            "CONF",
            {
                "DingoOnline.ClientAutoLoginEnabled": "true",
                "DingoOnline.CdnBaseUrl": "http://127.0.0.1/cdn/production",
                "DingoOnline.Events.Enabled": "true",
                "DingoOnline.ProfileLoadoutId": "profile8",
                "DingoOnline.Skatepass.Enabled": "true",
                "AmpSettings.Endpoint": "http://127.0.0.1:50051",
                "AmpSettings.Environment": "prod",
                "AmpSettings.Namespace": "dingo",
                "AmpSettings.DataLineage": "default",
            },
        )
    payload += tdf_string("ESRC", "local")
    payload += tdf_string("INST", "dingo-1-pc")
    payload += tdf_string("MAID", "local-machine")
    payload += tdf_int("MINR", 0)
    payload += tdf_string("NASP", "cem_ea_id")
    payload += tdf_string("PILD", "skate-2022")
    payload += tdf_int("PLAT", 4)
    payload += tdf_string("RELT", "prod")
    payload += tdf_string("RSRC", "local")
    payload += tdf_string("SVER", "15.1.1.11.2")
    payload.append(0)
    return bytes(payload)


def persona_details_payload():
    payload = bytearray()
    payload += tdf_string("DSNM", "Local Skater")
    payload += tdf_raw_int(0xC29900, LOCAL_PERSONA_ID)
    payload += tdf_int("STAT", 0)
    payload.append(0)
    return bytes(payload)


def login_response_payload():
    payload = bytearray()
    payload += tdf_int("BUID", LOCAL_BLAZE_ID)
    payload += tdf_raw_int(0xD69900, LOCAL_ACCOUNT_ID)
    payload += tdf_int("FRST", 0)
    payload += tdf_raw_int(0x9E5BC0, 1)
    payload += tdf_raw_string(0xAE5E40, "local-session-key")
    payload += tdf_raw_group(0xC24D2C, persona_details_payload())
    payload.append(0)
    return bytes(payload)


def user_identification_payload():
    payload = bytearray()
    payload += tdf_int("BUID", LOCAL_BLAZE_ID)
    payload += tdf_raw_int(0xA64000, LOCAL_BLAZE_ID)
    payload += tdf_string("NAME", "Local Skater")
    payload += tdf_string("NASP", "cem_ea_id")
    payload.append(0)
    return bytes(payload)


def user_session_login_info_payload():
    payload = bytearray()
    payload += tdf_int("BUID", LOCAL_BLAZE_ID)
    payload += tdf_raw_int(0xD69900, LOCAL_ACCOUNT_ID)
    payload += tdf_string("DSNM", "Local Skater")
    payload += tdf_raw_int(0xC29900, LOCAL_PERSONA_ID)
    payload += tdf_string("NASP", "cem_ea_id")
    payload += tdf_int("PLAT", 4)
    payload += tdf_raw_string(0xAE5E40, "local-session-key")
    payload.append(0)
    return bytes(payload)


def notify_user_added_payload():
    payload = bytearray()
    payload += tdf_group("EDAT", b"")
    payload += tdf_group("USER", user_identification_payload())
    payload.append(0)
    return bytes(payload)


def notify_user_authenticated_payload():
    payload = bytearray()
    payload += tdf_group("USER", user_session_login_info_payload())
    payload.append(0)
    return bytes(payload)


def blaze_notifications_for_mode():
    notices = [
        (
            "UserSessions.UserAdded",
            fire2_notification_packet(USERSESSIONS_COMPONENT, 2, notify_user_added_payload()),
        )
    ]
    if "authnotify" in BLAZE_MODE:
        notices.append(
            (
                "UserSessions.UserAuthenticated",
                fire2_notification_packet(USERSESSIONS_COMPONENT, 8, notify_user_authenticated_payload()),
            )
        )
    return notices


def redirector_response():
    body = """<?xml version="1.0" encoding="UTF-8"?>
<serverinstanceinfo>
<address member="0">
<valu>
<hostname>127.0.0.1</hostname>
<ip>2130706433</ip>
<port>44325</port>
</valu>
</address>
<secure>1</secure>
<defaultdnsaddress>0</defaultdnsaddress>
</serverinstanceinfo>
"""
    body_bytes = body.encode("utf-8")
    headers = [
        "HTTP/1.1 200 OK",
        "Content-Type: text/xml",
        "X-BLAZE-COMPONENT: redirector",
        "X-BLAZE-COMMAND: getServerInstance",
        f"Content-Length: {len(body_bytes)}",
        "X-BLAZE-SEQNO: 0",
        "Connection: close",
        "",
        "",
    ]
    return "\r\n".join(headers).encode("ascii") + body_bytes


def ca_certificates_response():
    cert_text = ROOT_CA.read_text(encoding="ascii")
    cert_b64 = "".join(
        line.strip()
        for line in cert_text.splitlines()
        if "BEGIN CERTIFICATE" not in line and "END CERTIFICATE" not in line
    )
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<cacertificate>
<certificatelist>
<certificatelist enc="base64">{cert_b64}</certificatelist>
</certificatelist>
</cacertificate>
"""
    body_bytes = body.encode("ascii")
    headers = [
        "HTTP/1.1 200 OK",
        "Content-Type: text/xml",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
        "",
        "",
    ]
    return "\r\n".join(headers).encode("ascii") + body_bytes


def parse_client_hello(data):
    result = {}
    try:
        if len(data) < 5 or data[0] != 0x16:
            return result
        record_len = int.from_bytes(data[3:5], "big")
        body = data[5 : 5 + record_len]
        if len(body) < 42 or body[0] != 0x01:
            return result
        result["client_version"] = f"0x{body[4]:02x}{body[5]:02x}"
        offset = 4 + 2 + 32
        session_len = body[offset]
        offset += 1 + session_len
        cipher_len = int.from_bytes(body[offset : offset + 2], "big")
        offset += 2 + cipher_len
        comp_len = body[offset]
        offset += 1 + comp_len
        if offset + 2 > len(body):
            return result
        ext_len = int.from_bytes(body[offset : offset + 2], "big")
        offset += 2
        end = min(len(body), offset + ext_len)
        alpn = []
        while offset + 4 <= end:
            ext_type = int.from_bytes(body[offset : offset + 2], "big")
            ext_size = int.from_bytes(body[offset + 2 : offset + 4], "big")
            ext = body[offset + 4 : offset + 4 + ext_size]
            offset += 4 + ext_size
            if ext_type == 0 and len(ext) >= 5:
                list_len = int.from_bytes(ext[0:2], "big")
                pos = 2
                names = []
                while pos + 3 <= min(len(ext), 2 + list_len):
                    name_type = ext[pos]
                    name_len = int.from_bytes(ext[pos + 1 : pos + 3], "big")
                    pos += 3
                    name = ext[pos : pos + name_len]
                    pos += name_len
                    if name_type == 0:
                        names.append(name.decode("ascii", "replace"))
                if names:
                    result["sni"] = ",".join(names)
            elif ext_type == 16 and len(ext) >= 2:
                list_len = int.from_bytes(ext[0:2], "big")
                pos = 2
                while pos + 1 <= min(len(ext), 2 + list_len):
                    size = ext[pos]
                    pos += 1
                    alpn.append(ext[pos : pos + size].decode("ascii", "replace"))
                    pos += size
        if alpn:
            result["alpn"] = ",".join(alpn)
    except Exception as exc:
        result["parse_error"] = repr(exc)
    return result


def main():
    global BLAZE_MODE, CERT_PATH, FORCE_TLS12, KEEP_BLAZE_OPEN, KEY_PATH, LISTEN_HOST, PORT443_CERT_PATH, PORT443_KEY_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--ports", nargs="+", type=int, required=True)
    parser.add_argument("--host", default=LISTEN_HOST, help="Interface to bind TLS listeners to.")
    parser.add_argument("--log", default=str(ROOT / "tls_probe_log.jsonl"))
    parser.add_argument("--tls12", action="store_true", help="Force TLS 1.2 for older ProtoSSL clients.")
    parser.add_argument("--cert", default=str(CERT), help="PEM server certificate or chain.")
    parser.add_argument("--key", default=str(KEY), help="PEM private key for the server certificate.")
    parser.add_argument("--cert443", help="Optional PEM server certificate or chain used only for port 443.")
    parser.add_argument("--key443", help="Optional PEM private key used only for port 443.")
    parser.add_argument("--keep-blaze-open", action="store_true", help="Keep Blaze sockets open across idle recv timeouts.")
    parser.add_argument(
        "--blaze-mode",
        default=BLAZE_MODE,
        choices=[
            "echo16",
            "type1",
            "type1000",
            "type2000",
            "id80000000",
            "fire2_response",
            "fire2_notify",
            "fire2_error",
            "fire2_response_le",
            "fire2_response_id80000000",
            "fire2_preauth_min",
            "fire2_preauth_full",
            "fire2_preauth_full_le",
            "fire2_preauth_min_len24",
            "fire2_preauth_full_len24",
            "fire2_preauth_full_len24_le",
            "fire2_preauth_min_header",
            "fire2_preauth_full_header",
            "fire2_preauth_full_header_type3",
            "fire2_auto_basic",
            "fire2_auto_empty_fetch",
            "fire2_auto_preauth_full",
            "fire2_auto_fetch_noterm",
            "fire2_auto_fetch_string",
            "fire2_auto_full_config",
            "fire2_auto_full_config_usernotify",
            "fire2_auto_full_config_authnotify",
        ],
        help="Experimental empty Fire2 response header variant.",
    )
    ns = parser.parse_args()

    FORCE_TLS12 = ns.tls12
    CERT_PATH = Path(ns.cert)
    KEY_PATH = Path(ns.key)
    PORT443_CERT_PATH = Path(ns.cert443) if ns.cert443 else None
    PORT443_KEY_PATH = Path(ns.key443) if ns.key443 else None
    BLAZE_MODE = ns.blaze_mode
    KEEP_BLAZE_OPEN = ns.keep_blaze_open
    LISTEN_HOST = ns.host
    logger = Logger(ns.log)
    logger.write(
        "config",
        blaze_mode=BLAZE_MODE,
        cert=str(CERT_PATH),
        cert443=str(PORT443_CERT_PATH) if PORT443_CERT_PATH else None,
        host=LISTEN_HOST,
        key=str(KEY_PATH),
        key443=str(PORT443_KEY_PATH) if PORT443_KEY_PATH else None,
        keep_blaze_open=KEEP_BLAZE_OPEN,
        tls12=FORCE_TLS12,
    )
    stop = threading.Event()
    threads = []
    for port in ns.ports:
        thread = threading.Thread(target=serve_port, args=(port, logger, stop), daemon=True)
        thread.start()
        threads.append(thread)
    print(ns.log)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
