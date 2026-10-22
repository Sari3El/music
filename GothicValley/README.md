# Gothic Valley : carte « Gothic Vampire Map » pour Unreal Engine (Nanos World)

Réalisation du cahier des charges *Gothic Vampire Map: Design Document for Unreal Engine* (51 pages) : une vallée de
3 × 3 km avec un château sur son éperon, une ville fortifiée (église, manoir, 294 bâtiments), 22 points d'intérêt,
des routes, une rivière, un ruisseau et une cascade. Cible : ADK Nanos World (UE 5.7).

> **État : phases 1 (relief) et 2 (greybox) terminées et vérifiées automatiquement.** La phase 0 (test
> World Partition sur un serveur Nanos World) et l'import dans Unreal se font chez vous. Les phases 3 à 10
> (matériaux, architecture finale, lumière, gameplay, optimisation) viennent ensuite.

Tout est généré par les scripts de ce dossier, sans asset tiers ni contenu de franchise. Le paquet prêt à
importer (FBX, heightmap, script Unreal, rendus, contrôles) se reconstruit avec `scripts/run_all.sh`.

## Résultats

| Contrôle | Résultat |
|---|---|
| Altitudes des 22 POI (±10 m) | 22/22, écart maximal 4,7 m |
| Ravin du ruisseau, cascade (crête 116 m, pied 56/60 m) | conformes |
| Greybox | 86 maillages `SM_GB_*`, 161 794 triangles, 8 044 collisions simples `UCX_` |
| Intérieurs visitables (cahier : ≥ 25) | 28 |
| Bâtiments dans les murs (cahier : 260 à 320) | 294 (plus 52 au faubourg Est) |
| Test de marche, château | 37/37 pièces, tunnel jusqu'à sa sortie, 0 chute vers les vides |
| Test de marche, ville | 81/81 pièces, 0 chute vers les vides |
| Test de marche, sites secondaires | toutes les pièces atteintes, dont la grotte de la cascade |
| Plafonds ≥ 4 m, escaliers du château ≤ 28° | conformes |
| Vues héros V1 à V8 | rendues depuis les caméras du cahier (`screenshots/`) |

Écarts au cahier et questions ouvertes (par exemple les pentes des routes basse du château et commerciale, 12 et
14 % au lieu de 10 %) : voir le journal de build [`pack/BUILD_LOG.md`](pack/BUILD_LOG.md).

## Installation dans Unreal

Voir [`pack/README_FR.md`](pack/README_FR.md) : import manuel du paysage (heightmap 4033², échelle 75/75/200),
puis le script `pack/Unreal/setup_map.py`. Il importe et place les maillages, crée les matériaux, les points
d'apparition, les caméras des vues héros, les volumes et la rivière, règle le GameMode à None et le Kill Z à
-20000, puis tague le ciel `Sun`.

## Contenu du dossier

```
scripts/        générateurs Python (relief, greybox, tests de marche, export Blender, rendus, journal, paquet)
data/           annexe A (layout_manifest.json), tracés finaux des routes, parcelles du plan de la ville
doc/            plans du cahier utilisés par les contrôles de superposition
greybox/        métadonnées lues par le relief (vides couverts, plateformes) et configurations des tests de marche
pack/           script Unreal, guide d'installation, journal de build (copiés dans le paquet)
checks/         résultats des contrôles (POI, règles, tests de marche, temps de trajet, superpositions)
screenshots/    vues héros V1 à V8 et vue d'ensemble (rendus greybox)
```

## Reconstruire le paquet

Prérequis : Python 3 avec numpy, scipy, numba et Pillow, ainsi que Blender 4.5 (`blender` dans le PATH).

```bash
cd GothicValley
python3 scripts/terrain_gv.py "$PWD" && python3 scripts/terrain_check.py "$PWD" && touch terrain/check_done
scripts/run_all.sh "$PWD"          # greybox, tests de marche, export FBX, rendus, journal, paquet
```

Le relief lit les métadonnées de `greybox/` (vides sous les souterrains et le tunnel, plateformes, talus), et les
générateurs du greybox lisent le relief. Il faut donc relancer `terrain_gv.py` si le château, la ville ou les
sites changent. Le paquet est écrit dans `pack_out/GothicValley_Greybox_Phase2.zip`.
