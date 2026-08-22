# Régime de neutre & liaison N‑PE — installation off‑grid 48 V

Document d'accompagnement du synoptique `installation_pv_synoptique v2.drawio`.
Objet : expliquer **pourquoi** et **comment** réaliser la liaison neutre‑terre (N‑PE)
dans cette installation **autonome** (MultiPlus‑II 48/10000) avec **EDF en secours via
inverseur de source**. C'est le point de sécurité le plus délicat du schéma : mal traité,
les différentiels 30 mA ne protègent plus les personnes.

> Référentiel : NF C 15‑100 (régimes de neutre, DDR) et UTE C15‑712‑2 (PV autonome avec stockage).

---

## 1. Le problème en une phrase

Un différentiel (DDR / interrupteur différentiel 30 mA) ne peut détecter un courant de
fuite **que si le neutre du réseau est référencé à la terre par exactement UN point de
liaison N‑PE**.

- **Trop de liaisons** (double pont) → courant de neutre qui reboucle par le PE →
  déclenchements intempestifs et DDR « aveuglé ».
- **Aucune liaison** (neutre flottant) → en cas de 1er défaut, le DDR ne voit rien,
  des tensions dangereuses apparaissent sur les masses → **risque d'électrocution**.

Or ici il y a **deux sources** (l'onduleur off‑grid et EDF) avec **deux logiques de mise
à la terre différentes**. Il faut garantir **un seul pont N‑PE actif à tout instant**.

---

## 2. Les deux sources et leur référence de terre

### a) EDF = régime TT (réseau public français)
- Le neutre est mis à la terre **chez le distributeur** (au transformateur).
- Côté installation : **aucun pont N‑PE**. Les masses sont reliées à la **prise de terre
  locale** (piquet / barrette de terre). La protection des personnes repose entièrement
  sur les **DDR** (la boucle de défaut passe par la terre, donc impédance élevée → un
  fusible ne suffit pas, il faut un différentiel).

### b) Onduleur MultiPlus‑II = source isolée
- En mode onduleur, le MultiPlus génère un 230 V **sans aucune référence de terre amont**
  (pas d'EDF en entrée). Un réseau non référencé est dangereux et incompatible DDR.
- → Il faut **créer la référence** en pontant N‑PE **une fois**, à la source.
  C'est le rôle du **relais de terre interne** du MultiPlus (voir §3). La sortie devient
  alors un **îlot TN‑S local** : N et PE séparés en aval, DDR 30 mA opérationnels, le PE
  raccordé à la **même prise de terre** que le reste du bâtiment.

> Le **PE (terre) est commun et n'est JAMAIS commuté** : toutes les masses (châssis PV,
> MPPT, MultiPlus, bâti batterie, coffrets) restent reliées en permanence à la barrette
> de terre puis au piquet. Ce qui se commute, c'est **L et N** (voir §5).

---

## 3. Le relais de terre du MultiPlus‑II

Le MultiPlus‑II intègre un **relais de terre** (ground relay) qui gère automatiquement le
pont N‑PE :

| État de l'appareil | Relais de terre | Pont N‑PE |
|---|---|---|
| Mode onduleur (pas d'AC‑IN accepté) | **fermé** | **assuré par le MultiPlus** (sortie = TN‑S local) |
| AC‑IN connecté et accepté (réseau présent) | **ouvert** | assuré par le réseau amont (évite le double pont) |

- Réglage dans **VEConfigure → onglet Grid / « Ground relay »** : **activé** (valeur par défaut).
- Le relais s'ouvre **avant** que le relais d'entrée AC ne se ferme, et inversement →
  jamais deux ponts simultanés côté MultiPlus.

**Conséquence dans NOTRE topologie (EDF en aval via inverseur, AC‑IN non utilisé) :**
le MultiPlus est **toujours en mode onduleur**, donc son **relais de terre reste fermé en
permanence** quand il fonctionne. Le pont N‑PE de l'îlot onduleur est donc **toujours
présent**. C'est correct — à condition que ce neutre ne soit jamais mis en commun avec
celui d'EDF (§4‑5).

---

## 4. Le piège : inverseur de source qui ne coupe PAS le neutre

L'« inverseur de source » du schéma sélectionne qui alimente le tableau maison
(onduleur **ou** EDF). Si cet inverseur **ne commute que la phase** (1 pôle) et **laisse
les neutres reliés en permanence** :

```
   MultiPlus N ─────┬────────────── N tableau maison
                    │
   EDF N ───────────┘   (neutres communs en permanence)
```

Alors quand on bascule sur EDF :
- le neutre du tableau vient d'EDF (déjà mis à la terre chez le distributeur, régime TT),
- **MAIS** le relais de terre du MultiPlus continue de ponter N‑PE localement,
- → on obtient **deux ponts N‑PE** sur le même neutre (un chez EDF + un au MultiPlus).

Résultat : une partie du courant de neutre EDF revient par le **conducteur PE** →
- **déclenchements intempestifs** des DDR 30 mA,
- circulation de courant dans les masses,
- DDR potentiellement **aveuglé** sur un vrai défaut.

C'est exactement la situation à éviter.

---

## 5. La règle d'or et le câblage correct

> **Un seul pont N‑PE actif à la fois ⇒ l'inverseur de source DOIT commuter la phase ET
> le neutre (inverseur 2 pôles L+N pour du monophasé).**

Ainsi les **neutres des deux sources ne sont jamais reliés** entre eux, et chaque source
garde sa **propre** mise à la terre, unique :

```
                         ┌───────────── PE (commun, jamais commuté) ──────────────┐
                         │                                                        │
  MULTIPLUS-II           │   INVERSEUR DE SOURCE 2P (L+N)        TABLEAU MAISON    │
  (mode onduleur)        │   ┌───────────────┐                  ┌──────────────┐  │
   L ───────────────────────►│ I  \          │                  │ DDR 30 mA /  │  │
   N ──┐ relais de       │   │     \ ───── L ─┼───────────────►  │  groupe      │  │
       │ terre FERMÉ     │   │  II /          │                  │              │  │
       └──[N-PE]──► PE ───┐  │ I  \           │── N ───────────► │              │  │
                          │  │     \ ───── N ─┤                  └──────┬───────┘  │
  EDF (secours, TT)       │  │  II /          │                         │          │
   L ───────────────────────►│               │                         ▼ masses   │
   N ──(terre chez ───────►  └───────────────┘                    ───► barrette ───┘
        distributeur)                                                  de terre → piquet
```

- Position **I** = onduleur : pont N‑PE = relais de terre MultiPlus (îlot TN‑S local).
- Position **II** = EDF : pont N‑PE = côté distributeur (régime TT). Le neutre MultiPlus
  est **physiquement séparé** → pas de double pont.
- Le **PE reste commun** aux deux positions et relie toutes les masses à la barrette de
  terre puis au piquet (prise de terre unique du bâtiment).
- Les **DDR 30 mA par groupe** (tableau) sont fonctionnels dans les **deux** positions.

> Recouvrement : utiliser un inverseur à **coupure franche** (break‑before‑make) — les
> deux sources ne doivent jamais être reliées simultanément, même fugitivement.

---

## 6. Variante recommandée : EDF sur l'AC‑IN du MultiPlus

Si on accepte de faire transiter EDF **par l'entrée AC‑IN** du MultiPlus au lieu d'un
inverseur externe :

- le **transfert** source↔onduleur est **automatique et interne** (relais de transfert),
- le **relais de terre gère seul** le pont N‑PE (fermé en onduleur, ouvert sur réseau),
- EDF peut en plus **recharger la batterie** et alimenter les charges (PowerAssist),
- **plus besoin d'inverseur externe ni de commuter le neutre manuellement**.

Inconvénient vs le schéma actuel : il faut respecter la logique « entrée réseau » du
MultiPlus (et, en France, la question du raccordement/Consuel si on n'est pas réellement
isolé). Le choix « inverseur de source externe » du synoptique reste valable pour rester
**strictement autonome**, mais il impose la commutation du neutre (§5) et **EDF ne
rechargera pas la batterie**.

---

## 7. Réglages MultiPlus (VEConfigure / VictronConnect)

- **Ground relay : activé** (pont N‑PE automatique en mode onduleur).
- AC‑IN : non raccordé dans la topologie « inverseur externe » → le MultiPlus reste en
  mode onduleur, relais de terre fermé en permanence (comportement voulu).
- Vérifier la **type/sensibilité du DDR** en aval : type **A 30 mA** (présent sur la
  sortie off‑grid) compatible avec le relais de terre du MultiPlus.

---

## 8. Vérifications à la mise en service

1. **Continuité PE** : barrette de terre ↔ piquet, et chaque masse (châssis PV, MPPT,
   MultiPlus, bâti batterie, coffrets) ↔ barrette (< quelques ohms).
2. **Résistance de la prise de terre** (piquet) : valeur compatible avec la sensibilité
   du DDR (Ra × IΔn ≤ 50 V → ex. 30 mA ⇒ Ra largement < 1667 Ω, viser < 100 Ω).
3. **Pont N‑PE onduleur** : MultiPlus en marche, mesurer une faible impédance N↔PE en
   sortie (relais fermé). Doit être **présent** en position « onduleur ».
4. **Pas de double pont** : en position « EDF », vérifier que le neutre EDF n'est pas
   relié au neutre/PE de l'onduleur (l'inverseur a bien coupé le N de l'onduleur).
5. **Test bouton DDR** + test d'injection de courant de défaut sur chaque groupe, dans
   **les deux positions** de l'inverseur.
6. Vérifier la **coupure franche** (break‑before‑make) de l'inverseur de source.

---

## 9. Sections des conducteurs de protection

La liaison N‑PE ne sert à rien si le PE qui la matérialise est sous‑dimensionné : c'est lui
qui doit écouler le courant de défaut jusqu'au déclenchement du DDR ou du fusible.

### a) La règle générale (NF C 15‑100 §543.1)

Un PE se dimensionne **d'après le conducteur actif du circuit qu'il accompagne** :

| Section des actifs S | Section du PE |
|---|---|
| S ≤ 16 mm² | **S** (identique) |
| 16 < S ≤ 35 mm² | **16 mm²** |
| S > 35 mm² | **S / 2** |

Deux conducteurs échappent à cette table et ont leurs propres minima : le **conducteur de
terre** (barrette → piquet, §542.3) et les **liaisons équipotentielles** (§544).

### b) Sections retenues dans cette installation

| Segment | Section | Justification |
|---|---|---|
| **Barrette de terre → piquet** (conducteur de terre) | **16 mm² Cu isolé** sous gaine, ou **25 mm² Cu nu** si enterré en direct | §542.3 : 16 mm² = protégé contre la corrosion mais pas mécaniquement ; 25 mm² dès qu'il est nu dans le sol. Seul conducteur qui voit **tous** les défauts **et** les courants d'onde des parafoudres |
| **PE du circuit AC‑Out** (MultiPlus → tableau maison) | **10 mm²** | AC‑Out câblé en 10 mm² et 10 ≤ 16 → PE de même section |
| **PE de l'arrivée EDF** (disj. 2P 50 A) | **10 mm²** si arrivée 10 mm², **16 mm²** si arrivée 16 mm² | Le tronc PE tableau ↔ barrette doit tenir le défaut de **la source la plus puissante** : l'Icc du réseau EDF, très supérieur au court‑circuit du MultiPlus (qui s'autolimite). Dans le doute → **16 mm²** |
| **Masses côté DC** (châssis MPPT, MultiPlus, Lynx, bâti batterie, coffrets) | **6 mm²** | UTE C15‑712‑1 : 6 mm² Cu mini pour la liaison équipotentielle des masses PV. Le 4 mm² n'est admis qu'en intérieur protégé mécaniquement |
| **Structure / rails / cadres PV** | **6 mm²** (**16 mm²** si paratonnerre) | Avec un LPS, le bond structure ↔ prise de terre doit tenir un courant de foudre (NF EN 62305) |
| **Terre des parafoudres** (Type 2 : 2× DC + 2× AC) | **4 mm² mini, 10 mm² recommandé** | §534. Ici **la longueur prime sur la section** : règle des **50 cm** (aller actif + retour PE cumulés). Au‑delà, la chute inductive annule la protection quelle que soit la section |
| **Liaison équipotentielle principale** (canalisations eau / gaz) | **6 mm² mini** = moitié du PE principal, plafonné à 25 mm² | §544.1 |

> Couleur **vert‑jaune obligatoire et exclusive** sur tous ces conducteurs.

### c) Le piège : « les câbles batterie font 50 mm², faut‑il 25 mm² de terre ? »

**Non.** La règle S/2 vise le PE **d'un circuit**, celui qui écoule le courant de défaut. Côté
48 V DC, le PE ne fait ce travail **que si le − batterie est ponté à la terre** — ce qui
**n'est pas le cas ici** (DC flottant, §9d). Vérifions quand même cette hypothèse, la plus
défavorable : elle borne le besoin par le haut.

Un défaut **+ 48 V → châssis** renvoie alors le courant par le PE jusqu'au pont −/PE.
Contrainte thermique (formule adiabatique, NF C 15‑100 §543.1.2) :

```
S ≥ √(I²t) / k        k = 115 (Cu, isolant PVC, 70 → 160 °C)
```

| I²t total de coupure du Class‑T 225 A | Section mini du PE |
|---|---|
| 50 000 A²s | 1,9 mm² |
| 200 000 A²s | 3,9 mm² |

→ **6 mm² passe avec un facteur 1,5 à 3 de marge**, même dans l'hypothèse haute. Ce n'est pas
la section du câble de puissance qui dicte celle du PE, mais **l'énergie laissée passer par la
protection** : le Class‑T coupe en quelques millisecondes sous 7,5 kA, bien avant d'échauffer
le PE.

⚠️ Les deux valeurs d'I²t ci‑dessus sont un **encadrement d'ordre de grandeur**, pas une lecture
de fiche technique : à confirmer sur la datasheet **Bussmann JJN‑225** (ou Littelfuse JLLN‑225).

Ce qui justifie le **16 mm²** sur le tronc barrette → piquet n'est donc pas le défaut DC, mais
les **parafoudres** (onde 8/20 µs de plusieurs kA) et la tenue mécanique.

### d) Choix retenu : **DC flottant** (aucun pont −/PE)

**Décision : le circuit 48 V DC reste isolé de la terre.** Aucun conducteur actif (+ ni −)
n'est relié au PE, nulle part. Seules les **masses** (châssis MPPT, MultiPlus, Lynx, bâti
batterie, coffrets) sont raccordées à la barrette, pour l'équipotentialité.

```
   BATTERIE 48V            MPPT / MultiPlus / Lynx
     +  ─────────────────►  (électronique)          ✗ aucun pont vers le PE
     −  ─────────────────►
                                ┌── châssis métalliques ──┐
                                │                          │
                                └──► PE 6mm² ──► BARRETTE ──► piquet
```

Trois raisons :

1. **48 V = TBT.** Sous 120 V DC, aucun risque d'électrocution ne justifie de créer une
   référence de terre. Le risque réel côté DC est l'**arc et l'incendie** — traité par les
   fusibles (§4 de `batterie_securite_arret_urgence.md`), pas par la mise à la terre.
2. **Les MPPT ne sont pas à isolation galvanique** (− PV et − batterie communs). Ponter le −
   batterie reviendrait donc à mettre **tout le champ PV en « négatif à la terre »**, avec le
   + PV en permanence à **+450 V/terre** — ce qui change l'agencement attendu des parafoudres
   DC et sort du schéma standard UTE C15‑712. *(À confirmer sur le manuel du MPPT RS 450/100,
   `Doc/RS/`.)*
3. **Les protections fonctionnent déjà sans le pont.** Le Class‑T et les MEGA coupent le
   défaut qui compte, et qui existe dans les deux configurations : le **court‑circuit + ↔ −**.

**Contrepartie à assumer.** En DC flottant, un **1er défaut d'isolement** (+ ou − vers une
masse) ne produit **aucun courant** : il est indolore mais **invisible**. C'est le **2ᵉ**
défaut qui devient un court‑circuit franc, et il se boucle alors par le **réseau PE en
6 mm²**, pas par le 50 mm².

> **Contrôle d'isolement périodique — non optionnel.** Mesure **Riso** au mégohmmètre
> (500 V DC, installation consignée) entre **chaque pôle DC et le PE**, à la mise en service
> puis **annuellement**. Attendu : plusieurs MΩ. Toute chute franche = 1er défaut présent,
> à localiser **avant** qu'un 2ᵉ n'arrive.

**Conséquence sur `batterie_securite_arret_urgence.md` §2 :** la justification « le défaut
dangereux est le court‑circuit du + vers une masse » supposait le − ponté. Elle est remplacée
par la bonne raison — le **court‑circuit + ↔ −**. La conclusion (fusible sur le +, au plus
près de la borne) est **inchangée**.

C'est le pendant DC de la règle « un seul pont N‑PE » du §5 : **la référence de terre du DC
est une décision unique, explicite et documentée** — ici : *aucune*.

---

## 10. À reporter sur le synoptique

- Étiquette ajoutée sur la protection de sortie : « Liaison N‑PE : relais de terre MultiPlus ».
- Préciser que l'**inverseur de source est 2 pôles (L+N)** à coupure franche.
- Symboliser le **pont N‑PE** au niveau du MultiPlus (relais de terre) et la **prise de
  terre unique** (barrette → piquet) commune aux deux sources.
- **Coter les sections de PE** (§9) : 6 mm² masses DC, 10 mm² AC‑Out, 16 mm² barrette → piquet.
- Mention **« DC flottant : aucun pont −/PE »** sur la barrette de terre (§9d).

---

## 11. Synthèse (checklist)

- [ ] Un **seul** pont N‑PE actif à tout instant.
- [ ] Onduleur : pont N‑PE par **relais de terre** (activé dans VEConfigure).
- [ ] EDF : pont N‑PE **chez le distributeur** (régime TT), aucun pont interne.
- [ ] Inverseur de source **2P (L+N)**, coupure franche → neutres jamais communs.
- [ ] **PE commun**, jamais commuté ; toutes masses → barrette → piquet.
- [ ] **DDR 30 mA type A** par groupe, fonctionnels dans les deux positions.
- [ ] Prise de terre mesurée et compatible avec la sensibilité des DDR.
- [ ] **Sections PE** conformes au §9 : 6 mm² (masses DC), 10 mm² (AC‑Out), 16 mm² (barrette →
      piquet) — 25 mm² si cuivre nu enterré en direct.
- [ ] Parafoudres : liaison de terre ≥ 4 mm² **et longueur totale ≤ 50 cm**.
- [ ] **DC flottant** confirmé : aucun pont −/PE nulle part dans l'installation (§9d).
- [ ] **Riso mesuré** (mégohmmètre 500 V, pôles DC ↔ PE) à la mise en service, puis chaque
      année.

---

### Références
- NF C 15‑100 — régimes de neutre (TT/TN/IT), protection par DDR.
- NF C 15‑100 — §534 (parafoudres), §542.3 (conducteur de terre), §543.1 (sections des PE et
  formule adiabatique), §544 (liaisons équipotentielles).
- UTE C15‑712‑1 — liaison équipotentielle des masses PV (6 mm² Cu mini).
- NF EN 62305 — protection contre la foudre (liaison structure PV ↔ prise de terre).
- UTE C15‑712‑2 — installations photovoltaïques **autonomes** avec stockage.
- Victron Energy — *MultiPlus‑II 230 V, manuel* (relais de terre / ground relay,
  liaison N‑PE en mode onduleur) :
  https://www.victronenergy.com/upload/documents/MultiPlus-II_230V/32424-MultiPlus-II___Quattro-II-pdf-en.pdf
