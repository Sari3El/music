# Gothic Valley : greybox (phases 1 et 2 du cahier des charges)

Ce paquet contient la carte « Gothic Vampire Map » au stade **greybox** : le relief complet (3 024 m de côté) et tous les volumes jouables. On y trouve le château des vampires, la ville avec ses remparts, l'église, le manoir, 294 bâtiments dans les murs (plus 52 au faubourg Est) et 28 intérieurs visitables, ainsi que les 15 sites secondaires, les routes, les ponts, les points d'apparition et les caméras des 8 vues héros.
Le greybox est généré par les scripts du projet à partir du cahier des charges. La phase 4 a commencé avec les modèles des packs fournis par le commanditaire (licences et autorisations déclarées par lui ; crédits dans `BUILD_LOG.md`). Elle contient la **maison des chasseurs** au sud-ouest (modèle « Fantasy Castle »), avec sa grande salle, son cabinet et le passage secret derrière une armoire. Ce passage mène, par un colimaçon et un long escalier, à une **bibliothèque souterraine** de 45 × 120 m bâtie avec le kit « Classic Library ». Le **château des vampires** est le modèle « Castle 2.0 » posé sur l'éperon. Il contient la grande salle, la salle du trône, la chapelle, la salle de guerre, la bibliothèque, les appartements et le cabinet. Sous le palais, deux niveaux de sous-sols abritent la salle de banquet, la cuisine, le garde-manger, la cave, la crypte et les cachots. Un panneau derrière le trône ouvre sur un colimaçon jusqu'à la crypte, d'où un tunnel de 244 m mène à une porte cachée au pied de la falaise. Le château et la maison sont meublés uniquement avec les props des packs fournis (trône gothique, tapis, lustres, candélabres, tableaux, crucifix, cercueils, mobilier simple) ; la liste de ce qui manque encore est dans `doc/props_et_textures.md` du dépôt.

## Contenu

| Dossier | Contenu |
|---|---|
| `Heightmap/heightmap_base_4033.png` | Relief 16 bits, 4033 × 4033, encodé `32768 + 64 × altitude (m)` |
| `Content/` | 90 maillages FBX (`SM_GB_*`) avec collisions simples `UCX_`, rangés comme l'exige le cahier : `Environment/Castle`, `City`, `Church`, `Manor`, `Ruins`, `Nature`, `Landscape`, `Lodge`, `Library`, `Props`. S'y ajoutent les maillages des packs : `Environment/Castle/SM_C2_Castle` (le château, collision complexe par polygone), `Environment/Lodge/SM_FC_Lodge` (la maison) `Props/LibraryKit/SM_LB_*` (colonnes, voûtes, rayonnages et livres, escaliers en colimaçon, lustres, tables, verrière, etc.) et les props `Props/<pack>/SM_PR_*` (`Throne`, `RugsDark`, `RugsLight`, `Furniture`, `Chandelier`, `Candelabra`, `Paintings`, `Crucifixion`, `ChurchCross`, `Coffin`) ainsi que la cabane `Environment/Shack/SM_PR_Shack` |
| `Unreal/setup_map.py` | Script d'installation automatique pour l'éditeur (ADK Nanos World, UE 5.7) |
| `Textures/` | Textures générées (couleur, relief, rugosité) de chaque surface et du paysage, la carte de répartition du sol `T_GV_Splat`, et les textures des packs renommées `T_LB_*` (bibliothèque) et `T_FC_*` (maison) |
| `Data/` | Annexe A (`layout_manifest.json`), routes finales, positions et pivots des maillages, salles, vides, volumes, placements des pièces des packs (`placements_*.json`), matériaux des packs (`materials_kit.json`) et lumières (`lights.json`) |
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
   - importe les 90 maillages avec leurs collisions et Nanite, importe les textures et crée les matériaux texturés `M_GB_MasterTex` / `MI_GB_*` ;
   - importe les maillages des packs et crée leurs matériaux (`MI_LB_*`, `MI_FC_*`, `MI_C2_*`, `MI_PR_*` ; double face pour la coque de la maison, les tapis et les draps ; verre translucide `M_GB_MasterGlass` ; flammes et découpes en mode masqué `M_GB_MasterMasked`), place les 930 pièces et props du château, de la maison et de la bibliothèque (sans collision propre : les enveloppes `UCX_` des maillages `SM_GB_*` la portent, le mobilier y a sa boîte englobante) et les 124 lumières ponctuelles (bougies, lustres, lampes) ;
   - place chaque maillage à sa position exacte (1 m = 100 UU, +X = nord, +Y = est) ; les portes, herses, grilles et trappes sont en *Movable* avec le tag `ScriptedDoor` ;
   - pose les 6 points d'apparition (`SPAWN_*`, celui de la place du marché porte le tag `DefaultSpawn`), les 8 caméras `HERO_V1…V8`, les volumes de blocage derrière les frontières naturelles et les NavMeshBoundsVolume ;
   - crée la rivière (plugin Water), règle *GameMode Override* = None et Kill Z = -20000, puis ajoute le ciel (DirectionalLight, SkyLight, SkyAtmosphere, brouillard volumétrique) tagué `Sun` ;
   - applique au paysage l'auto-matériau `M_GV_Landscape` (herbe, boue, chemins, roche, neige selon le relief) ;
   - vérifie l'orientation (un cube témoin doit tomber à +1000 m nord / +500 m est) et l'altitude du relief : basse-cour du château (relief de la colline du modèle), place du marché à +33,9 m, etc.
5. Lisez les lignes `GV |` du *Output Log* : la dernière ligne résume le travail et liste les avertissements éventuels.
6. Enregistrez, puis testez en PIE. Points d'apparition : `SPAWN_city_square`, `SPAWN_castle_inner_ward`, etc.
7. Passage secret : l'armoire du cabinet (`GB_Lodge_SecretWardrobe`) est *Movable* avec les tags `ScriptedDoor`, `Slide` et `SlideOffsetCm_-200_0_0`. Votre script la fait glisser de 2 m vers le sud (-X) pour ouvrir la porte cachée.

Vous pouvez relancer le script : il supprime d'abord ce qu'il a placé (dossiers `GV/...` de l'Outliner).

## Export Nanos World

Cuisez depuis l'ADK, copiez le dossier cuit dans `Assets/` du serveur sous un nom en kebab-case (par exemple `gothic-valley`), complétez `NanosWorld/Assets.toml` et placez `GothicValley.webp` à côté du `.umap`.

## Important pour la suite

- Sous le palais, le cachot, la crypte de l'église, la cave du manoir, l'abbaye, le tunnel secret et la grotte de la cascade, le terrain est **volontairement abaissé**. Ces « vides couverts » évitent que le paysage traverse les souterrains, et les dalles et murs du greybox les recouvrent. Si vous sculptez ou érodez le paysage dans Unreal, ne remplissez pas ces zones : leurs coordonnées sont dans `Data/*_meta.json` (`voids`, `void_paths`).
- La phase 0 (carte test World Partition de 1 km², cuite et chargée sur un serveur Nanos World local) se fait chez vous : elle décide de la méthode de streaming (voir le journal).
