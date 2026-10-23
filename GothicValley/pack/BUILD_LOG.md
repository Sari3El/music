# Journal de build : Gothic Vampire Map

Document de référence : *Gothic Vampire Map: Design Document for Unreal Engine* (51 pages, version 1.0). Unités : mètres, +X nord, +Y est, +Z haut.
Toute la géométrie est générée par les scripts du projet (aucun asset tiers, aucun contenu de franchise). Les licences d'assets seront consignées à partir de la phase 4 (kits modulaires sous licence).

## Phase 0 : mise en place (à faire chez vous)

Elle demande l'ADK Nanos World et un serveur local, que je n'ai pas : projet UE 5.7 dans l'ADK, carte test World Partition de 1 km² cuite et chargée sur un serveur Nanos World local, puis traversée de plusieurs cellules.
**Choix du streaming : en attente de ce test.** S'il réussit, World Partition (cellules de 256 m, chargement à 768 m, HLOD pour le château, le clocher, les remparts et le Grand Pont). S'il échoue, niveau persistant et sous-niveaux (section 11).

## Phase 1 : relief

- Paysage 4033 × 4033, 0,75 m entre sommets, 3 024 m de côté, centré sur l'origine. Relief de -26.7 m à 440.0 m.
- **22 POI sur 22 à ±10 m de leur altitude** (écart maximal 4.7 m) :

| # | POI | cible | terrain | écart |
|---|---|---|---|---|
| 1 | Castle | 204 | 203.9 | -0.1 |
| 2 | Barbican and Great Bridge | 200 | 199.1 | -0.9 |
| 3 | Serpentine Road and Castle Stairs | 142 | 141.5 | -0.5 |
| 4 | Watchtower ruin | 67 | 66.5 | -0.5 |
| 5 | North Cemetery | 23 | 23.1 | +0.1 |
| 6 | Walled City | 34 | 34.0 | +0.0 |
| 7 | Great Church | 35 | 35.4 | +0.4 |
| 8 | Noble Manor | 34 | 33.8 | -0.2 |
| 9 | West Bridge | -1 | 1.9 | +2.9 |
| 10 | Gallows Hill and crossroads | 9 | 4.3 | -4.7 |
| 11 | Abbey ruin | 88 | 88.0 | +0.0 |
| 12 | Woodcutters' camp | 83 | 83.0 | -0.0 |
| 13 | Stone circle | 119 | 119.0 | +0.0 |
| 14 | River falls | 82 | 82 | +0.0 |
| 15 | East Faubourg | 19 | 19.0 | +0.0 |
| 16 | Watermills and tannery | -4 | -2.9 | +1.1 |
| 17 | Farming hamlet | 7 | 7.1 | +0.1 |
| 18 | Quarry | 150 | 150.0 | -0.0 |
| 19 | East Pass border post | 95 | 96.6 | +1.6 |
| 20 | West Pass | 35 | 35.0 | +0.0 |
| 21 | The Fen | 4 | 3.4 | -0.6 |
| 22 | River gorge | -21 | -20.0 | +1.0 |

- Rocher du château : sommet plat à +204 m (posé à +203,85 m, 15 cm sous les sols du palais, dans la tolérance de ±1 m), 216 × 232 m (cahier : environ 240 × 220), falaise sud 51.3 m, falaise est 88.1 m. La façade sud du palais prolonge la falaise (bord du rocher sur la face extérieure de la façade).
- Terrasse de la barbacane à +199.0 m, flanc à 25.0° ; ravin de 91.7 m sous le pont (fond +108.3, parois à 75.0°).
- Ville : couronne +35.4 m, place +33.9 m ; marais : cuvette +3.4 m, bord minimal +8.8 m.
- Ravin du ruisseau du château : le lit suit le ruisseau de X 430 à 1000 (écart maximal 0.0 m). Le flanc de la terrasse le comblait sur environ 270 m ; il est recreusé après la terrasse jusqu'au débouché (X 380), et le contrôle porte désormais sur toute la longueur.
- Cascade : crête 116.0 m (cible 116), vasque 56.0 m, lit au pied 56.0 m (cible 60). Un creux d'érosion de 65 m sous la chute a été comblé, et le contrôle vérifie désormais la crête et le pied.
- Routes : profils recalculés au plus près de l'annexe A sous les limites de pente (`data/roads_log.txt`) :

  - castle_road_lower (cart road, 644.0 m) : pente max du profil 12.0 % (règle 10.0 %) : **hors règle**
  - serpentine (cart road, 1335.0 m) : pente max du profil 12.0 % (règle 12.0 %) : OK
  - castle_stairs (stairs, 526.0 m) : pente max du profil 48.8 % (règle 53.2 %) : OK
  - west_road (cart road, 782.0 m) : pente max du profil 17.9 % (règle 35.0 %) : OK
  - trade_road (cart road, 1716.0 m) : pente max du profil 14.0 % (règle 10.0 %) : **hors règle**
  - abbey_road (track, 587.0 m) : pente max du profil 18.2 % (règle 35.0 %) : OK
  - fen_path (footpath, 750.0 m) : pente max du profil 7.0 % (règle 35.0 %) : OK
  - forest_track (track, 984.0 m) : pente max du profil 17.4 % (règle 35.0 %) : OK
  - quarry_road (track, 590.0 m) : pente max du profil 33.8 % (règle 35.0 %) : OK
  - mill_track (track, 348.0 m) : pente max du profil 11.4 % (règle 35.0 %) : OK
  - dock_lane (track, 69.0 m) : pente max du profil 11.6 % (règle 35.0 %) : OK
  - falls_path (footpath, 1018.0 m) : pente max du profil 7.0 % (règle 35.0 %) : OK
  - hunters_track (track, 786.0 m) : pente max du profil 14.0 % (règle 35.0 %) : OK

## Phase 2 : greybox

**86 maillages** (`SM_GB_*`), 164 170 triangles, 8 053 coques de collision simples (UCX). Pivots à la base de chaque objet, et sur la charnière pour les portes, herses, grilles et trappes.

### Château
- Barbacane, Grand Pont (100 m, tablier de 6 m, parapets de 1,1 m, 4 piles dont la plus haute fait 93.3 m, pont-levis), châtelet (tours de 13 m sur 28 m, herse), courtine (17 m côté porte, 9 m sur les falaises, 3 m d'épaisseur, parapets de 1,1 m des deux côtés et merlons), **10 tours** rondes de 11 m (30 à 35 m) traversées par le chemin de ronde, dont 2 tours-escaliers. Viennent ensuite la basse-cour et ses bâtiments, la porte intérieure, la cour intérieure, le palais (146 × 69 m, faîte à +38 m), le donjon (75 m, aire à +65 m, balcon), le pont couvert et la chapelle.
- 12 salles principales aux dimensions exactes du cahier, plus les salles secondaires (37 pièces en tout) :

| Salle | construite (L × l × h) | cahier | conforme |
|---|---|---|---|
| Great Hall | 32 × 20 × 16.0 | 32 × 20 × 16 | oui |
| Throne Room | 45 × 20 × 20.0 | 45 × 20 × 20 | oui |
| Banquet Hall | 36 × 14 × 12.0 | 36 × 14 × 12 | oui |
| Kitchen | 16 × 12 × 8.0 | 16 × 12 × 8 | oui |
| War Room | 16 × 12 × 7.0 | 16 × 12 × 7 | oui |
| Lord's Study | 12 × 9 × 6.0 | 12 × 9 × 6 | oui |
| Library | 24 × 14 × 9.0 | 24 × 14 × 9 | oui |
| Lord's Apartments | 14 × 10 × 6.0 | 14 × 10 × 6 | oui |
| Larder | 18 × 10 × 5.0 | 18 × 10 × 5 | oui |
| Crypt | 26 × 14 × 6.0 | 26 × 14 × 6 | oui |
| Dungeon | 40 × 24 × 4.5 | 40 m corridor, 10 cells 3 x 3, guard room, interrogation room, pit cell | oui |
| Chapel | 32 × 12 × 15.0 | 32 × 12 × 15 | oui |

- Escalier dérobé : panneau derrière l'estrade du trône, puis colimaçon qui relie la crypte (L-2), le trône (L0), le cabinet (L1) et les appartements (L2). Tunnel secret de **297.7 m** jusqu'à la porte cachée au pied de la falaise sud [574, 384, 118].
### Ville
- Remparts (ellipse 460 × 600 m, 10,5 m de haut, 2,5 m d'épaisseur, chemin de ronde de 2,85 m avec parapets, hourds), **16 tours** carrées de 18 à 25 m, **4 portes** (porte Nord double avec barbacane, tour de 30 m et herse ; porte Est avec péage ; porte Ouest ; porte d'Eau), rue de ronde de 5 m, 4 escaliers d'accès au chemin de ronde.
- **294 bâtiments dans les murs** (cahier : 260 à 320) posés sur les 295 parcelles du plan (3 parcelles écartées car elles chevauchaient un monument, 2 pour ouvrir la vue V1 sur le donjon) : 271 maisons fermées en 16 variantes (2 à 4 étages, pignon ou gouttereau sur rue, encorbellement, toits de 50 à 60°, fenêtres éclairées ou sombres), plus les édifices publics.
- Grande église : église-halle 76 × 32 m, voûtes à 22 m sur 10 piliers, chœur et abside polygonale, porche sud, portail nord, sacristie, tribune d'orgue, crypte sous le chœur, tour ouest de 72 m avec escalier en colimaçon jouable jusqu'à la chambre des cloches (+45 m). Cimetière clos d'un mur de 1,2 m, charnier, vieux tilleul, presbytère.
- Manoir noble : enclos de 110 × 90 m (mur de 4 m), châtelet aux armes vierges, cour et puits, deux ailes avec loggia, tour d'angle de 25 m et sa salle haute. Huit pièces : vestibule, grande chambre de 20 × 10 m avec estrade, cabinet des archives, salle à manger, deux chambres, cuisine, salle des gardes, chambre forte en cave. S'y ajoutent les écuries, la chapelle et le jardin clos avec fontaine, pavillon et terrasse face au château.
- **Intérieurs visitables : 28** (cahier : au moins 25) : Great Church, Noble Manor, Town hall, Guild hall, City Watch barracks, Parish house, Main inn, Tavern at the East Gate, Tavern in the River Quarter, Blacksmith, Apothecary, Bakery, Butcher, Cloth merchant and tailor, General store, Bathhouse, Barber-surgeon, Scribe and notary, Poor house 1, Poor house 2, Artisan house 1, Artisan house 2, Merchant house 1, Merchant house 2, Mortuary chapel, Faubourg stables, Watermill, Dock warehouse.
### Sites secondaires et routes
- Escaliers du château : 3 m de large, palier tous les 15 m (26 paliers), pente maximale 28.0° (règle ≤ 28°), 2 passerelles au-dessus de la serpentine, 8 croisements à niveau. Muret côté vallée sur la serpentine (39 tronçons), 42 pieux vides en lisière du bois mort, charrette et squelette de cheval au premier lacet.
- Tour de guet en ruine (escalier jusqu'au sommet sans toit), cimetière Nord (120 × 120 m, 300 tombes, chapelle mortuaire de 14 × 22 m, 3 mausolées, ossuaire, cabane du gardien, ifs), gibet et carrefour (croix, borne), abbaye en ruine (nef de 45 × 14 m, arcs, moignon de tour, cloître, reliquaire caché sous le chœur), camp des bûcherons, cercle de pierres, grotte derrière la cascade, faubourg Est (52 bâtiments, écuries visitables), moulins et tannerie, quais et 3 entrepôts, hameau (12 fermes dont une brûlée, église en bois à flèche, tombes fraîches), carrière, poste frontière Est (palissade), éboulement du col Ouest, marais (passerelles, cabane sur pilotis, bouleaux morts), pont Ouest (5 arches, 60 m, oratoire), panneaux aux carrefours, montagnes de fond.
### Contrôles d'acceptation de la phase 2

**Tests de marche** : simulation de la capsule Nanos World (rayon 0,35 m, hauteur 1,8 m, marche franchissable 0,4 m, pente maximale d'environ 39°) sur les collisions réelles et le relief, à 0,5 m × 0,1 m de résolution. La recherche de chute vers les vides a été faite pour le château et la ville, pas pour les sites. Le test avec le vrai personnage reste à faire dans Unreal.

- Château : 37/37 pièces atteintes depuis la basse-cour et la terrasse, ainsi que le chemin de ronde, les 10 tours, le Grand Pont, le pont-levis, le balcon, l'aire du donjon et le tunnel jusqu'à sa sortie. Chutes vers les vides : 0.
- Ville : 81/81 pièces atteintes depuis la place, ainsi que les 16 tours, les 4 portes vers l'extérieur, la chambre des cloches, la tribune d'orgue et la tour du manoir. Chutes vers les vides : 0.
- Site « approach » : 2/2 pièces atteintes depuis la route.
- Site « cemetery » : 6/6 pièces atteintes depuis la route.
- Site « abbey » : 2/2 pièces atteintes depuis la route.
- Site « camp » : 2/2 pièces atteintes depuis la route.
- Site « falls » : 1/1 pièces atteintes depuis la route.
- Site « faubourg » : 1/1 pièces atteintes depuis la route.
- Site « mills_docks » : 2/2 pièces atteintes depuis la route.
- Site « hamlet » : 1/1 pièces atteintes depuis la route.
- Site « quarry » : 1/1 pièces atteintes depuis la route.
- Site « border » : 1/1 pièces atteintes depuis la route.
- Site « fen » : 1/1 pièces atteintes depuis la route.

**Temps de trajet** (vitesses du cahier : marche 1,5 m/s, course 6 m/s, cheval 12 m/s ; à remesurer avec le vrai personnage) :

| Trajet | distance construite | cahier | marche | course | cheval |
|---|---|---|---|---|---|
| Market square to North Gate | 232 m | 230 m | 2.6 min | 0.6 min | 0.3 min |
| North Gate to castle gate by road | 2101 m | 2050 m | 23.3 min | 5.8 min | 2.9 min |
| North Gate to castle gate by the stairs | 1308 m | 1270 m | 14.5 min | 3.6 min | 1.8 min |
| East Gate to hamlet | 900 m | 890 m | 10.0 min | 2.5 min | 1.3 min |
| West Gate to abbey ruin | 895 m | 890 m | 9.9 min | 2.5 min | 1.2 min |
| East Gate to east pass (arrival) | 1722 m | 1710 m | 19.1 min | 4.8 min | 2.4 min |

Aucun trajet entre deux pôles ne dépasse 6 minutes en courant.

**Règles du cahier vérifiées sur la géométrie** :

- interiors >= 25 : oui
- city buildings 260-320 : oui
- city towers 16 : oui
- ceilings >= 4 m : oui
- castle stairs <= 28 deg : oui
- no stray primitives : oui
- Portes principales de 3 × 4,5 m sur les circulations publiques, portes de service d'au moins 1,6 × 2,6 m, couloirs d'au moins 2 m (service) et 3 m (public), escaliers d'au moins 2,5 m, colimaçons à marches de 2,2 m, marches de 20 cm maximum, parapets de 1,1 m sur les ponts, balcons et chemins de ronde : appliqués par construction et confirmés par les tests de marche.

**Audit géométrique** (`scripts/gb_audit.py`, `Checks/audit.json`) : chaque pièce visible doit reposer sur quelque chose, le terrain, une autre pièce dessous ou une pièce accolée. Le premier audit a trouvé un pilier de l'abbaye à moitié au-dessus de la trémie de l'escalier, des têtes d'arc et des linteaux tenus d'un seul côté, des hourds en bois détachés des remparts, des merlons plus larges que le parapet, une cloche et une cage pendues dans le vide, des contreforts décrochés sous le palais, des clôtures, tombes et charrettes flottant sur les pentes, et le terrain qui traversait le sol de 16 pièces. Tout est corrigé. Il reste 32 pièces isolées en partie sans appui, vérifiées une à une en image : couronnes d'ifs sur leur tronc, peaux qui sèchent sous leur perche, chaîne de la cage, toits de mausolées. Pièces avec du terrain au-dessus du sol : 0.

**Vues héros** (rendus texturés Cycles dans `Screenshots/`, à refaire dans Unreal de jour et de nuit aux phases suivantes) : V1 Market square, V2 Throne Room balcony, V3 Great Bridge, V4 Great Hall portal, V5 Church bell chamber, V6 Third hairpin, V7 East pass, V8 Abbey ruin at dusk, V0 Valley overview.

## Textures (début de la phase 3)

- 22 jeux de textures tuilables générés par `scripts/make_textures.py`, sans aucun asset tiers. Pour les bâtiments (16) : pierre de taille sombre (château, remparts), calcaire clair (église), dalles, enduit intérieur, enduit à la chaux, planches, colombages, tuiles de terre cuite, ardoise, fer rouillé, tissu, terre, feuillage, vitraux sertis de plomb (éteints ou éclairés), roche naturelle. Pour le sol (6) : herbe, boue, chemin, pavés, roche, neige. Chacun a une carte de couleur, de relief (normal map, convention OpenGL, canal vert inversé à l'import Unreal) et de rugosité, en 1024 px pour une tuile de 2 m (bâtiments) ou de 4 m (sol).
- UV à l'échelle du monde (`gb_build.py`) : sols en plan, chaque autre face dans son plan avec le haut vers le haut, ce qui garde les assises et les tuiles horizontales et le motif continu d'un bâtiment à l'autre.
- Paysage : herbe, boue des berges et du marais, chemins, pavés (ville et plateau du château), roche (pentes de plus de 35° environ) et neige (au-dessus de +385 m), mélangés par deux cartes de répartition calculées à partir du relief final (`T_GV_Splat`, `T_GV_Splat2`, 2048 px sur toute la carte). Le script Unreal construit `M_GV_Landscape` avec la même logique et l'applique au paysage importé.
- Les kits d'architecture sous licence de la phase 4 remplaceront ces surfaces ; les noms de matériaux (`MI_GB_*`) restent les mêmes.

## Phase 4 (en cours) : maison des chasseurs et bibliothèque souterraine

- Maison de la famille de chasseurs (modèle « Fantasy Castle ») : le point le plus éloigné du château des vampires, à [-1400, -700], sur une plate-forme à +81 m. La porte regarde la vallée (nord). Le modèle n'a pas d'intérieur : l'aile basse est aménagée en grande salle (cheminée, table, lustres, coffres, râteliers) et en cabinet de travail (bibliothèque, table de lecture). Ses matériaux sont rendus double face pour que les murs se voient de l'intérieur ; la porte et les panneaux sombres derrière les fenêtres de cette aile sont retirés.
- Passage secret : dans le cabinet, une armoire coulisse de 2 m (maillage *Movable*, tags `ScriptedDoor`, `Slide`) et découvre une porte cachée. Derrière, un escalier en colimaçon en fer (kit de la bibliothèque) descend de 4,8 m. Ensuite, un long escalier de pierre voûté de 69 m (154 marches de 16,9 cm sur 32 cm, 10 volées, paliers éclairés de torches) descend de 26,1 m jusqu'au balcon de la bibliothèque. Il reste au moins 4,0 m de roche au-dessus de sa voûte.
- Bibliothèque souterraine : nef gothique de 45 × 120 m, sol à +40 m, voûtes à +68,1 m, avec au moins 12 m de roche au-dessus. Elle est construite avec les pièces du kit « Classic Library » : colonnes, croisées d'ogives et nervures à l'échelle 1,5, rayonnages et livres à l'échelle 1. On arrive par un balcon. Un escalier d'honneur (volée centrale, palier, puis deux volées) descend dans la nef. Deux galeries de bois courent dans chaque bas-côté (+5,1 et +10,2 m), reliées par quatre escaliers en colimaçon. Il y a des rayonnages muraux à trois niveaux, des épis de rayonnages doubles, des tables de lecture et de grands lustres, et une grande verrière gothique au fond.
- 665 pièces de kit placées (`Data/placements_lodge.json`), 70 lumières ponctuelles (`Data/lights.json`). Les collisions sont des enveloppes `UCX_` invisibles portées par les maillages `SM_GB_Lodge_*` et `SM_GB_Library_*` ; les pièces du kit n'en ont pas. Les colimaçons ont une rampe hélicoïdale de collision.
- Test de marche (`nav_lodge.json`, depuis l'extérieur de la porte) : 15/15 salles atteintes, 10/10 points de contrôle, 0 fuite. Le chemin passe par l'armoire ouverte, le colimaçon, l'escalier secret, le balcon, les galeries et les quatre colimaçons.
- Relief : plate-forme de la maison et vide sous le puits secret. Les salles souterraines sont marquées `sealed` : le relief n'y est jamais creusé, et l'audit vérifie la roche au-dessus.
- Chemin des chasseurs : piste de 3 m, longue de 793 m, du sentier du marais (même rive que la maison) jusqu'à sa porte, pente maximale 14 % (calcul du chemin le moins coûteux, `track_lodge.py`).

## Modèles tiers (phase 4)

Le commanditaire déclare détenir les licences et les autorisations écrites des créateurs pour ces modèles, utilisés dans la carte. Les crédits et attributions sont conservés ici :

- « Fantasy Castle » par **Hawtor Studio** : maison des chasseurs (coque extérieure, textures). Attribution requise.
- « Classic Library for Blender Eevee and Cycles » par **denniswoo1993** : kit de la bibliothèque souterraine et mobilier de la maison. Ses textures intégrées viennent d'ambientCG, de Poly Haven et de Textures.com.
- « Castle 2,0 » par **EldersCrawler** : château des vampires (à venir).
- « Medieval Houses Package » par **Daniel** : maisons de la ville (à venir).
- « Medieval Church » par **Daniel** : vitraux et textures de l'église (à venir). Attribution requise.
- « Medieval castle » par **Misha Kiselev** : maison du noble (à venir).

Trois cartes de couleur du pack « Fantasy Castle » (enduit, toit, bois) étaient vides, et le kit de bibliothèque n'avait pas de couleur pour la pierre, le fer et les vitraux. Ces cartes ont été recalculées à partir des cartes de relief et de rugosité du même pack (`fc_fix_colors.py`, `lib_fix_colors.py`). Les vitraux utilisent un motif au plomb généré.

## Écarts au cahier des charges et raisons

- Heightmap : le cahier mentionne un `heightmap_base_4033.png` livré avec le document, mais je ne l'ai pas reçu. Je l'ai généré à partir de l'annexe A, avec le même encodage et la même orientation.
- Pentes : la route basse du château (au mieux 12 %) et la route commerciale (au mieux 14 %) ne peuvent pas respecter 10 % sur les tracés de l'annexe sans allonger le tracé (question ouverte). Les autres routes respectent leur règle.
- Serpentine, point 5 : z 205 → 200 (la terrasse est plate à +199, exigence MUST). Route ouest au pont : le -1 m de l'annexe est le niveau de la rivière. Le tablier du pont Ouest va de +12,4 à +9,0 m (5 arches, 60 m, 1,1 m de parapet).
- Raccords : les routes secondaires partent à l'altitude de la route qu'elles rejoignent : forest_track 25,3 m (annexe 16), quarry_road 21 m (annexe 9), mill_track 23 m (annexe 22).
- Escaliers × serpentine : 2 passerelles en [507, -40] et [597, -40] (l'escalier passe 8 à 11 m au-dessus de la route), croisements à niveau ailleurs.
- Palais : la crête est tenue à +38 m (exigence de silhouette) par des toits à 55° tronqués, avec les gouttières à +29 m pour loger le niveau L2 (+22). Les arcs-boutants côté vallée partent de piles encorbellées dans la falaise, puisque la façade prolonge la falaise.
- Souterrains : au lieu de trous dans le paysage, que Python ne sait pas peindre, le terrain est abaissé sous le palais, le cachot, la crypte de l'église, la cave du manoir, la nef de l'abbaye, le tunnel et la grotte. Murs de 1,6 m, dalles et talus en masquent les bords. Le rocher est posé à +203,85 m (15 cm sous les sols) pour éviter le scintillement.
- Règle caméra (plafonds d'au moins 4 m) : les intérieurs de ville ont des étages de 5,0 et 4,6 m, plus hauts que des maisons réelles. Le tunnel secret fait 4 m de haut.
- Tunnel secret (298 m) : galerie sinueuse sous le palais, puis traversée droite de la falaise sud sous un éboulis jusqu'à la porte cachée [574, 384, 118].
- Caserne du guet : la boîte de l'annexe dépassait de 10 m hors du rempart ; elle a été glissée de 15,5 m vers l'intérieur.
- Puits du marché et fontaine sèche de la cour intérieure : déplacés hors des points d'apparition imposés par l'annexe.
- Grotte de la cascade : accès depuis la berge par une rampe, puis par une corniche de 4 m posée sur la vasque au pied de la falaise, sous le rideau d'eau, jusqu'à l'entrée de la grotte. Le chemin de la cascade passe 40 m plus haut.
- Cimetière Nord : centré sur son POI. La route du château de l'annexe le traverse, d'où des portes dans le mur à son passage.
- Moulins : posés sur la berge nord. L'ancienne plateforme de terrain bouchait la rivière ; elle a été supprimée et aucune plateforme ne touche plus le lit.
- Auberge principale : salle commune de 12 × 11,5 m (une parcelle) au lieu d'environ 18 × 10 m, et 6 chambres sur 2 étages.
- Faubourg Est : 52 bâtiments générés le long de la route commerciale (le plan en dessine 18, le texte en demande environ 50).
- Tour de guet : 11 × 11 m pour loger un colimaçon à marches de 2,2 m (le cahier ne donne que la hauteur de 18 m).
- Vue V1 : 2 parcelles au nord-est de la place ne sont pas bâties, pour que le donjon apparaisse entre les toits comme le demande le cahier.
- Balcon de la salle du trône (V2) : sa moitié extérieure est 0,8 m plus bas (4 marches de 20 cm dans l'ouverture de la façade). Sinon le parapet de 1,1 m masquait la ville depuis la caméra imposée.
- Vue V7 : la route commerciale monte au col Est par une vallée ouverte (flancs à 14°), et non dans une tranchée de 40 m, pour que le plan d'établissement voie la vallée.
- Vue V6 : depuis le troisième lacet, l'éperon entre la route et le bord du ravin montait 13 m au-dessus de la caméra du cahier. Il est entaillé sous la ligne de visée (1,5 m de marge, flancs à 45°) pour que les murs du château apparaissent au-dessus.
- Chambre des cloches (V5) : l'étage des cloches est octogonal sur la tour carrée de l'annexe, avec une baie par face. Sur une chambre carrée, la ligne vers le donjon tombait dans l'angle ; la face nord-est regarde désormais le château (« la tour fait face à la tour »). Abat-sons seulement au-dessus de la hauteur des yeux.
- Abbaye (V8) : la dernière travée nord de la nef est effondrée et le pignon du chœur a une vraie baie vide, sa moitié nord étant tombée. Depuis la caméra du cahier, le château apparaît entre les arcs brisés.
- Pied de la cascade dessiné explicitement (vasque à +56, lit à +60, berges, falaise verticale), car l'érosion y laissait un creux de 65 m.

Journal du solveur de routes :

    castle_road_lower: grade rule 10% cannot be met on the Appendix polyline (best 12%); needs a longer alignment (open question)
    serpentine endpoint [320.0, -95.0] pinned to castle_road_lower at z 66.5 (Appendix 67)
    serpentine point 5 [722.0, -70.0, 205.0] -> z 200.0: hairpin on the barbican terrace: terrace is flat at +199 (MUST), Appendix says 205
    castle_stairs endpoint [320.0, -95.0] pinned to castle_road_lower at z 66.5 (Appendix 67)
    west_road point 1 [-452.0, -855.0, -1.0] -> z 7.0: West Bridge deck at +7 m: the -1 m of the Appendix is the river level (POI tolerance 10 m kept)
    trade_road: grade rule 10% cannot be met on the Appendix polyline (best 14%); needs a longer alignment (open question)
    forest_track endpoint [40.0, -300.0] pinned to castle_road_lower at z 25.3 (Appendix 16)
    quarry_road endpoint [-250.0, 900.0] pinned to trade_road at z 21.0 (Appendix 9)
    mill_track endpoint [-450.0, -140.0] pinned to trade_road at z 23.0 (Appendix 22)
    stairs x serpentine at [328.9, -90.5]: stairs 68.8 m, road 67.7 m -> level
    stairs x serpentine at [507.0, -40.0]: stairs 123.2 m, road 111.8 m -> footbridge
    stairs x serpentine at [597.0, -40.0]: stairs 154.0 m, road 145.3 m -> footbridge
    stairs x serpentine at [647.0, -40.0]: stairs 177.9 m, road 177.6 m -> level
    stairs x serpentine at [730.0, -12.7]: stairs 198.6 m, road 200.0 m -> level
    stairs x serpentine at [736.8, 14.3]: stairs 199.3 m, road 200.0 m -> level
    stairs x serpentine at [738.4, 34.2]: stairs 199.5 m, road 200.0 m -> level
    stairs x serpentine at [739.9, 54.2]: stairs 199.7 m, road 200.0 m -> level

## Questions ouvertes

- Avez-vous le `heightmap_base_4033.png` d'origine ? Mon pipeline peut le reprendre (nivellement des routes, vides et contrôles).
- Routes basse du château et commerciale : peut-on allonger leurs tracés (lacets) pour tenir 10 %, ou accepte-t-on 12 et 14 % ?
- Phase 0 : résultat du test World Partition sur votre serveur Nanos World.
- Taille réelle de la capsule du personnage Nanos World, pour refaire le test de marche avec ses valeurs exactes.
- Tag « Sun » : le script le pose sur la lumière directionnelle, la SkyLight, le SkyAtmosphere et le brouillard. À confirmer selon votre version de Nanos World.
- Plugin Water : largeur et profondeur des points de spline de la rivière à vérifier dans l'éditeur, car Python n'y a pas toujours accès.

## Étapes suivantes

Phase 3 (sol et eau : auto-matériau, splines de routes, rivière, ruisseau, cascade, gués, mares du marais), puis phases 4 et 5 (architecture et intérieurs à partir de kits modulaires sous licence, consignés ici), 6 (nature et histoire), 7 (lumière), 8 (gameplay), 9 (optimisation) et 10 (export).
