# -*- coding: utf-8 -*-
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets", "components")
D = json.load(open(os.path.join(ASSETS, "_imgdata.json")))

def V(s):
    """Escape a value (which contains HTML markup) for an XML attribute."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def img_style(name, extra=""):
    return ("shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;"
            "aspect=fixed;%simage=data:image/png,%s;" % (extra, D[name]["b64"]))

cells = []
def node(id, value, x, y, w, h, style):
    cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                 '<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/></mxCell>'
                 % (id, V(value), style, x, y, w, h))
def img(id, name, x, y, w, h, extra=""):
    cells.append('<mxCell id="%s" value="" style="%s" vertex="1" parent="1">'
                 '<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/></mxCell>'
                 % (id, img_style(name, extra), x, y, w, h))
def edge(id, src, tgt, style, value="", points=None):
    geo = '<mxGeometry relative="1" as="geometry">'
    if points:
        geo += '<Array as="points">' + ''.join('<mxPoint x="%s" y="%s"/>' % (px, py) for px, py in points) + '</Array>'
    geo += '</mxGeometry>'
    cells.append('<mxCell id="%s" value="%s" style="%s" edge="1" source="%s" target="%s" parent="1">%s</mxCell>'
                 % (id, V(value), style, src, tgt, geo))

# ---- styles ----
LBL   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F7;strokeColor=#95A5A6;fontSize=10;align=center;spacingTop=2;"
LBLpv = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#F9A825;fontSize=10;align=center;"
LBLbi = "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;fontSize=10;align=center;"
BADGE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#263238;strokeColor=none;fontColor=#FFFFFF;fontSize=16;fontStyle=1;"
FUSE  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFF3CD;strokeColor=#C0392B;fontSize=8;align=center;"
BOXr  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FDEAEA;strokeColor=#C0392B;fontSize=9;align=center;"
GRIDs = "rounded=1;whiteSpace=wrap;html=1;fillColor=#922B21;strokeColor=#5B1810;fontColor=#FFFFFF;fontSize=10;fontStyle=1;align=center;"
TABL  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#5D6D7E;strokeColor=#34495E;fontColor=#FFFFFF;fontSize=9;fontStyle=1;align=center;"

EP  = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#E60000;strokeWidth=3;fontSize=9;fontStyle=1;"
EN  = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=3;fontSize=9;fontStyle=1;"
EDC = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#B8860B;strokeWidth=2;fontSize=8;fontStyle=1;"
EDCb= "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#2E7D32;strokeWidth=2;fontSize=8;fontStyle=1;"
EAC = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#8B4513;strokeWidth=2;fontSize=9;fontStyle=1;"
ECOM= "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#1B75BB;strokeWidth=1;dashed=1;fontSize=8;"
EPE = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#1E8449;strokeWidth=2;fontSize=8;"

# unicode helpers
X = "×"; MD = "—"; MID = "·"; MIN = "−"; SQ = "²"
ARR = "→"; WARN = "⚠"; DEG = "°"; HL = "━"; DL = "┄"; NB = " "

# ---- TITLE ----
node("title",
     "<b>INSTALLATION PHOTOVOLTAIQUE 48V " + MD + " SYNOPTIQUE</b><br/>"
     "18" + X + " AIKO Neostar 2S+ 500W (9 kWc) " + MID + " Victron MPPT RS 450/100 + 2" + X + " MPPT 150/35 " + MID +
     " MultiPlus-II 48/10000 " + MID + " Parc Pylontech US5000 " + MID + " Cerbo GX",
     40, 12, 1670, 46,
     "text;html=1;rounded=1;fillColor=#D6EAF8;strokeColor=#2E86C1;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=13;")

# ---- PV FIELDS ----
A, B, C = 480, 880, 1230
img("pvA_img", "aiko_mono.png",     A-43, 72, 86, 145)
img("pvB_img", "aiko_mono.png",     B-43, 72, 86, 145)
img("pvC_img", "aiko_bifacial.png", C-43, 72, 86, 145)
node("pvA_badge", X + "12", A+50, 105, 64, 34, BADGE)
node("pvB_badge", X + "3",  B+50, 105, 56, 34, BADGE)
node("pvC_badge", X + "3",  C+50, 105, 56, 34, BADGE)
node("pvA_lbl", "<b>CHAMP 1</b><br/>12" + X + " AIKO 500W (mono)<br/>2 strings 6S " + MID + " 6.0 kWc<br/>Vstring 270V (~291V a froid)", A-140, 228, 280, 78, LBLpv)
node("pvB_lbl", "<b>CHAMP 2</b><br/>3" + X + " AIKO 500W (mono)<br/>3S " + MID + " 1.5 kWc<br/>Vstring 135V (~145V a froid)", B-140, 228, 280, 78, LBLpv)
node("pvC_lbl", "<b>CHAMP 3 " + MD + " BIFACIAL</b><br/>3" + X + " AIKO 500W ABC bifacial<br/>3S " + MID + " 1.5 kWc (+gain face arriere)<br/>Vstring 135V (~145V a froid)", C-140, 228, 280, 78, LBLbi)

# ---- CHARGE CONTROLLERS ----
img("rs450_img", "rs450_100.png",   A-60, 330, 120, 168)
img("mppt1_img", "mppt_150_35.png", B-78, 360, 156, 96)
img("mppt2_img", "mppt_150_35.png", C-78, 360, 156, 96)
node("rs450_lbl", "<b>SmartSolar MPPT RS 450/100</b><br/>Vin 450V max " + MID + " 100A " + MID + " 2 trackers<br/>P max ~7500W " + MID + " comm VE.Can", A-150, 506, 300, 56, LBL)
node("mppt1_lbl", "<b>SmartSolar MPPT 150/35</b><br/>Vin 150V max " + MID + " 35A<br/>comm VE.Direct", B-130, 470, 260, 52, LBL)
node("mppt2_lbl", "<b>SmartSolar MPPT 150/35</b> (bifacial)<br/>Vin 150V max " + MID + " 35A<br/>comm VE.Direct", C-130, 470, 260, 52, LBL)

node("warn",
     "<b>" + WARN + " ATTENTION MPPT 150/35</b><br/>3S : Voc ~135V (STC), ~145V a -10" + DEG + "C<br/>"
     "tres proche des 150V max.<br/>Coeff. temp. Voc -0.22%/" + DEG + "C " + MD + " verifier<br/>ou limiter a 2 panneaux en serie.",
     1190, 560, 280, 92,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDE7;strokeColor=#F39C12;fontSize=9;align=left;spacingLeft=8;")

node("fzRS", "Fus.<br/>125A", A-22, 600, 44, 40, FUSE)
node("fzM1", "Fus.<br/>50A",  B-22, 600, 44, 40, FUSE)
node("fzM2", "Fus.<br/>50A",  C-22, 600, 44, 40, FUSE)

# ---- DC BUS / LYNX ----
node("lynxLbl", "<b>VICTRON LYNX " + MD + " Bus DC 48V</b> (Power-In + Distributor + Shunt VE.Can)", 250, 666, 760, 18,
     "text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=11;fontColor=#10293b;")
node("busPos", "+ BUS 48V", 250, 688, 1080, 22,
     "rounded=2;whiteSpace=wrap;html=1;fillColor=#E60000;strokeColor=#8B0000;fontColor=#FFFFFF;fontSize=11;fontStyle=1;")
node("busNeg", MIN + " BUS (negatif commun)", 250, 742, 1080, 22,
     "rounded=2;whiteSpace=wrap;html=1;fillColor=#1A1A1A;strokeColor=#000000;fontColor=#FFFFFF;fontSize=11;fontStyle=1;")
img("lynx_img", "lynx_distributor.png", 1140, 688, 190, 76)

# ---- BATTERY ----
img("bat1", "pylontech_us5000.png", 70, 800, 170, 65)
img("bat2", "pylontech_us5000.png", 70, 868, 170, 65)
img("bat3", "pylontech_us5000.png", 70, 936, 170, 65)
node("bat_lbl", "<b>Parc batterie Pylontech</b><br/>n" + X + " US5000 " + MD + " 48V " + MID + " 4.8kWh " + MID + " 100A<br/>en parallele " + MID + " BMS CAN bus",
     40, 1006, 230, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#EAF7F0;strokeColor=#1E8449;fontSize=9;align=center;")
node("batFuse", "<b>Fusible<br/>Class-T 250A</b>", 300, 772, 88, 46, FUSE)
img("batSwitch", "battery_switch.png", 305, 868, 78, 80)
node("batSw_lbl", "Sectionneur<br/>batterie 275A", 290, 950, 110, 30, "text;html=1;align=center;fontSize=8;")

# ---- MULTIPLUS ----
img("mp_img", "multiplus_10k.png", 540, 812, 120, 200)
node("mp_lbl", "<b>Victron MultiPlus-II 48/10000</b><br/>Onduleur + Chargeur " + MID + " 10000VA<br/>Charge 140A " + MID + " Transfert 100A<br/>comm VE.Bus",
     490, 1018, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#D6EAF8;strokeColor=#2E86C1;fontSize=9;align=center;")
node("mpFuse", "<b>Fusible 300A</b><br/>Class-T", 545, 772, 110, 34, FUSE)

# ---- GRID + AC ----
node("grid",   "<b>RESEAU EDF</b><br/>230V / 50Hz<br/>AC-In", 770, 800, 140, 66, GRIDs)
node("djGrid", "<b>Disj. 2P 50A</b><br/>+ parafoudre AC T2<br/>protection AC-In", 765, 892, 150, 58, BOXr)
node("acProt", "<b>Protection AC-Out</b><br/>Diff. 2P 40A 30mA type A<br/>+ parafoudre AC T2 40kA", 720, 1022, 205, 60, BOXr)
node("tableau","<b>TABLEAU DIVISIONNAIRE AC</b><br/>Disj. par circuit (10/16/20A)<br/>Diff. 30mA par groupe", 935, 1022, 220, 60, TABL)

# ---- CERBO ----
img("cerbo_img", "cerbo_gx.png", 1505, 430, 180, 120)
node("cerbo_lbl", "<b>Victron Cerbo GX + GX Touch</b><br/>Supervision / monitoring<br/>VE.Can " + MID + " VE.Direct " + MID + " VE.Bus " + MID + " CAN-BMS",
     1475, 556, 240, 56, "rounded=1;whiteSpace=wrap;html=1;fillColor=#2C3E50;strokeColor=#1A252F;fontColor=#ECF0F1;fontSize=9;align=center;")

# ---- EARTH ----
node("terre", "<b>BARRETTE DE TERRE</b><br/>Liaison equipotentielle<br/>Chassis PV " + MID + " MPPT " + MID + " MultiPlus<br/>Bati batterie " + MID + " coffrets<br/>Cable V/J 16mm" + SQ + " " + ARR + " piquet",
     1475, 800, 240, 100, "rounded=0;whiteSpace=wrap;html=1;fillColor=#EAF7F0;strokeColor=#1E8449;fontSize=9;align=center;")
node("terreSym", "", 1565, 912, 60, 50, "shape=mxgraph.electrical.signal_sources.signal_ground;html=1;strokeColor=#1E8449;strokeWidth=2;")

# ---- LEGEND ----
node("legend",
     "<b>LEGENDE</b><br/>"
     "<font color='#E60000'>" + HL + HL + "</font> DC + (48V)" + NB + NB + "<font color='#111111'>" + HL + HL + "</font> DC " + MIN + "<br/>"
     "<font color='#B8860B'>" + HL + HL + "</font> String PV" + NB + NB + "<font color='#8B4513'>" + HL + HL + "</font> AC 230V<br/>"
     "<font color='#1E8449'>" + HL + HL + "</font> Terre PE" + NB + NB + "<font color='#1B75BB'>" + DL + DL + "</font> Communication",
     40, 100, 352, 116,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#F8F9F9;strokeColor=#7F8C8D;fontSize=9;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6;")

# ================= EDGES =================
edge("e_pvA", "pvA_img", "rs450_img", EDC, "4mm" + SQ + " " + MID + " 2 strings")
edge("e_pvB", "pvB_img", "mppt1_img", EDC, "4mm" + SQ)
edge("e_pvC", "pvC_img", "mppt2_img", EDCb, "4mm" + SQ)

edge("e_rs_f", "rs450_img", "fzRS", EP, "16mm" + SQ)
edge("e_f_rs", "fzRS", "busPos", EP)
edge("e_m1_f", "mppt1_img", "fzM1", EP, "10mm" + SQ)
edge("e_f_m1", "fzM1", "busPos", EP)
edge("e_m2_f", "mppt2_img", "fzM2", EP, "10mm" + SQ)
edge("e_f_m2", "fzM2", "busPos", EP)

edge("e_rs_n", "rs450_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.21;entryY=0;", MIN)
edge("e_m1_n", "mppt1_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.58;entryY=0;", MIN)
edge("e_m2_n", "mppt2_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.90;entryY=0;", MIN)

edge("e_b12", "bat1", "bat2", "edgeStyle=none;html=1;endArrow=none;strokeColor=#888888;strokeWidth=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;")
edge("e_b23", "bat2", "bat3", "edgeStyle=none;html=1;endArrow=none;strokeColor=#888888;strokeWidth=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;")
edge("e_bf", "bat1", "batFuse", EP, "95mm" + SQ + " +")
edge("e_fb", "batFuse", "busPos", EP, "", [(344, 740)])
edge("e_bs", "bat3", "batSwitch", EN, "95mm" + SQ + " " + MIN)
edge("e_sb", "batSwitch", "busNeg", EN)

edge("e_mp_pf", "busPos", "mpFuse", EP, "70mm" + SQ + " +")
edge("e_mpf_mp", "mpFuse", "mp_img", EP)
edge("e_mp_n", "busNeg", "mp_img", EN, "70mm" + SQ + " " + MIN)

edge("e_g_dj", "grid", "djGrid", EAC)
edge("e_dj_mp", "djGrid", "mp_img", EAC, "AC-In 6mm" + SQ)
edge("e_mp_acp", "mp_img", "acProt", EAC, "AC-Out 6mm" + SQ)
edge("e_acp_tab", "acProt", "tableau", EAC)

for cid, src in [("c1", "rs450_img"), ("c2", "mppt1_img"), ("c3", "mppt2_img"), ("c4", "mp_img"), ("c5", "bat2")]:
    edge("e_" + cid, src, "cerbo_img", ECOM)

edge("e_pe1", "mp_img", "terre", EPE, "16mm" + SQ + " PE")
edge("e_pe2", "terre", "terreSym", EPE)

# ---- assemble ----
xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml += '<mxfile host="app.diagrams.net" modified="2026-06-19" version="21.0.0">\n'
xml += '  <diagram id="pv_synoptique" name="Synoptique PV (images)">\n'
xml += ('    <mxGraphModel dx="1600" dy="1100" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1754" pageHeight="1300" math="0" shadow="0">\n')
xml += '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
xml += "\n".join("        " + c for c in cells)
xml += '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n'

outp = os.path.join(ROOT, "installation_pv_synoptique.drawio")
open(outp, "w", encoding="utf-8").write(xml)
print("written", outp, "size KB:", os.path.getsize(outp) // 1024, "cells:", len(cells))
