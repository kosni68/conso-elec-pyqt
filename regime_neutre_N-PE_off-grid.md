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

## 9. À reporter sur le synoptique

- Étiquette ajoutée sur la protection de sortie : « Liaison N‑PE : relais de terre MultiPlus ».
- Préciser que l'**inverseur de source est 2 pôles (L+N)** à coupure franche.
- Symboliser le **pont N‑PE** au niveau du MultiPlus (relais de terre) et la **prise de
  terre unique** (barrette → piquet) commune aux deux sources.

---

## 10. Synthèse (checklist)

- [ ] Un **seul** pont N‑PE actif à tout instant.
- [ ] Onduleur : pont N‑PE par **relais de terre** (activé dans VEConfigure).
- [ ] EDF : pont N‑PE **chez le distributeur** (régime TT), aucun pont interne.
- [ ] Inverseur de source **2P (L+N)**, coupure franche → neutres jamais communs.
- [ ] **PE commun**, jamais commuté ; toutes masses → barrette → piquet.
- [ ] **DDR 30 mA type A** par groupe, fonctionnels dans les deux positions.
- [ ] Prise de terre mesurée et compatible avec la sensibilité des DDR.

---

### Références
- NF C 15‑100 — régimes de neutre (TT/TN/IT), protection par DDR.
- UTE C15‑712‑2 — installations photovoltaïques **autonomes** avec stockage.
- Victron Energy — *MultiPlus‑II 230 V, manuel* (relais de terre / ground relay,
  liaison N‑PE en mode onduleur) :
  https://www.victronenergy.com/upload/documents/MultiPlus-II_230V/32424-MultiPlus-II___Quattro-II-pdf-en.pdf
