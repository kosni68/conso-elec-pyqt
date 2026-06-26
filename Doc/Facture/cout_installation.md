# Coût de l'installation PV 48V

Récapitulatif du coût du matériel. Prix **TTC**, en euros.
- **Prix fermes** : fiches `Doc/*/prix.md`, facture PV (`Doc/PV/Facture_AIKO5002S.md`) et achats indiqués.
- **Prix de référence** : relevés sur le même fournisseur ([kitsolaire-discount.com](https://kitsolaire-discount.com)) pour les postes sans facture (marqués « réf. » / « ≈ », à confirmer au devis).

Quantités relevées sur le schéma de câblage (`installation_pv_cablage.drawio`).

## 1. Composants principaux (prix fermes)

| Composant | Réf. / modèle | Qté | PU TTC | Total TTC |
| --- | --- | ---: | ---: | ---: |
| Panneaux solaires (mono) | AiKO Neostar 2S 500 W (facture) | 15 | 108,99 € | 1 634,85 € |
| Panneaux solaires (bifacial) | AiKO Neostar 2S+ 500 W ABC Bifacial | 3 | 109,00 € | 327,00 € |
| Kit de montage PV | Amazon | 3 | 40,84 € | 122,52 € |
| Régulateur MPPT | Victron SmartSolar MPPT RS 450/100 | 1 | 1 063,80 € | 1 063,80 € |
| Régulateur MPPT | Victron SmartSolar MPPT 150/35 | 2 | 177,30 € | 354,60 € |
| Onduleur-chargeur | Victron MultiPlus-II 48/10000 (140/100) | 1 | 1 667,70 € | 1 667,70 € |
| Batterie lithium | Pylontech US5000 48V 4,8 kWh | 3 | 949,00 € | 2 847,00 € |
| Distribution DC | Victron Lynx Distributor 1000V | 1 | 193,50 € | 193,50 € |
| Sectionneur batterie | Victron Battery Switch 275A | 1 | 37,74 € | 37,74 € |
| Supervision | Victron Cerbo GX | 1 | 238,50 € | 238,50 € |
| Écran supervision | Victron GX Touch 50 | 1 | 197,40 € | 197,40 € |
| **Sous-total composants principaux** | | | | **8 684,61 €** |

## 2. Protections, câblage & accessoires (prix de référence)

Prix indicatifs relevés sur le même fournisseur, à confirmer au devis selon les références exactes.

| Poste | Réf. / modèle | Qté | PU TTC | Total TTC |
| --- | --- | ---: | ---: | ---: |
| Distribution DC | Victron Lynx Power In (M10) | 1 | ≈ 125,00 € | ≈ 125,00 € |
| Coffret DC champ RS | Coffret protection DC 1000V 2 MPPT + parafoudre | 1 | 586,50 € | 586,50 € |
| Coffrets DC champs 150/35 | Coffret protection DC 600V string + parafoudre | 2 | ≈ 150,00 € | ≈ 300,00 € |
| Fusible batterie | MEGA 250A/80V (alt. Class-T 250A) + porte-fusible | 1 | 104,04 € | 104,04 € |
| Fusible sortie RS | MEGA 125A/58V | 1 | 33,66 € | 33,66 € |
| Fusibles sorties MPPT 150/35 | 40A (logés dans le Lynx Distributor) | 2 | inclus | — |
| Coffret protection AC-In | Coffret AC monophasé 6kW 32A + parafoudre T2 | 1 | 129,99 € | 129,99 € |
| Coffret protection AC-Out | Coffret AC monophasé 6kW 32A + différentiel 30mA | 1 | 129,99 € | 129,99 € |
| Câblage DC/AC + cosses + terre | Câbles 95/70/16/10/6/4 mm², MC4, barrette/piquet terre | 1 | ≈ 250,00 € | ≈ 250,00 € |
| **Sous-total protections & accessoires** | | | | **≈ 1 659,18 €** |

## 3. Total estimatif matériel

| | TTC |
| --- | ---: |
| Composants principaux (fermes) | 8 684,61 € |
| Protections & accessoires (réf.) | ≈ 1 659,18 € |
| **Total matériel estimé** | **≈ 10 343,79 €** |

> Hors **pose / main-d'œuvre**, hors **tableau divisionnaire AC** existant (disjoncteurs par circuit), et hors raccordement Enedis éventuel.

## Notes

- **Champ PV = 18 panneaux 500 W** : 15 mono (facture, 1 362,38 € HT / 1 634,85 € TTC) + 3 bifaciaux (109,00 €). Le synoptique indique « 18× 450Wc » (libellé ancien) ; la puissance réelle est de 18 × 500 W ≈ **9 kWc**.
- **MPPT 150/35** : variante SmartSolar (177,30 €) retenue, conforme au schéma ; BlueSolar à 161,10 €.
- **Capacité batterie** : 3 × 4,8 kWh = **14,4 kWh**.
- **Lynx Shunt VE.Can retiré** : redondant avec le BMS Pylontech qui remonte déjà SOC/tension/courant au Cerbo GX via CAN. À ne réintégrer que pour une mesure de courant indépendante du BMS.
- Les fusibles 40A des sorties MPPT 150/35 sont assurés par les positions fusibles du **Lynx Distributor** (déjà compté).

## Sources (prix de référence)

- [Lynx Distributor 1000V — 193,50 €](https://kitsolaire-discount.com/fr/protections-batterie/1995-systemes-distribution-dc-lynx-distributor-1000v-victron-energy-9085823106314.html)
- [GX Touch 50 — 197,40 €](https://kitsolaire-discount.com/fr/affichages-et-moniteurs/2112-superviseur-gx-touch-50-victron-energy-9085823106093.html)
- [Fusible MEGA 125A/58V — 33,66 €](https://kitsolaire-discount.com/fr/protections-batterie/898-fusible-mega-fuse-125a58v-pour-systeme-48v.html)
- [Porte-fusible MEGA-Fuse — 26,52 €](https://kitsolaire-discount.com/fr/protections-batterie/590-porte-fusible-mega-fuse-victron-energy-9331416833816.html)
- [Coffret protection DC 1000V 2 MPPT + parafoudre — 586,50 €](https://kitsolaire-discount.com/fr/coffrets-de-protection/1930-coffret-de-protection-dc-1000v-2-mppt-parafoudre-madenr-9331416835537.html)
- [Coffret AC 6kW 32A monophasé — 129,99 €](https://kitsolaire-discount.com/fr/coffrets-de-protection/953-coffret-ac-6kw-32a-monophase-technideal-9331361836429.html)
