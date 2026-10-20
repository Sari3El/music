# Classe Chronomancien : conception

Ce document décrit ce que fait chaque capacité du mod « Classe Chronomancien ». Tout est généré par
`outils/build.py` à partir de `outils/contenu.py` (capacités et sorts) et `outils/progressions.py`
(ce qu'on gagne à chaque niveau).

Tous les objets du mod portent le préfixe `CHR_` ; le mod ne dépend d'aucun autre mod.

## Classe

Socle : d8 (8 PV au niveau 1, puis 5 par niveau), lanceur complet à l'Intelligence, sorts à
préparer, sauvegardes Intelligence et Dextérité, armures légères et armes courantes, 2 compétences,
dons aux niveaux 4, 8, 12, 16 et 19. Pas de sous-classe : tout est dans la classe.

**Jusqu'au niveau 20** : les niveaux 13 à 20 nécessitent un mod qui débloque le niveau 20 (il fournit
l'expérience et les emplacements de sort 7 à 9).

**Sablier** : 2 charges au niveau 1, +1 aux niveaux 5, 9, 13 et 17 (6 au maximum), rechargées au repos
court ; +1 au début de chaque combat à partir du niveau 12.

### Sorts du jeu à préparer : espace, temps, entropie

| Niv. de sort | Sorts |
|---|---|
| Tours (3 au niv. 1, +1 aux niv. 4 et 10) | Main de mage, Coup au but, Protection contre les armes, Illusion mineure, Frisson osseux |
| 1 | Projectile magique, Bouclier, Chute de plume, Repli expéditif, Grande foulée, Saut amélioré |
| 2 | Foulée brumeuse, Flou, Immobilisation de personne, Image miroir, Rayon affaiblissant, Ténèbres |
| 3 | Hâte, Lenteur, Clignotement, Contresort, Forme gazeuse |
| 4 | Porte dimensionnelle, Bannissement, Sphère résiliente d'Otiluke, Flétrissement |
| 5 | Immobilisation de monstre, Télékinésie |
| 6 | Portail arcanique, Globe d'invulnérabilité, Désintégration, Cercle de mort |

### Capacités et sorts propres (toujours préparés)

| Niv. | Capacité | Effet |
|---|---|---|
| 1 | Prescience | +5 à l'initiative, jamais surpris. |
| 1 | Résonance temporelle | Les tours de magie infligent en plus le modificateur d'Intelligence en force (1 fois par attaque). |
| 1 | Accélération | 1 Sablier, 1 fois par tour, sans action : +1 action ce tour (base : Sursaut d'action). |
| 1 | Rembobinage (réaction) | 1 Sablier : un coup ennemi sur toi ou un allié à 9 m n'inflige aucun dégât. |
| 1 | Éclat temporel (tour) | 1d10 force (jusqu'à 4d10) + mouvement réduit de moitié. |
| 1 | Rayon d'entropie (sort niv. 1) | 3d10 nécrotique (jusqu'à 10d10) + ralenti 2 tours. |
| 2 | Ralentir | Action bonus, 1 Sablier : sauvegarde de Sagesse ou ralenti 2 tours (mouvement /2, -2 CA, ni action bonus ni réaction). |
| 2 / 6 / 10 / 14 | Mémoire du temps | Au repos court, récupère un emplacement de niv. 1, puis aussi 2, 3 et 4. |
| 3 | Faille | Action bonus, 1 Sablier : téléportation à 18 m, ou échange de place avec une créature. |
| 3 | Fracture spatiale (sort niv. 2) | 3 m : 4d8 force (jusqu'à 11d8) + à terre. |
| 5 | Effondrement gravitationnel (sort niv. 3) | 6 m : attire vers le centre, 6d8 force (jusqu'à 12d8) + à terre. |
| 6 | Écho temporel | 1 fois par tour, un sort qui blesse frappe à nouveau au tour suivant : 2d8 force (jusqu'à 5d8). |
| 7 | Vieillissement accéléré (sort niv. 4) | 8d8 nécrotique (jusqu'à 14d8) + désavantage aux attaques et -2 CA, 3 tours. |
| 9 | Prison temporelle | 2 Sabliers, 1 fois par repos court : cible figée 2 tours (rien à faire, immunisée aux dégâts). |
| 9 | Onde chronique (sort niv. 5) | Cône 9 m : 10d8 force (jusqu'à 15d8) + ralenti. |
| 10 | Double temporel | 2 réactions par round. |
| 10 | Maître de l'entropie | Force et nécrotique ignorent la résistance. |
| 11 / 19 | Arrêt du temps | 1 fois par repos long (repos court au niv. 19) : tu récupères action, action bonus, réaction et mouvement, donc un tour complet de plus. |
| 11 | Rayon du néant (sort niv. 6) | 12d10 force (jusqu'à 16d10), évité par une sauvegarde de Dextérité. |
| 12 | Sablier inépuisable | +1 Sablier au début de chaque combat. |
| 13 | Singularité (sort niv. 7) | 9 m : aspire vers le centre, 14d8 force (16d8 au niv. 20) + à terre. |
| 14 | Réécrire l'instant (réaction) | 1 Sablier : une sauvegarde ratée par un allié devient un 20, une sauvegarde réussie par un ennemi devient un 1. |
| 14 / 18 | Réalité brisée | Critique sur 19-20, puis 18-20. |
| 15 | Altération (sort niv. 8) | 6 m : 8d8 psychique + ennemis vulnérables à tous les dégâts, 3 tours. |
| 17 | Effacement (sort niv. 9) | Une créature à 150 PV ou moins est effacée ; sinon 16d10 force. |
| 18 | Ancrage temporel | Immunité à Ralenti, Paralysé, Étourdi, Entravé, Banni, À terre. |
| 20 | Paradoxe | 1 fois par repos long : toi et tes alliés à 18 m retrouvez tous vos PV, emplacements et capacités. |

### Équipement de départ

- **Sceptre du Continuum** (légendaire, créé pour le mod, apparence de Markoheshkir) : +3 aux attaques,
  dégâts, jets d'attaque des sorts et DD des sorts ; +2d6 force par coup ; +2 Sabliers ; +3 à
  l'initiative ; 1 fois par tour, +3d6 force sur un sort qui blesse ; au début de chaque combat, un
  emplacement de niveau 3 récupéré ; sort **Stase** (1 fois par repos court : 4d8 force et ralenti aux
  ennemis à 9 m, sauvegarde de Sagesse pour moitié).
- **Tenue de l'ensorceleur** (robe) et bottes de cuir.
- **Teinture noir et blanc arlequin** dans l'inventaire : le jeu n'a pas de teinture blanche pure, et la
  tenue ne peut être livrée déjà teinte qu'avec l'identifiant de la couleur, introuvable sans les fichiers
  du jeu. Combine la teinture avec la robe pour l'appliquer.

### Ce qui n'est pas faisable sans script

- Un vrai retour en arrière (remettre les positions, annuler les actions d'un tour) : remplacé par
  Rembobinage, Réécrire l'instant et Paradoxe.
- Un clone de soi venu du futur, ou copier un sort ennemi.

## À tester en priorité

Ces points reposent sur des mécanismes du jeu que je n'ai pas pu vérifier sans lancer le jeu.

1. La classe Chronomancien apparaît à la création, avec ses tours de magie et ses sorts à préparer.
2. Accélération donne bien une action en plus.
3. Rembobinage : la réaction se propose quand un ennemi frappe un allié proche, et il ne subit rien.
4. Éclat temporel (basé sur Décharge occulte) ne tire qu'un seul rayon.
5. Faille : téléportation au sol et échange de place avec une créature.
6. Effondrement gravitationnel et Singularité attirent bien les créatures vers le centre.
7. Arrêt du temps rend bien un tour complet.
8. Réécrire l'instant se propose sur les jets de sauvegarde.
9. Effacement efface une créature sous 150 PV.
10. Sceptre du Continuum : il a bien l'apparence de Markoheshkir, son nom, ses bonus et le sort Stase.

## Pistes pour plus tard

- Icônes propres à la classe.
- Traduction anglaise (le fichier anglais reprend le français pour l'instant).
