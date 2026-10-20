# Classe Chronomancien — mod Baldur's Gate 3

Un mod **indépendant** qui ajoute une seule classe : le **Chronomancien**, un mage qui plie le **temps**,
l'**espace**, puis la **réalité** à partir du niveau 14.

- Lanceur de sorts complet à l'**Intelligence**, d8, sorts à préparer (espace, temps, entropie).
- **Sablier** : une ressource (2 à 6 charges, repos court) pour Accélération (+1 action), Rembobinage
  (un coup n'a jamais eu lieu), Ralentir, Faille (téléportation ou échange de place), Prison temporelle,
  Réécrire l'instant.
- **Beaucoup de dégâts** : un sort de dégâts propre à chaque niveau de sort, de Rayon d'entropie (niv. 1)
  à Effacement (niv. 9), qui montent tous avec le niveau du personnage.
- Progression **jusqu'au niveau 20** (avec un mod qui débloque le niveau 20).

Le détail de chaque capacité est dans [CONCEPTION.md](CONCEPTION.md).

> **État : version 1, pas encore testée en jeu.** Les points à vérifier en priorité sont à la fin
> de [CONCEPTION.md](CONCEPTION.md#à-tester-en-priorité).

---

## Contenu du dossier

```
ClasseChronomancien/     <- LE MOD (dossier à glisser sur le Multitool)
outils/           <- le générateur (Python) qui fabrique le dossier ci-dessus
CONCEPTION.md     <- description complète et liste des tests
```

Ne modifie pas `ClasseChronomancien/` à la main : il est régénéré à partir de `outils/`.

---

## Installer le mod pour le tester

1. **Ferme le jeu.**
2. Dézippe le fichier reçu.
3. Dans le **Multitool**, glisse le dossier **`ClasseChronomancien`** (celui qui contient `Mods`,
   `Public` et `Localization`) sur la zone bleue.
4. Le Multitool fabrique un `.zip` qui contient `ClasseChronomancien.pak`. Copie ce `.pak` dans :
   `%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods`
   (colle ce chemin dans la barre d'adresse de l'Explorateur Windows pour ouvrir le dossier).
5. Lance le jeu, ouvre le menu **Mods** et active **Classe Chronomancien** (ou utilise BG3 Mod Manager).
6. Crée un **nouveau personnage** : la classe **Chronomancien** est dans la liste des classes.

Pour une nouvelle version : ferme le jeu, supprime l'ancien `ClasseChronomancien.pak` du dossier `Mods`,
puis refais les étapes 2 à 4.

---

## Modifier le mod

- `outils/contenu.py` : toutes les capacités, sorts et états ;
- `outils/progressions.py` : ce qu'on gagne à chaque niveau ;
- `outils/build.py` : écrit les fichiers du jeu et vérifie qu'ils sont cohérents.

Après une modification, avec Python 3 installé, lance depuis le dossier `Chronomancien` :

```
python outils/build.py
```

Le script régénère `ClasseChronomancien/` et affiche `Vérifications : OK` si tout est cohérent.

**Règle importante :** ne renomme jamais une capacité, un sort ou la classe une fois le mod publié.
Leurs identifiants sont calculés à partir de leur nom ; en changer casserait les sauvegardes.
Modifier un texte ou un chiffre ne pose aucun problème.

---

## Publier dans le gestionnaire de mods du jeu (mod.io)

À faire quand le mod marche bien en jeu, avec le **Toolkit officiel de Larian** : on crée un projet
`ClasseChronomancien`, on y copie les données du mod, puis on publie depuis **Project Settings**. Je
t'accompagnerai pas à pas le moment venu. Guide officiel :
<https://docs.baldursgate3.game/index.php?title=Getting_Started:_Publishing_a_Mod>

## Crédits

- Conception : Evans (cahier des charges « Classe Chronomancien »).
