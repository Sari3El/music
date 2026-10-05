# Conception — Divinités de l'Ordre et du Chaos (version 1)

Ce document décrit ce que le mod fait réellement en jeu, capacité par capacité, et signale chaque
écart avec le cahier des charges. Les valeurs chiffrées sont indicatives et seront ajustées après
les tests.

**Principe technique.** Le mod n'utilise que les fichiers de données du jeu, sans Script Extender.
C'est la condition pour pouvoir le publier dans le gestionnaire de mods du jeu (mod.io). Les sorts
exclusifs reprennent un sort du jeu de base (animation, sons, effets visuels) et en changent les
dégâts et les effets.

**Paliers.** Les sorts marqués « augmente aux paliers » gagnent en puissance aux niveaux 5, 9 et 12
du personnage.

---

## Race : Divinité

| Niv. | Capacité | Ce que fait le mod |
|---|---|---|
| 1 | Vitesse | Déplacement de 9 m, quelle que soit la forme. |
| 1 | Vue divine | Vision dans le noir 24 m. |
| 1 | Volonté divine | Avantage aux sauvegardes contre Charmé et Effrayé ; immunité au sommeil magique. |
| 1 | Étincelle immortelle | Une fois par repos long, tombe à 1 PV au lieu de 0 (même mécanique qu'Endurance implacable). |
| 1 | Présence | Thaumaturgie + maîtrise de Religion et d'Intimidation. |
| 1 | Caractéristiques | Un second bonus +2/+1 au choix, qui s'ajoute à celui de la classe (+4/+2 au total). |
| 3 | Injonction divine | Le sort Injonction (5 ordres), une fois par repos long, sans emplacement. |
| 5 | Forme divine | Action bonus, une fois par repos long, 3 tours : vol + 1d6 dégâts de force aux attaques (armes et mains nues). |

- **Apparence :** le jeu choisit les visages et coiffures selon la race. Il y a donc **11 races
  Divinité**, une par peuple jouable (Divinité humaine, elfe, drow, demi-elfe, naine, halfeline,
  gnome, tieffeline, githyanki, drakéide, demi-orque). Chacune copie la race du jeu : couleurs,
  visages, coiffures, cornes, corps, et les **mêmes sous-races** (haut-elfe et elfe des bois,
  10 couleurs de drakéide, duergar…), qui portent le nom du jeu. Les pouvoirs divins sont les mêmes
  pour toutes ; les traits raciaux du peuple imité ne sont pas accordés. Données tirées des tables du
  jeu par `tools/extraire_donnees_jeu.py`.
- **Écart :** les icônes des formes sont vides (icônes de sous-race à créer en V2).
- **Écart :** les yeux lumineux, les marques divines et le halo ou l'aura sombre de la Forme divine
  ne sont pas encore faits. Ils demandent des ressources visuelles à créer dans le Toolkit (V2).
- **Écart :** les sous-races du cahier des charges (Céleste, Infernal, Astral, Élémentaire) sont
  reportées en V2 : en V1, les sous-races servent à choisir l'apparence.
- **Hors périmètre V1 :** la quête liée à la Couronne de Karsus (nouveaux dialogues). Le lore passe
  par la description de la race.

## Socle commun des deux classes

- PV : 10 au niveau 1, puis 6 par niveau (d10).
- Lanceur de sorts complet : emplacements de sort de magicien ou de clerc, niveaux de sort 1 à 6.
- Domaine (sous-classe) choisi au niveau 1 ; dons aux niveaux 4, 8 et 12.
- Multiclassage possible.
- Équipement de départ : masse, bouclier et cotte d'écailles (Ordre) ; dague, arbalète légère et
  armure de cuir (Chaos).

|  | Divinité de l'Ordre | Divinité du Chaos |
|---|---|---|
| Incantation | Sagesse, sorts **préparés** | Charisme, sorts **connus** |
| Sauvegardes | Sagesse, Constitution | Charisme, Dextérité |
| Armures | Légères, intermédiaires, boucliers | Légères |
| Armes | Courantes | Courantes + rapières, épées courtes, cimeterres (armes de finesse de guerre) |
| Sorts du jeu | Listes du clerc (niv. 1 à 6) + du paladin (niv. 1 et 2) | Liste de l'ensorceleur + 1 tour de magie d'occultiste |
| Tours de magie | 3 (+1 aux niv. 4 et 10) | 4 d'ensorceleur + 1 d'occultiste (+1 aux niv. 4 et 10) |

**Écart (Chaos) :** les sorts d'occultiste de niveau 1 et plus ne sont pas inclus, car le jeu ne
fournit pas de liste réutilisable pour eux. Seuls les tours de magie d'occultiste sont proposés.
On pourra ajouter des sorts d'occultiste un par un en V2.

### Progression

| Niv. | Divinité de l'Ordre | Divinité du Chaos |
|---|---|---|
| 1 | **Loi absolue** : vos jets de d20 ne donnent jamais moins de 5 | **Chaos primordial** : critique sur 19-20 ; 1 chance sur 20 de déclencher un Déferlement à chaque sort à emplacement ; un 1 naturel à une attaque en déclenche un |
| 2 | **Décrets** (2 charges, repos court) : Protéger, Purifier, Lier | **Entropie** (max 3) : Pas chaotique, Défaire, Détoner |
| 6 | Loi absolue 8 ; **Aura d'Ordre** 3 m ; 3 Décrets | Critique 18-20 ; **Aura de Chaos** 3 m ; Entropie max 4 |
| 7 | **Inébranlable** : impossible à renverser ou à repousser | **Indomptable** : immunité à Paralysé et à Entravé |
| 10 | Aura 9 m ; 4 Décrets | Aura 9 m ; Entropie max 5 |
| 11 | Loi absolue 10 (aura comprise) | Critique 17-20 |
| 12 | **Ordre parfait** | **Tempête primordiale** |

### Ressources

- **Décrets** (Ordre, repos court) :
  - Protéger : réaction, divise par deux les dégâts subis par un allié à 9 m.
  - Purifier : action bonus, retire Empoisonné, Aveuglé, Charmé, Effrayé, Paralysé, Étourdi,
    Entravé et les maladies.
  - Lier : action, sauvegarde de Sagesse ; la cible ne peut ni bouger ni réagir pendant 2 tours.
  - **Écart :** Lier n'empêche pas la téléportation, le jeu n'a pas d'effet de données pour cela.
- **Entropie** (Chaos) : +1 par coup critique et par ennemi éliminé, remise à zéro au début et à
  la fin de chaque combat.
  - Pas chaotique (1) : téléportation de 18 m.
  - Défaire (2) : pendant 2 tours, **vos dégâts ignorent les résistances**. Écart : le jeu ne
    permet pas de retirer les résistances d'une cible, donc l'effet porte sur vos dégâts.
  - Détoner (3) : explosion d'un élément aléatoire, 4d6 aux ennemis à 6 m.
- **Déferlement de chaos** : table de Magie sauvage du jeu + 6 effets divins (bénédiction de
  groupe, éclat de force, vol, soins, +1 Entropie, contrecoup de 1d10).
- **Ordre parfait** (1/repos long, 10 tours) : les alliés à 9 m ne subissent plus de critiques et
  ne tombent pas sous 1 PV.
- **Tempête primordiale** (1/repos long, 10 tours) : un Déferlement au début de chaque tour,
  critiques sur 15-20.
  - **Écart :** le choix « entre 2 déferlements » n'est pas possible sans script, il n'y en a
    qu'un.

### Sorts exclusifs de classe (un par niveau de sort, toujours préparés)

| Niv. de sort | Ordre | Chaos |
|---|---|---|
| 1 | Verdict lumineux (4d6 radiants, avantage) | Trait primordial (3d8 force) |
| 2 | Chaînes de la Loi (paralysie + 2d8 radiants, sans concentration, toute créature) | Fracture du réel (3d8 force, zone 4 m) |
| 3 | Égide de l'Ordre (6 alliés : +2 CA, +2 sauvegardes) | Foudre du chaos (4d10 foudre) |
| 4 | Bannissement absolu (3 tours, sans concentration) | Grêle d'entropie (6d8 force + Hébété) |
| 5 | Décret d'immobilité (paralysie de zone, sans concentration) | Flétrissure du chaos (9d8 force) |
| 6 | Jugement de l'Ordre (10d8 radiants, zone 6 m) | Apocalypse primordiale (6d8 feu + 6d8 force) |

---

## Domaines

### Affinité divine (tous les domaines)

- Niv. 1 : résistance au type du domaine.
- Niv. 6 : immunité.
- Niv. 10 : absorption. Chaque fois que ce type de dégâts vous atteint (sort, attaque, état ou
  surface), vous récupérez 3d8 PV. **Écart :** c'est un soin fixe ; le jeu ne permet pas de soigner
  exactement le montant des dégâts annulés.
- **Contrepoids :** vulnérabilité au type du domaine opposé. C'est un passif **activable** : il est
  activé par défaut, et le joueur peut le désactiver.
- Sorts de domaine toujours préparés aux niveaux 1, 3, 5, 7 et 9. Chaque domaine a 2 sorts
  exclusifs liés à son élément.

| Domaine (classe) | Type | Opposé |
|---|---|---|
| Vie (Ordre) | Radiant | Nécrotique |
| Justice (Ordre) | Foudre | Poison |
| Magie (Ordre) | Force | Acide |
| Soleil (Ordre) | Feu | Froid |
| Paix (Ordre) | Psychique | Tonnerre |
| Mort (Chaos) | Nécrotique | Radiant |
| Tromperie (Chaos) | Poison | Foudre |
| Sorcellerie (Chaos) | Acide | Force |
| Lune (Chaos) | Froid | Feu |
| Guerre (Chaos) | Tonnerre | Psychique |

### Vie (Ordre, radiant)

- **Niv. 1 — Vie débordante :** vos soins (hors tours de magie) rendent en plus autant de PV que
  votre niveau, et la cible gagne autant de PV temporaires.
- **Niv. 3 — Fil de vie :** action bonus, 1/repos court. Un allié protégé pendant 10 tours tombe à
  1 PV au lieu de 0. **Écart :** c'est une protection posée à l'avance et non une réaction, car le
  jeu ne peut pas réagir « juste avant 0 PV ».
- **Niv. 6 — Aura vitale :** les alliés à 3 m récupèrent 1d4 PV à chaque tour.
- **Niv. 10 — Renaissance :** 1/repos long, les alliés inconscients à 9 m se relèvent avec 50 % de
  leurs PV.
- **Sorts exclusifs :** Souffle de vie (soins de groupe + retrait d'états), Éclat de vie.

### Justice (Ordre, foudre)

- **Niv. 1 — Marque du jugement :** action bonus. +1d6 foudre contre la cible marquée ; elle subit
  1d6 si elle attaque quelqu'un d'autre que vous.
- **Niv. 3 — Vision véritable :** vous voyez les créatures invisibles. **Écart :** pas d'immunité
  aux illusions ni de limite à 9 m.
- **Niv. 6 — Rétribution (réaction) :** 2d8 foudre à l'ennemi qui touche un allié à 9 m.
- **Niv. 10 — Verdict final :** 1/repos long. Exécute la cible si elle échoue sa sauvegarde et a
  moins de 25 % de ses PV ; sinon 10d10, ou 6d10 si elle réussit.
- **Sorts exclusifs :** Jugement céleste (doublé contre une cible marquée), Glaive de la sentence.
  **Écart :** Jugement céleste est doublé si la cible est marquée, et non « si elle a frappé un
  allié ».

### Magie (Ordre, force)

- **Niv. 1 — Codex :** apprendre des sorts à partir des parchemins, comme un magicien.
- **Niv. 3 — Arbitre de la Trame :** un Contresort sans emplacement par repos court.
- **Niv. 6 — Focalisation absolue :** les dégâts ne brisent pas la concentration.
- **Niv. 10 — Maîtrise des sorts :** un sort de niv. 1 et un de niv. 2 lançables sans emplacement,
  une fois par tour.
- **Sorts exclusifs :** Salve de l'Ordre (5 projectiles), Pulsation arcanique. **Écart :** la Salve
  tire 5 projectiles fixes au lieu de +1 par palier.

### Soleil (Ordre, feu)

- **Niv. 1 — Feu solaire :** vos dégâts de feu ignorent la résistance de vos cibles (sauf la vôtre : sans cette condition, vos propres flammes ignoraient votre Affinité divine).
- **Niv. 3 — Éruption solaire :** cône de 12 m, Aveuglé et En feu 2 tours (sauvegarde de
  Constitution), 1/repos court.
- **Niv. 6 — Halo :** aura de 9 m qui brûle uniquement les ennemis (1d6 par tour). **Écart :** elle
  ne dissipe pas encore les ténèbres magiques.
- **Niv. 10 — Supernova :** 12d6 feu + sol enflammé, 1/repos long. Les flammes vous soignent grâce à
  l'absorption.
- **Sorts exclusifs :** Lance solaire (feu + radiant + surface enflammée dès le niveau 1), Colonne
  solaire.

### Paix (Ordre, psychique)

- **Niv. 1 — Lien de paix :** jusqu'à 3 alliés gagnent +1d4 aux attaques, tests et sauvegardes,
  jusqu'au repos long. **Écart :** le bonus s'applique à chaque jet, et non à un seul jet par tour.
- **Niv. 3 — Apaisement :** l'ennemi ne peut plus agir pendant 2 tours, sauf s'il subit des dégâts.
- **Niv. 6 — Lien protecteur (réaction) :** les dégâts subis par un allié lié sont divisés par deux.
  **Écart :** pas de téléportation à ses côtés.
- **Niv. 10 — Armistice :** les ennemis à 9 m ne peuvent plus agir pendant 2 tours ; les alliés
  récupèrent 3d8 PV.
- **Sorts exclusifs :** Trêve sacrée (3 alliés protégés, riposte de 2d6 psychiques), Onde
  d'apaisement.

### Mort (Chaos, nécrotique)

- **Niv. 1 — Tribut du faucheur :** PV temporaires quand **vous** éliminez un ennemi. **Écart :** le
  jeu ne signale pas les morts causées par les autres.
- **Niv. 3 — Lever les morts :** squelette ou zombie, 1/repos court, sans emplacement.
- **Niv. 6 — Toucher flétrissant :** les cibles de vos dégâts nécrotiques ne peuvent pas être
  soignées jusqu'à votre prochain tour.
- **Niv. 10 — Outre-tombe :** 1/repos long. Au lieu de mourir, vous restez à 1 PV puis vous
  remontez aussitôt à 50 % de vos PV, avec une aura nécrotique pendant 3 tours.
- **Sorts exclusifs :** Moisson des âmes (zone, rend la moitié des dégâts infligés), Étreinte du
  tombeau.

### Tromperie (Chaos, poison)

- **Niv. 1 — Double illusoire :** Image miroir + avantage au corps à corps, 1/repos court.
- **Niv. 3 — Escamotage (réaction) :** quand vous êtes touché, vous devenez invisible 2 tours et
  pouvez vous téléporter en action bonus.
- **Niv. 6 — Langue d'argent :** Tromperie et Persuasion valent 15 minimum au dé.
- **Niv. 10 — Marionnettiste :** un ennemi passe de votre côté pendant 3 tours (sauvegarde de
  Sagesse).
- **Sorts exclusifs :** Baiser du traître (poison + Charmé 1 tour), Nuée de venin. **Écart :** la
  durée de Charmé ne passe pas à 2 tours au niveau 9.

### Sorcellerie (Chaos, acide)

- **Niv. 1 — Marées du chaos :** passif du jeu (Marées du chaos de l'ensorceleur). Le sort suivant
  déclenche un Déferlement.
- **Niv. 3 — Métamagie chaotique :** 2 options de métamagie, des points de sorcellerie (2/4/6) et
  +1 point par critique ou élimination. **Écart :** le jeu ne permet pas de payer la métamagie avec
  l'Entropie, donc ce sont les critiques et éliminations qui rechargent les points de sorcellerie.
- **Niv. 6 — Chaos maîtrisé :** vos Déferlements ne tirent plus que dans la table divine.
  **Écart :** ce n'est pas un double tirage au choix.
- **Niv. 10 — Tempête arcanique :** pendant 3 tours, chaque sort déclenche en plus une nova
  aléatoire (feu, foudre ou froid). **Écart :** ce n'est pas un sort aléatoire du jeu.
- **Sorts exclusifs :** Faille acide (déclenche un Déferlement), Pluie corrosive.

### Lune (Chaos, froid)

- **Niv. 1 — Phases lunaires :** une phase au hasard à chaque repos long : nouvelle (avantage en
  Discrétion), croissante (+3 m), pleine (+1d6 froid au corps à corps), décroissante (+1d4 aux
  sorts).
- **Niv. 3 — Pas de l'ombre :** le sort du moine de l'Ombre, d'ombre en ombre en action bonus,
  avantage à l'attaque suivante.
- **Niv. 6 — Bête lunaire :** forme de loup sanguinaire, 1/repos court. **Écart :** pas encore de
  bonus à la pleine lune.
- **Niv. 10 — Éclipse :** ténèbres magiques, régénération de 2d8 par tour, 2d8 froid par tour aux
  ennemis à 9 m.
- **Sorts exclusifs :** Clair de lune glacé (zone + ralentissement), Éclat lunaire. **Écart :** le
  rayon ne se déplace pas d'un tour à l'autre.

### Guerre (Chaos, tonnerre)

- **Niv. 1 — Né pour la guerre :** armures lourdes et armes de guerre ; Attaque supplémentaire au
  niv. 5.
- **Niv. 3 — Cri de guerre :** ennemis à 6 m Effrayés, alliés +2 aux dégâts, 1/repos court.
- **Niv. 6 — Carnage :** une attaque bonus après chaque élimination.
- **Niv. 10 — Incarnation de la guerre :** 3 tours avec une action supplémentaire, résistance aux
  dégâts physiques et immunité à la peur.
- **Sorts exclusifs :** Fracas de guerre, Tonnerre de bataille.

### Divinité pure

Une Divinité (race) qui joue une Divinité de l'Ordre ou du Chaos gagne +1 Décret ou +1 Entropie
maximum. Sa Forme divine inflige alors le type de dégâts de son domaine au lieu de la force. Les
ailes enflammées et les auras visuelles sont prévues en V2.

---

## À tester en priorité

Ces points reposent sur des mécanismes du jeu que je n'ai pas pu vérifier sans lancer le jeu. Si
l'un d'eux ne marche pas, il suffit de me le dire.

1. La race Divinité apparaît dans la création de personnage, et chaque forme a un corps, des
   visages et des coiffures (vérifier surtout les formes drakéide et tieffeline).
2. Les deux classes apparaissent, ainsi que leurs 5 domaines au niveau 1.
3. Les sorts du clerc (Ordre) se préparent, et les sorts de l'ensorceleur (Chaos) se choisissent à
   chaque niveau.
4. Le double bonus +2/+1 (race + classe) s'affiche correctement.
5. L'Entropie tombe bien à 0 en combat et remonte sur un critique ou une élimination.
6. Les Déferlements de chaos se déclenchent (forcer le test avec Marées du chaos en Sorcellerie).
7. Les auras (Ordre, Chaos, Vie, Soleil) s'appliquent aux bonnes cibles.
8. Les réactions (Protéger, Rétribution, Escamotage, Arbitre, Lien protecteur) se proposent bien.
9. Maîtrise des sorts (Magie, niv. 10) : les sorts choisis se lancent sans emplacement.
10. Outre-tombe et Ordre parfait gardent bien le personnage à 1 PV.
11. Le multiclassage vers ces classes ne donne pas d'emplacements de sort en double.

## Prévu pour la V2

- Sous-races (Céleste, Infernal, Astral, Élémentaire).
- Visuels : yeux lumineux, marques, halo ou aura sombre en Forme divine, ailes selon le domaine.
- Icônes personnalisées pour les classes et les sorts (pour l'instant, ce sont des icônes du jeu).
- Traduction anglaise : le fichier English contient pour l'instant le texte français, pour qu'aucun
  texte ne manque en jeu.
- Sorts d'occultiste pour le Chaos, choix entre deux déferlements, et le reste des écarts listés
  ci-dessus.
