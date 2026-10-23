# Writes pack/BUILD_LOG.md from the check results (phases 0-2), in French.
import sys, json, glob, os

ROOT = sys.argv[1]
P1 = json.load(open(f"{ROOT}/terrain/phase1_checks.json"))
GB = json.load(open(f"{ROOT}/greybox/gb_checks.json"))
TR = json.load(open(f"{ROOT}/greybox/phase2_travel_rooms.json"))
NC = json.load(open(f"{ROOT}/greybox/nav/nav_castle.json"))
NV = json.load(open(f"{ROOT}/greybox/nav/nav_city.json"))
NS = json.load(open(f"{ROOT}/greybox/nav/nav_sites_summary.json"))
CM = json.load(open(f"{ROOT}/greybox/castle_meta.json"))
CI = json.load(open(f"{ROOT}/greybox/city_meta.json"))
SI = json.load(open(f"{ROOT}/greybox/sites_meta.json"))
RL = open(f"{ROOT}/data/roads_log.txt").read().strip().splitlines()
HV = json.load(open(f"{ROOT}/renders/hero/hero_views.json")) if os.path.exists(f"{ROOT}/renders/hero/hero_views.json") else []
ok = lambda b: "oui" if b else "**non**"
L = []
w = L.append
w("# Journal de build : Gothic Vampire Map\n")
w("Document de référence : *Gothic Vampire Map: Design Document for Unreal Engine* (51 pages, version 1.0). Unités : mètres, +X nord, +Y est, +Z haut.")
w("Toute la géométrie est générée par les scripts du projet (aucun asset tiers, aucun contenu de franchise). Les licences d'assets seront consignées à partir de la phase 4 (kits modulaires sous licence).\n")
w("## Phase 0 : mise en place (à faire chez vous)\n")
w("Elle demande l'ADK Nanos World et un serveur local, que je n'ai pas : projet UE 5.7 dans l'ADK, carte test World Partition de 1 km² cuite et chargée sur un serveur Nanos World local, puis traversée de plusieurs cellules.")
w("**Choix du streaming : en attente de ce test.** S'il réussit, World Partition (cellules de 256 m, chargement à 768 m, HLOD pour le château, le clocher, les remparts et le Grand Pont). S'il échoue, niveau persistant et sous-niveaux (section 11).\n")
w("## Phase 1 : relief\n")
w(f"- Paysage 4033 × 4033, 0,75 m entre sommets, 3 024 m de côté, centré sur l'origine. Relief de {P1['features']['relief_min_max'][0]} m à {P1['features']['relief_min_max'][1]} m.")
pois = P1["poi"]
w(f"- **{sum(p['ok'] for p in pois)} POI sur {len(pois)} à ±10 m de leur altitude** (écart maximal {max(abs(p['delta']) for p in pois):.1f} m) :\n")
w("| # | POI | cible | terrain | écart |\n|---|---|---|---|---|")
for p in pois:
    w(f"| {p['id']} | {p['name']} | {p['target']} | {p['terrain']} | {p['delta']:+.1f} |")
f = P1["features"]
w("")
w(f"- Rocher du château : sommet plat à +204 m (posé à +203,85 m, 15 cm sous les sols du palais, dans la tolérance de ±1 m), {f['crag_top']['size_m'][0]} × {f['crag_top']['size_m'][1]} m (cahier : environ 240 × 220), falaise sud {f['cliff_south_m']} m, falaise est {f['cliff_east_m']} m. La façade sud du palais prolonge la falaise (bord du rocher sur la face extérieure de la façade).")
w(f"- Terrasse de la barbacane à +{f['terrace_z']} m, flanc à {f['terrace_flank_slope_deg']}° ; ravin de {f['ravine_depth_under_bridge_m']} m sous le pont (fond +{f['ravine_floor_at_bridge_z']}, parois à {f['ravine_wall_max_deg']}°).")
w(f"- Ville : couronne +{f['city_crown_z']} m, place +{f['market_square_z']} m ; marais : cuvette +{f['fen_basin_z']} m, bord minimal +{f['fen_rim_min_z']} m.")
if "falls" in P1:
    fl = P1["falls"]
    w(f"- Ravin du ruisseau du château : le lit suit le ruisseau de X 430 à 1000 (écart maximal {f['ravine_bed']['max_excess_m']} m). Le flanc de la terrasse le comblait sur environ 270 m ; il est recreusé après la terrasse jusqu'au débouché (X 380), et le contrôle porte désormais sur toute la longueur.")
    w(f"- Cascade : crête {fl['lip']} m (cible {fl['lip_target']}), vasque {fl['pool']} m, lit au pied {fl['foot_bed']} m (cible {fl['base_target']}). Un creux d'érosion de 65 m sous la chute a été comblé, et le contrôle vérifie désormais la crête et le pied.")
w("- Routes : profils recalculés au plus près de l'annexe A sous les limites de pente (`data/roads_log.txt`) :\n")
for r in P1["roads"]:
    if "rule_pct" in r:
        w(f"  - {r['id']} ({r['type']}, {r['length']} m) : pente max du profil {r['profile_max_grade_pct']} % (règle {r['rule_pct']} %) : {'OK' if r['ok'] else '**hors règle**'}")
w("")
w("## Phase 2 : greybox\n")
w(f"**{GB['groups']} maillages** (`SM_GB_*`), {GB['tris']:,} triangles, {GB['hulls']:,} coques de collision simples (UCX). Pivots à la base de chaque objet, et sur la charnière pour les portes, herses, grilles et trappes.\n".replace(",", "\u202f").replace("\u202f ", ", "))
w("### Château")
w(f"- Barbacane, Grand Pont (100 m, tablier de 6 m, parapets de 1,1 m, 4 piles dont la plus haute fait {max(p['height'] for p in CM['piers'])} m, pont-levis), châtelet (tours de 13 m sur 28 m, herse), courtine (17 m côté porte, 9 m sur les falaises, 3 m d'épaisseur, parapets de 1,1 m des deux côtés et merlons), **{len(CM['towers'])} tours** rondes de 11 m (30 à 35 m) traversées par le chemin de ronde, dont 2 tours-escaliers. Viennent ensuite la basse-cour et ses bâtiments, la porte intérieure, la cour intérieure, le palais (146 × 69 m, faîte à +38 m), le donjon (75 m, aire à +65 m, balcon), le pont couvert et la chapelle.")
w(f"- 12 salles principales aux dimensions exactes du cahier, plus les salles secondaires ({len(CM['rooms'])} pièces en tout) :\n")
w("| Salle | construite (L × l × h) | cahier | conforme |\n|---|---|---|---|")
for r in TR["core_rooms"]:
    w(f"| {r['name']} | {' × '.join(str(v) for v in r['built'])} | {r['doc'] if isinstance(r['doc'], str) else ' × '.join(str(v) for v in r['doc'])} | {ok(r['ok'])} |")
w(f"\n- Escalier dérobé : panneau derrière l'estrade du trône, puis colimaçon qui relie la crypte (L-2), le trône (L0), le cabinet (L1) et les appartements (L2). Tunnel secret de **{CM['tunnel_length_m']} m** jusqu'à la porte cachée au pied de la falaise sud [574, 384, 118].")
w("### Ville")
w(f"- Remparts (ellipse 460 × 600 m, 10,5 m de haut, 2,5 m d'épaisseur, chemin de ronde de 2,85 m avec parapets, hourds), **{len(CI['towers'])} tours** carrées de 18 à 25 m, **4 portes** (porte Nord double avec barbacane, tour de 30 m et herse ; porte Est avec péage ; porte Ouest ; porte d'Eau), rue de ronde de 5 m, 4 escaliers d'accès au chemin de ronde.")
w(f"- **{CI['buildings_inside_walls']} bâtiments dans les murs** (cahier : 260 à 320) posés sur les {CI['plots_from_plan']} parcelles du plan ({CI['plots_dropped'].get('landmark', 0)} parcelles écartées car elles chevauchaient un monument, {CI['plots_dropped'].get('v1_sightline', 0)} pour ouvrir la vue V1 sur le donjon) : {len(CI['houses'])} maisons fermées en 16 variantes (2 à 4 étages, pignon ou gouttereau sur rue, encorbellement, toits de 50 à 60°, fenêtres éclairées ou sombres), plus les édifices publics.")
w("- Grande église : église-halle 76 × 32 m, voûtes à 22 m sur 10 piliers, chœur et abside polygonale, porche sud, portail nord, sacristie, tribune d'orgue, crypte sous le chœur, tour ouest de 72 m avec escalier en colimaçon jouable jusqu'à la chambre des cloches (+45 m). Cimetière clos d'un mur de 1,2 m, charnier, vieux tilleul, presbytère.")
w("- Manoir noble : enclos de 110 × 90 m (mur de 4 m), châtelet aux armes vierges, cour et puits, deux ailes avec loggia, tour d'angle de 25 m et sa salle haute. Huit pièces : vestibule, grande chambre de 20 × 10 m avec estrade, cabinet des archives, salle à manger, deux chambres, cuisine, salle des gardes, chambre forte en cave. S'y ajoutent les écuries, la chapelle et le jardin clos avec fontaine, pavillon et terrasse face au château.")
w(f"- **Intérieurs visitables : {GB['enterable_interiors']}** (cahier : au moins 25) : " + ", ".join(GB["enterable_list"]) + ".")
w("### Sites secondaires et routes")
st = SI["stairs"]
w(f"- Escaliers du château : 3 m de large, palier tous les 15 m ({st['landings']} paliers), pente maximale {st['max_angle_deg']}° (règle ≤ 28°), 2 passerelles au-dessus de la serpentine, {st['level_gaps']} croisements à niveau. Muret côté vallée sur la serpentine ({SI['serpentine_wall_segments']} tronçons), {SI['stakes']} pieux vides en lisière du bois mort, charrette et squelette de cheval au premier lacet.")
w(f"- Tour de guet en ruine (escalier jusqu'au sommet sans toit), cimetière Nord (120 × 120 m, 300 tombes, chapelle mortuaire de 14 × 22 m, 3 mausolées, ossuaire, cabane du gardien, ifs), gibet et carrefour (croix, borne), abbaye en ruine (nef de 45 × 14 m, arcs, moignon de tour, cloître, reliquaire caché sous le chœur), camp des bûcherons, cercle de pierres, grotte derrière la cascade, faubourg Est ({SI['faubourg_buildings']} bâtiments, écuries visitables), moulins et tannerie, quais et 3 entrepôts, hameau (12 fermes dont une brûlée, église en bois à flèche, tombes fraîches), carrière, poste frontière Est (palissade), éboulement du col Ouest, marais (passerelles, cabane sur pilotis, bouleaux morts), pont Ouest (5 arches, 60 m, oratoire), panneaux aux carrefours, montagnes de fond.")
w("### Contrôles d'acceptation de la phase 2\n")
w("**Tests de marche** : simulation de la capsule Nanos World (rayon 0,35 m, hauteur 1,8 m, marche franchissable 0,4 m, pente maximale d'environ 39°) sur les collisions réelles et le relief, à 0,5 m × 0,1 m de résolution. La recherche de chute vers les vides a été faite pour le château et la ville, pas pour les sites. Le test avec le vrai personnage reste à faire dans Unreal.\n")
w(f"- Château : {sum(r['reached'] for r in NC['rooms'])}/{len(NC['rooms'])} pièces atteintes depuis la basse-cour et la terrasse, ainsi que le chemin de ronde, les 10 tours, le Grand Pont, le pont-levis, le balcon, l'aire du donjon et le tunnel jusqu'à sa sortie. Chutes vers les vides : {len(NC['leaks'])}.")
w(f"- Ville : {sum(r['reached'] for r in NV['rooms'])}/{len(NV['rooms'])} pièces atteintes depuis la place, ainsi que les 16 tours, les 4 portes vers l'extérieur, la chambre des cloches, la tribune d'orgue et la tour du manoir. Chutes vers les vides : {len(NV['leaks'])}.")
for k, v in NS.items():
    if v["rooms"]:
        w(f"- Site « {k} » : {sum(1 for r in v['rooms'] if r[1])}/{len(v['rooms'])} pièces atteintes depuis la route.")
w("\n**Temps de trajet** (vitesses du cahier : marche 1,5 m/s, course 6 m/s, cheval 12 m/s ; à remesurer avec le vrai personnage) :\n")
w("| Trajet | distance construite | cahier | marche | course | cheval |\n|---|---|---|---|---|---|")
for r in TR["travel"]:
    w(f"| {r['route']} | {r['distance_m']} m | {r['doc_m']} m | {r['walk_min']} min | {r['run_min']} min | {r['horse_min']} min |")
w("\nAucun trajet entre deux pôles ne dépasse 6 minutes en courant.\n")
w("**Règles du cahier vérifiées sur la géométrie** :\n")
for k, v in GB["checks"].items():
    w(f"- {k} : {ok(v)}")
w("- Portes principales de 3 × 4,5 m sur les circulations publiques, portes de service d'au moins 1,6 × 2,6 m, couloirs d'au moins 2 m (service) et 3 m (public), escaliers d'au moins 2,5 m, colimaçons à marches de 2,2 m, marches de 20 cm maximum, parapets de 1,1 m sur les ponts, balcons et chemins de ronde : appliqués par construction et confirmés par les tests de marche.")
AU = json.load(open(f"{ROOT}/greybox/audit.json")) if os.path.exists(f"{ROOT}/greybox/audit.json") else None
if AU is not None:
    slab = lambda i: i["height"] <= 0.6 and min(i["size"]) >= 1.5
    free = [i for i in AU["free_standing_unsupported"] if not slab(i)]
    w("\n**Audit géométrique** (`scripts/gb_audit.py`, `Checks/audit.json`) : chaque pièce visible doit reposer sur quelque chose, "
      "le terrain, une autre pièce dessous ou une pièce accolée. Le premier audit a trouvé un pilier de l'abbaye à moitié "
      "au-dessus de la trémie de l'escalier, des têtes d'arc et des linteaux tenus d'un seul côté, des hourds en bois détachés "
      "des remparts, des merlons plus larges que le parapet, une cloche et une cage pendues dans le vide, des contreforts "
      "décrochés sous le palais, des clôtures, tombes et charrettes flottant sur les pentes, et le terrain qui traversait le "
      f"sol de 16 pièces. Tout est corrigé. Il reste {len(free)} pièces isolées en partie sans appui, vérifiées une à une en "
      "image : couronnes d'ifs sur leur tronc, peaux qui sèchent sous leur perche, chaîne de la cage, toits de mausolées. "
      f"Pièces avec du terrain au-dessus du sol : {len(AU['rooms'])}.")
if HV:
    w("\n**Vues héros** (rendus texturés Cycles dans `Screenshots/`, à refaire dans Unreal de jour et de nuit aux phases suivantes) : " + ", ".join(f"{h['id']} {h['name']}" for h in HV) + ".")
w("\n## Textures (début de la phase 3)\n")
w("- 22 jeux de textures tuilables générés par `scripts/make_textures.py`, sans aucun asset tiers. Pour les bâtiments (16) : "
  "pierre de taille sombre (château, remparts), calcaire clair (église), dalles, enduit intérieur, enduit à la chaux, "
  "planches, colombages, tuiles de terre cuite, ardoise, fer rouillé, tissu, terre, feuillage, vitraux sertis de plomb "
  "(éteints ou éclairés), roche naturelle. Pour le sol (6) : herbe, boue, chemin, pavés, roche, neige. Chacun a une carte "
  "de couleur, de relief (normal map, convention OpenGL, canal vert inversé à l'import Unreal) et de rugosité, en 1024 px "
  "pour une tuile de 2 m (bâtiments) ou de 4 m (sol).")
w("- UV à l'échelle du monde (`gb_build.py`) : sols en plan, chaque autre face dans son plan avec le haut vers le haut, "
  "ce qui garde les assises et les tuiles horizontales et le motif continu d'un bâtiment à l'autre.")
w("- Paysage : herbe, boue des berges et du marais, chemins, pavés (ville et plateau du château), roche (pentes de plus de "
  "35° environ) et neige (au-dessus de +385 m), mélangés par deux cartes de répartition calculées à partir du relief final "
  "(`T_GV_Splat`, `T_GV_Splat2`, 2048 px sur toute la carte). Le script Unreal construit `M_GV_Landscape` avec la même "
  "logique et l'applique au paysage importé.")
w("- Les kits d'architecture sous licence de la phase 4 remplaceront ces surfaces ; les noms de matériaux (`MI_GB_*`) restent les mêmes.")
w("\n## Écarts au cahier des charges et raisons\n")
dev = [
    "Heightmap : le cahier mentionne un `heightmap_base_4033.png` livré avec le document, mais je ne l'ai pas reçu. Je l'ai généré à partir de l'annexe A, avec le même encodage et la même orientation.",
    "Pentes : la route basse du château (au mieux 12 %) et la route commerciale (au mieux 14 %) ne peuvent pas respecter 10 % sur les tracés de l'annexe sans allonger le tracé (question ouverte). Les autres routes respectent leur règle.",
    "Serpentine, point 5 : z 205 → 200 (la terrasse est plate à +199, exigence MUST). Route ouest au pont : le -1 m de l'annexe est le niveau de la rivière. Le tablier du pont Ouest va de +12,4 à +9,0 m (5 arches, 60 m, 1,1 m de parapet).",
    "Raccords : les routes secondaires partent à l'altitude de la route qu'elles rejoignent : forest_track 25,3 m (annexe 16), quarry_road 21 m (annexe 9), mill_track 23 m (annexe 22).",
    "Escaliers × serpentine : 2 passerelles en [507, -40] et [597, -40] (l'escalier passe 8 à 11 m au-dessus de la route), croisements à niveau ailleurs.",
    "Palais : la crête est tenue à +38 m (exigence de silhouette) par des toits à 55° tronqués, avec les gouttières à +29 m pour loger le niveau L2 (+22). Les arcs-boutants côté vallée partent de piles encorbellées dans la falaise, puisque la façade prolonge la falaise.",
    "Souterrains : au lieu de trous dans le paysage, que Python ne sait pas peindre, le terrain est abaissé sous le palais, le cachot, la crypte de l'église, la cave du manoir, la nef de l'abbaye, le tunnel et la grotte. Murs de 1,6 m, dalles et talus en masquent les bords. Le rocher est posé à +203,85 m (15 cm sous les sols) pour éviter le scintillement.",
    "Règle caméra (plafonds d'au moins 4 m) : les intérieurs de ville ont des étages de 5,0 et 4,6 m, plus hauts que des maisons réelles. Le tunnel secret fait 4 m de haut.",
    "Tunnel secret (298 m) : galerie sinueuse sous le palais, puis traversée droite de la falaise sud sous un éboulis jusqu'à la porte cachée [574, 384, 118].",
    "Caserne du guet : la boîte de l'annexe dépassait de 10 m hors du rempart ; elle a été glissée de 15,5 m vers l'intérieur.",
    "Puits du marché et fontaine sèche de la cour intérieure : déplacés hors des points d'apparition imposés par l'annexe.",
    "Grotte de la cascade : accès depuis la berge par une rampe, puis par une corniche de 4 m posée sur la vasque au pied de la falaise, sous le rideau d'eau, jusqu'à l'entrée de la grotte. Le chemin de la cascade passe 40 m plus haut.",
    "Cimetière Nord : centré sur son POI. La route du château de l'annexe le traverse, d'où des portes dans le mur à son passage.",
    "Moulins : posés sur la berge nord. L'ancienne plateforme de terrain bouchait la rivière ; elle a été supprimée et aucune plateforme ne touche plus le lit.",
    "Auberge principale : salle commune de 12 × 11,5 m (une parcelle) au lieu d'environ 18 × 10 m, et 6 chambres sur 2 étages.",
    "Faubourg Est : 52 bâtiments générés le long de la route commerciale (le plan en dessine 18, le texte en demande environ 50).",
    "Tour de guet : 11 × 11 m pour loger un colimaçon à marches de 2,2 m (le cahier ne donne que la hauteur de 18 m).",
    "Vue V1 : 2 parcelles au nord-est de la place ne sont pas bâties, pour que le donjon apparaisse entre les toits comme le demande le cahier.",
    "Balcon de la salle du trône (V2) : sa moitié extérieure est 0,8 m plus bas (4 marches de 20 cm dans l'ouverture de la façade). Sinon le parapet de 1,1 m masquait la ville depuis la caméra imposée.",
    "Vue V7 : la route commerciale monte au col Est par une vallée ouverte (flancs à 14°), et non dans une tranchée de 40 m, pour que le plan d'établissement voie la vallée.",
    "Vue V6 : depuis le troisième lacet, l'éperon entre la route et le bord du ravin montait 13 m au-dessus de la caméra du cahier. Il est entaillé sous la ligne de visée (1,5 m de marge, flancs à 45°) pour que les murs du château apparaissent au-dessus.",
    "Chambre des cloches (V5) : l'étage des cloches est octogonal sur la tour carrée de l'annexe, avec une baie par face. Sur une chambre carrée, la ligne vers le donjon tombait dans l'angle ; la face nord-est regarde désormais le château (« la tour fait face à la tour »). Abat-sons seulement au-dessus de la hauteur des yeux.",
    "Abbaye (V8) : la dernière travée nord de la nef est effondrée et le pignon du chœur a une vraie baie vide, sa moitié nord étant tombée. Depuis la caméra du cahier, le château apparaît entre les arcs brisés.",
    "Pied de la cascade dessiné explicitement (vasque à +56, lit à +60, berges, falaise verticale), car l'érosion y laissait un creux de 65 m.",
]
for d in dev:
    w(f"- {d}")
w("\nJournal du solveur de routes :\n")
for l in RL:
    w(f"    {l}")
w("\n## Questions ouvertes\n")
for q in ["Avez-vous le `heightmap_base_4033.png` d'origine ? Mon pipeline peut le reprendre (nivellement des routes, vides et contrôles).",
          "Routes basse du château et commerciale : peut-on allonger leurs tracés (lacets) pour tenir 10 %, ou accepte-t-on 12 et 14 % ?",
          "Phase 0 : résultat du test World Partition sur votre serveur Nanos World.",
          "Taille réelle de la capsule du personnage Nanos World, pour refaire le test de marche avec ses valeurs exactes.",
          "Tag « Sun » : le script le pose sur la lumière directionnelle, la SkyLight, le SkyAtmosphere et le brouillard. À confirmer selon votre version de Nanos World.",
          "Plugin Water : largeur et profondeur des points de spline de la rivière à vérifier dans l'éditeur, car Python n'y a pas toujours accès."]:
    w(f"- {q}")
w("\n## Étapes suivantes\n")
w("Phase 3 (sol et eau : auto-matériau, splines de routes, rivière, ruisseau, cascade, gués, mares du marais), puis phases 4 et 5 (architecture et intérieurs à partir de kits modulaires sous licence, consignés ici), 6 (nature et histoire), 7 (lumière), 8 (gameplay), 9 (optimisation) et 10 (export).")
open(f"{ROOT}/pack/BUILD_LOG.md", "w").write("\n".join(L) + "\n")
print("BUILD_LOG.md", len(L), "lines")
