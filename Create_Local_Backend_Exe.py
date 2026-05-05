import base64
import hashlib
import json
from pathlib import Path
import zlib

OUTPUT_EXE = "preservation_client.exe"
EXPECTED_SOURCE_SHA256 = "066FD6F38C1CD8F7656BA99016A18CEEB7B9E4EEA81AEB2CDE4C6D5431123703"
EXPECTED_OUTPUT_SHA256 = "3735610743A2AAA8557D68286788F0CB4425684D3C959374C1F3B2A579CB884C"

PATCH_PAYLOAD = """
c-rloS#skz42JKL=RA-E2$E;%>IZqd{}JW`orsEK$9qrDl$EMZL=g+I@fWE6^-Hpan)Usyh4J(D`~6qcC@ouke_MqR*Rp)Rm}RL-
D``)^A7N^i`2MzC?eEnzW^+E{z9Dhj(kAq4&^EO!`G__pv|O9bTuW5==;ytpP+Lw=hS={Vgj530k7<6$z0a<aPOo)2+cI{^1z9Rm
#z<w&EH00c#z@Y&TFGW24U-x(q|~%4W}70Kbf=SUS#%WDDvHvjNa0e=F*lyBY?mi(R-qByYMdo-ixyeei;==e%D4{>wM?2Z(?%1r
3i4yl%#Y3=&9bDTR++&aTJl?(O)%m)_elalpo&{`LV6PPbiUBICL5p2{gyegG{4terdgX3uqi9#spMQfsR~qMPV_ZwnX_4p5qF>5
7W9)w47hQ<km_q_SjqCR2y2AWuS7VgMM)Su<SDzYH>@D(7Cn;sJ&`X9TEnMS7Wc*dXB#3Mv0TDWgj2i7JEckYPSUg(bN?*oG?$6q
IR}lijA%QR{rG~qMlwKGc!wFxpKMDY=Crehw`9zd@cveGagQIwBXI53BNlV%y5?ZJF-twBw*(4tQ%0=U>^6l8c|6QX-
P6LVH{J76u(IuJi?U3>FBu&xfybyc!HKp>D<WL*1xcg3B59RYa6yeBr`smGXCz9+7M19Vwzd^<i`3$gTh*+jovyv^U>~<ol~`OiI
3kQ3l1gj`(t!{x!M2Kp5Rq()-eewjQ2aRZre%CZRuU5;#Mw&Fa6C2a*Vneja`1MZ*aZ)u*Us<ABa@VN@W2-
=l8NY15Vy^ZH8W(cU7*4lQN1P<Jo_{gIU^rRi1^NP)q2iSI*Ras!V=Jf3^Iz}n4Pd0e76aWy>_AzmSDc1L=oqrmWa;DHiJq%zp7E
Jy$aZBJjvNtTD($Cwqm8&-
B(WCSRrRc<e6ItNn7Sk{GDvgT6=|KEkV6TAZ<ht#T)zCx@WIvr2E&aQ}&FeZeUZgl7ekDt!zb<NTE=cB>R$vblZy8sEJi+uL(P%Y
ejBl=^2BquqYAU)a?$Hxo0XdR*6MyJZlrP+pPPC%vq(K1m`fG+ddAdp%!};+NcL{>7l)^I8-
37dDK~IIa*LxdG585d?f~0SJ%*MqY=j*&&k)%Z?6ck^Q3}!{hTGI<n{7oWkDLXeqY_${ywS$e=|#1FhS;<Aan6tb-
y`18DCi82K%qA74g-2JP^Ist2wJIzAM3za7{y->UJRO*p33ZwRVm0E;&L-
dW^Xys~oU9zBhIjY9(1{WGgBM84)0nI#)cm+1${%5qQ|ev#@xr+vI>gYQ%BzN|<m@CZ?5`7cYc(bi^+@P|tWE>_`@S3^mrZmZ<C8
eD%H*Dq1Cz9m*uH9qO(l8wQ^WAEHcc<N3@CVwBq9`!yVh{e;cbgP&}Hlzl&uW|-
KNteuc8UVUbcs6uQ}F9=Hl7Ei2g?FEtfg&J5quheT0duX99vvPJ}Oou1%foJrJ9Ij-aXC^D+DSHk(SEYnd*|B@ZtC`55D)7{Ir$T
Lxo(klm4sCpWM9!KT#NJQEA^tq8unC4|)mVqjGOXu&dL|Ogu>c$=?9j{$nOkAU^9?>pRJZ22OWlf&EQ;?T*up(W_DzKvpkC9m^t{
s<4PXRp<Mq(%8Jb2kBM!9ZwvXX^qL!Tu97JI6h&12#DS+%R?9^U2s8AqGfFk>c`Ck(@h<(>6x{*zo(&qDrQE)}_?9Pq`I*w^Q?@)
2f3sZPquj_TauGjUt{zKQt-pUSWyhY2Dc8d|;Z9xxG(pDBT3vW6S7>fdmca+Az@vMXt4ke^;TtbRhNElT5jlZ7YpReW5OI5D5e&g
21y%)9T_JsnBpTVqQ`shpa5q}SK1OXzR7Nd@nK^5NpvHe>>>u8_f&*=Z`-viL>hd$4&ooLv<%{;f~6Q-|yo*}>WUQYR-
@;(p0FYfKkd^Eu)$Lo4K-eCyS^*x+!;q>)Q%lk7!o8H?w(yP&Ux<7+GHB6`aFlaaTUV883N&OZ)g=yxM<d3{K=(mjL-
G5j1US?{X;{AkkeV8&G_FnMXQ~NE*`LV|`ub}rQ!*pqng?Wp<3c5e2mx2cWa{nYu-+Ly#-*K`}GTV@q5CsqInGnVQa-
ReZ?&^(D4Nmk!KJ8{9dF{TaH$q*xxgSE-KA;CeeEgBV$84S6$2-*n!8>RA9)pkfxt`kt!8@<M$LsnDp_)UbuXxiz&v(3Oy^nSY-
W(KW9^v<6&zYlz*wNUJICRX89b+6jdmMA5pL^VgNe4G`eD(uA{XB=f1(RmqVdmY94Zfd`4NSUt;+XXcd^#xmIp!IxI%enE`@A2xb
&UI4;a3bho|S&qa5;t@l&znW{#|(X^qJwTcl8tcN1Y$eTwC|?84NpS`_~PR$FqZf@$-l2-1*_Pc=nS&FU+lf({KT{9W-
9o{v^&FlKtKO&tl$3pAG))ICr*n>KOlG%sc2>-
{WpM54;WY&XUFV(PQ{`%<#H;Jr*AHb^q@8BQBn2Yv?uqxo3mtaq+Xy17BG9|Bq!$@pq~vmMx`)?^w2UEb+JXPLF>hH|tzW-vckjs
WV;c`F&*{^?sasZ@+Zt@82_i;?c#ZdELLXkNQbhL&r_?H*aG+b<BE8Pj&F{??e7pJo=Px*nHK|+V^kR4*RHMcExXhwx@bM?!2duI
<GYOcZL6zp6aai{@bJ%)_hP;^|_ex@9U$^ab*4t|Fw8=Q2RO8eb{m4Rs8$>+i>LI;b*@CQ!d7RPrd<P4h~)qUs&@TwyU8;KT)1f>
h~kEJX;^<>;BBY9^ap>kFhUbE9^(gA%}4ye<;77Sbm{y@f`I`&%W2c9v$>PlF!rsXcc(0qdbm(p)gaGqzAf`RBqwp|HI}hAJ2%3Z
GsgK>8l*0XHN-WmYt*EqnxT7YEq@0hz_3Zzwt=BW1Q-
tZEC&3HfKH7^l;5h<$nIhr2+mAqK=XLXlX|!>!BSPxxtPzb!i74ZvB6;+_#dMS3S&5MxJ7)nSaxIAhG569M5zK6>ySlDYK81cp~4
FcaatQ>Gnz)674`n{|f&e88au9L*6Rw(i-YC;FJj9*IVoEDUS9ajtids{}Dc#r{2Z$?f3700QbOtCj
"""



def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def find_source(root, output):
    for candidate in sorted(root.glob("*.exe")):
        if candidate.resolve() == output.resolve():
            continue
        data = candidate.read_bytes()
        digest = sha256(data)
        if digest == EXPECTED_SOURCE_SHA256:
            return candidate, bytearray(data)
    return None, None


def main():
    root = Path(__file__).resolve().parent
    output = root / OUTPUT_EXE

    if output.exists() and sha256(output.read_bytes()) == EXPECTED_OUTPUT_SHA256:
        print(f"{OUTPUT_EXE} already exists and is valid.")
        return

    source, data = find_source(root, output)
    if source is None:
        raise SystemExit("No supported local executable was found in this folder.")

    patches = json.loads(zlib.decompress(base64.b85decode(''.join(PATCH_PAYLOAD.split()))).decode('ascii'))
    patched_bytes = 0
    for offset, replacement_hex in patches:
        replacement = bytes.fromhex(replacement_hex)
        data[offset:offset + len(replacement)] = replacement
        patched_bytes += len(replacement)

    output_hash = sha256(data)
    if output_hash != EXPECTED_OUTPUT_SHA256:
        raise SystemExit(f"Patch verification failed. Got {output_hash}.")

    output.write_bytes(data)
    print(f"Created {OUTPUT_EXE} from {source.name} ({patched_bytes} patched bytes).")


if __name__ == "__main__":
    main()
