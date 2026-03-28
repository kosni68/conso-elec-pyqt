# Analyse de consommation électrique

Application bureau en `PyQt6` pour analyser un export de consommation électrique au pas de 30 minutes, filtrer une plage de dates, visualiser les usages et simuler une installation photovoltaïque avec batterie.

L’application s’appuie sur `pandas`, `numpy` et `matplotlib`, avec une structure refactorisée pour garder la logique métier et l’interface nettement plus lisibles.

## Fonctionnalités

- chargement d’un fichier CSV au format `Énergie;Date;Consommation`
- affichage de KPI de consommation et de coût estimé au tarif base
- visualisations de consommation journalière, mensuelle et du profil horaire moyen
- filtres par plage de dates et découpage jour/nuit paramétrable
- simulation PV + batterie avec estimation des économies annuelles
- annualisation d’un historique partiel pour produire une année complète de simulation

## Prérequis

- `Python 3.13` ou compatible
- Windows, Linux ou macOS avec interface graphique

## Installation

```bash
python -m pip install -r requirements.txt
```

## Lancement

Depuis la racine du projet :

```bash
python main.py
```

Ou avec un fichier précis :

```bash
python main.py "C:\Users\Nico\Desktop\Consommation electrique\112486686.csv"
```

## Format CSV attendu

Colonnes obligatoires :

- `Énergie`
- `Date`
- `Consommation`

Exemple :

```csv
Énergie;Date;Consommation
Électricité;"19/06/2025 08:30:00";"0.182 kWh"
Électricité;"19/06/2025 09:00:00";"0.140 kWh"
```

Le chargeur tolère aussi l’ancienne variante de texte corrompu si un export historique en contient encore.

## Utilisation

1. Ouvrir l’application.
2. Charger un CSV avec `Parcourir…` ou lancer `main.py` avec un chemin de fichier.
3. Lire les KPI et la `Vue globale`.
4. Ajuster les dates et le découpage jour/nuit dans `Filtres`.
5. Régler les paramètres PV et batterie dans `Simulation`.
6. Lire les économies annuelles, l’autonomie et le retour simple.

## Hypothèses de simulation

- tarif v1 : `Base`
- pas de revente de surplus
- pas de charge batterie depuis le réseau
- pas d’arbitrage tarifaire
- pas de météo réelle
- production PV répartie avec des coefficients mensuels fixes
- profil intra-journalier PV reconstruit avec une courbe sinusoïdale
- année reconstituée pour annualiser un fichier partiel

## Tests

Les deux commandes suivantes doivent fonctionner depuis la racine du dépôt :

```bash
python -m pytest -q
```

```bash
pytest -q
```

## Structure du projet

```text
.
|-- README.md
|-- main.py
|-- requirements.txt
|-- 112486686.csv
|-- conso_app/
|   |-- __init__.py
|   |-- models.py
|   |-- theme.py
|   |-- analysis/
|   |   |-- __init__.py
|   |   |-- csv_loader.py
|   |   |-- analyzer.py
|   |   |-- annualizer.py
|   |   `-- simulation.py
|   `-- ui/
|       |-- __init__.py
|       |-- main_window.py
|       |-- controls.py
|       |-- simulation_panel.py
|       `-- charts.py
`-- tests/
    |-- conftest.py
    |-- test_analysis.py
    `-- test_ui.py
```
