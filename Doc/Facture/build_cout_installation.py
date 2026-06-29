# -*- coding: utf-8 -*-
"""
Génère les PDF de coût d'installation PV à partir de HTML (rendu par Edge headless).

Sorties (dans ce dossier) :
  - cout_installation.pdf        (FR, installation initiale + facture Altamira)
  - cout_installation_de.pdf     (DE, idem en allemand)
  - cout_installation_v2_de.pdf  (DE, extension +12 kWc)

Le HTML source est conservé dans ./src/ pour pouvoir ré-éditer facilement.
Relancer :  python build_cout_installation.py
"""
import subprocess
import pathlib

BASE = pathlib.Path(__file__).parent
SRC = BASE / "src"
SRC.mkdir(exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# --------------------------------------------------------------------------- CSS
CSS = """
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
@page{size:A4;margin:12mm 11mm}
body{font-family:"Segoe UI",Arial,sans-serif;color:#1f2933;font-size:10.5px;line-height:1.45;margin:0}
.header{background:linear-gradient(135deg,#0f766e,#0b3d3a);color:#fff;padding:15px 18px;border-radius:8px}
.header h1{margin:0;font-size:19px;font-weight:700}
.header .sub{margin-top:5px;font-size:11px;color:#d1faf4}
.meta{font-size:9px;color:#6b7280;margin:8px 2px 2px;line-height:1.55}
.meta code{font-family:Consolas,monospace;color:#0b3d3a;background:#ecfdf9;padding:0 3px;border-radius:3px}
h2.section{font-size:13px;margin:15px 0 6px;padding:5px 9px;background:#ecfdf9;border-left:4px solid #0f766e;border-radius:3px;color:#0b3d3a;break-after:avoid;page-break-after:avoid}
h3.sub{font-size:11px;margin:11px 0 4px;color:#374151;display:flex;justify-content:space-between;align-items:flex-end;gap:10px;break-after:avoid;page-break-after:avoid}
.unit{break-inside:avoid;page-break-inside:avoid}
h3.sub .desc{font-weight:400;color:#6b7280;font-size:9px}
.badge{font-size:8.5px;font-weight:600;color:#0b3d3a;background:#d1faf4;padding:2px 8px;border-radius:10px;white-space:nowrap}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:9.3px;margin-bottom:2px}
thead th{background:#0b3d3a;color:#fff;text-align:left;padding:5px 7px;font-weight:600}
th.r,td.r{text-align:right}
th.c,td.c{text-align:center}
tbody td{padding:4px 7px;border-bottom:1px solid #e3e8ee;vertical-align:top}
tbody tr:nth-child(even):not(.sum):not(.grand) td{background:#f6fafb}
td.ref{font-family:Consolas,monospace;font-size:8.6px;color:#475569;white-space:nowrap}
td.tot{font-weight:700;color:#0b3d3a;white-space:nowrap}
a.lk{color:#0d9488;text-decoration:none;font-weight:600;white-space:nowrap}
.src{color:#6b7280;font-size:8.8px}
tr.sum td{background:#eef6f5;font-weight:600}
tr.sum td.lbl{text-align:right;color:#374151}
tr.grand td{background:#0f766e;color:#fff;font-weight:700;font-size:10.2px}
tr.grand td.lbl{text-align:right}
tr,td,th{break-inside:avoid;page-break-inside:avoid}
.note{font-size:8.6px;color:#6b7280;margin:3px 2px 0;font-style:italic}
ul.notes{font-size:9.4px;margin:5px 0;padding-left:16px}
ul.notes li{margin:2.5px 0}
ul.links{font-size:8.7px;color:#475569;margin:4px 0;padding-left:15px;columns:1}
ul.links li{margin:1.5px 0}
.footer{margin-top:14px;border-top:1px solid #e3e8ee;padding-top:6px;font-size:8.2px;color:#6b7280;font-style:italic}
"""

# ---------------------------------------------------------------------- helpers
def page(title, lang, body):
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>')

def lk(url, label):
    return f'<a class="lk" href="{url}">{label}</a>'

# column classes for the invoice tables: name / ref / qty / unit / total / link
COLS = ["", "ref c", "c", "r", "tot r", "c"]

def table(headers, rows, sums):
    """headers: list[(label,cls)] ; rows: list[list[6 cells]] ; sums: list[(label,value,cls)]"""
    h = "".join(f'<th class="{c}">{lbl}</th>' for lbl, c in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f'<td class="{c}">{v}</td>' for v, c in zip(r, COLS)) + "</tr>"
    n = len(headers)
    for label, value, cls in sums:
        vcls = "tot r" if cls == "sum" else "r"
        body += (f'<tr class="{cls}"><td class="lbl" colspan="{n-1}">{label}</td>'
                 f'<td class="{vcls}">{value}</td></tr>')
    return f'<div class="unit"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'

def render(path, html):
    path.write_text(html, encoding="utf-8")

def to_pdf(html_path, pdf_path):
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
                   check=True, capture_output=True)
    print(f"  -> {pdf_path.name}")

# product URLs (suppliers)
U = {
    "aiko_mono": "https://kitsolaire-discount.com/fr/recherche?search_query=NEOSTAR+2S",
    "lynx_dist": "https://kitsolaire-discount.com/fr/protections-batterie/1995-systemes-distribution-dc-lynx-distributor-1000v-victron-energy-9085823106314.html",
    "mppt15035": "https://kitsolaire-discount.com/fr/regulateurs-de-charge/137-regulateur-solaire-smartsolar-mppt-15035-1224v-50a-8424511843192.html",
    "cerbo": "https://kitsolaire-discount.com/fr/affichages-et-moniteurs/858-supervision-des-panneaux-et-du-systeme-cerbo-gx-victron-energy-9085823107069.html",
    "mpptrs": "https://kitsolaire-discount.com/fr/regulateurs-de-charge/1417-regulateur-de-charge-100a-mppt-rs-450100-smartsolar-victron-energy-9085823107465.html",
    "us5000": "https://kitsolaire-discount.com/fr/batteries-lithium/1623-batterie-lithium-48kwh-us5000-48v-100a-pylontech-9331416826511.html",
    "cab10r": "https://kitsolaire-discount.com/fr/cables-connectique-outils/450-cable-solaire-10-mm2-au-metre-rouge-8414822162976.html",
    "cab10n": "https://kitsolaire-discount.com/fr/cables-connectique-outils/446-cable-solaire-10-mm2-au-metre-noir-8414822162969.html",
    "cab25r": "https://kitsolaire-discount.com/fr/cables-connectique-outils/989-cable-solaire-10-mm2-au-metre-noir-9085823105270.html",
    "cab25n": "https://kitsolaire-discount.com/fr/cables-connectique-outils/988-cable-solaire-10-mm2-au-metre-noir-9085823105263.html",
    "cab50": "https://kitsolaire-discount.com/fr/recherche?search_query=50mm2+M10",
    "coffdc2": "https://kitsolaire-discount.com/fr/coffrets-de-protection/79-coffret-de-protection-dc-2pv-2-mppt-parafoudre-8414824003123.html",
    "multiplus": "https://kitsolaire-discount.com/fr/multiplus/2150-convertisseur-chargeur-10000va-48v-140100-multiplus-ii-victron-energy-9331416834530.html",
    "mega60": "https://allo.solar/mega-fusible-60a-32v-victron-energy.html",
    "mega200": "https://allo.solar/mega-fusible-200a-80v-sachet-5-pcs-victron-energy.html",
    "mega125": "https://allo.solar/mega-fusible-125a-58v-pour-produits-48v-victron-energy-1.html",
    "lynxct": "https://allo.solar/systemes-distribution-dc-lynx-class-t-distributor-1000v-m10-victron-energy.html",
    "batsw": "https://allo.solar/interrupteur-de-batterie-marche-arret-275a.html",
    "coffdc1": "https://allo.solar/coffret-dc-parafoudre-1-string-1-mppt-500v-technideal.html",
    "aiko_bi": "https://allo.solar/panneau-solaire-500wc-noir-double-vitrage-n-type-neostar-2s-aiko.html",
    "bosytro": "https://amazon.fr/dp/B0F7Y2HF28",
    "gxtouch": "https://kitsolaire-discount.com/fr/recherche?search_query=GX+Touch+50",
    "coffac": "https://kitsolaire-discount.com/fr/recherche?search_query=coffret+AC+32A+monophase",
    "fronius": "https://www.fronius.com/fr-fr/france/energie-solaire/produits/tous-les-produits/onduleurs/fronius-primo/fronius-primo-6-0-1",
    # Altamira
    "alt_plaque": "https://e-altamira.fr/fr_FR/p/Plaque-de-terre-Plaque-de-contact/138",
    "alt_borne": "https://e-altamira.fr/fr_FR/p/Borne-de-mise-a-terre-pour-cables-16mm-aluminium-anodise-A2/518",
    "alt_pcentr": "https://e-altamira.fr/fr_FR/p/Pince-centrale-H25-L50-brute-avec-vis-M8x20-et-insert-pour-panneaux-de-30mm/1020",
    "alt_plat": "https://e-altamira.fr/fr_FR/p/Pince-laterale-30mm-avec-vis-et-insert-Peint-en-noir/193",
    "alt_adapt": "https://e-altamira.fr/fr_FR/p/Adaptateur-de-montage-M12-80x30x5-mm-acier-inoxydable-1.4301/604",
    "alt_conn": "https://e-altamira.fr/fr_FR/p/Connecteur-profile-12cm/85",
    "alt_ecrou": "https://e-altamira.fr/fr_FR/p/Ecrou-hexagonal-a-embase-DIN-6923-avec-denture-M10/139",
    "alt_tige": "https://e-altamira.fr/fr_FR/p/Tiges-filetees-DIN-976-M12x1000-Acier-inoxydable-A2/185",
    "alt_vis250": "https://e-altamira.fr/fr_FR/p/Vis-a-double-filetage-pour-la-fixation-de-modules-solaires-en-acier-A2-M12-x-250/601",
    "alt_vis300": "https://e-altamira.fr/fr_FR/p/Vis-a-double-filetage-pour-la-fixation-de-modules-solaires-en-acier-A2-M12-x-300/602",
    "alt_equerre": "https://e-altamira.fr/fr_FR/p/Equerre-dancrage-KK-11-210x43x40x4%2C0-mm/1271",
    "alt_profil": "https://e-altamira.fr/fr_FR/p/Profile-aluminium-240cm-40x40-pour-boulons-hexagonaux/462",
}

# Altamira rows reused (only product label differs FR/DE) -> (key, ref, qty, pu, total)
ALT = [
    ("alt_plaque", "PV-20", "21", "0,06 €", "1,33 €"),
    ("alt_borne", "PV-24-04", "10", "0,63 €", "6,32 €"),
    ("alt_pcentr", "PV-04-16", "40", "0,77 €", "30,63 €"),
    ("alt_plat", "PV-03-23", "14", "0,73 €", "10,23 €"),
    ("alt_adapt", "PV-07-07", "20", "0,30 €", "6,07 €"),
    ("alt_conn", "PV-18-02", "20", "0,67 €", "13,39 €"),
    ("alt_ecrou", "PV-13-02", "30", "0,07 €", "2,12 €"),
    ("alt_tige", "000-003", "5", "2,95 €", "14,77 €"),
    ("alt_vis250", "PV-06-06", "6", "1,60 €", "9,57 €"),
    ("alt_vis300", "PV-06-07", "6", "1,42 €", "8,52 €"),
    ("alt_equerre", "000-126", "4", "1,36 €", "5,42 €"),
    ("alt_profil", "PV-01-27", "24", "15,38 €", "369,15 €"),
]
ALT_FR_NAMES = [
    "Plaque de terre / plaque de contact",
    "Borne de mise à la terre — câbles 16 mm² alu anodisé A2",
    "Pince centrale H25 L50 + vis M8×20 (modules 30 mm)",
    "Pince latérale 30 mm + vis + insert — noir",
    "Adaptateur de montage M12 80×30×5 mm inox 1.4301",
    "Connecteur de profilé 12 cm",
    "Écrou hexagonal à embase DIN 6923 cranté M10",
    "Tige filetée DIN 976 M12×1000 — inox A2",
    "Vis à double filetage A2 M12×250",
    "Vis à double filetage A2 M12×300",
    "Équerre d'ancrage KK 11 — 210×43×40×4 mm",
    "Profilé aluminium 240 cm 40×40 (boulons hexagonaux)",
]
ALT_DE_NAMES = [
    "Erdungsplatte / Kontaktplatte",
    "Erdungsklemme — Kabel 16 mm² Alu eloxiert A2",
    "Mittelklemme H25 L50 + Schraube M8×20 (Module 30 mm)",
    "Endklemme 30 mm + Schraube + Einsatz — schwarz",
    "Montageadapter M12 80×30×5 mm Edelstahl 1.4301",
    "Profilverbinder 12 cm",
    "Sechskant-Flanschmutter DIN 6923 gezahnt M10",
    "Gewindestange DIN 976 M12×1000 — Edelstahl A2",
    "Doppelgewindeschraube A2 M12×250",
    "Doppelgewindeschraube A2 M12×300",
    "Ankerwinkel KK 11 — 210×43×40×4 mm",
    "Aluminiumprofil 240 cm 40×40 (für Sechskantschrauben)",
]


def altamira_rows(names, fiche):
    rows = []
    for nm, (key, ref, qty, pu, tot) in zip(names, ALT):
        rows.append([nm, ref, qty, pu, tot, lk(U[key], fiche)])
    return rows


# ============================================================ FR — installation
def build_main_fr():
    H = [("Produit", ""), ("Réf.", "c"), ("Qté", "r"),
         ("PU TTC", "r"), ("Total TTC", "r"), ("Lien", "c")]
    F = "Fiche ↗"

    aiko = table(H,
        [["Panneau solaire AiKO 500 W NEOSTAR 2S — monocristallin", "9059", "15", "108,99 €", "1 634,85 €", lk(U["aiko_mono"], F)]],
        [("Sous-total facture AiKO", "1 634,85 €", "sum")])

    kit = table(H, [
        ["Distribution DC — Lynx Distributor 1000 V", "LYN060102010", "2", "193,50 €", "387,00 €", lk(U["lynx_dist"], F)],
        ["Régulateur MPPT 150/35 SmartSolar", "SCC115035210", "2", "177,30 €", "354,60 €", lk(U["mppt15035"], F)],
        ["Supervision — Cerbo GX", "BPP900450110", "1", "238,50 €", "238,50 €", lk(U["cerbo"], F)],
        ["Régulateur MPPT RS 450/100 SmartSolar MC4", "SCC145110512", "1", "1 063,80 €", "1 063,80 €", lk(U["mpptrs"], F)],
        ["Batterie lithium Pylontech US5000 48 V 4,8 kWh", "7012", "3", "909,00 €", "2 727,00 €", lk(U["us5000"], F)],
        ["Câble solaire 10 mm² rouge (au mètre)", "5012", "10", "2,88 €", "28,80 €", lk(U["cab10r"], F)],
        ["Câble solaire 10 mm² noir (au mètre)", "5011", "10", "2,88 €", "28,80 €", lk(U["cab10n"], F)],
        ["Câble 25 mm² rouge (au mètre)", "5026", "5", "9,00 €", "45,00 €", lk(U["cab25r"], F)],
        ["Câble 25 mm² noir (au mètre)", "5025", "5", "9,00 €", "45,00 €", lk(U["cab25n"], F)],
        ["Paire câble + cosse 50 mm² 2×M10 50 cm (R/N)", "5047+5048", "2", "44,99 €", "89,98 €", lk(U["cab50"], F)],
        ["Coffret protection DC 2 entrées PV — 2 MPPT + parafoudre (champ RS)", "4022", "1", "209,99 €", "209,99 €", lk(U["coffdc2"], F)],
        ["Onduleur-chargeur MultiPlus-II 48/10000 (140/100)", "PMP483105000", "1", "1 667,70 €", "1 667,70 €", lk(U["multiplus"], F)],
    ], [("Sous-total produits", "6 886,17 €", "sum"),
        ("Livraison", "186,34 €", "sum"),
        ("Total payé — commande MTBNWFQOX", "7 072,51 €", "grand")])

    allo = table(H, [
        ["MEGA fusible 60A/80V (sachet 5 pcs)", "CIP138060020", "1", "36,48 €", "36,48 €", lk(U["mega60"], F)],
        ["MEGA fusible 200A/80V (sachet 5 pcs)", "CIP138200020", "1", "36,48 €", "36,48 €", lk(U["mega200"], F)],
        ["MEGA-fuse 125A/80V (sachet 5 pcs)", "CIP138125020", "1", "36,43 €", "36,43 €", lk(U["mega125"], F)],
        ["Distribution DC — Lynx Class-T Power In 1000 V (M10)", "LYN060404010", "1", "173,76 €", "173,76 €", lk(U["lynxct"], F)],
        ["Interrupteur de batterie marche/arrêt 275A", "VBS127010010", "1", "35,52 €", "35,52 €", lk(U["batsw"], F)],
        ["Coffret DC parafoudre 1 string 1 MPPT 500 V — Technideal (champs 150/35)", "COFDC3KW1T500V", "2", "119,99 €", "239,98 €", lk(U["coffdc1"], F)],
        ["Panneau solaire 500 Wc bifacial NEOSTAR 2S+ — double vitrage N-Type", "G2-A500-MAH60Db", "3", "109,30 €", "327,90 €", lk(U["aiko_bi"], F)],
    ], [("Sous-total produits (DEEE 2,07 € inclus)", "888,62 €", "sum"),
        ("Livraison", "89,00 €", "sum"),
        ("Total TTC — commande 214760", "977,62 €", "grand")])

    amz = table(H,
        [["BOSYTRO kit de montage PV (rail + clips + pinces, 4 modules)", "B0F7Y2HF28", "3", "40,84 €", "122,52 €", lk(U["bosytro"], F)]],
        [("Sous-total facture Amazon", "122,52 €", "sum")])

    alt = table(H, altamira_rows(ALT_FR_NAMES, F),
        [("Sous-total produits", "477,52 €", "sum"),
         ("Livraison — Dachser/Schenker", "95,37 €", "sum"),
         ("Total — facture Altamira", "572,88 €", "grand")])

    recap = table(H[:1] + [("", "c"), ("", "r"), ("", "r"), ("Montant TTC", "r"), ("", "c")],
        [], [
        ("Facture AiKO — panneaux mono", "1 634,85 €", "sum"),
        ("Facture Kitsolaire-discount (MTBNWFQOX, livraison incl.)", "7 072,51 €", "sum"),
        ("Facture Allo Solar (214760, livraison incl.)", "977,62 €", "sum"),
        ("Facture Amazon — kits de montage", "122,52 €", "sum"),
        ("Facture Altamira — structure de montage (livraison incl.)", "572,88 €", "sum"),
        ("TOTAL ACHATS FACTURÉS (livraisons incluses)", "10 380,38 €", "grand"),
    ])

    restants = table([("Poste", ""), ("Type", "c"), ("Qté", "r"), ("PU TTC", "r"), ("Total TTC", "r"), ("Lien", "c")], [
        ["Écran de supervision GX Touch 50", "réf.", "1", "197,40 €", "197,40 €", lk(U["gxtouch"], F)],
        ["Coffret protection AC-In monophasé 6 kW 32A + parafoudre T2", "réf.", "1", "129,99 €", "129,99 €", lk(U["coffac"], F)],
        ["Coffret protection AC-Out monophasé 6 kW 32A + différentiel 30 mA", "réf.", "1", "129,99 €", "129,99 €", lk(U["coffac"], F)],
        ["Connecteurs MC4, rallonges 6 mm², câble AC, barrette + piquet de terre", "réf. à confirmer", "1", "≈ 120,00 €", "≈ 120,00 €", '<span class="src">à confirmer</span>'],
    ], [("Sous-total postes restants (estimé)", "≈ 577,38 €", "grand")])

    synth = table([("Désignation", ""), ("", "c"), ("", "r"), ("", "r"), ("Montant TTC", "r"), ("", "c")], [], [
        ("Total achats facturés (réel, livraisons incluses)", "10 380,38 €", "sum"),
        ("Postes restants estimés (référence, à confirmer)", "≈ 577,38 €", "sum"),
        ("TOTAL INSTALLATION (matériel)", "≈ 10 957,76 €", "grand"),
    ])

    body = f"""
<div class="header">
  <h1>Coût de l'installation photovoltaïque 48 V</h1>
  <div class="sub">Base : prix réels facturés (TTC, €) — champ PV ≈ 9 kWc / batterie 14,4 kWh</div>
</div>
<div class="meta">Établi le 26/06/2026, <b>mis à jour le 29/06/2026 (ajout de la facture Altamira)</b> — d'après les factures
AiKO, Kitsolaire-discount (cmd MTBNWFQOX), Allo Solar (cmd 214760), Amazon et Altamira. Quantités relevées sur
<code>installation_pv_cablage.drawio</code>. Un lien fournisseur est associé à chaque ligne (colonne « Lien »).</div>

<h2 class="section">1. Achats facturés (prix réels TTC)</h2>

<h3 class="sub"><span>1.1 — Facture AiKO · panneaux monocristallins</span><span class="badge">Kitsolaire-discount</span></h3>
{aiko}
<h3 class="sub"><span>1.2 — Facture Kitsolaire-discount · commande MTBNWFQOX</span><span class="badge">Kitsolaire-discount</span></h3>
{kit}
<h3 class="sub"><span>1.3 — Facture Allo Solar · commande 214760</span><span class="badge">Allo Solar</span></h3>
{allo}
<h3 class="sub"><span>1.4 — Facture Amazon · kits de montage</span><span class="badge">Amazon</span></h3>
{amz}
<h3 class="sub"><span>1.5 — Facture Altamira · structure de montage</span><span class="badge">e-altamira.fr</span></h3>
{alt}
<div class="note">Structure de fixation des 18 modules : rails alu 40×40, pinces centrales/latérales, adaptateurs et tiges M12,
plaques et bornes de mise à la terre, visserie inox. Prix de ligne issus de la commande Altamira (valeur du contrat 572,88 €).</div>

<h3 class="sub"><span>Récapitulatif des factures</span></h3>
{recap}
<div class="note">Dont livraisons facturées : 370,71 € (Kitsolaire 186,34 € + Allo Solar 89,00 € + Altamira 95,37 €). Port AiKO/Amazon non détaillé sur facture.</div>

<h2 class="section">2. Postes restants — non facturés · prix de référence</h2>
{restants}
<div class="note">Postes nécessaires non couverts par les factures ci-dessus. Prix relevés chez le même type de fournisseur, à confirmer au devis.</div>

<h2 class="section">3. Synthèse</h2>
{synth}
<div class="note">Hors pose / main-d'œuvre, hors tableau divisionnaire AC existant (disjoncteurs par circuit), et hors raccordement Enedis éventuel.</div>

<h3 class="sub"><span>Écarts notables vs estimation de référence initiale (≈ 10 343,79 €)</span></h3>
<ul class="notes">
  <li>Batteries Pylontech : 909,00 €/u réel contre 949,00 € estimé → −120,00 € sur les 3.</li>
  <li>Lynx Distributor : 2 unités achetées (387,00 €) au lieu d'une seule prévue.</li>
  <li>Coffrets DC : réels nettement moins chers (209,99 € + 239,98 € = 449,97 €) que l'estimation (586,50 € + 300,00 € = 886,50 €) → ≈ −436 €.</li>
  <li>Protection batterie : Lynx Class-T Power In (173,76 €) + jeu de MEGA-fusibles (109,39 €) à la place du MEGA 250A + porte-fusible estimés.</li>
  <li>Câblage DC désormais ferme (320,38 € de câbles 10/25/50 mm² + cosses), et livraisons (370,71 €) intégrées au coût réel.</li>
  <li><b>Structure de montage désormais ferme</b> (facture Altamira, 572,88 €) : rails alu 40×40, pinces, plaques et bornes de terre, visserie inox — auparavant non chiffrée.</li>
</ul>

<h2 class="section">4. Notes techniques</h2>
<ul class="notes">
  <li>Champ PV = 18 panneaux 500 W : 15 mono (NEOSTAR 2S) + 3 bifaciaux (NEOSTAR 2S+) ≈ 9 kWc. Le synoptique indique « 18×450 Wc » (libellé ancien).</li>
  <li>Capacité batterie : 3 × 4,8 kWh = 14,4 kWh.</li>
  <li>MPPT 150/35 : variante SmartSolar (177,30 €) retenue, conforme au schéma.</li>
  <li>Lynx Shunt VE.Can retiré : redondant avec le BMS Pylontech qui remonte déjà SOC/tension/courant au Cerbo GX via CAN.</li>
  <li>Les fusibles 40A des sorties MPPT 150/35 sont logés dans les positions du Lynx Distributor (déjà compté).</li>
  <li>Structure : profilés alu 40×40 (240 cm), pinces centrales/latérales, adaptateurs M12, tiges filetées M12 inox et plaques/bornes de terre (facture Altamira) pour la fixation des 18 modules.</li>
</ul>

<h3 class="sub"><span>Sources &amp; liens</span></h3>
<ul class="links">
  <li>Commande Kitsolaire-discount (réf. MTBNWFQOX) : kitsolaire-discount.com</li>
  <li>Commande Allo Solar 214760 : allo.solar/sales/order/view/order_id/214760/</li>
  <li>Facture Altamira (structure de montage) : e-altamira.fr — réf. PV-20, PV-24-04, PV-04-16, PV-03-23, PV-07-07, PV-18-02, PV-13-02, 000-003, PV-06-06/07, 000-126, PV-01-27</li>
  <li>Kit de montage PV BOSYTRO (Amazon ASIN B0F7Y2HF28) : amazon.fr/dp/B0F7Y2HF28</li>
  <li>MultiPlus-II 48/10000 · MPPT RS 450/100 · MPPT 150/35 · Cerbo GX · Pylontech US5000 · Lynx Distributor : kitsolaire-discount.com</li>
  <li>Lynx Class-T Power In · Interrupteur batterie 275A · Coffret DC 1 string/1 MPPT 500 V : allo.solar</li>
</ul>

<div class="footer">Coût de l'installation PV 48 V — document de synthèse établi le 26/06/2026, mis à jour le 29/06/2026 (ajout facture Altamira).
Prix TTC en euros, susceptibles d'évoluer selon stocks et devis.</div>
"""
    return page("Coût de l'installation PV 48 V — prix réels facturés", "fr", body)


# ============================================================ DE — installation
def build_main_de():
    H = [("Produkt", ""), ("Art.-Nr.", "c"), ("Menge", "r"),
         ("EP inkl. MwSt.", "r"), ("Gesamt inkl. MwSt.", "r"), ("Link", "c")]
    F = "Details ↗"

    aiko = table(H,
        [["Solarmodul AiKO 500 W NEOSTAR 2S — monokristallin", "9059", "15", "108,99 €", "1 634,85 €", lk(U["aiko_mono"], F)]],
        [("Zwischensumme Rechnung AiKO", "1 634,85 €", "sum")])

    kit = table(H, [
        ["DC-Verteilung — Lynx Distributor 1000 V", "LYN060102010", "2", "193,50 €", "387,00 €", lk(U["lynx_dist"], F)],
        ["MPPT-Laderegler 150/35 SmartSolar", "SCC115035210", "2", "177,30 €", "354,60 €", lk(U["mppt15035"], F)],
        ["Überwachung — Cerbo GX", "BPP900450110", "1", "238,50 €", "238,50 €", lk(U["cerbo"], F)],
        ["MPPT-Laderegler RS 450/100 SmartSolar MC4", "SCC145110512", "1", "1 063,80 €", "1 063,80 €", lk(U["mpptrs"], F)],
        ["Lithium-Batterie Pylontech US5000 48 V 4,8 kWh", "7012", "3", "909,00 €", "2 727,00 €", lk(U["us5000"], F)],
        ["Solarkabel 10 mm² rot (pro Meter)", "5012", "10", "2,88 €", "28,80 €", lk(U["cab10r"], F)],
        ["Solarkabel 10 mm² schwarz (pro Meter)", "5011", "10", "2,88 €", "28,80 €", lk(U["cab10n"], F)],
        ["Kabel 25 mm² rot (pro Meter)", "5026", "5", "9,00 €", "45,00 €", lk(U["cab25r"], F)],
        ["Kabel 25 mm² schwarz (pro Meter)", "5025", "5", "9,00 €", "45,00 €", lk(U["cab25n"], F)],
        ["Kabelpaar + Kabelschuh 50 mm² 2×M10 50 cm (rot/schwarz)", "5047+5048", "2", "44,99 €", "89,98 €", lk(U["cab50"], F)],
        ["DC-Schutzkasten 2 PV-Eingänge — 2 MPPT + Überspannungsschutz (RS-Feld)", "4022", "1", "209,99 €", "209,99 €", lk(U["coffdc2"], F)],
        ["Wechselrichter-Ladegerät MultiPlus-II 48/10000 (140/100)", "PMP483105000", "1", "1 667,70 €", "1 667,70 €", lk(U["multiplus"], F)],
    ], [("Zwischensumme Produkte", "6 886,17 €", "sum"),
        ("Versand", "186,34 €", "sum"),
        ("Bezahlter Gesamtbetrag — Bestellung MTBNWFQOX", "7 072,51 €", "grand")])

    allo = table(H, [
        ["MEGA-Sicherung 60 A/80 V (5er-Pack)", "CIP138060020", "1", "36,48 €", "36,48 €", lk(U["mega60"], F)],
        ["MEGA-Sicherung 200 A/80 V (5er-Pack)", "CIP138200020", "1", "36,48 €", "36,48 €", lk(U["mega200"], F)],
        ["MEGA-Sicherung 125 A/80 V (5er-Pack)", "CIP138125020", "1", "36,43 €", "36,43 €", lk(U["mega125"], F)],
        ["DC-Verteilung — Lynx Class-T Power In 1000 V (M10)", "LYN060404010", "1", "173,76 €", "173,76 €", lk(U["lynxct"], F)],
        ["Batterie-Trennschalter Ein/Aus 275 A", "VBS127010010", "1", "35,52 €", "35,52 €", lk(U["batsw"], F)],
        ["DC-Schutzkasten 1 String 1 MPPT 500 V — Technideal (Felder 150/35)", "COFDC3KW1T500V", "2", "119,99 €", "239,98 €", lk(U["coffdc1"], F)],
        ["Solarmodul 500 Wp bifazial NEOSTAR 2S+ — Doppelglas N-Type", "G2-A500-MAH60Db", "3", "109,30 €", "327,90 €", lk(U["aiko_bi"], F)],
    ], [("Zwischensumme Produkte (inkl. WEEE 2,07 €)", "888,62 €", "sum"),
        ("Versand", "89,00 €", "sum"),
        ("Gesamt inkl. MwSt. — Bestellung 214760", "977,62 €", "grand")])

    amz = table(H,
        [["BOSYTRO PV-Montagesatz (Schiene + Clips + Klemmen, 4 Module)", "B0F7Y2HF28", "3", "40,84 €", "122,52 €", lk(U["bosytro"], F)]],
        [("Zwischensumme Rechnung Amazon", "122,52 €", "sum")])

    alt = table(H, altamira_rows(ALT_DE_NAMES, F),
        [("Zwischensumme Produkte", "477,52 €", "sum"),
         ("Versand — Dachser/Schenker", "95,37 €", "sum"),
         ("Gesamt — Rechnung Altamira", "572,88 €", "grand")])

    recap = table(H[:1] + [("", "c"), ("", "r"), ("", "r"), ("Betrag inkl. MwSt.", "r"), ("", "c")], [], [
        ("Rechnung AiKO — Module mono", "1 634,85 €", "sum"),
        ("Rechnung Kitsolaire-discount (MTBNWFQOX, inkl. Versand)", "7 072,51 €", "sum"),
        ("Rechnung Allo Solar (214760, inkl. Versand)", "977,62 €", "sum"),
        ("Rechnung Amazon — Montagesätze", "122,52 €", "sum"),
        ("Rechnung Altamira — Montagestruktur (inkl. Versand)", "572,88 €", "sum"),
        ("SUMME RECHNUNGSKÄUFE (inkl. Versand)", "10 380,38 €", "grand"),
    ])

    restants = table([("Position", ""), ("Typ", "c"), ("Menge", "r"), ("EP inkl. MwSt.", "r"), ("Gesamt inkl. MwSt.", "r"), ("Link", "c")], [
        ["Überwachungsdisplay GX Touch 50", "Ref.", "1", "197,40 €", "197,40 €", lk(U["gxtouch"], F)],
        ["AC-In-Schutzkasten einphasig 6 kW 32 A + Überspannungsschutz T2", "Ref.", "1", "129,99 €", "129,99 €", lk(U["coffac"], F)],
        ["AC-Out-Schutzkasten einphasig 6 kW 32 A + FI 30 mA", "Ref.", "1", "129,99 €", "129,99 €", lk(U["coffac"], F)],
        ["MC4-Stecker, Verlängerungen 6 mm², AC-Kabel, Erdungsschiene + Erdspieß", "Ref. — zu bestätigen", "1", "≈ 120,00 €", "≈ 120,00 €", '<span class="src">zu bestätigen</span>'],
    ], [("Zwischensumme verbleibende Positionen (geschätzt)", "≈ 577,38 €", "grand")])

    synth = table([("Bezeichnung", ""), ("", "c"), ("", "r"), ("", "r"), ("Betrag inkl. MwSt.", "r"), ("", "c")], [], [
        ("Summe Rechnungskäufe (real, inkl. Versand)", "10 380,38 €", "sum"),
        ("Geschätzte verbleibende Positionen (Referenz, zu bestätigen)", "≈ 577,38 €", "sum"),
        ("GESAMT ANLAGE (Material)", "≈ 10 957,76 €", "grand"),
    ])

    body = f"""
<div class="header">
  <h1>Kosten der Photovoltaik-Anlage 48 V</h1>
  <div class="sub">Grundlage: tatsächlich berechnete Preise (inkl. MwSt., €) — PV-Feld ≈ 9 kWp / Batterie 14,4 kWh</div>
</div>
<div class="meta">Erstellt am 26.06.2026, <b>aktualisiert am 29.06.2026 (Hinzufügung der Altamira-Rechnung)</b> — auf Basis der Rechnungen
AiKO, Kitsolaire-discount (Best. MTBNWFQOX), Allo Solar (Best. 214760), Amazon und Altamira. Mengen aus
<code>installation_pv_cablage.drawio</code> entnommen. Jeder Zeile ist ein Lieferanten-Link zugeordnet (Spalte „Link").</div>

<h2 class="section">1. Berechnete Käufe (tatsächliche Preise inkl. MwSt.)</h2>

<h3 class="sub"><span>1.1 — Rechnung AiKO · monokristalline Module</span><span class="badge">Kitsolaire-discount</span></h3>
{aiko}
<h3 class="sub"><span>1.2 — Rechnung Kitsolaire-discount · Bestellung MTBNWFQOX</span><span class="badge">Kitsolaire-discount</span></h3>
{kit}
<h3 class="sub"><span>1.3 — Rechnung Allo Solar · Bestellung 214760</span><span class="badge">Allo Solar</span></h3>
{allo}
<h3 class="sub"><span>1.4 — Rechnung Amazon · Montagesätze</span><span class="badge">Amazon</span></h3>
{amz}
<h3 class="sub"><span>1.5 — Rechnung Altamira · Montagestruktur</span><span class="badge">e-altamira.fr</span></h3>
{alt}
<div class="note">Befestigungsstruktur der 18 Module: Aluschienen 40×40, Mittel-/Endklemmen, Adapter und Gewindestangen M12,
Erdungsplatten und -klemmen, Edelstahlschrauben. Zeilenpreise aus der Altamira-Bestellung (Vertragswert 572,88 €).</div>

<h3 class="sub"><span>Zusammenfassung der Rechnungen</span></h3>
{recap}
<div class="note">Davon berechneter Versand: 370,71 € (Kitsolaire 186,34 € + Allo Solar 89,00 € + Altamira 95,37 €). Versand AiKO/Amazon nicht separat ausgewiesen.</div>

<h2 class="section">2. Verbleibende Positionen — nicht berechnet · Referenzpreise</h2>
{restants}
<div class="note">Notwendige Positionen, die nicht durch die obigen Rechnungen abgedeckt sind. Preise bei vergleichbaren Lieferanten erhoben, im Angebot zu bestätigen.</div>

<h2 class="section">3. Zusammenfassung</h2>
{synth}
<div class="note">Ohne Montage / Arbeitslohn, ohne bestehende AC-Unterverteilung (Sicherungsautomaten je Stromkreis) und ohne eventuellen Netzanschluss (Enedis).</div>

<h3 class="sub"><span>Wesentliche Abweichungen ggü. der ursprünglichen Referenzschätzung (≈ 10 343,79 €)</span></h3>
<ul class="notes">
  <li>Pylontech-Batterien: real 909,00 €/Stk. statt geschätzt 949,00 € → −120,00 € für die 3 Stück.</li>
  <li>Lynx Distributor: 2 Einheiten gekauft (387,00 €) statt der einen geplanten.</li>
  <li>DC-Schutzkästen: real deutlich günstiger (209,99 € + 239,98 € = 449,97 €) als geschätzt (586,50 € + 300,00 € = 886,50 €) → ≈ −436 €.</li>
  <li>Batterieschutz: Lynx Class-T Power In (173,76 €) + MEGA-Sicherungssatz (109,39 €) anstelle der geschätzten MEGA 250 A + Sicherungshalter.</li>
  <li>DC-Verkabelung nun verbindlich (320,38 € Kabel 10/25/50 mm² + Kabelschuhe) und Versandkosten (370,71 €) in die realen Kosten einbezogen.</li>
  <li><b>Montagestruktur nun verbindlich</b> (Rechnung Altamira, 572,88 €): Aluschienen 40×40, Klemmen, Erdungsplatten und -klemmen, Edelstahlschrauben — zuvor nicht beziffert.</li>
</ul>

<h2 class="section">4. Technische Hinweise</h2>
<ul class="notes">
  <li>PV-Feld = 18 Module 500 W: 15 mono (NEOSTAR 2S) + 3 bifazial (NEOSTAR 2S+) ≈ 9 kWp. Das Schema zeigt „18×450 Wp" (alte Bezeichnung).</li>
  <li>Batteriekapazität: 3 × 4,8 kWh = 14,4 kWh.</li>
  <li>MPPT 150/35: Variante SmartSolar (177,30 €) gewählt, schemakonform.</li>
  <li>Lynx Shunt VE.Can entfernt: redundant zum Pylontech-BMS, das SOC/Spannung/Strom bereits via CAN an den Cerbo GX meldet.</li>
  <li>Die 40-A-Sicherungen der MPPT-150/35-Ausgänge sitzen in den Positionen des Lynx Distributor (bereits eingerechnet).</li>
  <li>Struktur: Aluprofile 40×40 (240 cm), Mittel-/Endklemmen, M12-Adapter, M12-Gewindestangen aus Edelstahl sowie Erdungsplatten/-klemmen (Rechnung Altamira) zur Befestigung der 18 Module.</li>
</ul>

<h3 class="sub"><span>Quellen &amp; Links</span></h3>
<ul class="links">
  <li>Bestellung Kitsolaire-discount (Ref. MTBNWFQOX): kitsolaire-discount.com</li>
  <li>Bestellung Allo Solar 214760: allo.solar/sales/order/view/order_id/214760/</li>
  <li>Rechnung Altamira (Montagestruktur): e-altamira.fr — Ref. PV-20, PV-24-04, PV-04-16, PV-03-23, PV-07-07, PV-18-02, PV-13-02, 000-003, PV-06-06/07, 000-126, PV-01-27</li>
  <li>PV-Montagesatz BOSYTRO (Amazon ASIN B0F7Y2HF28): amazon.fr/dp/B0F7Y2HF28</li>
  <li>MultiPlus-II 48/10000 · MPPT RS 450/100 · MPPT 150/35 · Cerbo GX · Pylontech US5000 · Lynx Distributor: kitsolaire-discount.com</li>
  <li>Lynx Class-T Power In · Batterie-Trennschalter 275 A · DC-Schutzkasten 1 String/1 MPPT 500 V: allo.solar</li>
</ul>

<div class="footer">Kosten der PV-Anlage 48 V — Übersichtsdokument, erstellt am 26.06.2026, aktualisiert am 29.06.2026 (Hinzufügung der Altamira-Rechnung).
Preise in Euro inkl. MwSt., Änderungen je nach Lagerbestand und Angebot vorbehalten.</div>
"""
    return page("Kosten der PV-Anlage 48 V — tatsächlich berechnete Preise", "de", body)


# ============================================================ DE — extension v2
def build_ext_de():
    H = [("Produkt", ""), ("Art.-Nr.", "c"), ("Menge", "r"),
         ("EP inkl. MwSt.", "r"), ("Gesamt inkl. MwSt.", "r"), ("Quelle", "c")]

    def src(t):
        return f'<span class="src">{t}</span>'

    dc = table(H, [
        ["Solarmodul AiKO 500 W NEOSTAR 2S — monokristallin", "9059", "12", "108,99 €", "1 307,88 €", src("Kitsolaire")],
        ["MPPT-Laderegler RS 450/100 SmartSolar MC4", "SCC145110512", "1", "1 063,80 €", "1 063,80 €", src("Kitsolaire")],
        ["DC-Schutzkasten 2 PV-Eingänge + Überspannungsschutz", "4022", "1", "209,99 €", "209,99 €", src("Kitsolaire")],
        ["PV-Montagesatz BOSYTRO (Schiene + Clips, 4 Module)", "B0F7Y2HF28", "3", "40,84 €", "122,52 €", src("Amazon")],
        ["Kabel 25 mm² rot — MPPT → 48-V-Bus (pro Meter)", "5026", "5", "9,00 €", "45,00 €", src("Kitsolaire")],
        ["Kabel 25 mm² schwarz — MPPT → 48-V-Bus (pro Meter)", "5025", "5", "9,00 €", "45,00 €", src("Kitsolaire")],
        ["Solarkabel 10 mm² rot — PV-Strings (pro Meter)", "5012", "20", "2,88 €", "57,60 €", src("Kitsolaire")],
        ["Solarkabel 10 mm² schwarz — PV-Strings (pro Meter)", "5011", "20", "2,88 €", "57,60 €", src("Kitsolaire")],
        ["MEGA-Sicherung 125 A/80 V (5er-Pack) — Schutz MPPT-Ausgang", "CIP138125020", "1", "36,43 €", "36,43 €", src("Allo Solar")],
        ["MC4-Stecker + DC-Kleinmaterial", "zu bestätigen", "1", "≈ 40,00 €", "≈ 40,00 €", src("Ref.")],
    ], [("Zwischensumme DC-Feld", "2 985,82 €", "grand")])

    ac = table(H, [
        ["Solarmodul AiKO 500 W NEOSTAR 2S — monokristallin", "9059", "12", "108,99 €", "1 307,88 €", src("Kitsolaire")],
        ["Wechselrichter Fronius Primo 6.0-1 — einphasig 230 V (DC→AC, 6 kW)", "4,210,069", "1", "≈ 1 290,00 €", "≈ 1 290,00 €", src("Ref.")],
        ["DC-String-Schutzkasten + Überspannungsschutz T2 1000 V — Fronius-Eingang", "zu bestätigen", "1", "≈ 129,99 €", "≈ 129,99 €", src("Ref.")],
        ["AC-Schutzkasten 32 A + FI 30 mA + Überspannungsschutz T2 — AC-Out-Kopplung", "953", "1", "129,99 €", "129,99 €", src("Kitsolaire")],
        ["PV-Montagesatz BOSYTRO (Schiene + Clips, 4 Module)", "B0F7Y2HF28", "3", "40,84 €", "122,52 €", src("Amazon")],
        ["Solarkabel 10 mm² rot — PV-Strings (pro Meter)", "5012", "20", "2,88 €", "57,60 €", src("Kitsolaire")],
        ["Solarkabel 10 mm² schwarz — PV-Strings (pro Meter)", "5011", "20", "2,88 €", "57,60 €", src("Kitsolaire")],
        ["AC-Kabel 3G6 mm² — Fronius → AC-Out (pro Meter)", "zu bestätigen", "15", "≈ 3,50 €", "≈ 52,50 €", src("Ref.")],
        ["MC4-Stecker + Kleinmaterial", "zu bestätigen", "1", "≈ 40,00 €", "≈ 40,00 €", src("Ref.")],
    ], [("Zwischensumme AC-Feld (Fronius)", "3 188,08 €", "grand")])

    synth = table([("Bezeichnung", ""), ("", "c"), ("", "r"), ("", "r"), ("Betrag inkl. MwSt.", "r"), ("", "c")], [], [
        ("DC-Feld — 6 kWp (DC-Kopplung / MPPT RS 450/100)", "2 985,82 €", "sum"),
        ("AC-Feld — 6 kWp (Fronius-Wechselrichter, AC-Kopplung)", "3 188,08 €", "sum"),
        ("GESAMT ERWEITERUNG (Material) ≈ +12 kWp", "≈ 6 173,90 €", "grand"),
    ])

    synth2 = table([("Bezeichnung", ""), ("", "c"), ("", "r"), ("", "r"), ("Betrag inkl. MwSt.", "r"), ("", "c")], [], [
        ("Erstanlage — Material (Ref. cout_installation_de.pdf)", "≈ 10 957,76 €", "sum"),
        ("davon reale Rechnungskäufe (inkl. Versand)", "10 380,38 €", "sum"),
        ("Erweiterung — Material (siehe oben)", "≈ 6 173,90 €", "sum"),
        ("NEUE GESAMTANLAGE (Material) ≈ 21 kWp / 14,4 kWh", "≈ 17 131,66 €", "grand"),
    ])

    body = f"""
<div class="header">
  <h1>Kosten der Photovoltaik-Erweiterung — +12 kWp</h1>
  <div class="sub">Ausbau der 48-V-Anlage — DC-Feld 6 kWp (DC-Kopplung / MPPT) + AC-Feld 6 kWp (Fronius-Wechselrichter, AC-Kopplung) · Preise inkl. MwSt. (€)</div>
</div>
<div class="meta">Erstellt am 26.06.2026 — Ergänzung zum Dokument <code>cout_installation_de.pdf</code>. Mengen aus
<code>installation_pv_synoptique_v2.drawio</code> (Block „EXTENSION V2"). Preise aus den realen Rechnungen übernommen, wenn der Artikel
identisch ist; mit „Ref." gekennzeichnete Zeilen sind Referenzpreise, im Angebot zu bestätigen.</div>

<h2 class="section">1. DC-Feld — 6 kWp (DC-Kopplung am 48-V-Bus)</h2>
<h3 class="sub"><span class="desc">12× AiKO 500 W → DC-Schutzkasten → MPPT RS 450/100 → 48-V-Bus</span><span class="badge">Referenz Kitsolaire / Amazon</span></h3>
{dc}

<h2 class="section">2. AC-Feld — 6 kWp (Fronius-Wechselrichter, AC-Kopplung)</h2>
<h3 class="sub"><span class="desc">12× AiKO 500 W → DC-Schutzkasten → Fronius-Wechselrichter → AC-Out des MultiPlus</span><span class="badge">Referenz — im Angebot zu bestätigen</span></h3>
{ac}

<h2 class="section">3. Zusammenfassung — Kosten des Ausbaus</h2>
{synth}
<div style="height:6px"></div>
{synth2}
<div class="note">Ohne Montage / Arbeitslohn, ohne Anpassung der AC-Verteilung und ohne eventuellen Ausbau des Batteriespeichers. Versandkosten für die Erweiterungszeilen nicht enthalten.</div>

<h2 class="section">4. Technische Hinweise</h2>
<ul class="notes">
  <li>DC-Feld (6 kWp): 12× AiKO 500 W DC-gekoppelt über 1× MPPT RS 450/100 am 48-V-Bus (Lynx). MPPT-Ausgang ≈ 100 A × 57,6 V ≈ 5,7 kW: leichte Spitzenabregelung der 6 kWp, ohne nennenswerten Einfluss auf den Ertrag.</li>
  <li>AC-Feld (6 kWp): 12× AiKO 500 W → Fronius Primo 6.0-1 einphasig, gekoppelt am AC-Out des MultiPlus-II. Regelung per Frequenzverschiebung (Frequency-Shift Power Control), wenn die Batterie voll ist.</li>
  <li>AC-Kopplungsfaktor 1:1 eingehalten: 6 kW PV ≤ 8 kW des MultiPlus-II 48/10000. ✓</li>
  <li>Die Batterie (3× US5000 = 14,4 kWh) muss den PV-Überschuss bei AC-Kopplung aufnehmen; den maximal zulässigen Ladestrom überwachen. Ein Ausbau des Batteriespeichers kann sinnvoll sein (hier nicht beziffert).</li>
  <li>Ansteuerung des Fronius über den Cerbo GX (Modbus TCP / SunSpec) — Firmware-Version und Aktivierung der Wechselrichter-Regelung prüfen.</li>
  <li>Mit „Ref." gekennzeichnete Zeilen (Fronius, DC-String-Schutzkasten 1000 V, AC-Kabel): Richtpreise, im Lieferantenangebot zu bestätigen.</li>
</ul>

<h3 class="sub"><span>Quellen &amp; Links</span></h3>
<ul class="links">
  <li>Wechselrichter Fronius Primo 6.0-1 (einphasig): fronius.com → Primo 6.0-1 — Ref. 4,210,069</li>
  <li>MPPT RS 450/100 SmartSolar · DC-Schutzkasten 2 PV/2 MPPT + Überspannungsschutz · AC-Schutzkasten 6 kW 32 A einphasig: kitsolaire-discount.com</li>
  <li>Solarmodul AiKO 500 W NEOSTAR 2S (mono): kitsolaire-discount.com — Suche „NEOSTAR 2S"</li>
  <li>PV-Montagesatz BOSYTRO (Amazon ASIN B0F7Y2HF28): amazon.fr/dp/B0F7Y2HF28</li>
  <li>MEGA-Sicherung 125 A/80 V: allo.solar · Solarkabel / 25 mm² rot-schwarz: kitsolaire-discount.com</li>
</ul>

<div class="footer">Kosten der PV-Erweiterung 48 V — Ergänzung, erstellt am 26.06.2026 auf Basis realer Rechnungspreise und Lieferantenreferenzen.
Preise in Euro inkl. MwSt., Änderungen je nach Lagerbestand und Angebot vorbehalten.</div>
"""
    return page("Kosten der PV-Erweiterung — +12 kWp", "de", body)


# ----------------------------------------------------------------------- driver
def main():
    jobs = [
        ("cout_installation.html", "cout_installation.pdf", build_main_fr()),
        ("cout_installation_de.html", "cout_installation_de.pdf", build_main_de()),
        ("cout_installation_v2_de.html", "cout_installation_v2_de.pdf", build_ext_de()),
    ]
    for html_name, pdf_name, html in jobs:
        hp = SRC / html_name
        render(hp, html)
        to_pdf(hp, BASE / pdf_name)
    print("OK")


if __name__ == "__main__":
    main()
