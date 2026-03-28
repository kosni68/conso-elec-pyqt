# Analyse de consommation électrique

Application bureau en `PyQt6` pour analyser un export de consommation électrique au pas de 30 minutes, filtrer la période jour/nuit, visualiser les données et simuler la rentabilité d'une installation photovoltaïque avec batterie.

L'interface utilise un thème sombre et s'appuie sur `pandas`, `numpy` et `matplotlib`.

## Fonctionnalités

- chargement d'un fichier CSV au format `Énergie;Date;Consommation`
- affichage de KPI de consommation et coût estimé au tarif base
- visualisations:
  - consommation journalière
  - totaux mensuels
  - profil horaire moyen
- filtres:
  - plage de dates
  - découpage jour/nuit paramétrable
- simulation photovoltaïque + batterie:
  - puissance PV en `kWc`
  - productible annuel en `kWh/kWc/an`
  - coût PV
  - capacité batterie en `kWh`
  - puissance de charge/décharge
  - rendement aller-retour
  - SOC minimum
  - coût batterie
- calcul des indicateurs:
  - énergie réseau avant/après
  - coût avant/après
  - économies annuelles
  - taux d'autoconsommation
  - taux d'autonomie
  - retour sur investissement simple

## Prérequis

- `Python 3.13` ou compatible
- Windows, Linux ou macOS avec interface graphique

## Installation

Installer les dépendances:

```bash
python -m pip install -r requirements.txt
```

## Lancement

Depuis le dossier du projet:

```bash
python main.py
```

Ou en précisant un CSV particulier:

```bash
python main.py "C:\Users\Nico\Desktop\Consommation electrique\112486686.csv"
```

## Format CSV attendu

Le fichier doit contenir les colonnes suivantes:

- `Énergie`
- `Date`
- `Consommation`

Exemple:

```csv
Énergie;Date;Consommation
Électricité;"19/06/2025 08:30:00";"0.182 kWh"
Électricité;"19/06/2025 09:00:00";"0.140 kWh"
```

## Utilisation

1. Ouvrir l'application.
2. Charger un fichier CSV avec le bouton `Parcourir…` ou lancer `main.py` avec le chemin du fichier.
3. Vérifier les KPI et les graphiques dans `Vue globale`.
4. Ajuster les dates et le découpage `jour/nuit` dans l'onglet `Filtres`.
5. Renseigner les paramètres PV et batterie dans l'onglet `Simulation`.
6. Lire les économies annuelles et le retour simple.

## Hypothèses de simulation

La simulation est indicative, pas une étude photovoltaïque bancaire ou installateur.

- tarif v1: `Base`
- pas de revente de surplus
- pas de charge batterie depuis le réseau
- pas d'arbitrage tarifaire
- pas de météo réelle
- production PV répartie avec des coefficients mensuels fixes
- profil intra-journalier PV reconstruit avec une courbe sinusoïdale
- année reconstituée pour annualiser un fichier partiel

## Tests

Lancer les tests:

```bash
python -m pytest -q
```

## Structure du projet

```text
.
|-- README.md
|-- main.py
|-- requirements.txt
|-- 112486686.csv
|-- conso_app/
|   |-- analysis.py
|   |-- models.py
|   |-- theme.py
|   `-- ui.py
`-- tests/
    |-- test_analysis.py
    `-- test_ui.py
```

## Fichiers principaux

- `main.py`: point d'entrée de l'application
- `conso_app/ui.py`: interface PyQt
- `conso_app/analysis.py`: import CSV, agrégats, annualisation et simulation
- `conso_app/theme.py`: thème sombre global et style des graphiques
- `tests/`: tests unitaires et smoke test UI
