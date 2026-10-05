# Classe Phénix — mod Baldur's Gate 3

Un mod **indépendant** qui ajoute une seule classe : le **Phénix**.

- Lanceur de sorts complet au **Charisme** (sorts de l'ensorceleur + ses propres sorts de feu).
- Son feu **ne blesse jamais ses alliés** et peut même les soigner (Flamme bienfaitrice).
- Quand il tombe, ses **cendres couvent** et il se relève ; au niveau 10, il **renaît** dans une
  explosion de feu.
- **Braises** : une ressource gagnée par le feu, dépensée pour Attiser, Propager ou Purifier.
- 3 voies au niveau 3 : **Brasier** (dégâts), **Cendre** (soins), **Serres** (corps à corps).

Le détail de chaque capacité, et ce qui diffère du cahier des charges, est dans
[CONCEPTION.md](CONCEPTION.md).

> **État : version 1, pas encore testée en jeu.** Les points à vérifier en priorité sont à la fin
> de [CONCEPTION.md](CONCEPTION.md#à-tester-en-priorité).

---

## Contenu du dossier

```
ClassePhenix/     <- LE MOD (dossier à glisser sur le Multitool)
outils/           <- le générateur (Python) qui fabrique le dossier ci-dessus
CONCEPTION.md     <- description complète et liste des tests
```

Ne modifie pas `ClassePhenix/` à la main : il est régénéré à partir de `outils/`.

---

## Installer le mod pour le tester

1. **Ferme le jeu.**
2. Dézippe le fichier reçu.
3. Dans le **Multitool**, glisse le dossier **`ClassePhenix`** (celui qui contient `Mods`,
   `Public` et `Localization`) sur la zone bleue.
4. Le Multitool fabrique un `.zip` qui contient `ClassePhenix.pak`. Copie ce `.pak` dans :
   `%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods`
   (colle ce chemin dans la barre d'adresse de l'Explorateur Windows pour ouvrir le dossier).
5. Lance le jeu, ouvre le menu **Mods** et active **Classe Phénix** (ou utilise BG3 Mod Manager).
6. Crée un **nouveau personnage** : la classe **Phénix** est dans la liste des classes.

Pour une nouvelle version : ferme le jeu, supprime l'ancien `ClassePhenix.pak` du dossier `Mods`,
puis refais les étapes 2 à 4.

---

## Modifier le mod

- `outils/contenu.py` : toutes les capacités, sorts et états ;
- `outils/progressions.py` : ce qu'on gagne à chaque niveau, les voies ;
- `outils/build.py` : écrit les fichiers du jeu et vérifie qu'ils sont cohérents.

Après une modification, avec Python 3 installé, lance depuis le dossier `Phenix` :

```
python outils/build.py
```

Le script régénère `ClassePhenix/` et affiche `Vérifications : OK` si tout est cohérent.

**Règle importante :** ne renomme jamais une capacité, un sort ou la classe une fois le mod publié.
Leurs identifiants sont calculés à partir de leur nom ; en changer casserait les sauvegardes.
Modifier un texte ou un chiffre ne pose aucun problème.

---

## Publier dans le gestionnaire de mods du jeu (mod.io)

À faire quand le mod marche bien en jeu, avec le **Toolkit officiel de Larian** : on crée un projet
`ClassePhenix`, on y copie les données du mod, puis on publie depuis **Project Settings**. Je
t'accompagnerai pas à pas le moment venu. Guide officiel :
<https://docs.baldursgate3.game/index.php?title=Getting_Started:_Publishing_a_Mod>

## Crédits

- Conception : Evans (cahier des charges « Classe Phénix »).
