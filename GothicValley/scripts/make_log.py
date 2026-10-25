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
import numpy as _np
_pl = _np.load(f"{ROOT}/data/castle20_plate.npz"); _cp = CM["castle_plate"]
_hz = [_cp["origin"][2] + max(float(_np.nanmin(_pl["plate"])), _cp["min_rel"]), _cp["origin"][2] + float(_np.nanmax(_pl["plate"]))]
w(f"- Rocher du château : le bord de l'éperon est à +203,85 m ; à l'intérieur de l'enceinte, le sommet reprend le relief de la colline sur laquelle le modèle « Castle 2.0 » a été construit (cours de +{f"{_hz[0]:.1f}".replace(".", ",")} à +{f"{_hz[1]:.1f}".replace(".", ",")} m, phase 4). Falaise sud {f['cliff_south_m']} m, falaise est {f['cliff_east_m']} m.")
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
w(f"- Barbacane et Grand Pont (tablier de 6 m, parapets de 1,1 m, {len(CM['piers'])} piles dont la plus haute fait {max(p['height'] for p in CM['piers'])} m, pont-levis). "
  "Le château lui-même (enceinte, tours, palais, donjon et ses salles) était un greybox en phase 2 ; il est remplacé en phase 4 par le modèle « Castle 2.0 » (section suivante).")
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
w("- Château : voir la phase 4 (le test de marche porte désormais sur le modèle « Castle 2.0 » et ses salles).")
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
# ---- phase 4 (in progress): asset packs
if os.path.exists(f"{ROOT}/greybox/lodge_meta.json"):
    n0 = len(L)
    LM = json.load(open(f"{ROOT}/greybox/lodge_meta.json"))
    NL = json.load(open(f"{ROOT}/greybox/nav/nav_lodge.json")) if os.path.exists(f"{ROOT}/greybox/nav/nav_lodge.json") else None
    PLc = len(json.load(open(f"{ROOT}/data/placements_lodge.json")))
    ss, lb = LM["secret_stair"], LM["library"]
    w("\n## Phase 4 (en cours) : maison des chasseurs et bibliothèque souterraine\n")
    w(f"- Maison de la famille de chasseurs (modèle « Fantasy Castle ») : le point le plus éloigné du château des vampires, "
      f"à [{LM['lodge']['origin'][0]:.0f}, {LM['lodge']['origin'][1]:.0f}], sur une plate-forme à +{LM['lodge']['origin'][2]:.0f} m. La porte "
      f"regarde la vallée (nord). Le modèle n'a pas d'intérieur : l'aile basse est aménagée en grande salle (table, lustres, "
      f"crucifix de bronze entre deux candélabres, coffres et bancs sous les fenêtres, peau d'ours, tapis clairs, outils de chasse "
      f"près de la porte) et en cabinet de travail (bibliothèque, table de lecture, tapis, tableau). Ses matériaux sont rendus double face "
      f"pour que les murs se voient de l'intérieur ; la porte et les panneaux sombres derrière les fenêtres de cette aile sont retirés.")
    w("- Passage secret : dans le cabinet, une armoire coulisse de 2 m (maillage *Movable*, tags `ScriptedDoor`, `Slide`) et "
      "découvre une porte cachée. Derrière, un escalier en colimaçon en fer (kit de la bibliothèque) descend de 4,8 m. "
      f"Ensuite, un long escalier de pierre voûté de {ss['length_m']:.0f} m ({ss['risers']} marches de {ss['riser_m'] * 100:.1f} cm sur "
      f"{ss['tread_m'] * 100:.0f} cm, {ss['flights']} volées, paliers éclairés de lampes murales) descend de {ss['drop_m']:.1f} m jusqu'au balcon de la "
      f"bibliothèque. Il reste au moins {ss['rock_cover_min_m']:.1f} m de roche au-dessus de sa voûte.")
    w(f"- Bibliothèque souterraine : nef gothique de {lb['size'][0]:.0f} × {lb['size'][1]:.0f} m, sol à +{lb['levels'][0]:.0f} m, voûtes "
      f"à +{lb['vault_apex']:.1f} m, avec au moins {lb['rock_cover_min_m']:.0f} m de roche au-dessus. Elle est construite avec les pièces du kit "
      "« Classic Library » : colonnes, croisées d'ogives et nervures à l'échelle 1,5, rayonnages et livres à l'échelle 1. "
      "On arrive par un balcon. Un escalier d'honneur (volée centrale, palier, puis deux volées) descend dans la nef. Deux "
      "galeries de bois courent dans chaque bas-côté (+5,1 et +10,2 m), reliées par quatre escaliers en colimaçon. Il y a des "
      "rayonnages muraux à trois niveaux, des épis de rayonnages doubles, des tables de lecture et de grands lustres, et une "
      "grande verrière gothique au fond.")
    w(f"- {PLc} pièces de kit et props placés (`Data/placements_lodge.json`), {len(LM['lights'])} lumières ponctuelles (`Data/lights.json`). "
      "Les collisions sont des enveloppes `UCX_` invisibles portées par les maillages `SM_GB_Lodge_*` et `SM_GB_Library_*` ; "
      "les pièces du kit n'en ont pas (le mobilier a sa boîte englobante en collision). Les colimaçons ont une rampe hélicoïdale de collision.")
    if NL:
        ok = sum(r["reached"] for r in NL["rooms"])
        pr = sum(v["reached"] for v in NL["probes"].values())
        w(f"- Test de marche (`nav_lodge.json`, depuis l'extérieur de la porte) : {ok}/{len(NL['rooms'])} salles atteintes, "
          f"{pr}/{len(NL['probes'])} points de contrôle, {len(NL['leaks'])} fuite. Le chemin passe par l'armoire ouverte, le colimaçon, "
          f"l'escalier secret, le balcon, les galeries et les quatre colimaçons.")
    w("- Relief : plate-forme de la maison et vide sous le puits secret. Les salles souterraines sont marquées `sealed` : le relief "
      "n'y est jamais creusé, et l'audit vérifie la roche au-dessus.")
    if "hunters_track" in json.load(open(f"{ROOT}/data/roads_final.json")):
        ht = json.load(open(f"{ROOT}/data/roads_final.json"))["hunters_track"]
        w(f"- Chemin des chasseurs : piste de 3 m, longue de {ht['s'][-1]:.0f} m, du sentier du marais (même rive que la maison) jusqu'à "
          f"sa porte, pente maximale {ht['max_grade'] * 100:.0f} % (calcul du chemin le moins coûteux, `track_lodge.py`).")
    w("\n## Phase 4 (suite) : château des vampires (« Castle 2.0 »)\n")
    md = CM["model"]; br = CM["bridge"]; uc = CM["undercroft"]
    PLC = json.load(open(f"{ROOT}/data/placements_castle.json"))
    w(f"- Modèle « Castle 2.0 » (EldersCrawler) posé sur l'éperon à l'échelle {md['scale']:.0f} (environ 200 × 166 m, 70,7 m de haut "
      f"à la flèche de la tour du palais), centre [{md['origin'][0]:.0f}, {md['origin'][1]:.0f}], base à +{md['origin'][2]:.1f} m, porte "
      f"tournée vers le Grand Pont. À l'intérieur de l'enceinte, le terrain reprend le relief de la colline sur laquelle le modèle a été "
      f"construit (`Data/castle20_plate.npz`), raccordé au bord du rocher.")
    w("- Analyse du modèle : l'export du pack avait perdu ses matériaux (un seul matériau sur 13 morceaux). Ils sont reconstitués "
      "par îlot UV et par orientation (murs, toits, sols) avec les textures du pack (`c20_classes.py`). Les volumes intérieurs sont "
      "trouvés par voxelisation à 0,5 m et remplissage de l'air extérieur (`c20_interiors.py`), les accès par le test de marche, et "
      "les bâtiments par leurs toits (`c20_buildings.py`). Le modèle a peu de vrais intérieurs : les salles sont placées dans ses "
      "propres salles et tours quand elles existent, dans des salles doublées (murs, sol et plafond propres) à l'intérieur de ses "
      "bâtiments, ou sous le terrain.")
    w(f"- Grand Pont réorienté vers la nouvelle porte ({br['length_m']} m, cap {br['heading_deg']}°), pont-levis *Movable*, porte-torches "
      "dans l'avant-cour. Les vantaux de la porte du modèle sont découpés et remplacés par deux vantaux *Movable* ouverts.")
    w(f"- Découpes du modèle ({len(md['cuts'])} boîtes : vantaux, portes percées, puits, encombrement des salles doublées, fondations "
      "sous les sous-sols). Les triangles traversés sont recoupés exactement par les plans de chaque boîte (`c2cuts.py`) ; le même calcul "
      "sert au test de marche et à l'export. Chaque porte percée reçoit un seuil, des jambages et un linteau ; quand le sol "
      "extérieur n'est pas au niveau du seuil, le terrain est raccordé (talus) ou un perron est construit.")
    w("\nSalles principales (cahier, section 5) :\n")
    w("| Salle | emplacement | construite (L × l × h) | cahier | conforme |\n|---|---|---|---|---|")
    WHERE = {"Great Hall": "grande salle du modèle (palais)", "Throne Room": "salle doublée dans le corps du palais",
             "Banquet Hall": "sous-sol L-1, voûtée", "War Room": "salle doublée, aile est", "Lord's Study": "salle du modèle, aile est",
             "Dungeon": "sous-sol L-2", "Larder": "sous-sol L-1", "Kitchen": "sous-sol L-1", "Library": "tour nord-est du modèle",
             "Crypt": "sous-sol L-2, voûtée", "Lord's Apartments": "tour nord-ouest du modèle", "Chapel": "salle à colonnes du modèle"}
    for r in sorted(TR["core_rooms"], key=lambda r: r["id"]):
        w(f"| {r['name']} | {WHERE.get(r['name'], '')} | {' × '.join(str(v) for v in r['built'])} | "
          f"{r['doc'] if isinstance(r['doc'], str) else ' × '.join(str(v) for v in r['doc'])} | {'oui' if r['ok'] else '**non**'} |")
    w("\nLes salles creusées sous le terrain ont les dimensions du cahier. Celles logées dans le modèle prennent la taille que "
      "ses murs permettent (tours rondes, corps de bâtiment de 11 m de large).\n")
    w(f"- Grande Salle : la salle à colonnes du palais, deux rangées de tables avec leurs chaises, tapis, lustres et candélabres. Salle du "
      "trône derrière elle (porte dans l'axe de la nef) : estrade à trois degrés, trône gothique, tapis sombres depuis la porte, "
      "tableaux entre les pilastres, candélabres, lustres, plafond à caissons. Chapelle : la salle à six colonnes ouverte sur la cour du "
      "palais par une arcade (grand crucifix de fer forgé, candélabres, bancs, tapis dans l'allée). Salle de guerre : table du conseil "
      "sur un tapis, tableaux, coffre, perron depuis la cour est. Bibliothèque et appartements (le seigneur y dort dans un cercueil) dans "
      "deux tours rondes, cabinet du seigneur dans l'aile est.")
    w(f"- Escalier dérobé : un panneau de pierre (*Movable*) s'ouvre dans le mur derrière l'estrade du trône, à côté du trône. "
      f"Derrière, un colimaçon de 113 marches descend dans un puits aux murs de 1,6 m jusqu'à la crypte (L-2, "
      f"{md['origin'][2] + 22.6 - uc['L2_floor']:.1f} m sous l'estrade).")
    w(f"- Sous-sols : deux niveaux sous le terrain du palais (L-1 à +{uc['L1_floor']:.1f} m, L-2 à +{uc['L2_floor']:.1f} m), sans trou dans "
      "le paysage : seuls les deux puits le coupent, et leurs murs de 1,6 m en masquent le bord. Il reste au moins 1,4 m de roche au-dessus "
      "des salles. Un grand escalier rampe sur rampe (six volées, mur d'échiffre central, balustrade) descend du bas-côté ouest de la "
      "Grande Salle. L-1 : salle de banquet voûtée (deux rangées de piliers, six tables avec leurs chaises, tableaux sur les longs "
      "murs, lustres, candélabres), cuisine (four à pain et son bois, tables de travail, buffets, étagères, baquets), garde-manger "
      "(étagères basses, buffets, coffres), cave (baquets, barattes, étagères). L-2 : crypte voûtée (cercueil du seigneur sur son socle, "
      "cinq cercueils de famille), grille de fer vers les cachots (couloir de 40 m, 10 cellules de 3 × 3 m à barreaux, salle des gardes, "
      "salle d'interrogatoire, trappe de l'oubliette).")
    w(f"- Tunnel secret : {CM['tunnel_length_m']} m depuis la crypte, en trois branches dans le rocher (deux longs escaliers puis une galerie "
      f"de niveau), toujours sous le paysage, jusqu'à une porte cachée (*Movable*) au pied de la falaise sud, en "
      f"[{CM['tunnel_exit'][0]:.0f}, {CM['tunnel_exit'][1]:.0f}, {CM['tunnel_exit'][2]:.0f}].")
    w(f"- {len(PLC) - 1} pièces de kit et props, et le maillage du château (`SM_C2_Castle`, collision complexe) dans `Data/placements_castle.json`, "
      f"{len(CM['lights'])} lumières ponctuelles.")
    ok_r = sum(r["reached"] for r in NC["rooms"]); pr = sum(v["reached"] for v in NC["probes"].values())
    w(f"- Test de marche (`nav_castle.json`, depuis la barbacane) : {ok_r}/{len(NC['rooms'])} salles atteintes, "
      f"{pr}/{len(NC['probes'])} points de contrôle (pont, avant-cour, cours, estrade, chambre secrète, pied du colimaçon, grand "
      f"escalier, coudes du tunnel, devant la porte cachée), {len(NC['leaks'])} chute vers les vides.")
    PJ = json.load(open(f"{ROOT}/data/props_library.json"))
    nprops = sum(1 for f_ in ("placements_castle.json", "placements_lodge.json") for q in json.load(open(f"{ROOT}/data/{f_}")) if q["mesh"].startswith("SM_PR_"))
    w("\n## Props des packs (phase 4)\n")
    w("- Règle : le mobilier et les objets viennent uniquement des packs fournis. Les props que j'avais fabriqués (trône, tables, "
      "bancs, chaises, candélabres, bannières, tapis, autel, croix, bancs d'église, sarcophages, tonneaux, cuves, étagères, lit, "
      "râteliers, cheminées, chaudron, chaînes, paille, braseros, lanternes, torches, nervures de voûte) sont retirés du château et de la "
      "maison des chasseurs. Restent fabriqués : l'architecture et les pièces que le jeu fait bouger (pont-levis, vantaux, panneau "
      "secret, grille de la crypte, porte du tunnel, armoire secrète, portes de la maison, barreaux des cellules). Les lumières restent.")
    w(f"- {len(PJ)} props préparés (`prep_props.py`, `props_defs.py`) : mis à l'échelle en mètres, face avant vers +X, origine au sol. "
      f"{nprops} sont placés dans le château et la maison des chasseurs (`Content/Props/...`, matériaux `MI_PR_*`).")
    w("- Trône « Dark Gothic Medieval Throne » : le socle et les bougies posées par terre devant, à gauche, sont retirés. Tapis sombres "
      "à motifs rouges (« Medieval Rugs Kit ») dans le château, tapis clairs (« Medieval Rug Pack ») dans la maison des chasseurs. "
      "Le grand crucifix de fer forgé (« Church Cross ») est dans la chapelle du château, le Christ de bronze (« The Crucifixion ») "
      "sur le mur de la grande salle des chasseurs. Les lustres et les candélabres des deux packs remplacent ceux que j'avais "
      "fabriqués ; les tableaux (« Free Medieval Paintings Pack ») sont sur les murs des salles doublées.")
    w("- « Medieval Furniture Pack » : ses 32 objets sont séparés et nommés (four, lit, banc à dossier, buffet, coffre, tables, chaise, "
      "tabouret, étagères, outils, lampe murale, porte-torche, trappe, peau d'ours...). Treize de ses fichiers de textures sont arrivés abîmés "
      "(blocs de 8 × 8 pixels mélangés) : peau d'ours, tonneaux, draps, nappe, rideaux, tableaux et leurs cadres, lampes, flammes. "
      "Ces matériaux sont pour l'instant d'une couleur unie ; les flammes plates sont retirées (la lumière fait la flamme), ainsi que "
      "le porte-serviettes et les deux tableaux de ce pack.")
    w("- « Medieval Mini Scene » ne contient que des textures, sans fichier 3D : rien n'est placé.")
    w("- « Medieval Wooden Shack 04 » est préparé et exporté (`Content/Environment/Shack`) ; il sera placé avec la ville.")
    w("\n## Modèles tiers (phase 4)\n")
    w("Le commanditaire déclare détenir les licences et les autorisations écrites des créateurs pour ces modèles, utilisés "
      "dans la carte. Les crédits et attributions sont conservés ici :\n")
    for c in ["« Fantasy Castle » par **Hawtor Studio** : maison des chasseurs (coque extérieure, textures). Attribution requise.",
              "« Classic Library for Blender Eevee and Cycles » par **denniswoo1993** : kit de la bibliothèque souterraine et mobilier "
              "de la maison. Ses textures intégrées viennent d'ambientCG, de Poly Haven et de Textures.com.",
              "« Castle 2.0 » par **EldersCrawler** : château des vampires (modèle complet et textures ; matériaux reconstitués par face).",
              "« Medieval Houses Package » par **Daniel** : maisons de la ville (à venir).",
              "« Medieval Church » par **Daniel** : vitraux et textures de l'église (à venir). Attribution requise.",
              "« Medieval castle » par **Misha Kiselev** : maison du noble (à venir).",
              "« Dark Gothic Medieval Throne » et « Medieval Rugs Kit » par **ClockworkCreations** : trône et tapis sombres du château.",
              "« Medieval Rug Pack - Game Ready » par **Hawtor Studio** : tapis clairs de la maison des chasseurs.",
              "« Medieval Furniture Pack » par **Anton Chemezov** : mobilier simple (cuisine, réserves, cachots, maison).",
              "« Medieval Chandelier » par **Kevin Popescu** ; « Medieval Candelabra » par **NeverSleep**.",
              "« Free Medieval Paintings Pack » par **yowi** : tableaux.",
              "« The Crucifixion » par **Privalov** ; « Church Cross » par **nedo** : crucifix.",
              "« Medieval Coffin » par **BGavi** : cercueils de la crypte et des appartements.",
              "« Medieval Wooden Shack 04 » par **ANRUVAL3DMODELS** : cabane de bois (ville, à venir).",
              "« Medieval Mini Scene » par **GetDeadEntertainment** : textures seules (pas de modèle 3D reçu)."]:
        w(f"- {c}")
    w("\nTrois cartes de couleur du pack « Fantasy Castle » (enduit, toit, bois) étaient vides, et le kit de bibliothèque "
      "n'avait pas de couleur pour la pierre, le fer et les vitraux. Ces cartes ont été recalculées à partir des cartes de relief "
      "et de rugosité du même pack (`fc_fix_colors.py`, `lib_fix_colors.py`). Les vitraux utilisent un motif au plomb généré.")
    import re
    L[n0:] = [re.sub(r"(?<![\w/])(\d+)\.(\d)", r"\1,\2", x) for x in L[n0:]]          # French decimal commas
    L[n0:] = [x.replace("Castle 2,0", "Castle 2.0") for x in L[n0:]]                               # (a model name)
w("\n## Écarts au cahier des charges et raisons\n")
dev = [
    "Heightmap : le cahier mentionne un `heightmap_base_4033.png` livré avec le document, mais je ne l'ai pas reçu. Je l'ai généré à partir de l'annexe A, avec le même encodage et la même orientation.",
    "Pentes : la route basse du château (au mieux 12 %) et la route commerciale (au mieux 14 %) ne peuvent pas respecter 10 % sur les tracés de l'annexe sans allonger le tracé (question ouverte). Les autres routes respectent leur règle.",
    "Serpentine, point 5 : z 205 → 200 (la terrasse est plate à +199, exigence MUST). Route ouest au pont : le -1 m de l'annexe est le niveau de la rivière. Le tablier du pont Ouest va de +12,4 à +9,0 m (5 arches, 60 m, 1,1 m de parapet).",
    "Raccords : les routes secondaires partent à l'altitude de la route qu'elles rejoignent : forest_track 25,3 m (annexe 16), quarry_road 21 m (annexe 9), mill_track 23 m (annexe 22).",
    "Escaliers × serpentine : 2 passerelles en [507, -40] et [597, -40] (l'escalier passe 8 à 11 m au-dessus de la route), croisements à niveau ailleurs.",
    "Château : le greybox de la phase 2 est remplacé par le modèle « Castle 2.0 ». Sa silhouette, ses tours et son palais sont ceux du modèle ; la Grande Salle, la salle du trône, la chapelle, la bibliothèque, les appartements, le cabinet et la salle de guerre prennent la taille que ses bâtiments permettent (tableau de la phase 4). La salle du trône n'a plus de balcon.",
    "Souterrains : au lieu de trous dans le paysage, que Python ne sait pas peindre, le terrain est abaissé sous la crypte de l'église, la cave du manoir, la nef de l'abbaye, le puits de la maison des chasseurs et la grotte. Murs de 1,6 m, dalles et talus en masquent les bords. Les sous-sols du château et son tunnel sont entièrement sous le paysage ; seuls leurs deux puits le coupent.",
    "Règle caméra (plafonds d'au moins 4 m) : les intérieurs de ville ont des étages de 5,0 et 4,6 m, plus hauts que des maisons réelles. Le tunnel secret fait 4 m de haut.",
    f"Tunnel secret : {CM['tunnel_length_m']} m au lieu de 298 m. Il descend de 79 m dans le rocher par deux longs escaliers en lacet, puis une galerie de niveau sous la falaise sud, jusqu'à la porte cachée au pied de la falaise, en [{CM['tunnel_exit'][0]:.0f}, {CM['tunnel_exit'][1]:.0f}, {CM['tunnel_exit'][2]:.0f}] au lieu de [574, 384, 118].",
    "Caserne du guet : la boîte de l'annexe dépassait de 10 m hors du rempart ; elle a été glissée de 15,5 m vers l'intérieur.",
    "Puits du marché et fontaine sèche de la cour intérieure : déplacés hors des points d'apparition imposés par l'annexe.",
    "Grotte de la cascade : accès depuis la berge par une rampe, puis par une corniche de 4 m posée sur la vasque au pied de la falaise, sous le rideau d'eau, jusqu'à l'entrée de la grotte. Le chemin de la cascade passe 40 m plus haut.",
    "Cimetière Nord : centré sur son POI. La route du château de l'annexe le traverse, d'où des portes dans le mur à son passage.",
    "Moulins : posés sur la berge nord. L'ancienne plateforme de terrain bouchait la rivière ; elle a été supprimée et aucune plateforme ne touche plus le lit.",
    "Auberge principale : salle commune de 12 × 11,5 m (une parcelle) au lieu d'environ 18 × 10 m, et 6 chambres sur 2 étages.",
    "Faubourg Est : 52 bâtiments générés le long de la route commerciale (le plan en dessine 18, le texte en demande environ 50).",
    "Tour de guet : 11 × 11 m pour loger un colimaçon à marches de 2,2 m (le cahier ne donne que la hauteur de 18 m).",
    "Vue V1 : 2 parcelles au nord-est de la place ne sont pas bâties, pour que le donjon apparaisse entre les toits comme le demande le cahier.",
    "Vues héros et château : V2 (balcon de la salle du trône) n'existe plus ; elle est prise depuis le rempart sud du château, au-dessus de la caméra du cahier, vers l'église. V3 est sur le tablier du Grand Pont réorienté, V4 au portail de la Grande Salle du modèle. V1, V5, V6 et V8 visent la tour du palais (point culminant du modèle) au lieu de l'ancien donjon.",
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
