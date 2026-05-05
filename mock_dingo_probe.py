import argparse
import gzip
import hashlib
import json
import os
import re
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import h2.connection
import h2.config
import h2.events


LOG_PATH = ROOT / "last_rpc_log.jsonl"
SAVE_SEED_VALUES_PATH = ROOT / "save_seed_values.json"
SAVE_LEARNED_VALUES_PATH = ROOT / "save_learned_values.json"
PROGRESSION_VALUES_PATH = ROOT / "progression_learned_values.json"
EXE = Path(r"C:\skate\Skate 823\Skate\Skate.8-23.dingo-local-http-test.exe")
HOST = "127.0.0.1"
PORT = 50051
TLS_CERT = ROOT / "local_gos_server_chain.pem"
TLS_KEY = ROOT / "local_gos_server_key.pem"
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
CACHE_ROOTS = [
    LOCALAPPDATA / "Skate" / "data" / "cache" / "http" / "0" / "3768241699",
    ROOT / "cache" / "http" / "0" / "3768241699",
]
SMALL_BOARD_DATA_CHUNKS = (
    (
        "6fb1c60f12b12be533c61ea8919989a42d1542a3",
        Path(r"C:\Users\Daddy\Documents\SkateCPT\data\cache\http\0\3768215040\000000000000000b.cache"),
    ),
    (
        "6f10a8cfc6f8e028b6ac1dbf86e2167409953d9d",
        Path(r"C:\Users\Daddy\Documents\SkateCPT\data\cache\http\0\3768215040\0000000000000034.cache"),
    ),
)
SYNTHETIC_STORE_PRICE_CHUNK_ID = "b442780aeaa4e53d72b3a970cce04cc87cb39f19"
SYNTHETIC_STORE_CATEGORY_CHUNK_ID = "93c93a460e0d1f0f018bdbb02c58f8bf5ca9ad7a"
SYNTHETIC_STORE_STOREFRONT_CHUNK_ID = "e5d6fcb0f7e7fd4ae797d0edca3cfb4af73d9d2c"
SYNTHETIC_STORE_INVENTORY_CHUNK_ID = "68db11016f38d0ae8e202f2ad1d72219e2d200a2"
CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID = "1db14f7dba1f130d9470982116c025c8b73092dc"
CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK_ID = "20f5d425f5a7d59a13f84d785ae9163b6a821e46"
CUSTOMIZATION_CATEGORY_SPOOF_CHUNK_ID = "7fae0ad05f6d7e5a2730d21a33c458f12d52b71c"
SYNTHETIC_STORE_PRICE_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\0000000000000006.cache")
SYNTHETIC_STORE_CATEGORY_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\000000000000000e.cache")
SYNTHETIC_STORE_CATEGORY_EXTRA_SOURCES = (
    Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\0000000000000036.cache"),
    Path(r"C:\Users\Daddy\Documents\SkateCPT\data\cache\http\0\3768215040\000000000000002a.cache"),
)
SYNTHETIC_STORE_PREFAB_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\000000000000004e.cache")
SYNTHETIC_STORE_INVENTORY_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\000000000000000a.cache")
SYNTHETIC_STORE_PRICE_RECORD_IDS = (
    "category_alacarte_tops__item_collector_top_adidas_hoodie_gonzPrice",
)
SYNTHETIC_STORE_CATEGORY_RECORD_IDS = (
    "category_alacarte_tops",
    "drop_pool",
)
SYNTHETIC_STORE_STOREFRONT_RECORD_IDS = (
    "FeatureStore_ALaCarteStorefrontCollection",
    "storefront_alacarte_skater",
    "storefront_main",
)
SYNTHETIC_STORE_INVENTORY_RECORD_IDS = (
    "gs-item_collector_top_adidas_hoodie_gonz",
    "hard_currency",
)
CUSTOMIZATION_CATEGORY_RECORD_IDS = (
    "category_skater",
    "category_board",
    "category_cust",
)
UNLOCK_STATIC_RECORD_IDS = (
    "entitlement-inv",
    "level-xp",
    "progression-item",
    "own-create",
    "res",
    "own-sell",
    "own-use",
    "xp-event-update",
    "update-quest",
    "skate-pass-currency-accrue",
    "tier-rewards-xp",
    "drop-table-roll",
    "entitlement",
)
SYNTHETIC_STORE_PRODUCT_ID = "gs-item_collector_top_adidas_hoodie_gonz"
SYNTHETIC_STORE_PRICE_RECORD_ID = "category_alacarte_tops__item_collector_top_adidas_hoodie_gonzPrice"
SYNTHETIC_STORE_CATEGORY_ID = "category_alacarte_tops"
SYNTHETIC_STORE_MAIN_CATEGORY_ID = "drop_pool"
SYNTHETIC_STORE_DROP_POOL_PRICE_RECORD_ID = "drop_pool__item_N1_P01Price"
SYNTHETIC_STORE_PREFAB_RECORD_ID = "store-prefab-storefront_main"
SYNTHETIC_STORE_SKATER_STOREFRONT_ID = "storefront_alacarte_skater"
SYNTHETIC_STORE_COLLECTION_ID = "FeatureStore_ALaCarteStorefrontCollection"
SYNTHETIC_STORE_MAIN_STOREFRONT_ID = "storefront_main"
STORE_CURRENCY_IDS = (
    "CURRENCY_PREMIUM",
    "CURRENCY_MAT_CREATE_01",
    "CURRENCY_MAT_CREATE_02",
    "CURRENCY_MAT_FIND_01",
    "CURRENCY_MAT_FIND_02",
    "CURRENCY_MAT_SHARE_01",
    "CURRENCY_MAT_SHARE_02",
    "grind_secondary",
    "hard_currency",
    "influence",
    "key",
    "loadout_slots",
    "skatepass_currency",
    "soft_currency",
)
STORE_SYNTHETIC_CURRENCY_NAMES = {
    "CURRENCY_PREMIUM": "Taps",
    "CURRENCY_MAT_CREATE_01": "Create Material 1",
    "CURRENCY_MAT_CREATE_02": "Create Material 2",
    "CURRENCY_MAT_FIND_01": "Find Material 1",
    "CURRENCY_MAT_FIND_02": "Find Material 2",
    "CURRENCY_MAT_SHARE_01": "Share Material 1",
    "CURRENCY_MAT_SHARE_02": "Share Material 2",
    "grind_secondary": "Grind Secondary",
    "hard_currency": "San Van Bucks",
    "influence": "Influence",
    "key": "Key",
    "loadout_slots": "Loadout Slots",
    "skatepass_currency": "Tix",
    "soft_currency": "Soft Currency",
}
BOARD_RECORD_CHUNK_ID = "6b75c2e20b901b8a49d1ef08c0523945b61213e3"
OWNABLE_DATA_TYPE = "dingo.services.ownable.data.game.v1.OwnableData"
OWNABLE_DATA_SYSTEM = "ownable_v1"
INVENTORY_ITEM_TYPE = "amp.data.game.inventory.InventoryItem"
INVENTORY_ITEM_SYSTEM = "inventory"
GAMESTORE_PRICING_TYPE = "amp.data.game.gamestore.v1.GamestorePricing"
GAMESTORE_PRICING_SYSTEM = "store_v1"
SORTING_HAT_SYSTEM = "sorting_hat_v1"
SORTING_HAT_CATEGORY_TYPE = "dingo.data.game.sorting_hat.v1.Category"
UNLOCKS_DATA_SYSTEM = "unlocks_v1"
UNLOCKS_DATA_TYPE = "dingo.data.game.unlocks.v1.Unlock"
PRESENTABLES_OWNABLE_SYSTEM = "presentables"
PRESENTABLES_OWNABLE_TYPE = "amp.presentables.common.containers.ownable.v1.PresentablesContainerOwnables"
BOARD_RECORD_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\0000000000000002.cache")
PRESENTABLES_OWNABLE_SOURCE = Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\000000000000004d.cache")
BOARD_RECORD_OWNABLE_IDS = (
    "Own_DeckGraphic_Gen_Popsicle_00001",
    "Own_Truck_Gen_Default_00002",
    "Own_WheelGraphic_Gen_Classic00005",
    "Own_DeckGripColor_Gen_Popsicle_00004",
    "Own_DeckGripCutout_Gen_Popsicle_00001",
    "Own_WheelColor_Gen_Classic_00004",
)
EQUIPPED_COSMETIC_OWNABLE_IDS = (
    "Own_TopJacket_Gen_DenimOversize_00001",
    "Own_BottomPants_Gen_CargoBaggy_00001",
    "Own_ShoeSneaker_Gen_AthleticPuffy_00001",
    "Own_HeadwearHat_Gen_BallCap6Panel_00001",
)
SMOKE_WHITE_COSMETIC_OWNABLE_IDS = (
    "Own_TopCostume_Gen_JacketDemon_00002",
    "Own_BottomPants_Gen_CargoBaggy_00004",
    "Own_ShoeSneaker_Gen_AthleticPuffy_00001",
    "Own_HeadwearHelmet_Gen_HelmetSkateboard_00002",
    "Own_DeckGraphic_Gen_Popsicle_00029",
    "Own_DeckGripColor_Gen_Popsicle_00012",
    "Own_WheelColor_Gen_Classic_00009",
)
BODY_SKIN_SMOKE_OWNABLE_IDS = (
    "Own_CustBody_MEctoAvg_00001",
    "Own_CustBody_MEndoAvg_00001",
    "Own_CustBody_MMesoTall_00001",
    "Own_CustSkinType_Tone_00140",
    "Own_CustSkinType_Tone_00560",
)
LOCAL_BODYTYPE_ITEM_IDS = (
    "items/cust_bodytypes/own_bodytype_character_base",
    "items/cust_bodytypes/own_bodytype01",
    "items/cust_bodytypes/own_bodytype02",
    "items/cust_bodytypes/own_bodytype_anim_base",
    "items/cust_bodytypes/own_bodytype_cas_f",
    "items/cust_bodytypes/own_bodytype_cas_m",
    "items/cust_bodytypes/own_bodytype_cas_u",
)
LOCAL_VOICETYPE_ITEM_IDS = (
    "items/cust_voicetypes/own_voicetype01",
    "items/cust_voicetypes/own_voicetype02",
)
LOCAL_CLOTHING_FIT_ITEM_IDS_BY_CATEGORY = {
    "cust_hats": (
        "items/cust_hats/own_fit_hats_hat1_black",
        "items/cust_hats/own_fit_hats_hat1_blue",
        "items/cust_hats/own_fit_hats_hat1_white",
        "items/cust_hats/own_fit_hats_hat1_red",
    ),
    "cust_tops": (
        "items/cust_tops/own_fit_tops_shirt1_black",
        "items/cust_tops/own_fit_tops_shirt1_blue",
        "items/cust_tops/own_fit_tops_shirt1_white",
        "items/cust_tops/own_fit_tops_shirt1_red",
    ),
    "cust_bottoms": (
        "items/cust_bottoms/own_fit_bottoms_shorts1_black",
        "items/cust_bottoms/own_fit_bottoms_shorts1_blue",
        "items/cust_bottoms/own_fit_bottoms_shorts1_white",
        "items/cust_bottoms/own_fit_bottoms_shorts1_red",
    ),
    "cust_shoes": (
        "items/cust_shoes/own_fit_shoes_shoes1_black",
        "items/cust_shoes/own_fit_shoes_shoes1_blue",
        "items/cust_shoes/own_fit_shoes_shoes1_white",
        "items/cust_shoes/own_fit_shoes_shoes1_red",
    ),
}
LOCAL_CLOTHING_FIT_CATEGORY_ALIASES = {
    "cust_hats": ("cust_hats", "cust_headwear"),
    "cust_tops": ("cust_tops", "cust_top"),
    "cust_bottoms": ("cust_bottoms", "cust_bottom"),
    "cust_shoes": ("cust_shoes", "cust_shoe"),
}
CUSTOMIZATION_LOADOUTS = {
    "baseline": {
        "body": "items/cust_bodytypes/own_bodytype_character_base",
        "body_ownable": "Own_CustBody_MEndoAvg_00001",
        "skin_type": "Own_CustSkinType_Tone_00560",
        "voice_type": "items/cust_voicetypes/own_voicetype02",
        "top": "Own_TopJacket_Gen_DenimOversize_00001",
        "bottom": "Own_BottomPants_Gen_CargoBaggy_00001",
        "shoe": "Own_ShoeSneaker_Gen_AthleticPuffy_00001",
        "headwear": "Own_HeadwearHat_Gen_BallCap6Panel_00001",
        "deck": "Own_DeckGraphic_Gen_Popsicle_00001",
        "grip_color": "Own_DeckGripColor_Gen_Popsicle_00004",
        "grip_cutout": "Own_DeckGripCutout_Gen_Popsicle_00001",
        "truck": "Own_Truck_Gen_Default_00002",
        "wheel_color": "Own_WheelColor_Gen_Classic_00004",
        "wheel_graphic": "Own_WheelGraphic_Gen_Classic00005",
        "asset": "Own_WheelGraphic_Gen_Classic00005",
    },
    "white": {
        "body": "items/cust_bodytypes/own_bodytype_cas_m",
        "body_ownable": "Own_CustBody_MEctoAvg_00001",
        "skin_type": "Own_CustSkinType_Tone_00140",
        "voice_type": "items/cust_voicetypes/own_voicetype01",
        "top": "Own_TopCostume_Gen_JacketDemon_00002",
        "bottom": "Own_BottomPants_Gen_CargoBaggy_00004",
        "shoe": "Own_ShoeSneaker_Gen_AthleticPuffy_00001",
        "headwear": "Own_HeadwearHelmet_Gen_HelmetSkateboard_00002",
        "deck": "Own_DeckGraphic_Gen_Popsicle_00029",
        "grip_color": "Own_DeckGripColor_Gen_Popsicle_00012",
        "grip_cutout": "Own_DeckGripCutout_Gen_Popsicle_00001",
        "truck": "Own_Truck_Gen_Default_00002",
        "wheel_color": "Own_WheelColor_Gen_Classic_00009",
        "wheel_graphic": "Own_WheelGraphic_Gen_Classic00005",
        "asset": "Own_WheelGraphic_Chocolate_Classic_00002",
    },
    "adidas": {
        "body": "items/cust_bodytypes/own_bodytype_cas_f",
        "body_ownable": "Own_CustBody_MMesoTall_00001",
        "skin_type": "Own_CustSkinType_Tone_00560",
        "voice_type": "items/cust_voicetypes/own_voicetype02",
        "top": "Own_TopShirt_Adidas_HoodieRelaxed_00001",
        "bottom": "Own_BottomPants_Adidas_CargoBaggy_00001",
        "shoe": "Own_ShoeSneaker_Adidas_AlohaSuper_00001",
        "headwear": "Own_HeadwearHat_Adidas_BallCap6Panel_00001",
        "deck": "Own_DeckGraphic_Gen_Popsicle_00018",
        "grip_color": "Own_DeckGripColor_Gen_Popsicle_00044",
        "grip_cutout": "Own_DeckGripCutout_Gen_Popsicle_00005",
        "truck": "Own_Truck_Royal_TheRoyal_00003",
        "wheel_color": "Own_WheelColor_Gen_Classic_00002",
        "wheel_graphic": "Own_WheelGraphic_Girl_Classic_00004",
        "asset": "Own_WheelGraphic_Girl_Classic_00004",
    },
}
CUSTOMIZATION_CLIENT_SAVE_KEYS = (
    "Asset",
    "C_gestureslot01",
    "C_gestureslot02",
    "C_gestureslot04",
    "C_morphSetId",
    "SelectedCustomization",
    "Stance",
    "board_bottomart",
    "board_gripcolor",
    "board_gripcolor1",
    "board_grippattern",
    "board_wheelcolor",
    "cust_bottom",
    "cust_headwear",
    "cust_shoe",
    "cust_top",
    "loadout_bottom",
    "loadout_deck_graphic",
    "loadout_grip_color",
    "loadout_grip_cutout",
    "loadout_headwear",
    "loadout_shoe",
    "loadout_top",
    "loadout_trucks",
    "loadout_wheel_color",
    "loadout_wheel_graphic",
    "sb_trucks",
)
CUSTOMIZATION_VISIBLE_KEYS = (
    "SelectedCustomization",
    "cust_top",
    "cust_bottom",
    "cust_shoe",
    "cust_headwear",
    "board_bottomart",
    "board_gripcolor",
    "board_gripcolor1",
    "board_wheelcolor",
    "loadout_top",
    "loadout_bottom",
    "loadout_shoe",
    "loadout_headwear",
    "loadout_deck_graphic",
    "loadout_grip_color",
    "loadout_wheel_color",
    "cust_body",
    "cust_bodytypes",
    "cust_skintype",
    "cust_skintypes",
    "cust_skin",
    "cust_voicetypes",
    "loadout_body",
    "loadout_skin",
    "loadout_skin_type",
    "loadout_voice",
    "C_morphSetId",
    "CharacterMorphSet",
    "MorphEnabled",
    "BodyShaderPresetIndex",
    "VoiceType",
)
COSMETIC_CATEGORY_LIMITS = {
    "DeckGraphic": 18,
    "Truck": 12,
    "WheelGraphic": 12,
    "DeckGripColor": 12,
    "DeckGripCutout": 12,
    "WheelColor": 12,
    "TopShirt": 12,
    "TopJacket": 8,
    "BottomPants": 12,
    "BottomShorts": 8,
    "ShoeSneaker": 12,
    "Sock": 8,
    "HeadwearHat": 10,
    "HeadwearHelmet": 4,
    "EyewearGlasses": 8,
    "OutfitOveralls": 4,
    "CustHairScalp": 8,
    "CustHead": 4,
    "CustBody": 4,
    "CustSkinType": 6,
    "CustEye": 4,
}
COSMETIC_MODE_LIMITS = {
    "board": {},
    "baseline": {},
    "tiny": {
        "DeckGraphic": 2,
        "Truck": 2,
        "WheelGraphic": 2,
        "DeckGripColor": 2,
        "DeckGripCutout": 2,
        "WheelColor": 2,
        "TopShirt": 2,
        "BottomPants": 2,
        "ShoeSneaker": 2,
        "HeadwearHat": 2,
    },
    "board_more": {
        "DeckGraphic": 6,
        "Truck": 4,
        "WheelGraphic": 4,
        "DeckGripColor": 4,
        "DeckGripCutout": 4,
        "WheelColor": 4,
    },
}
INVENTORY_CATEGORY_BY_OWNABLE_CATEGORY = {
    "DeckGraphic": "board_bottomart",
    "Truck": "sb_trucks",
    "WheelGraphic": "board_wheelcolor",
    "DeckGripColor": "board_gripcolor",
    "DeckGripCutout": "board_grippattern",
    "WheelColor": "board_wheelcolor",
    "TopShirt": "cust_top",
    "TopJacket": "cust_top",
    "BottomPants": "cust_bottom",
    "BottomShorts": "cust_bottom",
    "ShoeSneaker": "cust_shoe",
    "Sock": "cust_sock",
    "HeadwearHat": "cust_headwear",
    "HeadwearHelmet": "cust_headwear",
    "EyewearGlasses": "cust_eyewear",
    "OutfitOveralls": "cust_outfit",
    "CustHairScalp": "cust_hair",
    "CustHead": "cust_head",
    "CustBody": "cust_body",
    "CustSkinType": "cust_skintypes",
    "CustEye": "cust_eye",
}
INVENTORY_UI_CATEGORY_ALIASES = {
    # Static category records use the singular catalog keys for item data, but
    # the Customize/Inventory UI also keeps bucket names for the rows it draws.
    "cust_top": ("cust_tops",),
    "cust_bottom": ("cust_bottoms",),
    "cust_headwear": ("cust_hats",),
    "cust_shoe": ("cust_shoes",),
    "cust_body": ("cust_bodytypes",),
    "cust_skintypes": ("cust_skin",),
}
BOARD_RECORD_TERMS = (
    b"board_bottomart",
    b"sb_trucks",
    b"board_wheelcolor",
    b"board_gripcolor",
    b"board_grippattern",
)
OWNABLE_ID_RE = re.compile(rb"Own_[A-Za-z0-9_]+")
OWNABLE_ID_VALID_RE = re.compile(r"^Own_[A-Za-z0-9_]*(?<!\d)\d{5}$")
CACHE_INDEXES = [(root, root / "index.0") for root in CACHE_ROOTS] + [(root, root / "index.1") for root in CACHE_ROOTS]
CACHE_URL_TO_FILE = None


def env_float(name, default):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return float(default)
    try:
        return float(raw)
    except ValueError:
        return float(default)


def env_int(name, default):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return int(default)
    try:
        return int(float(raw))
    except ValueError:
        return int(default)


def env_flag(name, default=True):
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return bool(default)
    return raw in ("1", "true", "on", "yes")


def customization_smoke_variant():
    raw = os.environ.get("SKATE_CUSTOMIZATION_SMOKE_VARIANT", "").strip().lower()
    if not raw:
        return "white" if env_flag("SKATE_CUSTOMIZATION_SMOKE_WHITE", False) else "baseline"
    aliases = {
        "base": "baseline",
        "default": "baseline",
        "control": "baseline",
        "client": "white",
        "client_saved": "white",
        "client-save": "white",
        "smoke": "white",
        "hoodie": "adidas",
        "loud": "adidas",
    }
    variant = aliases.get(raw, raw)
    if variant not in CUSTOMIZATION_LOADOUTS:
        return "white" if env_flag("SKATE_CUSTOMIZATION_SMOKE_WHITE", False) else "baseline"
    return variant


def customization_loadout():
    return dict(CUSTOMIZATION_LOADOUTS[customization_smoke_variant()])


def equipped_cosmetic_ownable_ids():
    loadout = customization_loadout()
    ids = (
        loadout["top"],
        loadout["bottom"],
        loadout["shoe"],
        loadout["headwear"],
        loadout.get("body_ownable", ""),
        loadout.get("skin_type", ""),
        loadout["deck"],
        loadout["grip_color"],
        loadout["grip_cutout"],
        loadout["truck"],
        loadout["wheel_color"],
        loadout["wheel_graphic"],
        loadout["asset"],
    )
    return tuple(dict.fromkeys(ownable_id for ownable_id in ids if ownable_id))


CACHE_DATA_APP_CHUNKS = None
CACHE_BOARD_RECORD_CHUNK = None
CACHE_OWNABLE_IDS = None
CACHE_OWNABLE_ITEM_IDS = None
CACHE_OWNABLE_CATALOG_META = None
CACHE_STORE_INVENTORY_IDS = None
CACHE_OWNABLE_IDS_BY_CHUNK = {}
CACHE_SYNTHETIC_STORE_CHUNKS = None
CACHE_CATEGORY_SPOOF_CHUNK = None
CACHE_LOCK = threading.Lock()
PROFILE_THUMBNAIL_PATH = "/profile8-thumbnail.png"
PROFILE_THUMBNAIL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000100ffff03000006000557bfab0d00000000"
    "49454e44ae426082"
)
ADDRESS_MODES = {
    "http": lambda host, port: f"http://{host}:{port}",
    "https": lambda host, port: f"https://{host}:{port}",
    "bare": lambda host, port: f"{host}:{port}",
    "host": lambda host, port: host,
}

DEFAULT_SERVER_NAMES = [
    "default",
    "amp.services.login.v1",
    "amp.services.inventory",
    "amp.services.entitlements.v1",
    "amp.services.server_discovery",
    "amp.services.gamestore.v1",
    "amp.services.data.game.v1",
    "dingo.services.profile.game.v1",
    "dingo.services.ownable.game.v1",
    "dingo.services.save.game.v1",
    "dingo.services.progression.game.v1",
    "dingo.services.unlocks.game.v1",
    "dingo.services.store.game.v1",
]

VERBOSE_SERVER_NAMES = DEFAULT_SERVER_NAMES + [
    "amp::services::login::v1::LoginService",
    "amp::services::inventory::InventoryService",
    "amp::services::entitlements::v1::EntitlementsService",
    "amp::services::server_discovery::ServerDiscoveryService",
    "amp::services::gamestore::v1::GameStoreService",
    "amp::services::data::game::v1::GameDataService",
    "dingo::services::profile::game::v1::ProfileService",
    "dingo::services::ownable::game::v1::OwnableService",
    "dingo::services::save::game::v1::SaveService",
    "dingo::services::progression::game::v1::ProgressionService",
    "dingo::services::unlocks::game::v1::UnlocksService",
    "dingo::services::store::game::v1::StoreService",
    "amp.services.login.v1.Login",
    "amp.services.inventory.Inventory",
    "amp.services.entitlements.v1.Entitlements",
    "amp.services.server_discovery.ServerDiscovery",
    "amp.services.gamestore.v1.GameStore",
    "amp.services.data.game.v1.GameData",
    "dingo.services.profile.game.v1.Profile",
    "dingo.services.ownable.game.v1.Ownable",
    "dingo.services.save.game.v1.Save",
    "dingo.services.progression.game.v1.Progression",
    "dingo.services.unlocks.game.v1.Unlocks",
    "dingo.services.store.game.v1.Store",
]


def varint(value):
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_varint(raw, offset):
    shift = 0
    value = 0
    while offset < len(raw):
        byte = raw[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            break
    raise ValueError("invalid varint")


def pb_string(field_number, text):
    raw = text.encode("utf-8")
    return pb_key(field_number, 2) + varint(len(raw)) + raw


def pb_bytes(field_number, raw):
    return pb_key(field_number, 2) + varint(len(raw)) + raw


def pb_varint(field_number, value):
    return pb_key(field_number, 0) + varint(value)


def pb_double(field_number, value):
    return pb_key(field_number, 1) + struct.pack("<d", float(value))


def pb_message(field_number, payload):
    return pb_key(field_number, 2) + varint(len(payload)) + payload


def pb_key(field_number, wire_type):
    return varint((field_number << 3) | wire_type)


def grpc_frame(payload, compressed=False):
    return (b"\x01" if compressed else b"\x00") + struct.pack(">I", len(payload)) + payload


def grpc_request_payload(body):
    if len(body) < 5:
        return b""
    payload_len = struct.unpack(">I", body[1:5])[0]
    end = 5 + payload_len
    if end > len(body):
        return b""
    return body[5:end]


def printable_strings(raw, limit=200):
    strings = []
    seen = set()
    for match in re.finditer(rb"[\x20-\x7e]{4,}", raw):
        value = match.group(0).decode("ascii", "replace")
        if value in seen:
            continue
        seen.add(value)
        strings.append(value)
        if len(strings) >= limit:
            break
    return strings


def protobuf_repeated_strings(raw, field_number):
    values = []
    offset = 0
    while offset < len(raw):
        try:
            key, offset = read_varint(raw, offset)
        except ValueError:
            break
        current_field = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            try:
                _, offset = read_varint(raw, offset)
            except ValueError:
                break
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            try:
                size, offset = read_varint(raw, offset)
            except ValueError:
                break
            value = raw[offset : offset + size]
            offset += size
            if current_field == field_number:
                values.append(value.decode("utf-8", "replace"))
        elif wire_type == 5:
            offset += 4
        else:
            break
    return values


def protobuf_string_fields(raw):
    fields = {}
    offset = 0
    while offset < len(raw):
        try:
            key, offset = read_varint(raw, offset)
        except ValueError:
            break
        current_field = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            try:
                _, offset = read_varint(raw, offset)
            except ValueError:
                break
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            try:
                size, offset = read_varint(raw, offset)
            except ValueError:
                break
            end = offset + size
            if end > len(raw):
                break
            value = raw[offset:end]
            offset = end
            fields.setdefault(current_field, []).append(value.decode("utf-8", "replace"))
        elif wire_type == 5:
            offset += 4
        else:
            break
    return fields


def protobuf_messages(raw, field_number):
    messages = []
    offset = 0
    while offset < len(raw):
        try:
            key, offset = read_varint(raw, offset)
        except ValueError:
            break
        current_field = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            try:
                _, offset = read_varint(raw, offset)
            except ValueError:
                break
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            try:
                size, offset = read_varint(raw, offset)
            except ValueError:
                break
            end = offset + size
            if end > len(raw):
                break
            value = raw[offset:end]
            offset = end
            if current_field == field_number:
                messages.append(value)
        elif wire_type == 5:
            offset += 4
        else:
            break
    return messages


def protobuf_first_string(fields, field_number, default=""):
    values = fields.get(field_number) or []
    return values[0] if values else default


def grpc_string_fields(body):
    return protobuf_string_fields(grpc_request_payload(body))


def http1_response(body, content_type="application/json"):
    body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
    headers = [
        "HTTP/1.1 200 OK",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
        "",
        "",
    ]
    return "\r\n".join(headers).encode("ascii") + body_bytes


def cache_url_path(url):
    if "://" not in url:
        return None
    rest = url.split("://", 1)[1]
    slash = rest.find("/")
    if slash < 0:
        return None
    return rest[slash:]


def cache_path_aliases(path):
    aliases = {path}
    chunk_prefixes = [
        "/data-app/chunks/",
        "/data/dingo-amp-prod-gcp-cdn-data-bucket/data-app/chunks/",
        "/cdn/production/",
    ]
    for prefix in chunk_prefixes:
        if path.startswith(prefix):
            chunk_id = path[len(prefix) :]
            if chunk_id:
                aliases.update(prefix + chunk_id for prefix in chunk_prefixes)
            break
    return aliases


def add_cache_mapping(mapping, path, cache_file):
    for alias in cache_path_aliases(path):
        mapping.setdefault(alias, cache_file)
        mapping.setdefault(alias.lower(), cache_file)


def load_cache_url_map():
    mapping = {}
    for root, index in CACHE_INDEXES:
        if not index.exists():
            continue
        data = index.read_bytes()
        for match in re.finditer(rb"https?://[^\x00\r\n]+", data):
            url = match.group(0).decode("latin1", "replace")
            path = cache_url_path(url)
            if not path:
                continue
            context = data[match.start() : match.start() + 320]
            internal = re.search(rb"internalId\x00(.{8})", context, re.S)
            if not internal:
                continue
            cache_id = int.from_bytes(internal.group(1), "little")
            cache_file = root / f"{cache_id:016x}.cache"
            if cache_file.exists():
                add_cache_mapping(mapping, path, cache_file)
    return mapping


def cache_blob_for_request_path(path):
    global CACHE_URL_TO_FILE
    request_path = path.split("?", 1)[0]
    with CACHE_LOCK:
        if CACHE_URL_TO_FILE is None:
            CACHE_URL_TO_FILE = load_cache_url_map()
        cache_file = CACHE_URL_TO_FILE.get(request_path) or CACHE_URL_TO_FILE.get(request_path.lower())
    if not cache_file:
        return None
    return cache_file.read_bytes(), cache_file


def data_app_chunks_from_cache():
    global CACHE_DATA_APP_CHUNKS
    with CACHE_LOCK:
        if CACHE_DATA_APP_CHUNKS is not None:
            return CACHE_DATA_APP_CHUNKS
        for root in CACHE_ROOTS:
            chunks = []
            seen = set()
            for index in (root / "index.0", root / "index.1"):
                if not index.exists():
                    continue
                data = index.read_bytes()
                for match in re.finditer(rb"https?://[^\x00\r\n]+", data):
                    url = match.group(0).decode("latin1", "replace")
                    path = cache_url_path(url)
                    if not path or "/data-app/chunks/" not in path:
                        continue
                    chunk_id = path.rsplit("/", 1)[-1]
                    if not chunk_id or chunk_id.lower() in seen:
                        continue
                    context = data[match.start() : match.start() + 320]
                    internal = re.search(rb"internalId\x00(.{8})", context, re.S)
                    if not internal:
                        continue
                    cache_id = int.from_bytes(internal.group(1), "little")
                    cache_file = root / f"{cache_id:016x}.cache"
                    if cache_file.exists():
                        seen.add(chunk_id.lower())
                        chunks.append((chunk_id, cache_file))
            if chunks:
                CACHE_DATA_APP_CHUNKS = tuple(chunks)
                return CACHE_DATA_APP_CHUNKS
        CACHE_DATA_APP_CHUNKS = tuple()
        return CACHE_DATA_APP_CHUNKS


def manifest_chunk_priority(chunk):
    chunk_id, chunk_source = chunk
    try:
        body = chunk_body_bytes(chunk_source)
    except OSError:
        return (50, chunk_id)
    record_ids = cache_record_ids(body, limit=64)
    record_text = " ".join(record_ids)
    if any(record_id.startswith("category_") for record_id in record_ids):
        return (0, chunk_id)
    if any(token in record_text for token in ("board_", "cust_", "skater", "sorting_hat")):
        return (1, chunk_id)
    if any(token in record_text for token in ("entitlement", "level-", "progression", "unlock", "drop-table")):
        return (20, chunk_id)
    return (10, chunk_id)


def stable_manifest_chunks(chunks):
    if not env_flag("SKATE_STABLE_LOCAL_CACHE_MANIFEST", True):
        return tuple(chunks)
    ordered = sorted(chunks, key=manifest_chunk_priority)
    max_chunks = env_int("SKATE_LOCAL_CACHE_MANIFEST_MAX_CHUNKS", 128)
    if max_chunks > 0:
        ordered = ordered[:max_chunks]
    return tuple(ordered)


def length_prefixed_cache_records(raw):
    offset = 0
    while offset < len(raw):
        record_len, body_offset = read_varint(raw, offset)
        end = body_offset + record_len
        if end > len(raw):
            return
        yield raw[offset:end], raw[body_offset:end]
        offset = end


def cache_record(body):
    return varint(len(body)) + body


def protobuf_fields(raw):
    offset = 0
    while offset < len(raw):
        try:
            field_start = offset
            key, offset = read_varint(raw, offset)
        except ValueError:
            return
        field_number = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            try:
                value, offset = read_varint(raw, offset)
            except ValueError:
                return
            yield field_start, field_number, wire_type, value, b""
        elif wire_type == 1:
            value = raw[offset : offset + 8]
            offset += 8
            yield field_start, field_number, wire_type, None, value
        elif wire_type == 2:
            try:
                size, offset = read_varint(raw, offset)
            except ValueError:
                return
            value = raw[offset : offset + size]
            offset += size
            yield field_start, field_number, wire_type, size, value
        elif wire_type == 5:
            value = raw[offset : offset + 4]
            offset += 4
            yield field_start, field_number, wire_type, None, value
        else:
            return


def catalog_item_ids_by_ownable():
    global CACHE_OWNABLE_ITEM_IDS
    with CACHE_LOCK:
        if CACHE_OWNABLE_ITEM_IDS is not None:
            return CACHE_OWNABLE_ITEM_IDS
    item_ids = {
        ownable_id: meta["item_id"]
        for ownable_id, meta in catalog_metadata_by_ownable().items()
        if meta.get("item_id")
    }
    with CACHE_LOCK:
        CACHE_OWNABLE_ITEM_IDS = item_ids
    return item_ids


def catalog_metadata_by_ownable():
    global CACHE_OWNABLE_CATALOG_META
    with CACHE_LOCK:
        if CACHE_OWNABLE_CATALOG_META is not None:
            return CACHE_OWNABLE_CATALOG_META
    item_ids = {}
    for root in CACHE_ROOTS:
        if not root.exists():
            continue
        for cache_file in root.glob("*.cache"):
            try:
                raw = cache_file.read_bytes()
                for _, body in length_prefixed_cache_records(raw):
                    ownable_id = None
                    meta = {}
                    for _, field_number, wire_type, _, value in protobuf_fields(body):
                        if field_number == 1 and wire_type == 2:
                            try:
                                candidate = value.decode("utf-8")
                            except UnicodeDecodeError:
                                continue
                            if is_valid_ownable_id(candidate):
                                ownable_id = candidate
                        elif field_number == 6 and wire_type == 2:
                            for _, nested_field, nested_wire, nested_value, nested_raw in protobuf_fields(value):
                                if nested_field == 5 and nested_wire == 2:
                                    try:
                                        meta["category"] = nested_raw.decode("utf-8")
                                    except UnicodeDecodeError:
                                        pass
                                elif nested_field == 9 and nested_wire == 0:
                                    meta["stack_hash"] = str(nested_value)
                                elif nested_field == 11 and nested_wire == 0:
                                    meta["item_id"] = str(nested_value & 0xFFFFFFFF)
                        if ownable_id and meta.get("item_id"):
                            item_ids.setdefault(ownable_id, meta)
                            break
            except (OSError, ValueError):
                continue
    with CACHE_LOCK:
        CACHE_OWNABLE_CATALOG_META = item_ids
    return item_ids


def curated_board_record_chunk():
    global CACHE_BOARD_RECORD_CHUNK
    with CACHE_LOCK:
        if CACHE_BOARD_RECORD_CHUNK is not None:
            return CACHE_BOARD_RECORD_CHUNK
        if not BOARD_RECORD_SOURCE.exists():
            CACHE_BOARD_RECORD_CHUNK = b""
            return CACHE_BOARD_RECORD_CHUNK
        wanted = {ownable_id.encode("utf-8"): False for ownable_id in BOARD_RECORD_OWNABLE_IDS}
        selected = []
        try:
            raw = BOARD_RECORD_SOURCE.read_bytes()
            for framed_record, record_body in length_prefixed_cache_records(raw):
                hits = [needle for needle, found in wanted.items() if not found and needle in record_body]
                if not hits:
                    continue
                selected.append(framed_record)
                for needle in hits:
                    wanted[needle] = True
                if all(wanted.values()):
                    break
        except (OSError, ValueError):
            selected = []
        if all(wanted.values()) and selected:
            CACHE_BOARD_RECORD_CHUNK = b"".join(selected)
        else:
            CACHE_BOARD_RECORD_CHUNK = b""
        return CACHE_BOARD_RECORD_CHUNK


def filtered_cache_records(source, wanted_ids):
    wanted = set(wanted_ids)
    selected = []
    try:
        raw = source.read_bytes()
        for framed_record, record_body in length_prefixed_cache_records(raw):
            record_id = None
            for _, field_number, wire_type, _, value in protobuf_fields(record_body):
                if field_number != 1 or wire_type != 2:
                    continue
                try:
                    record_id = value.decode("utf-8")
                except UnicodeDecodeError:
                    record_id = None
                break
            if record_id in wanted:
                selected.append(framed_record)
                wanted.remove(record_id)
                if not wanted:
                    break
    except (OSError, ValueError):
        return b""
    return b"".join(selected)


def filtered_cache_records_containing_ids(source, wanted_ids):
    wanted = {item_id.encode("utf-8"): item_id for item_id in wanted_ids}
    selected = []
    try:
        raw = source.read_bytes()
        for framed_record, record_body in length_prefixed_cache_records(raw):
            hits = [item_id for needle, item_id in wanted.items() if needle in record_body]
            if not hits:
                continue
            selected.append(framed_record)
            for item_id in hits:
                wanted.pop(item_id.encode("utf-8"), None)
            if not wanted:
                break
    except (OSError, ValueError):
        return b""
    return b"".join(selected)


def append_missing_cache_records(body, sources, wanted_ids):
    missing = set(wanted_ids) - set(cache_record_ids(body, limit=2048))
    if not missing:
        return body
    selected = [body]
    for source in sources:
        extra = filtered_cache_records(source, missing)
        if not extra:
            continue
        selected.append(extra)
        missing -= set(cache_record_ids(extra, limit=2048))
        if not missing:
            break
    return b"".join(selected)


def rewrite_top_level_varint_field(raw, target_field, new_value):
    out = bytearray()
    offset = 0
    changed = False
    while offset < len(raw):
        field_start = offset
        key, offset = read_varint(raw, offset)
        field_number = key >> 3
        wire_type = key & 7
        out += raw[field_start:offset]
        if wire_type == 0:
            value_start = offset
            _, offset = read_varint(raw, offset)
            if field_number == target_field:
                out += varint(new_value)
                changed = True
            else:
                out += raw[value_start:offset]
        elif wire_type == 1:
            out += raw[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            size_start = offset
            size, offset = read_varint(raw, offset)
            end = offset + size
            out += raw[size_start:end]
            offset = end
        elif wire_type == 5:
            out += raw[offset : offset + 4]
            offset += 4
        else:
            return raw
    return bytes(out) if changed else raw


def patched_customization_category_body():
    global CACHE_CATEGORY_SPOOF_CHUNK
    with CACHE_LOCK:
        if CACHE_CATEGORY_SPOOF_CHUNK is not None:
            return CACHE_CATEGORY_SPOOF_CHUNK
    category_source = None
    for chunk_id, chunk_source in data_app_chunks_from_cache():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        if is_customization_category_chunk(body):
            category_source = chunk_source
            break
    if category_source is None:
        return b""
    try:
        raw = chunk_body_bytes(category_source)
    except OSError:
        return b""
    selected = []
    try:
        for _, record_body in length_prefixed_cache_records(raw):
            record_id = None
            for _, field_number, wire_type, _, value in protobuf_fields(record_body):
                if field_number == 1 and wire_type == 2:
                    try:
                        record_id = value.decode("utf-8")
                    except UnicodeDecodeError:
                        record_id = None
                    break
            if record_id == "category_skater":
                record_body = rewrite_top_level_varint_field(record_body, 2, 2)
            selected.append(cache_record(record_body))
    except ValueError:
        return b""
    body = b"".join(selected)
    with CACHE_LOCK:
        CACHE_CATEGORY_SPOOF_CHUNK = body
    return body


def customization_category_spoof_chunks():
    if not env_flag("SKATE_SPOOF_SKATER_CATEGORY_AS_BOARD", False):
        return tuple()
    body = patched_customization_category_body()
    if not body:
        return tuple()
    return ((CUSTOMIZATION_CATEGORY_SPOOF_CHUNK_ID, body),)


def synthetic_store_price_records():
    if env_flag("SKATE_SYNTHETIC_STORE_DROP_POOL_BOX", True):
        return filtered_cache_records(SYNTHETIC_STORE_PRICE_SOURCE, (SYNTHETIC_STORE_DROP_POOL_PRICE_RECORD_ID,))
    if not env_flag("SKATE_SYNTHETIC_STORE_PREMIUM_PRICE", True):
        return filtered_cache_records(SYNTHETIC_STORE_PRICE_SOURCE, SYNTHETIC_STORE_PRICE_RECORD_IDS)
    currency_id = os.environ.get("SKATE_SYNTHETIC_STORE_PRICE_CURRENCY", "CURRENCY_PREMIUM").strip() or "CURRENCY_PREMIUM"
    amount = env_float("SKATE_SYNTHETIC_STORE_PRICE_AMOUNT", 0.0)
    price_data = (
        pb_varint(1, 0)
        + pb_message(2, pb_message(1, pb_string(1, "res") + pb_string(2, currency_id) + pb_double(3, amount)))
    )
    presentation = (
        pb_string(2, "Gonz Skate Head Hoodie")
        + pb_string(41, "cdn:/437f71f00ddbf05884eadc95048217486e6fbfef")
        + pb_varint(42, 0)
        + pb_string(43, "DEFAULT")
        + pb_string(44, "MEDIUM")
        + pb_varint(45, 343487741)
    )
    body = (
        pb_string(1, SYNTHETIC_STORE_PRICE_RECORD_ID)
        + pb_string(2, SYNTHETIC_STORE_PRODUCT_ID)
        + pb_varint(3, 0)
        + pb_message(4, price_data)
        + pb_message(10, presentation)
    )
    return cache_record(body)


def synthetic_store_category_records():
    if not env_flag("SKATE_SYNTHETIC_STORE_MINIMAL_CATEGORY", True):
        return filtered_cache_records(SYNTHETIC_STORE_CATEGORY_SOURCE, SYNTHETIC_STORE_CATEGORY_RECORD_IDS)

    def category_record(category_id, storefront_id, title, sort_index, image, price_record_id=None):
        category_meta = (
            pb_string(1, title)
            + pb_varint(2, sort_index)
            + pb_string(3, "TYPE_DEFAULT")
            + pb_string(4, image)
        )
        category = (
            pb_string(1, category_id)
            + pb_string(2, storefront_id)
            + pb_string(3, price_record_id or SYNTHETIC_STORE_PRICE_RECORD_ID)
            + pb_message(4, category_meta)
        )
        return cache_record(category)

    if env_flag("SKATE_SYNTHETIC_STORE_DROP_POOL_BOX", True):
        return category_record(
            SYNTHETIC_STORE_MAIN_CATEGORY_ID,
            SYNTHETIC_STORE_MAIN_STOREFRONT_ID,
            "Product Boxes",
            700,
            "cdn:/3dbd19487a021528d90e706b414c6331",
            SYNTHETIC_STORE_DROP_POOL_PRICE_RECORD_ID,
        )

    return b"".join(
        (
            category_record(
                SYNTHETIC_STORE_CATEGORY_ID,
                SYNTHETIC_STORE_SKATER_STOREFRONT_ID,
                "Top Essentials",
                1010,
                "cdn:/008d8beb303fa00d3f4cb4c473618fb8",
            ),
            category_record(
                SYNTHETIC_STORE_MAIN_CATEGORY_ID,
                SYNTHETIC_STORE_MAIN_STOREFRONT_ID,
                "Featured",
                1,
                "cdn:/a752d3ae62286908d807d72500eff62d",
            ),
        )
    )


def synthetic_store_sorting_hat_records():
    if env_flag("SKATE_SYNTHETIC_STORE_DROP_POOL_BOX", True):
        storefront = filtered_cache_records(
            SYNTHETIC_STORE_CATEGORY_EXTRA_SOURCES[0],
            (SYNTHETIC_STORE_MAIN_STOREFRONT_ID,),
        )
        prefab = filtered_cache_records(SYNTHETIC_STORE_PREFAB_SOURCE, (SYNTHETIC_STORE_PREFAB_RECORD_ID,))
        return storefront + prefab
    if not env_flag("SKATE_SYNTHETIC_STORE_MINIMAL_STOREFRONT", True):
        body = filtered_cache_records(SYNTHETIC_STORE_CATEGORY_SOURCE, SYNTHETIC_STORE_STOREFRONT_RECORD_IDS)
        return append_missing_cache_records(body, SYNTHETIC_STORE_CATEGORY_EXTRA_SOURCES, SYNTHETIC_STORE_STOREFRONT_RECORD_IDS)
    collection_meta = (
        pb_string(1, "ESSENTIALS")
        + pb_varint(2, 1)
        + pb_string(3, "TYPE_STOREFRONT_COLLECTIONS")
        + pb_string(4, "cdn:/6b538de161fe2bbe7eecad5656adab7b")
    )
    collection = (
        pb_string(1, SYNTHETIC_STORE_COLLECTION_ID)
        + pb_string(2, SYNTHETIC_STORE_MAIN_STOREFRONT_ID)
        + pb_message(4, collection_meta)
        + pb_string(5, SYNTHETIC_STORE_SKATER_STOREFRONT_ID)
    )
    main_card = (
        pb_string(1, "Ready To Use Items")
        + pb_string(2, "Ready To Use Items")
        + pb_string(3, "cdn:/a752d3ae62286908d807d72500eff62d")
        + pb_string(4, "#FFFFFF")
    )
    main = pb_string(1, SYNTHETIC_STORE_MAIN_STOREFRONT_ID) + pb_varint(5, 0) + pb_message(6, main_card)
    skater_card = pb_string(1, "Skater Essentials") + pb_string(3, "cdn:/4da79faf6c0692f91670c51737c97f9e")
    skater = pb_string(1, SYNTHETIC_STORE_SKATER_STOREFRONT_ID) + pb_varint(5, 0) + pb_message(6, skater_card)
    return b"".join(cache_record(record) for record in (collection, main, skater))


def synthetic_inventory_static_record(item_id, display_name=None, category="res"):
    presentation = (
        pb_string(1, "")
        + pb_string(2, display_name or STORE_SYNTHETIC_CURRENCY_NAMES.get(item_id, item_id))
        + pb_string(11, "")
    )
    body = (
        pb_string(1, item_id)
        + pb_string(3, category)
        + pb_message(4, presentation)
        + pb_string(7, "")
        + pb_varint(9, 0)
        + pb_varint(11, 0)
    )
    return cache_record(body)


def synthetic_store_inventory_static_records():
    if not env_flag("SKATE_SYNTHETIC_STORE_CURRENCY_STATIC", True):
        return b""
    record_ids = set()
    body = bytearray()
    try:
        source = SYNTHETIC_STORE_INVENTORY_SOURCE.read_bytes()
        for _, record_body in length_prefixed_cache_records(source):
            for _, field_number, wire_type, _, value in protobuf_fields(record_body):
                if field_number != 1 or wire_type != 2:
                    continue
                try:
                    record_ids.add(value.decode("utf-8"))
                except UnicodeDecodeError:
                    pass
                break
    except (OSError, ValueError):
        pass
    for item_id in STORE_CURRENCY_IDS:
        if item_id in record_ids:
            continue
        body += synthetic_inventory_static_record(item_id)
    return bytes(body)


def synthetic_store_chunks():
    global CACHE_SYNTHETIC_STORE_CHUNKS
    if not env_flag("SKATE_SYNTHETIC_STORE_CHUNKS", False):
        return tuple()
    with CACHE_LOCK:
        if CACHE_SYNTHETIC_STORE_CHUNKS is not None:
            return CACHE_SYNTHETIC_STORE_CHUNKS
    chunks = []
    price_body = synthetic_store_price_records()
    if price_body:
        chunks.append(synthetic_store_chunk_tuple(SYNTHETIC_STORE_PRICE_CHUNK_ID, price_body))
    category_body = synthetic_store_category_records()
    if category_body:
        chunks.append(synthetic_store_chunk_tuple(SYNTHETIC_STORE_CATEGORY_CHUNK_ID, category_body))
    storefront_body = synthetic_store_sorting_hat_records()
    if storefront_body:
        chunks.append(synthetic_store_chunk_tuple(SYNTHETIC_STORE_STOREFRONT_CHUNK_ID, storefront_body))
    inventory_body = filtered_cache_records(SYNTHETIC_STORE_INVENTORY_SOURCE, SYNTHETIC_STORE_INVENTORY_RECORD_IDS)
    inventory_body += synthetic_store_inventory_static_records()
    if env_flag("SKATE_SYNTHETIC_STORE_COLOCATE_STORE_V1_WITH_INVENTORY", False):
        # Diagnostic path: the client currently requests the inventory static
        # chunk, but not the advertised store_v1 chunks. Put the store_v1
        # records first so this fetched chunk is typed as store_v1 while still
        # advertising the inventory asset ids that make the client request it.
        inventory_body = price_body + category_body + inventory_body
    if inventory_body:
        chunks.append(synthetic_store_chunk_tuple(SYNTHETIC_STORE_INVENTORY_CHUNK_ID, inventory_body))
    with CACHE_LOCK:
        CACHE_SYNTHETIC_STORE_CHUNKS = tuple(chunks)
        return CACHE_SYNTHETIC_STORE_CHUNKS


def customization_inventory_static_chunks():
    if not env_flag("SKATE_CUSTOMIZATION_INVENTORY_STATIC_CHUNK", False):
        return tuple()
    if env_flag("SKATE_CUSTOMIZATION_INVENTORY_STATIC_ALL_COSMETICS", False):
        wanted_ids = cosmetic_ownable_ids()
    else:
        wanted_ids = tuple(dict.fromkeys(BOARD_RECORD_OWNABLE_IDS + equipped_cosmetic_ownable_ids()))
    extra_spec = os.environ.get("SKATE_CUSTOMIZATION_INVENTORY_STATIC_IDS", "").strip()
    if extra_spec:
        wanted_ids += tuple(part.strip() for part in extra_spec.split(",") if part.strip())
    missing = set(wanted_ids)
    selected = []
    sources = []
    if BOARD_RECORD_SOURCE.exists():
        sources.append(BOARD_RECORD_SOURCE)
    sources.extend(cache_file for _, cache_file in SMALL_BOARD_DATA_CHUNKS if cache_file.exists())
    for root in CACHE_ROOTS:
        if root.exists():
            sources.extend(sorted(root.glob("*.cache")))
    seen_sources = set()
    for source in sources:
        source_key = str(source).lower()
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        if env_flag("SKATE_CUSTOMIZATION_INVENTORY_STATIC_CONTAINS_FILTER", False):
            extra = filtered_cache_records_containing_ids(source, missing)
        else:
            extra = filtered_cache_records(source, missing)
        if not extra:
            continue
        selected.append(extra)
        found = set(cache_record_ids(extra, limit=4096))
        found.update(ownable_ids_in_bytes(extra))
        missing -= found
        if not missing:
            break
    if not selected:
        return tuple()
    return ((CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID, b"".join(selected)),)


def board_data_chunks_for_response():
    chunks = stable_manifest_chunks(data_app_chunks_from_cache())
    category_spoof_chunks = customization_category_spoof_chunks()
    if category_spoof_chunks:
        filtered_chunks = []
        spoof_ids = {CUSTOMIZATION_CATEGORY_SPOOF_CHUNK_ID}
        for chunk_id, chunk_source in chunks:
            try:
                body = chunk_body_bytes(chunk_source)
            except OSError:
                filtered_chunks.append((chunk_id, chunk_source))
                continue
            if is_customization_category_chunk(body):
                continue
            filtered_chunks.append((chunk_id, chunk_source))
        chunks = tuple(filtered_chunks)
    extra_chunks = (
        category_spoof_chunks
        + customization_inventory_static_chunks()
        + customization_presentables_static_chunks()
        + synthetic_store_chunks()
    )
    if chunks:
        return tuple(chunks) + extra_chunks
    if BOARD_RECORD_SOURCE.exists():
        return ((BOARD_RECORD_CHUNK_ID, BOARD_RECORD_SOURCE),) + extra_chunks
    chunks = tuple((chunk_id, cache_file) for chunk_id, cache_file in SMALL_BOARD_DATA_CHUNKS if cache_file.exists())
    if chunks:
        return chunks + extra_chunks
    return extra_chunks


def chunk_body_bytes(source):
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    return source.read_bytes()


def is_valid_ownable_id(value):
    if not isinstance(value, str):
        return False
    return 8 <= len(value) <= 96 and OWNABLE_ID_VALID_RE.match(value) is not None


def ownable_ids_in_bytes(body):
    ids = set()
    for match in OWNABLE_ID_RE.finditer(body):
        ownable_id = match.group(0).decode("ascii", "ignore")
        if is_valid_ownable_id(ownable_id):
            ids.add(ownable_id)
    return sorted(ids)


def ownable_ids_for_chunk(chunk_id, body):
    cache_key = chunk_id or hashlib.sha1(body).hexdigest()
    with CACHE_LOCK:
        cached = CACHE_OWNABLE_IDS_BY_CHUNK.get(cache_key)
        if cached is not None:
            return cached
    ids = tuple(ownable_ids_in_bytes(body))
    with CACHE_LOCK:
        CACHE_OWNABLE_IDS_BY_CHUNK[cache_key] = ids
    return ids


def cache_record_ids(body, limit=512):
    ids = []
    seen = set()
    try:
        records = length_prefixed_cache_records(body)
        for _, record_body in records:
            for _, field_number, wire_type, _, value in protobuf_fields(record_body):
                if field_number != 1 or wire_type != 2:
                    continue
                try:
                    record_id = value.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not record_id or record_id in seen:
                    continue
                seen.add(record_id)
                ids.append(record_id)
                break
            if len(ids) >= limit:
                break
    except ValueError:
        return tuple(ids)
    return tuple(ids)


def cache_record_string_values(body, limit=None):
    if limit is None:
        limit = int(env_float("SKATE_STORE_MANIFEST_LINKED_LIMIT", 16))
    values = []
    seen = set()
    try:
        records = length_prefixed_cache_records(body)
        for _, record_body in records:
            for _, _, wire_type, _, value in protobuf_fields(record_body):
                if wire_type != 2:
                    continue
                try:
                    text = value.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not text or text in seen:
                    continue
                if len(text) > 160:
                    continue
                if any(ord(ch) < 32 or ord(ch) >= 127 for ch in text):
                    continue
                if not any(
                    token in text
                    for token in (
                        "gs-",
                        "category_",
                        "storefront_",
                        "store-prefab",
                        "hard_currency",
                        "soft_currency",
                        "skatepass_currency",
                        "grind_secondary",
                    )
                ):
                    continue
                seen.add(text)
                values.append(text)
                if len(values) >= limit:
                    return tuple(values)
    except ValueError:
        return tuple(values)
    return tuple(values)


def manifest_asset_ids_for_chunk(system, body, record_asset_ids, chunk_id=None):
    if system == OWNABLE_DATA_SYSTEM:
        pinned_chunk_id = os.environ.get("SKATE_MANIFEST_OWNABLE_ASSET_CHUNK_ID", "").strip().lower()
        current_chunk_id = (chunk_id or hashlib.sha1(body).hexdigest()).lower()
        if pinned_chunk_id and pinned_chunk_id != current_chunk_id:
            return tuple()
        # Keep the default ownable manifest conservative. Advertising the
        # broader cosmetic set here changes boot ordering and can stop
        # Inventory/Ownable/Save-load from firing. Leave the broader manifest
        # as an explicit diagnostic mode.
        if os.environ.get("SKATE_MANIFEST_ALL_COSMETICS", "0").strip() not in ("", "0", "false", "off", "no"):
            return tuple(dict.fromkeys(BOARD_RECORD_OWNABLE_IDS + cosmetic_ownable_ids()))
        if os.environ.get("SKATE_MANIFEST_EQUIPPED_COSMETICS", "1").strip().lower() in ("", "1", "true", "on", "yes"):
            return tuple(dict.fromkeys(BOARD_RECORD_OWNABLE_IDS + equipped_cosmetic_ownable_ids()))
        return BOARD_RECORD_OWNABLE_IDS
    if env_flag("SKATE_STORE_MANIFEST_ALL_STRINGS", False) and system in (
        GAMESTORE_PRICING_SYSTEM,
        SORTING_HAT_SYSTEM,
        INVENTORY_ITEM_SYSTEM,
    ):
        return tuple(dict.fromkeys(tuple(record_asset_ids) + cache_record_string_values(body)))
    return record_asset_ids


def experimental_store_chunk_allowed(chunk_id):
    spec = os.environ.get("SKATE_STORE_CHUNK_ALLOWLIST", "").strip()
    if not spec:
        return True
    allowed = {part.strip().lower() for part in spec.split(",") if part.strip()}
    return (chunk_id or "").lower() in allowed


def synthetic_store_manifest_allowed(chunk_id):
    if not env_flag("SKATE_SYNTHETIC_STORE_MANIFEST", False) and not env_flag("SKATE_SYNTHETIC_STORE_DYNAMIC_CHUNK_IDS", False):
        return False
    if not env_flag("SKATE_SYNTHETIC_STORE_CHUNKS", False):
        return False
    with CACHE_LOCK:
        cached = CACHE_SYNTHETIC_STORE_CHUNKS
    if cached is None:
        synthetic_ids = {
            SYNTHETIC_STORE_PRICE_CHUNK_ID.lower(),
            SYNTHETIC_STORE_CATEGORY_CHUNK_ID.lower(),
            SYNTHETIC_STORE_STOREFRONT_CHUNK_ID.lower(),
            SYNTHETIC_STORE_INVENTORY_CHUNK_ID.lower(),
        }
    else:
        synthetic_ids = {cached_chunk_id.lower() for cached_chunk_id, _ in cached}
    chunk_id_l = (chunk_id or "").lower()
    if chunk_id_l not in synthetic_ids:
        return False
    if env_flag("SKATE_SYNTHETIC_STORE_DYNAMIC_CHUNK_IDS", False):
        return True
    return experimental_store_chunk_allowed(chunk_id)


def synthetic_store_chunk_id(default_id, body):
    if env_flag("SKATE_SYNTHETIC_STORE_DYNAMIC_CHUNK_IDS", False):
        salt = os.environ.get("SKATE_SYNTHETIC_STORE_CHUNK_ID_SALT", "").encode("utf-8")
        return hashlib.sha1(salt + body).hexdigest()
    return default_id


def synthetic_store_chunk_tuple(default_id, body):
    return synthetic_store_chunk_id(default_id, body), body


def is_customization_category_chunk(body):
    record_ids = set(cache_record_ids(body, limit=32))
    return bool(record_ids.intersection(CUSTOMIZATION_CATEGORY_RECORD_IDS))


def is_unlock_static_chunk(body):
    record_ids = set(cache_record_ids(body, limit=32))
    return bool(record_ids.intersection(UNLOCK_STATIC_RECORD_IDS))


def customization_category_chunk_ids():
    ids = []
    for chunk_id, chunk_source in board_data_chunks_for_response():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        if is_customization_category_chunk(body):
            ids.append(chunk_id)
    return tuple(ids)


def unlock_static_chunk_ids():
    ids = []
    for chunk_id, chunk_source in board_data_chunks_for_response():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        if is_unlock_static_chunk(body):
            ids.append(chunk_id)
    return tuple(ids)


def customization_ownable_chunk_ids():
    wanted = {ownable_id.encode("utf-8") for ownable_id in cosmetic_ownable_ids()}
    ids = []
    for chunk_id, chunk_source in board_data_chunks_for_response():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        record_ids = {record_id.encode("utf-8") for record_id in cache_record_ids(body, limit=4096)}
        if record_ids.intersection(wanted):
            ids.append(chunk_id)
    return tuple(ids)


def presentables_ownable_ids(body, limit=8192):
    ids = []
    seen = set()
    try:
        records = length_prefixed_cache_records(body)
        for _, record_body in records:
            for _, field_number, wire_type, _, entry_body in protobuf_fields(record_body):
                if field_number != 1 or wire_type != 2:
                    continue
                for _, entry_field, entry_wire, _, value in protobuf_fields(entry_body):
                    if entry_field != 5 or entry_wire != 2:
                        continue
                    try:
                        ownable_id = value.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    if not is_valid_ownable_id(ownable_id) or ownable_id in seen:
                        continue
                    seen.add(ownable_id)
                    ids.append(ownable_id)
                    if len(ids) >= limit:
                        return tuple(ids)
    except ValueError:
        return tuple(ids)
    return tuple(ids)


def filtered_presentables_ownable_records(source, wanted_ids):
    wanted = set(wanted_ids)
    try:
        data = Path(source).read_bytes()
    except OSError:
        return b""
    records = list(length_prefixed_cache_records(data))
    if not records:
        return b""
    selected = bytearray()
    for _, record_body in records:
        for _, field_number, wire_type, _, entry_body in protobuf_fields(record_body):
            if field_number != 1 or wire_type != 2:
                continue
            ownable_id = None
            for _, entry_field, entry_wire, _, value in protobuf_fields(entry_body):
                if entry_field != 5 or entry_wire != 2:
                    continue
                try:
                    candidate = value.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if candidate in wanted:
                    ownable_id = candidate
                    break
            if ownable_id:
                selected += pb_message(1, entry_body)
    if not selected:
        return b""
    return cache_record(bytes(selected))


def customization_presentables_static_chunks():
    if not env_flag("SKATE_CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK", False):
        return tuple()
    if env_flag("SKATE_CUSTOMIZATION_PRESENTABLES_STATIC_ALL_COSMETICS", False):
        wanted_ids = cosmetic_ownable_ids()
    else:
        wanted_ids = tuple(dict.fromkeys(equipped_cosmetic_ownable_ids()))
    body = filtered_presentables_ownable_records(PRESENTABLES_OWNABLE_SOURCE, wanted_ids)
    if not body:
        return tuple()
    return ((CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK_ID, body),)


def is_presentables_ownables_chunk(body):
    ids = set(presentables_ownable_ids(body))
    if not ids:
        return False
    wanted = set(cosmetic_ownable_ids())
    return len(ids.intersection(wanted)) >= 3


def presentables_ownable_chunk_ids():
    ids = []
    for chunk_id, chunk_source in board_data_chunks_for_response():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        if is_presentables_ownables_chunk(body):
            ids.append(chunk_id)
    return tuple(ids)


def is_inventory_static_chunk(body):
    if not env_flag("SKATE_BROAD_INVENTORY_STATIC_MANIFEST", False):
        return False
    category_hits = sum(
        1
        for token in (
            b"cust_top",
            b"cust_bottom",
            b"cust_shoe",
            b"cust_headwear",
            b"board_bottomart",
            b"board_gripcolor",
            b"board_wheelcolor",
        )
        if token in body
    )
    return category_hits >= 2 and (b"Own_" in body or b"own_" in body)


def inventory_static_asset_ids(body):
    record_ids = cache_record_ids(body, limit=4096)
    record_id_set = set(record_ids)
    ids = []
    for ownable_id in BOARD_RECORD_OWNABLE_IDS + cosmetic_ownable_ids():
        if ownable_id in record_id_set or ownable_id.encode("utf-8") in body:
            ids.append(ownable_id)
    limit = int(env_float("SKATE_INVENTORY_STATIC_MANIFEST_LIMIT", 512))
    for record_id in record_ids:
        if len(ids) >= limit:
            break
        ids.append(record_id)
    return tuple(dict.fromkeys(ids))


def chunk_manifest_type(body, chunk_id=None):
    synthetic_manifest = synthetic_store_manifest_allowed(chunk_id)
    if not env_flag("SKATE_EXPERIMENTAL_STORE_MANIFEST", False) and not synthetic_manifest:
        if (
            env_flag("SKATE_CUSTOMIZATION_INVENTORY_STATIC_CHUNK", False)
            and (chunk_id or "").lower() == CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID
        ):
            if env_flag("SKATE_CUSTOMIZATION_STATIC_AS_OWNABLE", False):
                return OWNABLE_DATA_SYSTEM, OWNABLE_DATA_TYPE, inventory_static_asset_ids(body)
            return INVENTORY_ITEM_SYSTEM, INVENTORY_ITEM_TYPE, inventory_static_asset_ids(body)
        if (
            env_flag("SKATE_CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK", False)
            and (chunk_id or "").lower() == CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK_ID
        ):
            return PRESENTABLES_OWNABLE_SYSTEM, PRESENTABLES_OWNABLE_TYPE, presentables_ownable_ids(body)
        if env_flag("SKATE_PRESENTABLES_OWNABLE_MANIFEST", False) and is_presentables_ownables_chunk(body):
            system = os.environ.get("SKATE_PRESENTABLES_OWNABLE_SYSTEM", PRESENTABLES_OWNABLE_SYSTEM).strip() or PRESENTABLES_OWNABLE_SYSTEM
            return system, PRESENTABLES_OWNABLE_TYPE, presentables_ownable_ids(body)
        if env_flag("SKATE_CUSTOMIZATION_CATEGORY_MANIFEST", True) and is_customization_category_chunk(body):
            return SORTING_HAT_SYSTEM, SORTING_HAT_CATEGORY_TYPE, cache_record_ids(body)
        if env_flag("SKATE_UNLOCKS_STATIC_MANIFEST", True) and is_unlock_static_chunk(body):
            return UNLOCKS_DATA_SYSTEM, UNLOCKS_DATA_TYPE, cache_record_ids(body)
        if is_inventory_static_chunk(body):
            return INVENTORY_ITEM_SYSTEM, INVENTORY_ITEM_TYPE, inventory_static_asset_ids(body)
        return OWNABLE_DATA_SYSTEM, OWNABLE_DATA_TYPE, tuple()
    if not synthetic_manifest and not experimental_store_chunk_allowed(chunk_id):
        return OWNABLE_DATA_SYSTEM, OWNABLE_DATA_TYPE, tuple()
    record_ids = cache_record_ids(body, limit=16)
    price_ids = sum(1 for record_id in record_ids if record_id.endswith("Price"))
    if price_ids:
        return GAMESTORE_PRICING_SYSTEM, GAMESTORE_PRICING_TYPE, cache_record_ids(body)
    if (
        any(record_id.startswith(("store-prefab", "storefront_")) for record_id in record_ids)
        or b"Ready To Use Items" in body
    ):
        sorting_hat_type = os.environ.get("SKATE_SORTING_HAT_CONTAINER_TYPE", SORTING_HAT_SYSTEM).strip() or SORTING_HAT_SYSTEM
        return SORTING_HAT_SYSTEM, sorting_hat_type, cache_record_ids(body)
    if (
        b"storefront_" in body
        or any(record_id.startswith(("category_", "drop_pool", "ftue_pool")) for record_id in record_ids)
        or any(record_id.startswith(("Bundles_", "Bundle_", "random_skater", "random_board", "welcome_offers", "currency_offers", "free_currency_offers")) for record_id in record_ids)
    ):
        return GAMESTORE_PRICING_SYSTEM, GAMESTORE_PRICING_TYPE, cache_record_ids(body)
    if (
        b"own-create" in body
        or b"gs-item" in body
        or any(record_id in ("hard_currency", "soft_currency", "skatepass_currency") for record_id in record_ids)
        or any(record_id.startswith(("gs-", "sp__")) for record_id in record_ids)
    ):
        return INVENTORY_ITEM_SYSTEM, INVENTORY_ITEM_TYPE, cache_record_ids(body)
    return OWNABLE_DATA_SYSTEM, OWNABLE_DATA_TYPE, tuple()


def catalog_ownable_ids():
    global CACHE_OWNABLE_IDS
    with CACHE_LOCK:
        if CACHE_OWNABLE_IDS is not None:
            return CACHE_OWNABLE_IDS

    ids = set(BOARD_RECORD_OWNABLE_IDS)
    for _, chunk_source in data_app_chunks_from_cache():
        try:
            ids.update(ownable_ids_in_bytes(chunk_body_bytes(chunk_source)))
        except OSError:
            continue
    for root in CACHE_ROOTS:
        if not root.exists():
            continue
        for cache_file in root.glob("*.cache"):
            try:
                ids.update(ownable_ids_in_bytes(cache_file.read_bytes()))
            except OSError:
                continue

    ordered = tuple(sorted(ownable_id for ownable_id in ids if is_valid_ownable_id(ownable_id)))
    with CACHE_LOCK:
        CACHE_OWNABLE_IDS = ordered
    return ordered


def ownable_category(ownable_id):
    parts = ownable_id.split("_")
    return parts[1] if len(parts) > 2 else ""


def cosmetic_category_limits():
    mode = os.environ.get("SKATE_COSMETIC_MODE", "tiny").strip().lower()
    if mode == "all":
        return None
    if mode in COSMETIC_MODE_LIMITS:
        return dict(COSMETIC_MODE_LIMITS[mode])
    if mode == "curated":
        return dict(COSMETIC_CATEGORY_LIMITS)

    limits = dict(COSMETIC_CATEGORY_LIMITS)
    spec = os.environ.get("SKATE_COSMETIC_LIMITS", "").strip()
    if not spec:
        return limits
    parsed = {}
    for part in spec.split(","):
        if "=" not in part:
            continue
        category, value = part.split("=", 1)
        category = category.strip()
        try:
            parsed[category] = max(0, int(value.strip()))
        except ValueError:
            continue
    return parsed or limits


def cosmetic_ownable_ids():
    selected = []
    seen = set()
    required_ids = BOARD_RECORD_OWNABLE_IDS + equipped_cosmetic_ownable_ids()
    if env_flag("SKATE_CUSTOMIZATION_SMOKE_WHITE", False):
        required_ids += SMOKE_WHITE_COSMETIC_OWNABLE_IDS
    if env_flag("SKATE_BODY_SKIN_SMOKE", False):
        required_ids += BODY_SKIN_SMOKE_OWNABLE_IDS
    for ownable_id in required_ids:
        if ownable_id not in seen:
            selected.append(ownable_id)
            seen.add(ownable_id)

    limits = cosmetic_category_limits()
    if limits is None:
        for ownable_id in catalog_ownable_ids():
            if ownable_id not in seen:
                selected.append(ownable_id)
                seen.add(ownable_id)
        max_count = int(env_float("SKATE_COSMETIC_MAX_COUNT", 0.0))
        return tuple(selected[:max_count] if max_count > 0 else selected)
    counts = {category: 0 for category in limits}
    for ownable_id in catalog_ownable_ids():
        if ownable_id in seen:
            continue
        category = ownable_category(ownable_id)
        limit = limits.get(category)
        if not limit or counts[category] >= limit:
            continue
        selected.append(ownable_id)
        seen.add(ownable_id)
        counts[category] += 1
    max_count = int(env_float("SKATE_COSMETIC_MAX_COUNT", 0.0))
    return tuple(selected[:max_count] if max_count > 0 else selected)


def local_director_config():
    endpoint = f"http://{HOST}:{PORT}" if PORT != 80 else f"http://{HOST}"
    keys = [
        "eadp.nexus.connect.grpc.v1",
        "eadp.eaid.grpc.model",
        "eadp.identity",
        "eadp.identity.proxy",
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
    config = {key: endpoint for key in keys}
    config.update(
        {
            "eadp.auth.account": endpoint,
            "eadp.authentication.useJwtToken": "false",
            "eadp.instrumentation.enabled": "false",
            "eadp.networkReachability.primaryEndpoint": HOST,
            "eadp.networkReachability.secondaryEndpoint": HOST,
            "AmpSettings.Endpoint": endpoint,
            "AmpSettings.Environment": "prod",
            "AmpSettings.Namespace": "dingo",
            "AmpSettings.DataLineage": "default",
            "DingoOnline.BlazeServiceNameOverride": "dingo-1-$platform$",
            "DingoOnline.ClientAutoLoginEnabled": "true",
            "DingoOnline.CdnBaseUrl": endpoint + "/cdn/production",
            "DingoOnline.Events.Enabled": "true",
            "DingoOnline.ProfileLoadoutId": "profile8",
            "DingoOnline.Skatepass.Enabled": "true",
        }
    )
    return json.dumps({"serverConfig": config}, separators=(",", ":"))


def delimited_setting(message):
    return varint(len(message)) + message


def setting_string(name, value):
    return delimited_setting(pb_string(1, name) + pb_varint(2, 0) + pb_string(3, value) + pb_varint(7, 1))


def setting_bool(name, value):
    return delimited_setting(pb_string(1, name) + pb_varint(2, 2) + pb_varint(5, 1 if value else 0) + pb_varint(7, 1))


def local_dingo_settings_config():
    # The game settings accessor consumes this as a stream of length-delimited
    # setting records, not as JSON. Start from a known-good cached config and
    # append local overrides for the pieces our emulator needs.
    cache_candidates = [
        Path(r"C:\Users\Daddy\AppData\Local\Skate\data\cache\http\0\3768241699\0000000000000013.cache"),
        Path(r"C:\Users\Daddy\AppData\Local\Skate.backup_before_823_20260503_162800\data\cache\http\0\3768241699\0000000000000013.cache"),
    ]
    body = b""
    for candidate in cache_candidates:
        if candidate.exists():
            body = candidate.read_bytes()
            break
    if not body:
        body = b""
    endpoint = f"http://{HOST}:{PORT}" if PORT != 80 else f"http://{HOST}"
    overrides = b"".join(
        [
            setting_bool("DingoOnline.ClientAutoLoginEnabled", True),
            setting_bool("DingoOnline.Events.Enabled", True),
            setting_string("DingoOnline.CdnBaseUrl", endpoint + "/cdn/production"),
            setting_string("DingoOnline.ProfileLoadoutId", "profile8"),
            setting_bool("DingoOnline.Skatepass.Enabled", True),
            setting_string("AmpSettings.Endpoint", endpoint),
            setting_string("AmpSettings.Environment", "prod"),
            setting_string("AmpSettings.Namespace", "dingo"),
            setting_string("AmpSettings.DataLineage", "default"),
            setting_string("eadp.auth.account", endpoint),
            setting_string("amp.services.inventory", endpoint),
            setting_string("amp.services.server_discovery", endpoint),
            setting_string("amp.services.gamestore.v1", endpoint),
            setting_string("amp.services.data.game.v1", endpoint),
            setting_string("dingo.services.profile.game.v1", endpoint),
            setting_string("dingo.services.ownable.game.v1", endpoint),
            setting_string("dingo.services.save.game.v1", endpoint),
            setting_string("dingo.services.progression.game.v1", endpoint),
            setting_string("dingo.services.unlocks.game.v1", endpoint),
            setting_string("dingo.services.store.game.v1", endpoint),
        ]
    )
    return body + overrides


def get_servers_response(address, names):
    payload = bytearray()
    for name in names:
        server = pb_string(1, name) + pb_string(2, address)
        payload += pb_message(1, server)
    return bytes(payload)


def data_lineage_message(lineage, namespace="dingo", language="en"):
    # amp.services.data.common.DataLineage: 2=lineage, 3=namespace, 4=language.
    return pb_string(2, lineage) + pb_string(3, namespace) + pb_string(4, language)


def get_lineages_response():
    lineages = [
        ("default", "", "en"),
        ("default", "dingo", "en"),
        ("default", "dingo", "en-US"),
        ("commonGameData", "dingo", "en"),
        ("gameData", "dingo", "en"),
    ]
    payload = bytearray()
    for lineage, namespace, language in lineages:
        payload += pb_message(1, data_lineage_message(lineage, namespace, language))
    return bytes(payload)


def login_response():
    # amp.services.login.v1.LoginResponse. Static inspection of the client
    # shows the early scalar fields as eId/accessToken/refreshToken/expiresAt
    # and username, which is enough for the caller to cache a local session.
    return (
        pb_string(1, "profile8")
        + pb_string(2, "local-access-token")
        + pb_string(3, "local-refresh-token")
        + pb_varint(4, 4102444800)
        + pb_string(6, "Local Skater")
    )


def login_response_with_logging(logger=None, stream_id=None, path=None):
    payload = login_response()
    if logger:
        logger.write(
            "login_response",
            stream=stream_id,
            path=path,
            eId="profile8",
            username="Local Skater",
            payload_len=len(payload),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="login_response")
    return payload


def profile_user(e_id, title_id="profile8"):
    # GetProfilesResponse.users[]:
    #   1=eId, 2=name, 3=level, 4=titleId, 5=storage metadata, 6=followers.
    # Field 5's metadata map is where the profile cache looks for "thumbnail".
    return (
        pb_string(1, e_id)
        + pb_string(2, "Local Skater")
        + pb_double(3, rep_level_value())
        + pb_string(4, title_id)
        + pb_message(5, profile_storage_metadata(e_id))
        + pb_varint(6, 0)
    )


def profile_response(logger=None, stream_id=None, path=None, request_body=b""):
    # The client can ask for either the login eId or the cached loadout id.
    # Returning both keeps profile lookup and loadout lookup consistent.
    users = [
        profile_user("profile8", "profile8"),
        profile_user("local-user", "profile8"),
    ]
    payload = b"".join(pb_message(1, user) for user in users)
    if logger:
        requested = protobuf_repeated_strings(grpc_request_payload(request_body), 1)
        logger.write(
            "profile_response",
            stream=stream_id,
            path=path,
            requested=requested,
            returned=["profile8", "local-user"],
            level=rep_level_value(),
            payload_len=len(payload),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="profile_response")
    return payload


def log_bootstrap_request(logger, stream_id, path, request_body, headers):
    if not logger:
        return
    payload = grpc_request_payload(request_body)
    if "ServerDiscovery/getServers" in path:
        logger.write(
            "server_discovery_request",
            stream=stream_id,
            path=path,
            authority=headers.get(":authority", ""),
            scheme=headers.get(":scheme", ""),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="server_discovery_request")
        return
    if "Login/" in path:
        logger.write(
            "login_request",
            stream=stream_id,
            path=path,
            strings=printable_strings(payload, limit=40),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="login_request")
        return
    if "GameData/getDataChunks" in path or "GameData/getDataChunk" in path:
        requested = requested_game_data_chunk_ids(request_body)
        logger.write(
            "game_data_chunks_request",
            stream=stream_id,
            path=path,
            requested=list(requested),
            requested_count=len(requested),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="game_data_chunks_request")
        return
    if "GameData/getData" in path:
        logger.write(
            "game_data_request",
            stream=stream_id,
            path=path,
            strings=printable_strings(payload, limit=40),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="game_data_request")
        return
    if "Profile/getProfiles" in path or "Profile/getCompactProfiles" in path:
        logger.write(
            "profile_request",
            stream=stream_id,
            path=path,
            requested=protobuf_repeated_strings(payload, 1),
            strings=printable_strings(payload, limit=40),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="profile_request")
        return
    if "Progression/getGameEvent" in path or "Progression/getGameEvents" in path:
        events = progression_request_events(request_body)
        logger.write(
            "progression_get_request",
            stream=stream_id,
            path=path,
            requested_count=len(events),
            requested=[{"event": event_name, "component": component_id} for event_name, component_id in events[:40]],
            body_len=len(request_body),
        )
        return
    if "Inventory/getAllInventoryItems" in path:
        logger.write("inventory_request", stream=stream_id, path=path, body_len=len(request_body))
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="inventory_request")
        return
    if "Ownable/getOwnableInstances" in path:
        logger.write("ownables_request", stream=stream_id, path=path, body_len=len(request_body))
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="ownables_request")
        return
    if "LevelRewards/getUserLevels" in path:
        logger.write("level_rewards_request", stream=stream_id, path=path, body_len=len(request_body))
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="level_rewards_request")
        return
    if "Save/load" in path or "Save/loadUser" in path or "Save/save" in path:
        fields = protobuf_string_fields(payload)
        if "Save/loadUser" in path:
            e_id = protobuf_first_string(fields, 1)
            key = protobuf_first_string(fields, 2)
        else:
            e_id = ""
            key = protobuf_first_string(fields, 1)
        logger.write(
            "save_request",
            stream=stream_id,
            path=path,
            key=key,
            eId=e_id,
            strings=printable_strings(payload, limit=40),
            body_len=len(request_body),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="save_request")


def storage_common_value(url, body, content_type):
    return (
        pb_string(1, url)
        + pb_string(2, hashlib.md5(body).hexdigest())
        + pb_string(3, content_type)
        + pb_varint(4, len(body))
    )


def storage_metadata_entry(key, value):
    return pb_string(1, key) + pb_message(2, value)


def profile_storage_metadata(owner_id="profile8"):
    thumbnail = storage_metadata_entry(
        "thumbnail",
        storage_common_value(
            f"http://{HOST}{PROFILE_THUMBNAIL_PATH}",
            PROFILE_THUMBNAIL_PNG,
            "image/png",
        ),
    )
    return (
        pb_string(1, f"{owner_id}-storage")
        + pb_string(2, owner_id)
        + pb_message(14, thumbnail)
    )


def ownable_instance(ownable_id):
    # OwnableInstanceData fields, per 8-23 client parse/print functions:
    #   1=eId, 2=instanceId, 3=ownableId, 4=isNew, 5=dynamicData.
    instance_id = "local-instance-" + ownable_id
    # eId is the owner entity, not a per-item id. Using synthetic per-ownable
    # eIds makes the client receive rows that do not belong to profile8.
    e_id = "profile8"
    return (
        pb_string(1, e_id)
        + pb_string(2, instance_id)
        + pb_string(3, ownable_id)
        + pb_varint(4, 0)
        + pb_string(5, "{}")
    )


def ownables_response(logger=None, stream_id=None, path=None):
    ownable_ids = cosmetic_ownable_ids()
    payload = bytearray()
    for ownable_id in ownable_ids:
        payload += pb_message(1, ownable_instance(ownable_id))
    response = bytes(payload)
    if logger:
        category_counts = {}
        for ownable_id in ownable_ids:
            category = ownable_category(ownable_id)
            category_counts[category] = category_counts.get(category, 0) + 1
        logger.write(
            "ownables_response",
            stream=stream_id,
            path=path,
            count=len(ownable_ids),
            category_counts=category_counts,
            payload_len=len(response),
            sample=list(ownable_ids[:12]),
        )
    return response


def inventory_item_data(ownable_id, item_id=None, category=None, balance=1.0, max_balance=1.0):
    # amp.services.inventory.InventoryItemData, per the 8-23 generated parser:
    #   1=category, 2=id, 3=balance, 4=growth, 5=max, 6=eId,
    #   7=growthMax, 8=min, 9=growthMin, 10=overflow.
    #
    # Cosmetics static data points at inventory-gated ownables, so publish each
    # selected Own_* id as a single-count inventory balance.
    category = category or INVENTORY_CATEGORY_BY_OWNABLE_CATEGORY.get(
        ownable_category(ownable_id),
        ownable_category(ownable_id) or "inventory",
    )
    inventory_id = item_id or ownable_id
    return (
        pb_string(1, category)
        + pb_string(2, inventory_id)
        + pb_double(3, balance)
        + pb_double(5, max_balance)
        + pb_string(6, "profile8")
    )


def inventory_item_data_with_ui_aliases(ownable_id, item_id=None, category=None, balance=1.0, max_balance=1.0):
    primary_category = category or INVENTORY_CATEGORY_BY_OWNABLE_CATEGORY.get(
        ownable_category(ownable_id),
        ownable_category(ownable_id) or "inventory",
    )
    rows = [
        inventory_item_data(
            ownable_id,
            item_id=item_id,
            category=primary_category,
            balance=balance,
            max_balance=max_balance,
        )
    ]
    if env_flag("SKATE_INVENTORY_UI_CATEGORY_ALIASES", False):
        for alias in INVENTORY_UI_CATEGORY_ALIASES.get(primary_category, ()):
            rows.append(
                inventory_item_data(
                    ownable_id,
                    item_id=item_id,
                    category=alias,
                    balance=balance,
                    max_balance=max_balance,
                )
            )
    return tuple(rows)


def customization_gate_inventory_items(ownable_id, meta):
    # Diagnostic only. Broad duplicate gate rows caused the client to skip the
    # rest of the boot inventory/ownable/level/save burst, so keep this opt-in.
    if not env_flag("SKATE_INVENTORY_INCLUDE_CUSTOMIZATION_GATE_CATEGORIES", False):
        return tuple()
    categories = tuple(
        dict.fromkeys(
            part.strip()
            for part in os.environ.get(
                "SKATE_INVENTORY_CUSTOMIZATION_GATE_CATEGORIES",
                "progression-item,unlock",
            ).split(",")
            if part.strip()
        )
    )
    ids = []
    item_id = meta.get("item_id")
    if item_id:
        ids.append(item_id)
    ids.append(ownable_id)
    stack_hash = meta.get("stack_hash")
    if stack_hash and env_flag("SKATE_INVENTORY_CUSTOMIZATION_GATE_INCLUDE_STACK", False):
        ids.append(stack_hash)
    rows = []
    for inventory_id in dict.fromkeys(i for i in ids if i):
        for category in categories:
            rows.append(inventory_item_data(ownable_id, item_id=inventory_id, category=category))
    return tuple(rows)


def store_currency_inventory_items():
    if not env_flag("SKATE_INVENTORY_INCLUDE_STORE_CURRENCIES", True):
        return tuple()
    balance = env_float("SKATE_INVENTORY_STORE_CURRENCY_BALANCE", 100000.0)
    return tuple(
        inventory_item_data(currency_id, item_id=currency_id, category="res", balance=balance, max_balance=balance)
        for currency_id in STORE_CURRENCY_IDS
    )


def store_product_inventory_items():
    if not env_flag("SKATE_INVENTORY_INCLUDE_STORE_PRODUCTS", False):
        return tuple()
    rows = []
    for item_id in store_inventory_item_ids():
        rows.append(inventory_item_data(item_id, item_id=item_id, category="gs-item"))
    return tuple(rows)


def local_bodytype_inventory_items():
    if not env_flag("SKATE_BODYTYPE_LOCAL_ITEMS", False):
        return tuple()
    rows = []
    for item_id in LOCAL_BODYTYPE_ITEM_IDS:
        bare_id = item_id.rsplit("/", 1)[-1]
        for category in ("cust_bodytypes", "cust_body"):
            rows.append(inventory_item_data(item_id, item_id=item_id, category=category))
            rows.append(inventory_item_data(item_id, item_id=bare_id, category=category))
    for item_id in LOCAL_VOICETYPE_ITEM_IDS:
        bare_id = item_id.rsplit("/", 1)[-1]
        rows.append(inventory_item_data(item_id, item_id=item_id, category="cust_voicetypes"))
        rows.append(inventory_item_data(item_id, item_id=bare_id, category="cust_voicetypes"))
    return tuple(rows)


def local_clothing_fit_inventory_items():
    if not env_flag("SKATE_CLOTHING_LOCAL_FIT_ITEMS", False):
        return tuple()
    rows = []
    for family, item_ids in LOCAL_CLOTHING_FIT_ITEM_IDS_BY_CATEGORY.items():
        categories = LOCAL_CLOTHING_FIT_CATEGORY_ALIASES.get(family, (family,))
        for item_id in item_ids:
            bare_id = item_id.rsplit("/", 1)[-1]
            for category in categories:
                rows.append(inventory_item_data(item_id, item_id=item_id, category=category))
                rows.append(inventory_item_data(item_id, item_id=bare_id, category=category))
    return tuple(rows)


def store_inventory_item_ids():
    global CACHE_STORE_INVENTORY_IDS
    with CACHE_LOCK:
        if CACHE_STORE_INVENTORY_IDS is not None:
            return CACHE_STORE_INVENTORY_IDS
    ids = []
    seen = set()
    for item_id in ("hard_currency", "soft_currency", "skatepass_currency"):
        ids.append(item_id)
        seen.add(item_id)
    token_re = re.compile(rb"(?:gs-item|[A-Za-z0-9_]+Price)[A-Za-z0-9_]*")
    for root in CACHE_ROOTS:
        if not root.exists():
            continue
        for cache_file in root.glob("*.cache"):
            try:
                raw = cache_file.read_bytes()
            except OSError:
                continue
            if b"storefront_" not in raw and b"gs-item" not in raw and b"Price" not in raw:
                continue
            for token in token_re.findall(raw):
                try:
                    item_id = token.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if item_id in seen:
                    continue
                seen.add(item_id)
                ids.append(item_id)
    limit = int(env_float("SKATE_STORE_INVENTORY_LIMIT", 240))
    with CACHE_LOCK:
        CACHE_STORE_INVENTORY_IDS = tuple(ids[: max(0, limit)])
        return CACHE_STORE_INVENTORY_IDS


def inventory_items_response(logger=None, stream_id=None, path=None):
    mode = os.environ.get("SKATE_INVENTORY_MODE", "tiny").strip().lower()
    if mode in ("", "empty", "off", "none"):
        if logger:
            logger.write("inventory_response", stream=stream_id, path=path, count=0, payload_len=0)
        return b""
    ownable_ids = cosmetic_ownable_ids()
    catalog_meta = catalog_metadata_by_ownable()
    catalog_item_ids = catalog_item_ids_by_ownable()
    payload = bytearray()
    missing_item_ids = []
    customization_gate_row_count = 0
    customization_gate_ownable_count = 0
    ui_alias_row_count = 0
    customization_gate_limit = int(env_float("SKATE_INVENTORY_CUSTOMIZATION_GATE_LIMIT", 10.0))
    store_currency_items = store_currency_inventory_items()
    for item in store_currency_items:
        payload += pb_message(1, item)
    store_product_items = store_product_inventory_items()
    for item in store_product_items:
        payload += pb_message(1, item)
    local_bodytype_items = local_bodytype_inventory_items()
    for item in local_bodytype_items:
        payload += pb_message(1, item)
    local_clothing_fit_items = local_clothing_fit_inventory_items()
    for item in local_clothing_fit_items:
        payload += pb_message(1, item)
    for ownable_id in ownable_ids:
        meta = catalog_meta.get(ownable_id, {})
        item_id = meta.get("item_id")
        if item_id is None:
            missing_item_ids.append(ownable_id)
            item_id = ownable_id
        item_rows = inventory_item_data_with_ui_aliases(ownable_id, item_id=item_id, category=meta.get("category"))
        ui_alias_row_count += max(0, len(item_rows) - 1)
        for item in item_rows:
            payload += pb_message(1, item)
        if customization_gate_limit <= 0 or customization_gate_ownable_count < customization_gate_limit:
            gate_items = customization_gate_inventory_items(ownable_id, meta)
        else:
            gate_items = tuple()
        if gate_items:
            customization_gate_ownable_count += 1
        customization_gate_row_count += len(gate_items)
        for item in gate_items:
            payload += pb_message(1, item)
        if item_id != ownable_id and os.environ.get("SKATE_INVENTORY_INCLUDE_OWNABLE_IDS", "1").strip() != "0":
            item_rows = inventory_item_data_with_ui_aliases(ownable_id, item_id=ownable_id, category=meta.get("category"))
            ui_alias_row_count += max(0, len(item_rows) - 1)
            for item in item_rows:
                payload += pb_message(1, item)
        stack_hash = meta.get("stack_hash")
        if stack_hash and stack_hash not in (item_id, ownable_id) and os.environ.get("SKATE_INVENTORY_INCLUDE_STACK_HASH", "1").strip() != "0":
            item_rows = inventory_item_data_with_ui_aliases(ownable_id, item_id=stack_hash, category=meta.get("category"))
            ui_alias_row_count += max(0, len(item_rows) - 1)
            for item in item_rows:
                payload += pb_message(1, item)
    response = bytes(payload)
    if logger:
        category_counts = {}
        for ownable_id in ownable_ids:
            category = ownable_category(ownable_id)
            category_counts[category] = category_counts.get(category, 0) + 1
        logger.write(
            "inventory_response",
            stream=stream_id,
            path=path,
            count=len(ownable_ids),
            customization_gate_row_count=customization_gate_row_count,
            customization_gate_ownable_count=customization_gate_ownable_count,
            ui_alias_row_count=ui_alias_row_count,
            store_currency_count=len(store_currency_items),
            store_currency_ids=list(STORE_CURRENCY_IDS),
            store_currency_balance=env_float("SKATE_INVENTORY_STORE_CURRENCY_BALANCE", 100000.0),
            store_product_item_count=len(store_product_items),
            local_bodytype_item_count=len(local_bodytype_items),
            local_bodytype_ids=list(LOCAL_BODYTYPE_ITEM_IDS),
            local_clothing_fit_item_count=len(local_clothing_fit_items),
            local_clothing_fit_families={
                family: list(item_ids)
                for family, item_ids in LOCAL_CLOTHING_FIT_ITEM_IDS_BY_CATEGORY.items()
            },
            mode=mode,
            category_counts=category_counts,
            payload_len=len(response),
            sample=list(ownable_ids[:12]),
            catalog_item_id_sample={ownable_id: catalog_item_ids.get(ownable_id) for ownable_id in ownable_ids[:12]},
            catalog_category_sample={ownable_id: (catalog_meta.get(ownable_id) or {}).get("category") for ownable_id in ownable_ids[:12]},
            missing_item_ids=missing_item_ids[:12],
        )
    return response


def entitlement_purchase_names():
    names = []
    catalog_meta = catalog_metadata_by_ownable()
    for ownable_id in cosmetic_ownable_ids():
        names.append(ownable_id)
        meta = catalog_meta.get(ownable_id, {})
        item_id = meta.get("item_id")
        if item_id:
            names.append(item_id)
        stack_hash = meta.get("stack_hash")
        if stack_hash:
            names.append(stack_hash)
        names.append("entitlement-inv:" + ownable_id)
        names.append("own-use:" + ownable_id)
        names.append("own-sell:" + ownable_id)
    for item_id in store_inventory_item_ids():
        if item_id.startswith(("gs-item", "sp__", "entitlement", "own-")):
            names.append(item_id)
    return tuple(dict.fromkeys(name for name in names if name))


def entitlement_entry(purchase_name):
    # The executable exposes amp.services.entitlements.v1 plus strings for
    # purchaseName/entitlementSource/entitlementTag/entitlementType/entitlementId.
    # Keep this diagnostic broad: unknown fields are harmless, and the client can
    # accept whichever identifier style it actually checks.
    return (
        pb_string(1, purchase_name)
        + pb_string(2, "LOCAL")
        + pb_string(3, purchase_name)
        + pb_string(4, "DEFAULT")
        + pb_string(5, purchase_name)
        + pb_varint(6, 1)
        + pb_varint(7, 1)
    )


def entitlements_response(logger=None, stream_id=None, path=None):
    if not env_flag("SKATE_ENTITLEMENTS_SERVICE_ENABLED", True):
        if logger:
            logger.write("entitlements_response", stream=stream_id, path=path, count=0, payload_len=0)
        return b""
    payload = bytearray()
    purchase_names = entitlement_purchase_names()
    for purchase_name in purchase_names:
        payload += pb_message(1, entitlement_entry(purchase_name))
    response = bytes(payload)
    if logger:
        logger.write(
            "entitlements_response",
            stream=stream_id,
            path=path,
            count=len(purchase_names),
            payload_len=len(response),
            sample=list(purchase_names[:16]),
        )
    return response


def rep_level_value():
    return env_float("SKATE_REP_LEVEL", 25.0)


def rep_xp_balance_value():
    base_xp = env_float("SKATE_REP_XP_BALANCE", 25000.0)
    with PROGRESSION_LOCK:
        passive_xp_events = sum(1 for key in PROGRESSION_VALUES if key.startswith("passivexp_"))
    return base_xp + (passive_xp_events * env_float("SKATE_PASSIVE_XP_VALUE", 250.0))


def level_reward_level_value(level_type):
    if level_type == "main_level":
        return rep_level_value()
    return env_float("SKATE_LEVEL_REWARDS_UNLOCK_LEVEL", max(rep_level_value(), 100.0))


def level_reward_xp_balance_value(level_type):
    if level_type == "main_level":
        return rep_xp_balance_value()
    return env_float("SKATE_LEVEL_REWARDS_UNLOCK_XP_BALANCE", 100000.0)


def level_rewards_user_level(owner_id="profile8", level_type="main_level"):
    # amp.services.level_rewards.v1.common.UserLevelData:
    #   1=eId, 2=type, 3=level, 4=xpBalance.
    return (
        pb_string(1, owner_id)
        + pb_string(2, level_type)
        + pb_double(3, level_reward_level_value(level_type))
        + pb_double(4, level_reward_xp_balance_value(level_type))
    )


def level_rewards_response():
    # amp.services.level_rewards.v1.common.UserLevelsData:
    #   1=levels[].
    level_types = ["main_level"]
    if env_flag("SKATE_LEVEL_REWARDS_INCLUDE_CUSTOMIZATION_TYPES", True):
        # Customize category loading calls FUN_141014810(0..4), which maps to
        # these exact level reward types before it builds each list.
        level_types.extend(["player_level", "create_level", "share_level", "find_level"])
    if env_flag("SKATE_LEVEL_REWARDS_INCLUDE_COLLECTIONSCORE", True):
        level_types.append("collectionscore")
    if env_flag("SKATE_LEVEL_REWARDS_INCLUDE_NEIGHBORHOODS", True):
        level_types.extend(
            [
                "neighbourhood_rank_entertainment",
                "neighbourhood_rank_financial",
                "neighbourhood_rank_historic",
                "neighbourhood_rank_laterotating_entertainment",
                "neighbourhood_rank_slam_entertainment",
                "neighbourhood_rank_stadium",
            ]
        )
    payload = bytearray()
    for level_type in dict.fromkeys(level_types):
        payload += pb_message(1, level_rewards_user_level("profile8", level_type))
    return bytes(payload)


def unlocked_item(unlock_id, is_new=False):
    # dingo.services.unlocks.game.v1.UnlockedItem:
    #   1=unlockId, 2=isNew.
    return pb_string(1, unlock_id) + pb_varint(2, 1 if is_new else 0)


def unlock_ids_for_response():
    # The static unlock graph uses generic unlock records such as own-create
    # and entitlement-inv, while runtime inventory/customization rows point at
    # ownable ids and numeric catalog ids. Return a compact union so either
    # lookup style can resolve during customization tests.
    ids = []
    for unlock_id in UNLOCK_STATIC_RECORD_IDS:
        ids.append(unlock_id)

    catalog_meta = catalog_metadata_by_ownable()
    for ownable_id in cosmetic_ownable_ids():
        ids.append(ownable_id)
        meta = catalog_meta.get(ownable_id, {})
        item_id = meta.get("item_id")
        if item_id:
            ids.append(item_id)
        stack_hash = meta.get("stack_hash")
        if stack_hash:
            ids.append(stack_hash)
        ids.append("own-create:" + ownable_id)
        ids.append("own-use:" + ownable_id)
        ids.append("entitlement-inv:" + ownable_id)
    return tuple(dict.fromkeys(unlock_id for unlock_id in ids if unlock_id))


def unlocks_response(logger=None, stream_id=None, path=None):
    if not env_flag("SKATE_UNLOCKS_SERVICE_ENABLED", True):
        if logger:
            logger.write("unlocks_response", stream=stream_id, path=path, count=0, payload_len=0)
        return b""

    unlock_ids = unlock_ids_for_response()
    payload = bytearray()
    for unlock_id in unlock_ids:
        payload += pb_message(1, unlocked_item(unlock_id, is_new=False))
    response = bytes(payload)
    if logger:
        logger.write(
            "unlocks_response",
            stream=stream_id,
            path=path,
            count=len(unlock_ids),
            payload_len=len(response),
            sample=list(unlock_ids[:16]),
        )
    return response


def compact_json(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def customization_active_unlock(ownable_id):
    return {"Asset": ownable_id}


def customization_scalar_payload(loadout):
    # Mirrors the scalar-only key shape from the client's own Save/save
    # Customization payload in rpc_customization_stable_restored_no_gate.
    morph_set_id = env_int("SKATE_MORPH_SET_ID", 0)
    payload = {
        "Asset": loadout["asset"],
        "C_gestureslot01": 0,
        "C_gestureslot02": 0,
        "C_gestureslot04": 0,
        "C_morphSetId": morph_set_id,
        "SelectedCustomization": loadout["top"],
        "Stance": 0,
        "board_bottomart": loadout["deck"],
        "board_gripcolor": loadout["grip_color"],
        "board_gripcolor1": loadout["grip_color"],
        "board_grippattern": loadout["grip_cutout"],
        "board_wheelcolor": loadout["wheel_color"],
        "cust_bottom": loadout["bottom"],
        "cust_headwear": loadout["headwear"],
        "cust_shoe": loadout["shoe"],
        "cust_top": loadout["top"],
        "loadout_bottom": loadout["bottom"],
        "loadout_deck_graphic": loadout["deck"],
        "loadout_grip_color": loadout["grip_color"],
        "loadout_grip_cutout": loadout["grip_cutout"],
        "loadout_headwear": loadout["headwear"],
        "loadout_shoe": loadout["shoe"],
        "loadout_top": loadout["top"],
        "loadout_trucks": loadout["truck"],
        "loadout_wheel_color": loadout["wheel_color"],
        "loadout_wheel_graphic": loadout["wheel_graphic"],
        "sb_trucks": loadout["truck"],
    }
    if env_flag("SKATE_BODY_MORPH_FIELDS", False):
        morph_enabled = env_int("SKATE_MORPH_ENABLED", 1)
        payload.update(
            {
                "CharacterMorphSet": morph_set_id,
                "MorphEnabled": morph_enabled,
                "C_characterMorphSet": morph_set_id,
                "C_morphEnabled": morph_enabled,
                "BodyShaderPresetIndex": env_int("SKATE_BODY_SHADER_PRESET_INDEX", 0),
                "VoiceType": env_int("SKATE_VOICE_TYPE_INDEX", 0),
            }
        )
    if env_flag("SKATE_BODY_SKIN_SMOKE", False):
        body = loadout.get("body", "")
        body_ownable = loadout.get("body_ownable", "")
        body_bare = body.rsplit("/", 1)[-1] if body else ""
        skin_type = loadout.get("skin_type", "")
        voice_type = loadout.get("voice_type", "")
        voice_bare = voice_type.rsplit("/", 1)[-1] if voice_type else ""
        payload.update(
            {
                "cust_body": body,
                "cust_bodytypes": body,
                "cust_bodytype": body,
                "cust_bodytype_id": body_bare,
                "cust_body_ownable": body_ownable,
                "loadout_body": body,
                "loadout_body_type": body,
                "loadout_bodytype": body,
                "cust_skin": skin_type,
                "cust_skintype": skin_type,
                "cust_skintypes": skin_type,
                "loadout_skin": skin_type,
                "loadout_skin_type": skin_type,
                "cust_voicetypes": voice_type,
                "cust_voicetype": voice_type,
                "cust_voicetype_id": voice_bare,
                "loadout_voice": voice_type,
                "loadout_voice_type": voice_type,
            }
        )
    return payload


def customization_save_payload():
    active_unlock_ids = cosmetic_ownable_ids()
    loadout = customization_loadout()
    payload = customization_scalar_payload(loadout)
    if env_flag("SKATE_CUSTOMIZATION_SCALAR_ONLY", False):
        return payload
    payload.update({
        "ActiveUnlocks": [customization_active_unlock(ownable_id) for ownable_id in active_unlock_ids],
        "stance": "regular",
    })
    return payload


def read_save_values_file(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): value for key, value in data.items() if isinstance(value, str)}


def write_save_values_file(path, values):
    path.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def merged_json_object_value(base_value, overlay_value):
    try:
        base_data = json.loads(base_value)
        overlay_data = json.loads(overlay_value)
    except (TypeError, json.JSONDecodeError):
        return base_value
    if not isinstance(base_data, dict) or not isinstance(overlay_data, dict):
        return base_value
    merged = dict(base_data)
    merged.update(overlay_data)
    return compact_json(merged)


CUSTOMIZATION_SAVE_KEYS = tuple(customization_save_payload().keys())
CUSTOMIZATION_SAVE_VALUE = compact_json(customization_save_payload())


def profile_save_without_customization(value):
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value
    if not isinstance(data, dict):
        return value
    cleaned = dict(data)
    for key in CUSTOMIZATION_SAVE_KEYS:
        cleaned.pop(key, None)
    return compact_json(cleaned)


def profile_loadout_overlay_value():
    payload = customization_save_payload()
    # Keep this smoke-test overlay scalar-only. The full ActiveUnlocks array in
    # Profile can change the boot state machine before separate saves are loaded.
    payload.pop("ActiveUnlocks", None)
    return compact_json(payload)


SAVE_VALUES = {
    "Profile": compact_json({"eId": "profile8", "profileId": "profile8"}),
    "audio": compact_json({"masterVolume": 1.0}),
    "Customization": CUSTOMIZATION_SAVE_VALUE,
    "profile8": CUSTOMIZATION_SAVE_VALUE,
}
SAVE_VALUES.update(read_save_values_file(SAVE_SEED_VALUES_PATH))
LEARNED_SAVE_VALUES = read_save_values_file(SAVE_LEARNED_VALUES_PATH)
if env_flag("SKATE_IGNORE_LEARNED_CUSTOMIZATION_SAVE", False) or env_flag("SKATE_CLEAR_LEARNED_CUSTOMIZATION_SAVE", False):
    for learned_key in ("Customization", "profile8"):
        LEARNED_SAVE_VALUES.pop(learned_key, None)
    if env_flag("SKATE_CLEAR_LEARNED_CUSTOMIZATION_SAVE", False):
        try:
            write_save_values_file(SAVE_LEARNED_VALUES_PATH, LEARNED_SAVE_VALUES)
        except OSError:
            pass
SAVE_VALUES.update(LEARNED_SAVE_VALUES)
if env_flag("SKATE_FORCE_SYNTHETIC_CUSTOMIZATION_SAVE", True):
    SAVE_VALUES["Customization"] = CUSTOMIZATION_SAVE_VALUE
    SAVE_VALUES["profile8"] = CUSTOMIZATION_SAVE_VALUE
SAVE_LOCK = threading.Lock()


def progression_key(event_name, component_id):
    return f"{event_name}\t{component_id}"


def split_progression_key(key):
    if "\t" in key:
        return key.split("\t", 1)
    return key, ""


def seed_progression_values_from_profile():
    try:
        profile = json.loads(SAVE_VALUES.get("Profile", "{}"))
    except json.JSONDecodeError:
        profile = {}
    if not isinstance(profile, dict):
        profile = {}
    values = {}
    for component_id, value in profile.items():
        if isinstance(value, (int, float, str)):
            values[progression_key("profile_save", str(component_id))] = str(value)
    if "OBQ_00" in profile:
        values[progression_key("onboarding_objective1", "OBQ_00")] = str(profile["OBQ_00"])
    if "OBQ_01" in profile:
        values[progression_key("onboarding_objective2", "OBQ_01")] = str(profile["OBQ_01"])
    if profile.get("Step_DoSprint"):
        values[progression_key("onboarding_stepcomplete_any", "-1126948530")] = "1"
    if profile.get("Step_DoOllie"):
        values[progression_key("onboarding_stepcomplete_any", "-1126948531")] = "1"
    if profile.get("Step_DoBrake"):
        values[progression_key("onboarding_stepcomplete_onboard", "-652735267")] = "1"
    if profile.get("Step_DoGetUp"):
        values[progression_key("onboarding_stepcomplete_wipeout", "1527069744")] = "1"
    return values


PROGRESSION_VALUES = seed_progression_values_from_profile()
PROGRESSION_VALUES.update(read_save_values_file(PROGRESSION_VALUES_PATH))
if env_flag("SKATE_FORCE_PROFILE_CUSTOMIZATION_SAVE", False):
    # Diagnostic only. The normal boot flow should load Profile first and then
    # request separate audio/Customization saves; putting customization arrays
    # into Profile can prevent that state machine from advancing.
    SAVE_VALUES["Profile"] = merged_json_object_value(SAVE_VALUES.get("Profile", "{}"), CUSTOMIZATION_SAVE_VALUE)
else:
    SAVE_VALUES["Profile"] = profile_save_without_customization(SAVE_VALUES.get("Profile", "{}"))
if env_flag("SKATE_PROFILE_LOADOUT_SMOKE", False):
    SAVE_VALUES["Profile"] = merged_json_object_value(SAVE_VALUES.get("Profile", "{}"), profile_loadout_overlay_value())
PROGRESSION_LOCK = threading.Lock()


def save_value_for(*keys):
    with SAVE_LOCK:
        for key in keys:
            if key in SAVE_VALUES:
                return SAVE_VALUES[key]
    return "{}"


def remember_save_value(key, value):
    if not key:
        return
    with SAVE_LOCK:
        value = merged_save_value(key, value)
        SAVE_VALUES[key] = value
        LEARNED_SAVE_VALUES[key] = value
        try:
            write_save_values_file(SAVE_LEARNED_VALUES_PATH, LEARNED_SAVE_VALUES)
        except OSError:
            pass


def save_value_summary(value):
    return {
        "value_len": len(value),
        "value_sha1": hashlib.sha1(value.encode("utf-8", "replace")).hexdigest(),
        "value_preview": value[:500],
    }


def customization_value_summary(value):
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {
            "customization_variant": customization_smoke_variant(),
            "customization_scalar_only": env_flag("SKATE_CUSTOMIZATION_SCALAR_ONLY", False),
            "customization_parse_error": True,
        }
    if not isinstance(data, dict):
        return {
            "customization_variant": customization_smoke_variant(),
            "customization_scalar_only": env_flag("SKATE_CUSTOMIZATION_SCALAR_ONLY", False),
            "customization_parse_error": True,
        }
    visible = {key: data[key] for key in CUSTOMIZATION_VISIBLE_KEYS if key in data}
    active_unlocks = data.get("ActiveUnlocks")
    return {
        "customization_variant": customization_smoke_variant(),
        "customization_scalar_only": env_flag("SKATE_CUSTOMIZATION_SCALAR_ONLY", False),
        "customization_key_count": len(data),
        "customization_has_exact_client_save_keys": tuple(sorted(data.keys())) == tuple(sorted(CUSTOMIZATION_CLIENT_SAVE_KEYS)),
        "customization_active_unlock_count": len(active_unlocks) if isinstance(active_unlocks, list) else 0,
        "customization_visible": visible,
    }


def merged_save_value(key, value):
    if key not in ("Profile", "Customization", "profile8"):
        return value
    return merged_json_object_value(SAVE_VALUES.get(key, "{}"), value)


def save_load_response(value):
    # dingo.services.save.game.v1.LoadResponse / LoadUserResponse:
    #   1=value. The value itself is the text blob parsed by the client.
    return pb_string(1, value)


def save_rpc_payload_for(path, request_body=b"", logger=None, stream_id=None):
    fields = grpc_string_fields(request_body)
    if "Save/loadUser" in path:
        eid = protobuf_first_string(fields, 1)
        key = protobuf_first_string(fields, 2)
        value = save_value_for(key, eid)
        if logger:
            summary = save_value_summary(value)
            if key in ("Customization", "profile8") or eid in ("Customization", "profile8"):
                summary.update(customization_value_summary(value))
            logger.write(
                "save_load_user",
                stream=stream_id,
                path=path,
                eId=eid,
                key=key,
                **summary,
            )
        return save_load_response(value)
    if "Save/load" in path:
        key = protobuf_first_string(fields, 1)
        value = save_value_for(key)
        if logger:
            summary = save_value_summary(value)
            if key in ("Customization", "profile8"):
                summary.update(customization_value_summary(value))
            logger.write(
                "save_load",
                stream=stream_id,
                path=path,
                key=key,
                **summary,
            )
        return save_load_response(value)
    if "Save/save" in path:
        key = protobuf_first_string(fields, 1)
        value = protobuf_first_string(fields, 2)
        remember_save_value(key, value)
        if logger:
            summary = save_value_summary(value)
            if key in ("Customization", "profile8"):
                summary.update(customization_value_summary(value))
            logger.write(
                "save_save",
                stream=stream_id,
                path=path,
                key=key,
                **summary,
            )
        return b""
    return b""


def progression_event_message(event_name, component_id, value):
    payload = pb_string(1, event_name) + pb_string(2, component_id) + pb_string(3, str(value))
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 1.0
    payload += pb_double(4, number)
    if number >= 0:
        payload += pb_varint(5, int(number))
    return payload


def progression_request_events(request_body):
    payload = grpc_request_payload(request_body)
    events = []
    for message in protobuf_messages(payload, 1):
        fields = protobuf_string_fields(message)
        event_name = protobuf_first_string(fields, 1)
        component_id = protobuf_first_string(fields, 2)
        if event_name:
            events.append((event_name, component_id))
    if not events:
        fields = protobuf_string_fields(payload)
        event_name = protobuf_first_string(fields, 1)
        component_id = protobuf_first_string(fields, 2)
        if event_name:
            events.append((event_name, component_id))
    return events


def progression_value_for(event_name, component_id):
    if event_name == "challengereset":
        return None
    if env_flag("SKATE_SYNTHETIC_CURRENCY_REWARDS", True) and (event_name or "").startswith("achievement_currencyreward_"):
        return str(env_float("SKATE_SYNTHETIC_CURRENCY_REWARD_VALUE", 100000.0))
    with PROGRESSION_LOCK:
        key = progression_key(event_name, component_id)
        if key in PROGRESSION_VALUES:
            return PROGRESSION_VALUES[key]
        profile_key = progression_key("profile_save", component_id)
        if profile_key in PROGRESSION_VALUES:
            return PROGRESSION_VALUES[profile_key]
    synthetic_value = synthetic_progression_value(event_name, component_id)
    if synthetic_value is not None:
        return synthetic_value
    return None


def synthetic_progression_value(event_name, component_id):
    if not env_flag("SKATE_SYNTHETIC_RANK_UNLOCKS", True):
        return None
    match = re.match(r"^challengecomplete_own_rank(\d+)_tier(\d+)$", event_name or "")
    if not match:
        return None
    rank = int(match.group(1))
    max_rank = int(env_float("SKATE_UNLOCK_RANK_MAX", rep_level_value()))
    if rank <= max_rank:
        return "1"
    return None


def remember_progression_event(event_name, component_id, value="1"):
    if not event_name:
        return
    with PROGRESSION_LOCK:
        PROGRESSION_VALUES[progression_key(event_name, component_id)] = str(value)
        try:
            write_save_values_file(PROGRESSION_VALUES_PATH, PROGRESSION_VALUES)
        except OSError:
            pass


def progression_rpc_payload_for(path, request_body=b"", logger=None, stream_id=None):
    events = progression_request_events(request_body)
    if "Progression/sendGameEvent" in path:
        for event_name, component_id in events:
            remember_progression_event(event_name, component_id, "1")
        if logger:
            logger.write(
                "progression_send",
                stream=stream_id,
                path=path,
                count=len(events),
                events=[{"event": event_name, "component": component_id} for event_name, component_id in events[:20]],
            )
        return b""
    if "Progression/getGameEvent" in path or "Progression/getGameEvents" in path:
        payload = bytearray()
        returned_events = []
        for event_name, component_id in events:
            value = progression_value_for(event_name, component_id)
            if value is None:
                continue
            payload += pb_message(1, progression_event_message(event_name, component_id, value))
            returned_events.append((event_name, component_id, value))
        if logger:
            logger.write(
                "progression_get",
                stream=stream_id,
                path=path,
                count=len(events),
                returned=len(returned_events),
                requested=[
                    {
                        "event": event_name,
                        "component": component_id,
                    }
                    for event_name, component_id in events[:40]
                ],
                events=[
                    {
                        "event": event_name,
                        "component": component_id,
                        "value": value,
                    }
                    for event_name, component_id, value in returned_events[:20]
                ],
            )
        return bytes(payload)
    return b""


def game_data_chunk_message(chunk_id, body):
    # amp.services.data.game.v1.GetDataResponse: 1=chunkId, 2=data.
    return pb_string(1, chunk_id) + pb_bytes(2, body)


def game_data_manifest_chunk_message(chunk_id, body):
    # amp.services.data.game.v1.GameDataChunk:
    #   1=chunkId, 2=system, 3=containerType, 4=metadata[],
    #   6=assetIds[], 7=validTimeWindows[], 8=size.
    #
    # The raw data bytes are not part of GetGameDataResponse.chunks[]; the
    # client uses this manifest entry to populate/fetch typed data chunks.
    system, container_type, record_asset_ids = chunk_manifest_type(body, chunk_id=chunk_id)
    payload = (
        pb_string(1, chunk_id)
        + pb_string(2, system)
        + pb_string(3, container_type)
        + pb_varint(8, len(body))
    )
    manifest_asset_ids = manifest_asset_ids_for_chunk(system, body, record_asset_ids, chunk_id=chunk_id)
    for asset_id in manifest_asset_ids:
        if asset_id.encode("utf-8") in body:
            payload += pb_string(6, asset_id)
    return payload


def forced_game_data_manifest_chunk_message(chunk_id, body, system, container_type, asset_ids):
    payload = (
        pb_string(1, chunk_id)
        + pb_string(2, system)
        + pb_string(3, container_type)
        + pb_varint(8, len(body))
    )
    for asset_id in dict.fromkeys(asset_ids):
        payload += pb_string(6, asset_id)
    return payload


def get_game_data_response(logger=None, stream_id=None, path=None):
    # amp.services.data.game.v1.GetGameDataResponse:
    #   1=datasetId, 2=chunks[], 3=subscribeTopic, 4=expiry.
    payload = bytearray(pb_string(1, "default"))
    chunk_count = 0
    asset_count = 0
    sample_assets = []
    sample_chunks = []
    all_chunk_ids = []
    system_counts = {}
    for chunk_id, chunk_source in board_data_chunks_for_response():
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        all_chunk_ids.append(chunk_id)
        if len(sample_chunks) < 16:
            sample_chunks.append(chunk_id)
        system, _, record_asset_ids = chunk_manifest_type(body, chunk_id=chunk_id)
        system_counts[system] = system_counts.get(system, 0) + 1
        manifest_asset_ids = manifest_asset_ids_for_chunk(system, body, record_asset_ids, chunk_id=chunk_id)
        present_assets = [asset_id for asset_id in manifest_asset_ids if asset_id.encode("utf-8") in body]
        chunk_count += 1
        asset_count += len(present_assets)
        if len(sample_assets) < 12:
            sample_assets.extend(present_assets[: 12 - len(sample_assets)])
        payload += pb_message(2, game_data_manifest_chunk_message(chunk_id, body))
        if (
            env_flag("SKATE_SYNTHETIC_STORE_DUPLICATE_INVENTORY_MANIFEST", False)
            and b"drop_pool__item_N1_P01Price" in body
        ):
            inventory_asset_ids = tuple(SYNTHETIC_STORE_INVENTORY_RECORD_IDS) + tuple(STORE_CURRENCY_IDS)
            payload += pb_message(
                2,
                forced_game_data_manifest_chunk_message(
                    chunk_id,
                    body,
                    INVENTORY_ITEM_SYSTEM,
                    INVENTORY_ITEM_TYPE,
                    inventory_asset_ids,
                ),
            )
            chunk_count += 1
            system_counts[INVENTORY_ITEM_SYSTEM] = system_counts.get(INVENTORY_ITEM_SYSTEM, 0) + 1
            inventory_present_assets = [
                asset_id for asset_id in inventory_asset_ids if asset_id.encode("utf-8") in body
            ]
            asset_count += len(inventory_present_assets)
    if logger:
        logger.write(
            "game_data_response",
            stream=stream_id,
            path=path,
            chunk_count=chunk_count,
            system_counts=system_counts,
            asset_count=asset_count,
            sample_assets=sample_assets,
            sample_chunks=sample_chunks,
            customization_chunk_present=CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID in all_chunk_ids,
            customization_chunk_id=CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID,
            manifest_ownable_asset_chunk_id=os.environ.get("SKATE_MANIFEST_OWNABLE_ASSET_CHUNK_ID", ""),
            cosmetic_mode=os.environ.get("SKATE_COSMETIC_MODE", ""),
            cosmetic_max_count=env_int("SKATE_COSMETIC_MAX_COUNT", 0),
            payload_len=len(payload),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="game_data_response")
    return bytes(payload)


def requested_game_data_chunk_ids(request_body):
    return protobuf_repeated_strings(grpc_request_payload(request_body), 1)


def get_data_chunks_response(request_body=b"", logger=None, stream_id=None, path=None):
    mode = os.environ.get("SKATE_DATA_CHUNKS_MODE", "empty").strip().lower()
    if mode in ("", "empty", "off", "none"):
        if logger:
            logger.write("game_data_chunks_response", stream=stream_id, path=path, mode=mode, requested=[], count=0, payload_len=0)
        return b""
    requested = requested_game_data_chunk_ids(request_body)
    chunk_map = {chunk_id: chunk_source for chunk_id, chunk_source in board_data_chunks_for_response()}
    if requested:
        chunks = [(chunk_id, chunk_map[chunk_id]) for chunk_id in requested if chunk_id in chunk_map]
    else:
        chunks = list(chunk_map.items())
    if requested and env_flag("SKATE_DATA_CHUNKS_APPEND_ALLOWLIST", False):
        appended = {chunk_id for chunk_id, _ in chunks}
        append_ids = [part.strip() for part in os.environ.get("SKATE_STORE_CHUNK_ALLOWLIST", "").split(",") if part.strip()]
        append_ids.extend(chunk_id for chunk_id, _ in synthetic_store_chunks())
        if env_flag("SKATE_DATA_CHUNKS_APPEND_CUSTOMIZATION_CATEGORIES", True):
            append_ids.extend(customization_category_chunk_ids())
        if env_flag("SKATE_DATA_CHUNKS_APPEND_UNLOCKS_STATIC", True):
            append_ids.extend(unlock_static_chunk_ids())
        if env_flag("SKATE_DATA_CHUNKS_APPEND_CUSTOMIZATION_OWNABLES", True):
            append_ids.extend(customization_ownable_chunk_ids())
        if env_flag("SKATE_DATA_CHUNKS_APPEND_CUSTOMIZATION_PRESENTABLES", False):
            append_ids.extend(chunk_id for chunk_id, _ in customization_presentables_static_chunks())
        if env_flag("SKATE_DATA_CHUNKS_APPEND_PRESENTABLES_OWNABLES", False):
            append_ids.extend(presentables_ownable_chunk_ids())
        for chunk_id in dict.fromkeys(append_ids):
            if chunk_id in appended or chunk_id not in chunk_map:
                continue
            chunks.append((chunk_id, chunk_map[chunk_id]))
            appended.add(chunk_id)
    payload = bytearray()
    for chunk_id, chunk_source in chunks:
        try:
            body = chunk_body_bytes(chunk_source)
        except OSError:
            continue
        payload += pb_message(1, game_data_chunk_message(chunk_id, body))
    response = bytes(payload)
    if logger:
        record_samples = {}
        for chunk_id, chunk_source in chunks[:8]:
            try:
                record_samples[chunk_id] = list(cache_record_ids(chunk_body_bytes(chunk_source), limit=8))
            except OSError:
                record_samples[chunk_id] = []
        logger.write(
            "game_data_chunks_response",
            stream=stream_id,
            path=path,
            mode=mode,
            requested=list(requested),
            requested_count=len(requested),
            count=len(chunks),
            payload_len=len(response),
            sample=[chunk_id for chunk_id, _ in chunks[:8]],
            record_samples=record_samples,
            customization_chunk_returned=any(chunk_id == CUSTOMIZATION_INVENTORY_STATIC_CHUNK_ID for chunk_id, _ in chunks),
        )
        logger.write("bootstrap_checkpoint", stream=stream_id, path=path, checkpoint="game_data_chunks_response")
    return response


def grpc_payload_for(path, request_body=b"", logger=None, stream_id=None):
    if "ServerDiscovery/getServers" in path:
        return None
    if "ServerDiscovery/getLineages" in path:
        return get_lineages_response()
    if "amp.services.login.v1.Login/" in path:
        if (
            "Login/login" in path
            or "Login/refresh" in path
            or "Login/autoLogin" in path
            or "Login/reconnect" in path
        ):
            return login_response_with_logging(logger=logger, stream_id=stream_id, path=path)
        return b""
    if "Inventory/getAllInventoryItems" in path:
        return inventory_items_response(logger=logger, stream_id=stream_id, path=path)
    if "Entitlements/getEntitlements" in path:
        return entitlements_response(logger=logger, stream_id=stream_id, path=path)
    if "amp.services.data.game.v1.GameData/" in path:
        if path.endswith("/getData"):
            return get_game_data_response(logger=logger, stream_id=stream_id, path=path)
        if path.endswith("/getDataChunk") or path.endswith("/getDataChunks"):
            return get_data_chunks_response(request_body, logger=logger, stream_id=stream_id, path=path)
        return b""
    if "amp.services.gamestore.v1." in path or "GameStore/" in path:
        return b""
    if "Profile/getProfiles" in path or "Profile/getCompactProfiles" in path:
        return profile_response(logger=logger, stream_id=stream_id, path=path, request_body=request_body)
    if "Ownable/getOwnableInstances" in path:
        return ownables_response(logger=logger, stream_id=stream_id, path=path)
    if "LevelRewards/getUserLevels" in path:
        if logger:
            logger.write(
                "level_rewards_response",
                stream=stream_id,
                path=path,
                level=rep_level_value(),
                xp_balance=rep_xp_balance_value(),
                synthetic_rank_unlocks=env_flag("SKATE_SYNTHETIC_RANK_UNLOCKS", True),
                unlock_rank_max=int(env_float("SKATE_UNLOCK_RANK_MAX", rep_level_value())),
            )
        return level_rewards_response()
    if "Save/load" in path or "Save/loadUser" in path or "Save/save" in path:
        return save_rpc_payload_for(path, request_body, logger=logger, stream_id=stream_id)
    if "Progression/" in path:
        return progression_rpc_payload_for(path, request_body, logger=logger, stream_id=stream_id)
    if "Unlocks/getUnlocks" in path:
        return unlocks_response(logger=logger, stream_id=stream_id, path=path)
    if "Stats/" in path or "Mail/" in path:
        return b""
    if logger and not (
        "sendClientBiEvents" in path
        or "logMetricsV2" in path
        or "Progression/getGameEvents" in path
        or "Progression/sendGameEvent" in path
        or "social_feed" in path
        or "lan.game.v1.Lan/" in path
    ):
        logger.write(
            "unhandled_rpc",
            stream=stream_id,
            path=path,
            body_len=len(request_body),
            request_strings=printable_strings(grpc_request_payload(request_body), limit=24),
        )
    return b""


class Logger:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.path.write_text("", encoding="utf-8")

    def write(self, event, **fields):
        row = {"t": round(time.time(), 3), "event": event, **fields}
        with self.lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


def make_tls_context(cert_path, key_path):
    if not cert_path or not key_path:
        return None
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.set_alpn_protocols(["h2", "http/1.1"])
    context.load_cert_chain(str(cert_path), str(key_path))
    return context


def pump_h2_flow_control(conn, h2c):
    data = conn.recv(65535)
    if not data:
        return False
    events = h2c.receive_data(data)
    for event in events:
        if isinstance(event, h2.events.DataReceived):
            h2c.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
    outbound = h2c.data_to_send()
    if outbound:
        conn.sendall(outbound)
    return True


def send_h2_data(conn, h2c, stream_id, body, logger, path):
    offset = 0
    logged_large = False
    while offset < len(body):
        window = h2c.local_flow_control_window(stream_id)
        while window <= 0:
            if not logged_large:
                logger.write("h2_large_response", stream=stream_id, path=path, body_len=len(body))
                logged_large = True
            if not pump_h2_flow_control(conn, h2c):
                raise ConnectionError("peer closed while waiting for HTTP/2 flow-control window")
            window = h2c.local_flow_control_window(stream_id)
        chunk_len = min(len(body) - offset, h2c.max_outbound_frame_size, window)
        h2c.send_data(stream_id, body[offset : offset + chunk_len])
        offset += chunk_len
        outbound = h2c.data_to_send()
        if outbound:
            conn.sendall(outbound)


def grpc_response_body(payload, request_headers):
    accepted = request_headers.get("grpc-accept-encoding", "")
    accepted_tokens = {token.strip().lower() for token in accepted.split(",")}
    compressed = False
    if compressed:
        wire_payload = gzip.compress(payload)
    else:
        wire_payload = payload
    return grpc_frame(wire_payload, compressed=compressed), compressed, len(wire_payload)


def serve(stop_event, logger, address, names, tls_context=None):
    config = h2.config.H2Configuration(client_side=False, header_encoding="utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(8)
        server.settimeout(0.5)
        logger.write("listen", host=HOST, port=PORT)
        while not stop_event.is_set():
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=handle_conn,
                args=(conn, addr, config, logger, address, names, tls_context),
                daemon=True,
            ).start()


def handle_conn(conn, addr, config, logger, address, names, tls_context=None):
    peer = f"{addr[0]}:{addr[1]}"
    logger.write("accept", addr=peer)
    is_tls = False
    conn.settimeout(0.5)
    try:
        if tls_context is not None:
            try:
                peek = conn.recv(5, socket.MSG_PEEK)
            except socket.timeout:
                peek = b""
            if peek.startswith(b"\x16\x03"):
                conn.settimeout(3.0)
                conn = tls_context.wrap_socket(conn, server_side=True)
                is_tls = True
                logger.write("tls", addr=peer, cipher=conn.cipher(), version=conn.version(), alpn=conn.selected_alpn_protocol())
                conn.settimeout(0.5)

        first = b""
        try:
            first = conn.recv(65535)
        except socket.timeout:
            pass
        if first.startswith((b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ", b"OPTIONS ")):
            handle_http1(conn, peer, logger, first)
            return
        if first:
            logger.write("first_bytes", addr=peer, data_hex=first[:128].hex(), tls=is_tls)

        streams = {}
        h2c = h2.connection.H2Connection(config=config)
        h2c.initiate_connection()
        conn.sendall(h2c.data_to_send())
        pending = first
        while True:
            if pending:
                data = pending
                pending = b""
            else:
                try:
                    data = conn.recv(65535)
                except socket.timeout:
                    continue
            if not data:
                logger.write("disconnect", addr=peer)
                return
            events = h2c.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.RequestReceived):
                    headers = dict(event.headers)
                    streams[event.stream_id] = {
                        "headers": headers,
                        "body": bytearray(),
                        "path": headers.get(":path", ""),
                    }
                    logger.write("request", stream=event.stream_id, path=headers.get(":path", ""), headers=headers)
                elif isinstance(event, h2.events.DataReceived):
                    stream = streams.setdefault(event.stream_id, {"headers": {}, "body": bytearray(), "path": ""})
                    stream["body"] += event.data
                    h2c.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
                elif isinstance(event, h2.events.StreamEnded):
                    stream = streams.get(event.stream_id, {"headers": {}, "body": bytearray(), "path": ""})
                    body = bytes(stream["body"])
                    path = stream["path"]
                    if "sendClientBiEvents" in path or "logMetricsV2" in path:
                        body_log_len = 8192
                    elif "Save/" in path or "save.game.v1" in path:
                        body_log_len = 4096
                    elif "GameData" in path or "data.game.v1" in path:
                        body_log_len = 512
                    else:
                        body_log_len = 64
                    logger.write("end", stream=event.stream_id, path=path, body_len=len(body), body_hex=body[:body_log_len].hex())
                    log_bootstrap_request(logger, event.stream_id, path, body, stream["headers"])
                    if "sendClientBiEvents" in path or "logMetricsV2" in path:
                        logger.write(
                            "request_strings",
                            stream=event.stream_id,
                            path=path,
                            body_len=len(body),
                            strings=printable_strings(grpc_request_payload(body)),
                        )
                    payload = grpc_payload_for(path, body, logger=logger, stream_id=event.stream_id)
                    if payload is None:
                        payload = get_servers_response(address, names)
                        logger.write(
                            "server_discovery_response",
                            stream=event.stream_id,
                            path=path,
                            address=address,
                            names=list(names),
                            server_count=len(names),
                            payload_len=len(payload),
                        )
                        logger.write("bootstrap_checkpoint", stream=event.stream_id, path=path, checkpoint="server_discovery_response")
                    response_body, compressed, wire_payload_len = grpc_response_body(payload, stream["headers"])
                    response_headers = [
                        (":status", "200"),
                        ("content-type", "application/grpc"),
                        ("grpc-accept-encoding", "gzip"),
                    ]
                    if compressed:
                        response_headers.append(("grpc-encoding", "gzip"))
                    h2c.send_headers(event.stream_id, response_headers)
                    send_h2_data(conn, h2c, event.stream_id, response_body, logger, path)
                    h2c.send_headers(event.stream_id, [("grpc-status", "0")], end_stream=True)
                    logger.write(
                        "response",
                        stream=event.stream_id,
                        path=path,
                        payload_len=len(payload),
                        compressed=compressed,
                        wire_payload_len=wire_payload_len,
                    )
            outbound = h2c.data_to_send()
            if outbound:
                conn.sendall(outbound)
    except Exception as exc:
        logger.write("conn_error", addr=peer, error=repr(exc), tls=is_tls)
    finally:
        try:
            conn.close()
        except OSError:
            pass


def handle_http1(conn, peer, logger, first):
    data = bytearray(first)
    try:
        while b"\r\n\r\n" not in data and len(data) < 65536:
            chunk = conn.recv(65535)
            if not chunk:
                break
            data.extend(chunk)
        header_blob = bytes(data).split(b"\r\n\r\n", 1)[0]
        request_line = header_blob.splitlines()[0].decode("iso-8859-1", "replace")
        method, path, _version = (request_line.split(" ", 2) + ["", ""])[:3]
        logger.write("http1_request", method=method, path=path, header_hex=header_blob[:512].hex())
        lowered_path = path.lower()
        content_type = "application/json"
        if lowered_path == PROFILE_THUMBNAIL_PATH:
            body = PROFILE_THUMBNAIL_PNG
            content_type = "image/png"
        elif (
            lowered_path.startswith("/data-app/chunks/")
            or lowered_path.startswith("/data/dingo-amp-prod-gcp-cdn-data-bucket/data-app/chunks/")
            or lowered_path.startswith("/cdn/production/")
        ):
            cached = cache_blob_for_request_path(path)
            if cached is None:
                body = b""
                content_type = "application/octet-stream"
            else:
                body, cache_file = cached
                content_type = "application/octet-stream"
                logger.write("http1_cache_hit", path=path, cache_file=str(cache_file), body_len=len(body))
        elif lowered_path.startswith("/application_id/dingo_pc_client"):
            body = local_dingo_settings_config()
            content_type = "application/octet-stream"
        elif (
            "director" in lowered_path
            or "config" in lowered_path
            or lowered_path.startswith("/application_id/")
            or path in {"/", ""}
        ):
            body = local_director_config()
        elif "token" in path or "connect" in path:
            body = json.dumps(
                {
                    "access_token": "local-access-token",
                    "refresh_token": "local-refresh-token",
                    "id_token": "local-id-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
                separators=(",", ":"),
            )
        else:
            body = "{}"
        conn.sendall(http1_response(body, content_type=content_type))
        logger.write("http1_response", path=path, body_len=len(body), content_type=content_type)
    except Exception as exc:
        logger.write("http1_error", addr=peer, error=repr(exc))
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main():
    global HOST, PORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--exe", default=str(EXE))
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--address-mode", choices=sorted(ADDRESS_MODES), default="http")
    parser.add_argument("--address", help="Override the address returned in ServerDiscovery responses.")
    parser.add_argument("--names", choices=["default", "verbose"], default="default")
    parser.add_argument("--server-only", action="store_true", help="Run the local mock until interrupted; do not launch the game.")
    parser.add_argument("--log", default=str(LOG_PATH), help="JSONL log path.")
    parser.add_argument("--tls-auto", action="store_true", help="Auto-detect TLS ClientHello on this port and serve gRPC over TLS.")
    parser.add_argument("--tls-cert", default=str(TLS_CERT), help="Certificate chain for --tls-auto.")
    parser.add_argument("--tls-key", default=str(TLS_KEY), help="Private key for --tls-auto.")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    ns = parser.parse_args()

    HOST = ns.host
    PORT = ns.port
    log_path = Path(ns.log)
    logger = Logger(log_path)
    address = ns.address or ADDRESS_MODES[ns.address_mode](HOST, PORT)
    names = VERBOSE_SERVER_NAMES if ns.names == "verbose" else DEFAULT_SERVER_NAMES
    tls_context = make_tls_context(Path(ns.tls_cert), Path(ns.tls_key)) if ns.tls_auto else None
    logger.write(
        "config",
        address=address,
        address_mode=ns.address_mode,
        names=ns.names,
        server_count=len(names),
        tls_auto=bool(tls_context),
        customization_variant=customization_smoke_variant(),
        customization_scalar_only=env_flag("SKATE_CUSTOMIZATION_SCALAR_ONLY", False),
        force_synthetic_customization=env_flag("SKATE_FORCE_SYNTHETIC_CUSTOMIZATION_SAVE", True),
        ignore_learned_customization=env_flag("SKATE_IGNORE_LEARNED_CUSTOMIZATION_SAVE", False),
        cosmetic_mode=os.environ.get("SKATE_COSMETIC_MODE", ""),
        cosmetic_max_count=env_int("SKATE_COSMETIC_MAX_COUNT", 0),
        inventory_mode=os.environ.get("SKATE_INVENTORY_MODE", ""),
        data_chunks_mode=os.environ.get("SKATE_DATA_CHUNKS_MODE", ""),
        manifest_ownable_asset_chunk_id=os.environ.get("SKATE_MANIFEST_OWNABLE_ASSET_CHUNK_ID", ""),
        stable_local_cache_manifest=env_flag("SKATE_STABLE_LOCAL_CACHE_MANIFEST", True),
        local_cache_manifest_max_chunks=env_int("SKATE_LOCAL_CACHE_MANIFEST_MAX_CHUNKS", 128),
        customization_inventory_static_chunk=env_flag("SKATE_CUSTOMIZATION_INVENTORY_STATIC_CHUNK", False),
        customization_static_as_ownable=env_flag("SKATE_CUSTOMIZATION_STATIC_AS_OWNABLE", False),
    )
    stop_event = threading.Event()
    thread = threading.Thread(target=serve, args=(stop_event, logger, address, names, tls_context), daemon=True)
    thread.start()
    time.sleep(0.8)

    if ns.server_only:
        print(log_path)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()
            return

    game_args = ns.args[1:] if ns.args[:1] == ["--"] else ns.args
    exe = Path(ns.exe)
    launch_args = [str(exe)] + game_args
    logger.write("launch", exe=str(exe), args=game_args)
    proc = subprocess.Popen(launch_args, cwd=str(exe.parent))
    logger.write("pid", pid=proc.pid)
    last_net = None
    try:
        deadline = time.time() + ns.seconds
        while time.time() < deadline and proc.poll() is None:
            try:
                snap = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        (
                            f"Get-NetTCPConnection -OwningProcess {proc.pid} -ErrorAction SilentlyContinue | "
                            "Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State | "
                            "ConvertTo-Json -Compress"
                        ),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=3,
                ).stdout.strip()
                if snap and snap != last_net:
                    logger.write("net", snapshot=snap)
                    last_net = snap
            except Exception as exc:
                logger.write("net_error", error=repr(exc))
            time.sleep(0.5)
    finally:
        stop_event.set()
        if proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/F", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.write("killed", pid=proc.pid)
        else:
            logger.write("exited", pid=proc.pid, code=proc.returncode)
    print(log_path)


if __name__ == "__main__":
    main()
