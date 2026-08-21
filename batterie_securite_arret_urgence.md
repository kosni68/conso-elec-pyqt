# Batterie Pylontech, sectionneur DC & arrêt d'urgence — 3 questions

Document d'accompagnement du synoptique `synoptique_DC_AC_coupling.drawio`.
Système concerné : **48 V off-grid Victron** — MultiPlus‑II 48/10000, MPPT RS 450/100 +
2× MPPT 150/35, **parc Pylontech US5000** (3 modules), Cerbo GX, sectionneur batterie 275 A,
protection DC **Lynx Class‑T Power In** (fusibles Class‑T) + **Lynx Distributor** (fusibles MEGA),
champ DC + champ AC (Fronius, AC‑coupling).

> Réponses aux 3 questions :
> 1. Faut‑il un module de gestion de batterie Pylontech ?
> 2. Pourquoi le sectionneur batterie est‑il sur le **−** et pas sur le **+** ?
> 3. Le Cerbo a‑t‑il un arrêt d'urgence ? Sinon, comment tout couper en urgence ?

---

## 1. Faut‑il un « module de gestion de batterie » Pylontech ?

**Non — il n'y a aucun module externe à acheter.** Chaque **US5000 embarque son propre
BMS** (Battery Management System) intégré : équilibrage des cellules, protections sur/sous‑
tension, sur‑courant, température, coupure interne. Le « module de gestion » que vous
imaginez est **déjà dans chaque batterie**.

Ce qu'il faut, ce n'est pas un module, c'est **la communication** entre le parc Pylontech
et le Cerbo (fonctionnement dit *closed‑loop* / batterie « managée ») :

| Élément | Rôle | Détail |
|---|---|---|
| **Câbles Link (RJ45)** entre batteries | Chaîner les US5000 en parallèle (Link Port 0/1), une **maître** + esclaves | Fournis avec les batteries. Adressage par DIP/rotatif ; terminaison sur le dernier module selon la notice. |
| **Câble CAN maître → Cerbo** | Le BMS envoie au Victron : CVL (tension de charge max), CCL/DCL (courants charge/décharge max), SoC | **Victron « VE.Can to CAN‑bus BMS type B Cable »** (réf. ASS030720018). ⚠ **Type B pour Pylontech** (le Type A est pour d'autres marques). |
| **Terminateur VE.Can** | Fermer le bus CAN | Bouchon dans le 2ᵉ port BMS‑Can du Cerbo. |
| **DVCC activé** (Cerbo) | Passe le système en pilotage par le BMS | Réglages → Services → port **BMS‑Can = 500 kbit/s** ; la batterie apparaît « Pylontech » ; **DVCC ON**. |

> Vous n'avez **pas** besoin de la console/écran propre à Pylontech : **le Cerbo est le
> cerveau et l'afficheur** du système.

**À ne pas confondre :** le **Lynx Smart BMS** de Victron n'est **PAS** pour les Pylontech
(il sert aux cellules lithium génériques/Victron). Sur du Pylontech, on garde le BMS interne
+ le câble CAN. En revanche un simple **Lynx Distributor** (jeux de barres + porte‑fusibles
MEGA) reste tout à fait valable comme point de distribution/protection DC.

**Vérification de dimensionnement (liée au nombre de US5000) :** chaque US5000 = **100 A
continu**. Le MultiPlus‑II 48/10000 peut tirer ~**180–210 A** en continu à pleine puissance
(≈ 10 kVA / 48 V), plus les pointes. Donc :

- il faut **au moins 2 à 3 US5000 en parallèle** pour suivre la puissance de l'onduleur ;
- avec **3 US5000** : parc = **300 A continus**, le **sectionneur 275 A** est donc au plus juste ;
  le calibre des fusibles doit suivre le **nombre réel** de modules (règle : I_max parc = n × 100 A).
  Voir **§4 — Fusibles : calibres et nombre**.

➡️ **Conclusion Q1 :** aucun module de gestion à ajouter. Il faut seulement les **câbles Link**
entre batteries + le **câble CAN Type B** vers le Cerbo + un **terminateur** + **DVCC activé**.

---

## 2. Pourquoi le sectionneur batterie est‑il sur le **−** et pas sur le **+** ?

### Le point clé d'abord : électriquement, un sectionneur unique fonctionne sur **n'importe quel** pôle
Le courant DC circule dans une **boucle**. Ouvrir **soit le +, soit le −** coupe la boucle et
isole la batterie de la même façon. Pour un **seul** interrupteur de coupure, le choix du pôle
est donc **électriquement équivalent** — ce n'est pas lui qui fait la sécurité.

### Ce qui, lui, n'est PAS au choix : la position du **fusible**
La règle qui compte : **la protection (fusible) doit être sur le +, au plus près de la borne
positive** de la batterie. Raison : dans un système où le **−/masse est référencé à la terre**,
le défaut dangereux est un **court‑circuit du + vers une masse métallique** ; c'est le fusible
sur le **+** qui le coupe. ✅ C'est ce que fait le **fusible Class‑T sur le +** (Lynx Class‑T
Power In) — et, par module, le **125 A MEGA** de chaque US5000 dans le Lynx Distributor.

### Du coup, pourquoi mettre le *sectionneur* sur le − ?
Comme le **+** porte déjà la **protection** (fusible), placer l'**isolateur manuel sur le −**
est un choix courant et propre, pour de bonnes raisons :

1. **Convention « interrupteur maître » sur le retour/masse** (héritage auto/marine) : on
   coupe le conducteur de retour (−), ce qui « débranche » toute la distribution négative.
2. **Regroupement côté −** : c'est le côté où se trouvent le **jeu de barres négatif** et le
   **shunt** de mesure (SmartShunt/BMV/Lynx Shunt, toujours dans le **−** au plus près de la
   batterie). On garde ainsi le **+** comme distribution « fusibée » propre.
3. **Fonctionnellement identique** pour « couper la batterie », sans ajouter un 2ᵉ contact en
   série sur le positif fusibé.

```
        BATTERIE 48V (parc Pylontech US5000)
          +  ──[ 125A MEGA / module ]──[ BUS Lynx ]──[ Class‑T ]──►  MultiPlus
                (fusible au + = protection)        (voir §4)
          −  ──[ SECTIONNEUR 275A ]──[ shunt ]►  Bus − 48V
                (isolateur manuel au −)
```

### ⚠️ Mises en garde importantes
- Avec le sectionneur **sur le − seulement**, quand il est ouvert le **bus + reste à +48 V**
  par rapport à la terre. Pour « couper la puissance » c'est efficace ; **pour intervenir en
  sécurité, considérez le + comme toujours dangereux.**
- Pour une **isolation franche de maintenance**, préférez un **sectionneur 2 pôles (L+ / L−)**
  ou ajoutez un isolateur sur le **+** — vous coupez alors les deux polarités.
- Vérifiez **où se situe le pont −/PE (mise à la terre du négatif)** par rapport au sectionneur :
  il doit rester cohérent pour que le **shunt et la référence du BMS** voient bien tout le
  courant (pont côté batterie, mesures en aval).

➡️ **Conclusion Q2 :** ce n'est **pas une obligation**, c'est un **choix de câblage** légitime.
L'essentiel — **fusible sur le +** — est respecté. Sachez juste que le **+ reste sous tension**
quand seul le − est ouvert ; pour de la maintenance, coupez **les deux pôles**.

---

## 3. Le Cerbo a‑t‑il un arrêt d'urgence ? Sinon, comment tout couper ?

### Non — le Cerbo ne coupe **rien** tout seul
Le **Cerbo GX est un cerveau de supervision**, pas un organe de puissance. Il **n'a pas de
bouton d'arrêt d'urgence** et **ne peut pas couper le courant batterie**. Couper l'alimentation
du Cerbo **n'arrête pas** l'installation : le **MultiPlus et les MPPT continuent** de
fonctionner en autonome.

Ce que le Cerbo sait faire (mais qui ne remplace **pas** une coupure de puissance) :
- **2 relais programmables** + **entrées numériques** : on peut y câbler un coup‑de‑poing pour
  **déclencher une alarme/notification** ou piloter une logique (Node‑RED), mais ces relais
  sont des **contacts de signal**, incapables de couper les centaines d'ampères de la batterie.
- Le **MultiPlus a une entrée « Remote on/off »** : un contact déporté peut **arrêter
  l'onduleur** — utile, mais ça **ne coupe pas** la batterie ni les MPPT/PV.

### Comment tout couper en urgence (c'est un système **multi‑sources**)
Un système off‑grid a **plusieurs sources d'énergie** qui doivent être coupées à des endroits
différents — et surtout : **les panneaux PV restent sous tension dès qu'il fait jour**, on ne
peut pas les « éteindre », seulement les **isoler**.

| Ordre / geste | Organe | Effet |
|---|---|---|
| 1. **Couper la batterie** | **Sectionneur batterie 275 A** | Prive MultiPlus + MPPT + bus 48 V → **l'onduleur s'arrête**, l'AC‑Out tombe → le Fronius AC‑couplé s'arrête (plus de réseau pour se synchroniser). |
| 2. **Isoler les panneaux** | **Sectionneurs DC** de chaque coffret (déjà au schéma) | Coupe les strings des MPPT et du Fronius. ⚠️ Les **modules restent sous tension** en amont du sectionneur. |
| 3. **Isoler le côté AC** | **Disj./différentiel 2P sortie OFF‑GRID** + **coupure AC du Fronius** | Isole la maison et l'onduleur AC‑couplé. |

> **Point de sécurité majeur :** même « tout coupé », les **panneaux PV produisent de la
> tension tant qu'il y a de la lumière**. Seul le câblage **en aval des sectionneurs DC** est
> mis hors tension, pas les modules eux‑mêmes.

### Recommandation : installer un **vrai** arrêt d'urgence
Le sectionneur 275 A est efficace mais c'est un **geste manuel local**. Pour un arrêt d'urgence
digne de ce nom :

- **Bouton coup‑de‑poing (arrêt d'urgence) → contacteur DC** sur la ligne batterie principale.
  Comme le Pylontech gère son BMS en interne, on ajoute un **contacteur haute intensité dédié**
  (type contacteur DC 48 V calibré au courant du parc), **piloté par la boucle d'arrêt
  d'urgence**, ou un **sectionneur batterie à déclenchement/motorisé**.
- Idéalement, un **dispositif de coupure d'urgence PV (« pompier » / rapid shutdown)** au plus
  près des strings si les panneaux sont sur un bâtiment, pour dé‑énergiser le câblage toiture.
- Regrouper et **étiqueter** clairement : « **ARRÊT D'URGENCE** », coupure **DC batterie**,
  coupure **PV**, coupure **AC** — exigence d'accessibilité des organes de coupure DC et AC
  (UTE C15‑712‑1/‑2).
- Le **relais/entrée du Cerbo** et le **Remote on/off du MultiPlus** peuvent **compléter** le
  dispositif (alarme, arrêt onduleur), mais **jamais le remplacer** : la coupure réelle se fait
  au niveau **puissance**.

➡️ **Conclusion Q3 :** le Cerbo **n'a pas** d'arrêt d'urgence et ne coupe pas la puissance.
La coupure d'urgence se fait **au niveau puissance**, en plusieurs points (**batterie 275 A**,
**sectionneurs PV**, **coupure AC**), car le système est multi‑sources et **le PV reste vivant
en journée**. Le mieux : un **coup‑de‑poing pilotant un contacteur DC** sur la batterie (+
coupure PV type « pompier »), étiqueté et accessible.

---

## 4. Fusibles : calibres et nombre (Class‑T + MEGA)

### Pourquoi un Class‑T et pas un MEGA sur la grosse branche
Un **US5000 débite ~2 500 A en court‑circuit** (manuel §5.7). Avec **3 modules en parallèle**, le
courant de défaut disponible sur la barre atteint **~7,5 kA**. Or :

| Fusible | Pouvoir de coupure (AIC) | Verdict sur 3× US5000 |
|---|---|---|
| **MEGA 80 V** | ~**2,5 kA** | OK **par module** (2,5 kA de contribution), **insuffisant** sur la barre |
| **Class‑T** | **20 kA** | ✅ seul adapté à la branche qui voit tout le parc |

C'est **la** raison d'être du **Lynx Class‑T Power In** dans l'installation : sous le calibre, un
MEGA « fond » mais **l'arc DC continue** — risque d'incendie.

### Les 3 contraintes de calibrage

| Contrainte | Valeur | Source |
|---|---|---|
| Parc 3× US5000 | **100 A max par paire de câbles** → 300 A continus pour le parc ; 2 500 A de court‑circuit par module | Manuel US5000 §5.10 / §5.7 |
| MultiPlus‑II 48/10000 | **Fusible CC recommandé 400 A**, câble **2× 50 mm² par borne** (0–5 m) ; ~180–200 A continus à 8 kW, ~450 A en pointe 20 kW | Manuel MultiPlus‑II §4.2 |
| Lynx Class‑T Power In (LYN060404010) | **2 emplacements**, calibres **225 / 250 / 300 / 350 / 400 A**, barre **1000 A**, boulons **3/8"**, couple **33 Nm** | Manuel Victron |

### ➡️ Choix retenu

> **2 fusibles Class‑T de 225 A**, **un par câble positif 50 mm²** du MultiPlus
> (les 2 paires 50 mm²/M10 achetées = « 2× 50 mm² par borne » exigés par Victron).
> Total **450 A ≥ 400 A** préconisés ; chaque conducteur 50 mm² est protégé à sa vraie tenue
> (~200–225 A). Charge réelle ≈ **105 A par fusible** à 8 kW continu, **225 A chacun** en pointe
> 20 kW → pas de fusion intempestive.

**Variante « un seul fusible »** (les deux cosses + sur le même goujon) : **1× 400 A**, calibre exact
du tableau Victron pour le 48/10000 ; le 2ᵉ emplacement reste libre pour une future 2ᵉ chaîne de
batteries.

⚠️ **Ne pas** se rabattre sur 250 A avec **un seul** câble 50 mm² : on serait à ~82 % du calibre en
permanence à 8 kW, et le MultiPlus serait **sous‑câblé** par rapport à sa notice.

**Quantité à commander :** le Class‑T est à **usage unique** → **3× 225 A** (2 en service + 1 de
rechange) ou **2× 400 A** (1 + 1). **Victron ne stocke pas les fusibles** : prendre du **Bussmann
JJN** ou **Littelfuse JLLN** (type **A3T**, 160 Vcc, 20 kA, embouts **3/8"**).

### Répartition complète des protections DC

| Emplacement | Départ | Fusible | Câble |
|---|---|---|---|
| **Lynx Class‑T Power In** | **MultiPlus‑II 48/10000** | **2× Class‑T 225 A** (1 par câble +) | 2× 50 mm² par pôle |
| **Lynx Distributor #1** | US5000 #1, #2, #3 (**un câble par module**) | **3× MEGA 125 A** | 25 mm² |
| **Lynx Distributor #2** | MPPT RS 450/100 | **MEGA 125 A** | 25 mm² |
| **Lynx Distributor #2** | MPPT 150/35 (×2) | **MEGA 60 A** (achetés ; 50 A convient aussi) | 10 mm² |

⚠️ **Interdiction de chaîner les 3 US5000 sur une seule sortie** : chaque paire de câbles Pylontech
est limitée à **100 A continus** (manuel §5.10) → **un câble par module** jusqu'au Lynx Distributor.

> Les **MEGA 200 A** achetés ne servent plus côté batterie : le Class‑T les remplace sur la branche
> onduleur. À garder en rechange.

### Montage
- Couple de serrage **33 Nm** sur les cosses **et** sur les fusibles.
- Pattes du Class‑T : si elles ne posent pas **à plat** sur la barre, **retourner le fusible de 180°**.
- Visserie fusible **3/8" (noire)** — à ne pas confondre avec la visserie **M10** des connexions DC
  (n° de série `HQxxxx` : visserie fusible en M10, non repérée en noir).

---

## 5. Synthèse (checklist)

- [ ] **Pylontech** : BMS **intégré** → pas de module externe. Câbles **Link** + câble
      **CAN Type B** vers Cerbo + **terminateur** + **DVCC ON**.
- [ ] **Nombre de US5000** cohérent avec le MultiPlus (n × 100 A) et avec le **sectionneur 275 A**.
- [ ] **Fusible sur le +** au plus près de la borne — ✅ l'essentiel de sécurité :
      **125 A MEGA par module** + **Class‑T** sur la branche MultiPlus (§4).
- [ ] **Class‑T commandés** : 2× 225 A (ou 1× 400 A) **+ 1 de rechange** — Victron ne les stocke pas.
- [ ] **Sectionneur sur le −** = choix valable ; le **+ reste sous tension** quand il est ouvert.
- [ ] Pour la maintenance : **couper les 2 pôles** (sectionneur 2P ou isolateur + en plus).
- [ ] **Arrêt d'urgence** : ne pas compter sur le Cerbo. Prévoir **coup‑de‑poing → contacteur DC**
      batterie + **coupure PV** + **coupure AC**, groupés et étiquetés.
- [ ] Rappel : **panneaux PV sous tension dès qu'il fait jour** — les sectionneurs isolent le
      câblage, pas les modules.

---

### Références
- **Pylontech US5000 + Victron** — installation & réglages (BMS‑Can, câble Type B, DVCC) :
  Victron Energy, *Battery Compatibility – Pylontech US5000*.
- **DVCC** — Victron Energy, manuel GX/Cerbo (pilotage *closed‑loop* par le BMS).
- **MultiPlus‑II 48/10000** — entrée *Remote on/off*, courants DC :
  https://www.victronenergy.com/upload/documents/MultiPlus-II_230V/32424-MultiPlus-II___Quattro-II-pdf-en.pdf
- **Lynx Class‑T Power In** (LYN060404010) — 2 fusibles Class‑T, calibres 225/250/300/350/400 A :
  https://www.victronenergy.com/dc-distribution-systems/lynx-class-t-power-in
- **Manuel Lynx Class‑T Power In** (conception système, couples, visserie) :
  https://www.victronenergy.com/upload/documents/Lynx_Class-T_Power_In/165891-Lynx_Class-T_Power_In-pdf-en.pdf
- **Pylontech US5000** — manuel §5.7 (dispositif de déconnexion, Icc 2 500 A/module) et §5.10
  (100 A max par paire de câbles) : `Doc/Batterie/Manuel d_utilisation US5000 FR.pdf`
- **MultiPlus‑II 48/10000** — §4.2 « Fusible CC recommandé » (400 A, 2× 50 mm²) :
  `Doc/Multiplus/Manuel-MultiPlus-II-8kV-10kV.pdf`
- **UTE C15‑712‑1/‑2** — installations PV (autonomes avec stockage) : organes de coupure DC/AC,
  accessibilité, coupure d'urgence.
- Voir aussi `regime_neutre_N-PE_off-grid.md` (liaison N‑PE, mise à la terre — le **PE reste
  commun et n'est jamais commuté**).
