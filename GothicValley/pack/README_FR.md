# Gothic Valley : greybox (phases 1 et 2 du cahier des charges)

Ce paquet contient la carte « Gothic Vampire Map » au stade **greybox** : le relief complet (3 024 m de côté) et tous les volumes jouables. On y trouve le château avec ses 12 salles, la ville avec ses remparts, l'église, le manoir, 294 bâtiments dans les murs (plus 52 au faubourg Est) et 28 intérieurs visitables, ainsi que les 15 sites secondaires, les routes, les ponts, les points d'apparition et les caméras des 8 vues héros.
Rien ne vient d'une licence existante : tout est généré par les scripts du projet à partir du cahier des charges.

## Contenu

| Dossier | Contenu |
|---|---|
| `Heightmap/heightmap_base_4033.png` | Relief 16 bits, 4033 × 4033, encodé `32768 + 64 × altitude (m)` |
| `Content/` | 86 maillages FBX (`SM_GB_*`) avec collisions simples `UCX_`, rangés comme l'exige le cahier : `Environment/Castle`, `City`, `Church`, `Manor`, `Ruins`, `Nature`, `Landscape`, `Props` |
| `Unreal/setup_map.py` | Script d'installation automatique pour l'éditeur (ADK Nanos World, UE 5.7) |
| `Textures/` | Textures générées (couleur, relief, rugosité) de chaque surface et du paysage, plus la carte de répartition du sol `T_GV_Splat` |
| `Data/` | Annexe A (`layout_manifest.json`), routes finales, positions et pivots des maillages, salles, vides, volumes |
| `Screenshots/` | Vues héros V1 à V8 et vue d'ensemble (rendus greybox) |
| `Checks/` | Résultats des contrôles : altitudes des POI, superposition sur la carte maîtresse et le plan de la ville, tests de marche, règles |
| `NanosWorld/` | Modèle d'`Assets.toml` et vignette `.webp` pour l'export |
| `BUILD_LOG.md` | Journal de build : ce qui est fait, écarts au cahier et pourquoi, questions ouvertes |

## Installation dans Unreal (ADK Nanos World)

1. Activez les plugins **Python Editor Script Plugin** et **Editor Scripting Utilities**, ainsi que **Water** (autorisé par Nanos World) si vous voulez la rivière. Redémarrez l'éditeur.
2. Créez un niveau vide dans `Content/GothicValley/Maps/` (nom conseillé : `GothicValley`).
3. **Paysage** (à faire à la main, car Unreal ne permet pas de le créer en Python) : *Landscape* › *Manage* › *New* › *Import from File*.
   - Fichier : `Heightmap/heightmap_base_4033.png`
   - Section Size : 63 × 63 quads ; Sections per Component : 2 × 2 ; Components : 32 × 32 (résolution 4033 × 4033)
   - Location : X = -151200, Y = -151200, Z = 0
   - Scale : X = 75, Y = 75, Z = 200
4. *Tools* › *Execute Python Script…* › choisissez `Unreal/setup_map.py`. Le script :
   - importe les 86 maillages avec leurs collisions et Nanite, importe les textures et crée les matériaux texturés `M_GB_MasterTex` / `MI_GB_*` ;
   - place chaque maillage à sa position exacte (1 m = 100 UU, +X = nord, +Y = est) ; les portes, herses, grilles et trappes sont en *Movable* avec le tag `ScriptedDoor` ;
   - pose les 6 points d'apparition (`SPAWN_*`, celui de la place du marché porte le tag `DefaultSpawn`), les 8 caméras `HERO_V1…V8`, les volumes de blocage derrière les frontières naturelles et les NavMeshBoundsVolume ;
   - crée la rivière (plugin Water), règle *GameMode Override* = None et Kill Z = -20000, puis ajoute le ciel (DirectionalLight, SkyLight, SkyAtmosphere, brouillard volumétrique) tagué `Sun` ;
   - applique au paysage l'auto-matériau `M_GV_Landscape` (herbe, boue, chemins, roche, neige selon le relief) ;
   - vérifie l'orientation (un cube témoin doit tomber à +1000 m nord / +500 m est) et l'altitude du relief : rocher du château à +204 m, place du marché à +33,9 m, etc.
5. Lisez les lignes `GV |` du *Output Log* : la dernière ligne résume le travail et liste les avertissements éventuels.
6. Enregistrez, puis testez en PIE. Points d'apparition : `SPAWN_city_square`, `SPAWN_castle_inner_ward`, etc.

Vous pouvez relancer le script : il supprime d'abord ce qu'il a placé (dossiers `GV/...` de l'Outliner).

## Export Nanos World

Cuisez depuis l'ADK, copiez le dossier cuit dans `Assets/` du serveur sous un nom en kebab-case (par exemple `gothic-valley`), complétez `NanosWorld/Assets.toml` et placez `GothicValley.webp` à côté du `.umap`.

## Important pour la suite

- Sous le palais, le cachot, la crypte de l'église, la cave du manoir, l'abbaye, le tunnel secret et la grotte de la cascade, le terrain est **volontairement abaissé**. Ces « vides couverts » évitent que le paysage traverse les souterrains, et les dalles et murs du greybox les recouvrent. Si vous sculptez ou érodez le paysage dans Unreal, ne remplissez pas ces zones : leurs coordonnées sont dans `Data/*_meta.json` (`voids`, `void_paths`).
- La phase 0 (carte test World Partition de 1 km², cuite et chargée sur un serveur Nanos World local) se fait chez vous : elle décide de la méthode de streaming (voir le journal).
