# -*- coding: utf-8 -*-
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets", "components")
D = json.load(open(os.path.join(ASSETS, "_imgdata.json")))

def V(s):
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
LBLpv = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E1;strokeColor=#F9A825;fontSize=9;align=center;"
LBLbi = "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;fontSize=9;align=center;"
LBL   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F7;strokeColor=#95A5A6;fontSize=10;align=center;"
BADGE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#263238;strokeColor=none;fontColor=#FFFFFF;fontSize=15;fontStyle=1;"
COFFBOX = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FDEAEA;strokeColor=#C0392B;fontSize=9;align=center;verticalAlign=top;dashed=1;fontStyle=1;spacingTop=3;"
TXT   = "text;html=1;fillColor=none;strokeColor=none;align=left;fontSize=8;verticalAlign=middle;"
TXTc  = "text;html=1;fillColor=none;strokeColor=none;align=center;fontSize=8;"
BOX   = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FDEAEA;strokeColor=#C0392B;fontSize=8;align=left;verticalAlign=middle;spacingLeft=4;"
GRIDs = "rounded=1;whiteSpace=wrap;html=1;fillColor=#922B21;strokeColor=#5B1810;fontColor=#FFFFFF;fontSize=10;fontStyle=1;align=center;"
TABL  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#5D6D7E;strokeColor=#34495E;fontColor=#FFFFFF;fontSize=9;fontStyle=1;align=center;"
INVL  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FCE4B6;strokeColor=#E67E22;fontSize=9;fontStyle=1;align=center;"

EP  = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#E60000;strokeWidth=3;fontSize=9;fontStyle=1;"
EN  = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=3;fontSize=9;fontStyle=1;"
EDC = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#B8860B;strokeWidth=2;fontSize=8;fontStyle=1;"
EDCb= "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#2E7D32;strokeWidth=2;fontSize=8;fontStyle=1;"
EAC = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#8B4513;strokeWidth=2;fontSize=9;fontStyle=1;"
ECOM= "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#1B75BB;strokeWidth=1;dashed=1;fontSize=8;"
EPE = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#1E8449;strokeWidth=2;fontSize=8;"
EOPEN = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=cross;startArrow=none;strokeColor=#922B21;strokeWidth=1.5;dashed=1;fontSize=8;"

X="×"; MD="—"; MID="·"; MIN="−"; SQ="²"; ARR="→"; WARN="⚠"; DEG="°"; HL="━"; DL="┄"; NB=" "; N1="①"; N2="②"

# ---- TITLE + LEGEND ----
node("title",
     "<b>INSTALLATION PHOTOVOLTAIQUE 48V " + MD + " OFF-GRID (isolee du reseau EDF)</b><br/>"
     "18" + X + " AIKO Neostar 2S+ 500W (9 kWc) " + MID + " MPPT RS 450/100 + 2" + X + " MPPT 150/35 " + MID +
     " MultiPlus-II 48/10000 " + MID + " Parc Pylontech US5000 " + MID + " Cerbo GX " + MID +
     " Alimentation maison au choix (inverseur de source)",
     30, 12, 1694, 50,
     "text;html=1;rounded=1;fillColor=#D6EAF8;strokeColor=#2E86C1;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=13;")
node("legend",
     "<b>LEGENDE</b><br/>"
     "<font color='#E60000'>" + HL + HL + "</font> DC + (48V)" + NB + NB + "<font color='#111111'>" + HL + HL + "</font> DC " + MIN + "<br/>"
     "<font color='#B8860B'>" + HL + HL + "</font> String PV" + NB + NB + "<font color='#8B4513'>" + HL + HL + "</font> AC 230V<br/>"
     "<font color='#1E8449'>" + HL + HL + "</font> Terre PE" + NB + NB + "<font color='#1B75BB'>" + DL + DL + "</font> Communication<br/>"
     "<i>Off-grid " + MID + " norme UTE C15-712-2 (PV autonome + stockage)</i>",
     40, 100, 352, 128,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#F8F9F9;strokeColor=#7F8C8D;fontSize=9;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6;")

# ---- PV FIELDS ----
A, B, C = 480, 880, 1230
img("pvA_img", "aiko_mono.png",     A-43, 72, 86, 145)
img("pvB_img", "aiko_mono.png",     B-43, 72, 86, 145)
img("pvC_img", "aiko_bifacial.png", C-43, 72, 86, 145)
node("pvA_badge", X + "12", A+48, 74, 60, 30, BADGE)
node("pvB_badge", X + "3",  B+48, 74, 56, 30, BADGE)
node("pvC_badge", X + "3",  C+48, 74, 56, 30, BADGE)
node("pvA_lbl", "<b>CHAMP 1</b><br/>12" + X + " AIKO 500W (mono)<br/>2 strings 6S " + MID + " 6.0 kWc<br/>Vstring 270V (~291V froid)", A+48, 110, 178, 104, LBLpv)
node("pvB_lbl", "<b>CHAMP 2</b><br/>3" + X + " AIKO 500W (mono)<br/>3S " + MID + " 1.5 kWc<br/>Vstring 135V (~145V froid)", B+48, 110, 178, 104, LBLpv)
node("pvC_lbl", "<b>CHAMP 3 " + MD + " BIFACIAL</b><br/>3" + X + " AIKO 500W ABC bifacial<br/>3S " + MID + " 1.5 kWc (+arriere)<br/>Vstring 135V (~145V froid)", C+48, 110, 178, 104, LBLbi)

# ---- COFFRETS DC (boitier dashed + image parafoudre DC + texte) ----
def coffret(idp, cx, title, ucpv, secA, secV):
    node(idp + "_box", "<b>COFFRET DC " + MD + " " + title + "</b>", cx-106, 228, 212, 104, COFFBOX)
    img(idp + "_pf", "parafoudre_dc.png", cx-94, 256, 40, 66)
    node(idp + "_txt", "Parafoudre DC<br/>Type 2 (Ucpv " + ARR + " " + ucpv + ")<br/>Sectionneur DC " + secA + " " + secV + "<br/>Bornier (+/" + MIN + ")", cx-48, 252, 142, 74, TXT)
coffret("coffA", A, "Champ 1", "600V", "32A", "1000V")
coffret("coffB", B, "Champ 2", "300V", "25A", "600V")
coffret("coffC", C, "Champ 3", "300V", "25A", "600V")

# ---- CHARGE CONTROLLERS ----
img("rs450_img", "rs450_100.png",   A-60, 342, 120, 168)
img("mppt1_img", "mppt_150_35.png", B-78, 366, 156, 96)
img("mppt2_img", "mppt_150_35.png", C-78, 366, 156, 96)
node("rs450_lbl", "<b>SmartSolar MPPT RS 450/100</b><br/>Vin 450V max " + MID + " 100A " + MID + " 2 trackers<br/>P max ~7500W " + MID + " comm VE.Can", A-150, 516, 300, 52, LBL)
node("mppt1_lbl", "<b>SmartSolar MPPT 150/35</b><br/>Vin 150V max " + MID + " 35A " + MID + " VE.Direct", B-130, 472, 260, 46, LBL)
node("mppt2_lbl", "<b>SmartSolar MPPT 150/35</b> (bifacial)<br/>Vin 150V max " + MID + " 35A " + MID + " VE.Direct", C-130, 472, 260, 46, LBL)
node("warn",
     "<b>" + WARN + " ATTENTION MPPT 150/35</b><br/>3S : Voc ~135V (STC), ~145V a -10" + DEG + "C<br/>"
     "tres proche des 150V max.<br/>Coeff. Voc -0.22%/" + DEG + "C " + MD + " verifier<br/>ou limiter a 2 panneaux en serie.",
     1340, 232, 275, 92,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFDE7;strokeColor=#F39C12;fontSize=9;align=left;spacingLeft=8;")

# ---- DC BUS = 2x LYNX DISTRIBUTOR accoles (fusibles MPPT + 2x 200A MEGA) + barres ----
# unit 2 (2x 200A MEGA -> MultiPlus) glued left, unit 1 (4 MPPT slots) glued right
img("lynxMega_img", "lynx_mega.png",  480, 586, 240, 128)
img("lynx_img",     "lynx_fuses.png", 720, 586, 464, 128)
node("busPos", "", 250, 690, 1080, 20, "rounded=2;whiteSpace=wrap;html=1;fillColor=#E60000;strokeColor=#8B0000;")
node("busNeg", MIN + " BUS 48V (negatif commun)", 250, 718, 1080, 22,
     "rounded=2;whiteSpace=wrap;html=1;fillColor=#1A1A1A;strokeColor=#000000;fontColor=#FFFFFF;fontSize=11;fontStyle=1;")
node("lynxNote", "<b>2" + X + " Lynx Distributor accoles</b><br/>4 fusibles MPPT (1 slot libre)<br/>+ 2" + X + " 200A MEGA " + ARR + " MultiPlus " + ARR,
     24, 600, 224, 50, "text;html=1;strokeColor=none;fillColor=none;align=right;fontSize=9;fontColor=#10293b;")

# ---- BATTERY ----
img("bat1", "pylontech_us5000.png", 70, 800, 170, 65)
img("bat2", "pylontech_us5000.png", 70, 868, 170, 65)
img("bat3", "pylontech_us5000.png", 70, 936, 170, 65)
node("bat_lbl", "<b>Parc batterie Pylontech</b><br/>n" + X + " US5000 " + MD + " 48V " + MID + " 4.8kWh " + MID + " 100A<br/>en parallele (max 4-5) " + MID + " BMS CAN bus",
     40, 1006, 230, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#EAF7F0;strokeColor=#1E8449;fontSize=9;align=center;")
img("batFuse", "fusible_mega.png", 292, 760, 92, 47)
node("batFuse_lbl", "Fusible Class-T 250A", 280, 808, 116, 16, TXTc)
img("batSwitch", "battery_switch.png", 305, 866, 78, 80)
node("batSw_lbl", "Sectionneur batterie 275A", 280, 948, 126, 16, TXTc)

# ---- MULTIPLUS ----
img("mp_img", "multiplus_10k.png", 540, 812, 120, 200)
node("mp_lbl", "<b>Victron MultiPlus-II 48/10000</b><br/>Onduleur off-grid + Chargeur<br/>10000VA " + MID + " charge 140A " + MID + " VE.Bus",
     672, 892, 168, 92, "rounded=1;whiteSpace=wrap;html=1;fillColor=#D6EAF8;strokeColor=#2E86C1;fontSize=9;align=center;")
node("acInNote", "<b>AC-In NON raccorde</b><br/>Installation isolee d'EDF :<br/>pas de charge/transfert<br/>depuis le reseau<br/>(reserve groupe electrogene)",
     672, 812, 168, 74, "rounded=1;whiteSpace=wrap;html=1;fillColor=#FDEDEC;strokeColor=#922B21;fontSize=8;align=center;dashed=1;")

# ---- AC : sortie off-grid + arrivee EDF + inverseur de source -> maison ----
node("acOut_box", "", 468, 1086, 218, 70, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FDEAEA;strokeColor=#C0392B;")
img("acOut_pf", "parafoudre_ac.png", 474, 1092, 36, 58)
node("acOut_txt", "<b>Protection sortie OFF-GRID</b><br/>Diff. 2P 40A 30mA type A<br/>+ parafoudre AC Type 2", 516, 1090, 164, 62, TXT)
img("inv_img", "inverseur_source.png", 716, 1082, 86, 86)
node("inv_lbl", "<b>INVERSEUR DE SOURCE 2P</b><br/>break-before-make<br/>" + N1 + " INSTALLATION (off-grid) / " + N2 + " RESEAU EDF<br/><b>isolation galvanique d'EDF</b>",
     808, 1086, 206, 82, INVL)
node("grid", "<b>RESEAU EDF</b><br/>230V / 50Hz<br/>(source secours)", 1030, 1006, 150, 60, GRIDs)
node("djGrid_box", "", 1022, 1086, 205, 70, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FDEAEA;strokeColor=#C0392B;")
img("djGrid_pf", "parafoudre_ac.png", 1028, 1092, 36, 58)
node("djGrid_txt", "<b>Arrivee EDF</b><br/>Disj. 2P 50A<br/>+ parafoudre AC Type 2", 1070, 1090, 152, 62, TXT)
node("tableau", "<b>TABLEAU MAISON (AC-Out)</b><br/>Disj. par circuit (10/16/20A)<br/>Diff. 30mA par groupe", 690, 1212, 215, 62, TABL)

# ---- CERBO ----
img("cerbo_img", "cerbo_gx.png", 1505, 430, 180, 120)
node("cerbo_lbl", "<b>Victron Cerbo GX</b><br/>Supervision / monitoring<br/>VE.Can " + MID + " VE.Direct " + MID + " VE.Bus " + MID + " CAN-BMS",
     1475, 556, 240, 56, "rounded=1;whiteSpace=wrap;html=1;fillColor=#2C3E50;strokeColor=#1A252F;fontColor=#ECF0F1;fontSize=9;align=center;")

# ---- EARTH ----
node("terre", "<b>BARRETTE DE TERRE</b><br/>Liaison equipotentielle<br/>Chassis PV " + MID + " MPPT " + MID + " MultiPlus<br/>Bati batterie " + MID + " coffrets<br/>PE 4-6mm" + SQ + " (DC) " + MID + " 16mm" + SQ + " " + ARR + " piquet",
     1475, 800, 240, 100, "rounded=0;whiteSpace=wrap;html=1;fillColor=#EAF7F0;strokeColor=#1E8449;fontSize=9;align=center;")
node("terreSym", "", 1565, 912, 60, 50, "shape=mxgraph.electrical.signal_sources.signal_ground;html=1;strokeColor=#1E8449;strokeWidth=2;")

# ================= EDGES =================
# PV -> coffret DC -> MPPT
edge("e_pvA", "pvA_img", "coffA_box", EDC, "4mm" + SQ + " (2 strings)")
edge("e_pvB", "pvB_img", "coffB_box", EDC, "4mm" + SQ)
edge("e_pvC", "pvC_img", "coffC_box", EDCb, "4mm" + SQ)
edge("e_cA", "coffA_box", "rs450_img", EDC, "6mm" + SQ)
edge("e_cB", "coffB_box", "mppt1_img", EDC, "6mm" + SQ)
edge("e_cC", "coffC_box", "mppt2_img", EDCb, "6mm" + SQ)

# MPPT + -> fusibles sur le Lynx unit 1 (slots 1/2/3, slot 4 libre)
edge("e_rs_f", "rs450_img", "lynx_img", EP + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.138;entryY=0;entryDx=0;entryDy=0;", "16mm" + SQ)
edge("e_m1_f", "mppt1_img", "lynx_img", EP + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.379;entryY=0;entryDx=0;entryDy=0;", "10mm" + SQ)
edge("e_m2_f", "mppt2_img", "lynx_img", EP + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.621;entryY=0;entryDx=0;entryDy=0;", "10mm" + SQ)
# MPPT - -> busNeg
edge("e_rs_n", "rs450_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.21;entryY=0;", MIN)
edge("e_m1_n", "mppt1_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.58;entryY=0;", MIN)
edge("e_m2_n", "mppt2_img", "busNeg",
     "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#111111;strokeWidth=2;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.90;entryY=0;", MIN)

# battery
edge("e_b12", "bat1", "bat2", "edgeStyle=none;html=1;endArrow=none;strokeColor=#888888;strokeWidth=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;")
edge("e_b23", "bat2", "bat3", "edgeStyle=none;html=1;endArrow=none;strokeColor=#888888;strokeWidth=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;")
edge("e_bf", "bat1", "batFuse", EP, "2" + X + "50mm" + SQ + " +")
edge("e_fb", "batFuse", "busPos", EP, "", [(338, 712)])
edge("e_bs", "bat3", "batSwitch", EN, "2" + X + "50mm" + SQ + " " + MIN)
edge("e_sb", "batSwitch", "busNeg", EN)

# bus -> multiplus  (+ protege par les 2x 200A MEGA du 2e Lynx Distributor)
edge("e_mp_pos", "lynxMega_img", "mp_img",
     EP + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;",
     "2" + X + "50mm" + SQ + " + (2" + X + "200A MEGA)")
edge("e_mp_n", "busNeg", "mp_img", EN, "2" + X + "50mm" + SQ + " " + MIN)

# AC
edge("e_acin_open", "mp_img", "acInNote", EOPEN, "AC-In (ouvert)")
edge("e_mp_acout", "mp_img", "acOut_box", EAC, "AC-Out 6mm" + SQ)
edge("e_acout_inv", "acOut_box", "inv_img", EAC, N1 + " Installation")
edge("e_grid_dj", "grid", "djGrid_box", EAC)
edge("e_dj_inv", "djGrid_box", "inv_img", EAC, N2 + " Reseau EDF")
edge("e_inv_tab", "inv_img", "tableau", EAC, "alimentation maison")

# comms
for cid, src in [("c1", "rs450_img"), ("c2", "mppt1_img"), ("c3", "mppt2_img"), ("c4", "mp_img"), ("c5", "bat2")]:
    edge("e_" + cid, src, "cerbo_img", ECOM)

# earth
edge("e_pe1", "mp_img", "terre", EPE, "16mm" + SQ + " PE")
edge("e_pe2", "terre", "terreSym", EPE)

# ---- assemble ----
xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml += '<mxfile host="app.diagrams.net" modified="2026-06-19" version="21.0.0">\n'
xml += '  <diagram id="pv_synoptique" name="Synoptique PV off-grid">\n'
xml += ('    <mxGraphModel dx="1600" dy="1100" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1754" pageHeight="1320" math="0" shadow="0">\n')
xml += '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
xml += "\n".join("        " + c for c in cells)
xml += '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n'

outp = os.path.join(ROOT, "installation_pv_synoptique.drawio")
open(outp, "w", encoding="utf-8").write(xml)
print("written", outp, "size KB:", os.path.getsize(outp) // 1024, "cells:", len(cells))
