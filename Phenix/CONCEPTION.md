# Classe Phénix : conception

Ce document décrit ce que fait chaque capacité du mod « Classe Phénix » et ce qui diffère du
cahier des charges. Tout est généré par `outils/build.py` à partir de `outils/contenu.py`
(capacités et sorts) et `outils/progressions.py` (ce qu'on gagne à chaque niveau).

Tous les objets du mod portent le préfixe `PHX_` ; le mod ne dépend d'aucun autre mod.

## Classe

Socle : d8 (8 PV au niveau 1, puis 5 par niveau), lanceur complet au Charisme (sorts connus), sauvegardes Constitution et Charisme, armures légères et armes
courantes, 2 compétences, voie (sous-classe) au niveau 3, dons aux niveaux 4, 8 et 12.

**Sorts appris : feu et lumière uniquement**, y compris à la création du personnage. Tours de magie
(2 au niveau 1, +1 aux niveaux 4 et 10) parmi Trait de feu, Production de flamme, Flamme sacrée,
Lumière et Lumières dansantes. Sorts (2 au niveau 1, puis 1 par niveau jusqu'au 11, avec
remplacement possible) parmi :

| Niv. de sort | Sorts |
|---|---|
| 1 | Mains brûlantes, Éclair traçant, Représailles infernales, Châtiment brûlant, Faveur divine, Lueurs féeriques |
| 2 | Rayon ardent, Sphère de feu, Chauffer le métal, Lame de feu, Rayon de lune, Châtiment révélateur |
| 3 | Boule de feu, Esprits gardiens, Aura du croisé, Lumière du jour, Châtiment aveuglant |
| 4 | Mur de feu, Bouclier de feu, Gardien de la foi |
| 5 | Colonne de flamme |
| 6 | Rayon de soleil |

Liste tirée de bg3.wiki (sorts de classe à dégâts de feu ou radiants, plus les sorts de lumière),
dans `outils/contenu.py` (`TOURS_FEU_LUMIERE`, `SORTS_FEU_LUMIERE`).

| Niv. | Capacité | Réalisation |
|---|---|---|
| 1 | Flamme loyale | Les dégâts de feu que le Phénix inflige à un allié (ou à lui-même) sont rendus aussitôt en PV, et l'état En feu est retiré. Tous les sorts du Phénix ne visent de toute façon que les ennemis. |
| 1 | Flamme bienfaitrice (sort niv. 1) | 1d8 + Cha PV, puis 1d6 PV par tour pendant 3 tours, avec le visuel « En feu ». |
| 1 | Cendres ardentes | À terre : au bout de 2 tours, relevé avec 1/6 des PV max (si personne ne l'a relevé avant). |
| 1 | Plume ardente (tour) | 1d10 feu (2d10 au niv. 5, 3d10 au niv. 10). Au niv. 5 s'ajoute « Plume ardente (rebond) » : 2 cibles. |
| 2 | Braises | +1 par tour quand le Phénix inflige ou subit du feu ; max 3, 5 au niv. 9, +2 en Brasier. Attiser (+1d6 feu), Propager (explosion 2d6 à 3 m autour de la cible), Purifier (retire Empoisonné, Aveuglé, Effrayé, Charmé, Paralysé, maladies aux alliés à 9 m). Chacun : action bonus + 1 Braise. |
| 3 | Bond de flamme (sort niv. 2) | Téléportation 9 m, 2d6 feu aux ennemis à 3 m au départ et à l'arrivée. |
| 5 | Ignifugé | Immunité au feu et à l'état En feu. |
| 5 | Pluie de plumes, Larmes de phénix (sorts niv. 3) | Zone 6 m : 4d6 feu aux ennemis, 2d8 PV aux alliés. Soin 4d8 + Cha et retire poison, maladies, malédictions. |
| 6 / 11 | Bouclier de flammes | 1d8 feu à l'attaquant au corps à corps (2d8 au niv. 11). |
| 7 / 11 | Feu sacré | Ignore la résistance au feu ; au niv. 11 ignore aussi l'immunité. |
| 7 | Bûcher sacré (sort niv. 4) | Aura de 6 m autour du Phénix pendant 4 tours : 2d8 feu aux ennemis, 1d8 PV aux alliés. |
| 9 | Cœur de phénix | Chaque fois que du feu l'atteint (même le sien) : +3d8 PV. |
| 9 | Plume de renaissance (sort niv. 5) | L'allié qui tombe à 0 PV renaît avec la moitié de ses PV, gerbe 3d6 feu aux ennemis (une fois). |
| 10 | Renaissance du phénix + Renouveau | 1 fois par repos long, à 0 PV : renaît avec tous ses PV, explosion 6d6 feu aux ennemis à 6 m, puis +1d6 feu sur attaques et sorts pendant 2 tours. |
| 11 | Envol du phénix (sort niv. 6) | Invoque un élémentaire de feu. |
| 12 | Avatar du phénix | 1 fois par repos long, 5 tours : vol + aura 3 m (2d6 feu aux ennemis, 2d6 PV aux alliés). |

Voie (une seule, au niveau 3) : **Voie du Phénix éternel**, qui réunit les trois voies prévues par
le cahier des charges :

| Niv. | Brasier (dégâts) | Cendre (soins) | Serres (corps à corps) |
|---|---|---|---|
| 3 | +Charisme aux dégâts des sorts de feu, +2 Braises | Soins +niveau de Phénix, Plume de renaissance gratuite 1/repos long | Armures intermédiaires, boucliers, armes de guerre, Charge ardente |
| 5 | | | Attaque supplémentaire |
| 10 | Nova : 8d6 feu à 9 m, soigne 4d8 | La Renaissance relève les alliés à terre à 6 m | |

Écarts avec le cahier des charges, tous dus à l'absence de script :

- **Renaissance du phénix** se déclenche quand le Phénix tombe à 0 PV, pas après une « mort
  totale » (le jeu ne laisse pas réagir à la mort sans script). Limitée à 1 fois par repos long
  (le garde-fou proposé). Ensuite, Cendres ardentes prend le relais.
- **Flamme loyale** ne peut pas empêcher les dégâts de feu des sorts du jeu (Boule de feu…) : elle
  les rend aussitôt en PV. Les surfaces de feu créées par ces sorts restent dangereuses.
- **Propager** fait exploser le feu autour de la cible au lieu de viser une 2e cible précise.
- **Bûcher sacré** est une aura autour du Phénix plutôt qu'une zone fixe.
- **Envol du phénix** invoque un élémentaire de feu (pas de modèle de phénix dans le jeu) et
  n'explose pas à sa mort.
- **Feu sacré** au niveau 11 ignore l'immunité au lieu de la réduire en résistance.
- Voie du Brasier : « zones de feu élargies » remplacé par +Charisme aux dégâts des sorts de feu.

## À tester en priorité

Ces points reposent sur des mécanismes du jeu que je n'ai pas pu vérifier sans lancer le jeu.

1. La classe Phénix apparaît à la création, et sa voie au niveau 3.
2. Flamme bienfaitrice : la cible a l'air en feu mais gagne des PV à chaque tour.
3. Cendres ardentes : à terre, le Phénix se relève seul au bout de 2 tours.
4. Renaissance du phénix (niv. 10) et Plume de renaissance (niv. 9) : renaissance dans une
   explosion de feu, sans dégâts aux alliés.
5. Braises : gain en infligeant ou en subissant du feu ; Attiser, Propager et Purifier.
6. Flamme loyale : une Boule de feu qui touche un allié lui rend aussitôt ses PV.
7. Bûcher sacré et Avatar du phénix : les ennemis brûlent, les alliés sont soignés.

## Pistes pour plus tard

- Icônes propres à la classe et à ses voies.
- Traduction anglaise (le fichier anglais reprend le français pour l'instant).
- Avec le Script Extender (hors mod.io) : vraie renaissance après la mort, phénix invoqué qui
  explose à sa mort, zones de feu fixes au sol.
