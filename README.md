# Divinités de l'Ordre et du Chaos — mod Baldur's Gate 3

Ce mod ajoute :

- la race **Divinité**, des dieux tombés sur Faerûn, avec 11 formes au choix (humaine, elfique, drow,
  demi-elfe, naine, halfeline, gnome, tieffeline, githyanki, drakéide, demi-orque) qui reprennent les
  corps, visages et couleurs des races du jeu ;
- deux classes : **Divinité de l'Ordre** (Sagesse, fiabilité) et **Divinité du Chaos** (Charisme,
  coups critiques et magie sauvage) ;
- **10 domaines** (sous-classes) en miroir : Vie/Mort, Justice/Tromperie, Magie/Sorcellerie,
  Soleil/Lune, Paix/Guerre ;
- l'Affinité divine (résistance, puis immunité, puis absorption), le contrepoids (optionnel) et le
  bonus Divinité pure ;
- 32 sorts exclusifs qui gagnent en puissance aux niveaux 5, 9 et 12, ainsi que les sorts du clerc,
  du paladin et de l'ensorceleur.

Le détail de chaque capacité, et ce qui diffère du cahier des charges, est dans
[docs/CONCEPTION.md](docs/CONCEPTION.md).

> **État : version 1, pas encore testée en jeu.** Tous les fichiers sont générés et vérifiés
> automatiquement (format, références croisées, noms du jeu de base), mais il faut maintenant
> tester en jeu. Les points les plus fragiles sont listés à la fin de
> [docs/CONCEPTION.md](docs/CONCEPTION.md#à-tester-en-priorité).

---

## Contenu du dépôt

```
DivinitesOrdreChaos/        <- LE MOD (dossier à transformer en .pak)
  Mods/DivinitesOrdreChaos/meta.lsx          fiche d'identité du mod
  Localization/French/…loca.xml              tous les textes (français)
  Localization/English/…loca.xml             copie du français, en attendant la traduction
  Public/DivinitesOrdreChaos/                race, classes, progressions, sorts, états…
tools/                      <- le générateur (Python) qui fabrique le dossier ci-dessus
docs/CONCEPTION.md          <- description complète et liste des tests
```

Ne modifie pas les fichiers de `DivinitesOrdreChaos/` à la main : ils sont régénérés à partir de
`tools/`. Si tu veux un changement, demande-le-moi ou modifie `tools/` (voir plus bas).

---

## Étape 2 : tester le mod sur ton PC

### 2.1 Récupérer le mod

Sur la page GitHub du dépôt, choisis la branche `claude/baldurs-gate-3-modes-fp33te`, puis
**Code ▸ Download ZIP**. Dézippe : tu obtiens un dossier qui contient `DivinitesOrdreChaos`.

### 2.2 Fabriquer le fichier .pak

1. Dans le **Multitool**, vérifie dans **Configuration** que le dossier des mods est bien :
   `%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods`
   (tu peux coller ce chemin dans la barre d'adresse de l'Explorateur Windows pour l'ouvrir).
2. **Glisse le dossier `DivinitesOrdreChaos`** (celui qui contient `Mods`, `Public` et
   `Localization`) sur la zone bleue du Multitool (« Drop mod workspace folder… »).
3. Le Multitool crée `DivinitesOrdreChaos.pak` directement dans le dossier des mods. Il convertit
   aussi les textes (`.loca.xml` en `.loca`).

### 2.3 Activer le mod

- **Avec le gestionnaire de mods du jeu :** lance Baldur's Gate 3, ouvre le menu **Mods**. Si
  « Divinités de l'Ordre et du Chaos » apparaît dans les mods installés, active-le.
- **Sinon, avec BG3 Mod Manager**, la méthode la plus fiable pour un mod local :
  1. Télécharge-le : <https://github.com/LaughingLeader/BG3ModManager/releases>.
  2. Lance-le : le mod apparaît à droite (mods inactifs).
  3. Glisse-le à gauche (mods actifs).
  4. Fais **Ctrl+S** pour enregistrer, puis **Ctrl+E** pour exporter l'ordre de chargement vers
     le jeu.
  5. Lance le jeu.

### 2.4 Jouer

Lance une **nouvelle partie**. En création de personnage, tu trouveras la race **Divinité** et les
classes **Divinité de l'Ordre** et **Divinité du Chaos**. Le domaine se choisit dès le niveau 1.

### 2.5 Me faire un retour

Pour chaque problème, envoie-moi :

- ce que tu as fait (par exemple « niveau 2, Divinité du Chaos, j'ai lancé Pas chaotique ») ;
- ce qui s'est passé, avec une capture d'écran si possible ;
- ce que tu attendais.

Les cas typiques : un texte qui affiche « Not Found » ou est vide, une capacité absente, un sort qui
ne fait rien, un chiffre faux. Je corrige et je régénère le mod ; tu n'as plus qu'à refaire les étapes 2.1 et 2.2.

> Si le jeu affiche « We were unable to create a working story… » au lancement d'une partie, appuie
> sur Échap, accepte, et continue. C'est un message habituel avec les mods qui ajoutent des
> classes.

---

## Étape 3 : publier dans le gestionnaire de mods du jeu (mod.io)

**À faire seulement quand le mod marche bien en jeu.**

Le gestionnaire de mods du jeu n'accepte que les mods publiés avec le **Toolkit officiel de
Larian**. Or le Toolkit ne sait pas importer les fichiers de stats (sorts, passifs, états) d'un mod
existant : il garde sa propre copie, dans un format interne. La publication se fera donc en 3
temps, et je t'accompagnerai pas à pas :

1. **Créer le projet dans le Toolkit** (**File ▸ New project**) avec le nom
   `DivinitesOrdreChaos`.
2. **Copier les données du mod** dans le projet (dossiers `Mods`, `Public` et `Localization`), puis
   générer la copie « éditeur » des stats. Un outil open source fait cette conversion
   automatiquement :
   [bg3-data-mcp](https://github.com/holypolarpanda7/bg3-data-mcp) (commande `toolkit_export`).
   Je te donnerai les commandes exactes le moment venu.
3. **Publier** : dans le Toolkit, ouvre **Project ▸ Project Settings**, remplis le nom, la
   description et la miniature, clique sur **Authenticate** (compte Larian ou Steam, lié à
   mod.io), puis sur **Publish**. Sur la page mod.io qui s'ouvre, complète la fiche et clique sur
   **Go live**.

Le guide officiel de Larian est ici :
<https://docs.baldursgate3.game/index.php?title=Getting_Started:_Publishing_a_Mod>

---

## Pour aller plus loin : modifier le mod toi-même

Tout le mod est décrit dans quelques fichiers Python lisibles :

- `tools/contenu.py` : la race, les socles de classe, les ressources et les sorts exclusifs de
  classe ;
- `tools/contenu_domaines.py` : les 10 domaines ;
- `tools/progressions.py` : ce qu'on gagne à chaque niveau ;
- `tools/build_mod.py` : écrit les fichiers du jeu et vérifie qu'ils sont cohérents.

Après une modification, régénère le mod avec Python 3 (<https://www.python.org/downloads/>, coche
« Add Python to PATH » à l'installation). Ouvre un terminal dans le dossier du dépôt et lance :

```
python tools/build_mod.py
```

Le script régénère `DivinitesOrdreChaos/` et affiche `Vérifications : OK` si tout est cohérent.

**Règle importante :** ne renomme jamais une capacité, un sort ou une classe déjà publiés. Leurs
identifiants sont calculés à partir de leur nom ; en changer casserait les sauvegardes des joueurs.
Modifier un texte ou un chiffre ne pose aucun problème.

---

## Crédits

- Conception : Evans (cahier des charges).
- Références techniques : données du jeu de base, wiki officiel du modding de Larian, BG3
  Community Library, bg3.wiki.
