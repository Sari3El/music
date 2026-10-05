"""Génère le mod « Classe Phénix » dans ../ClassePhenix/ puis le vérifie.

Usage :  python3 Phenix/outils/build.py            (génère + vérifie)
         python3 Phenix/outils/build.py --check    (vérifie seulement)

Aucune dépendance : Python 3.8+ suffit.
"""
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
import contenu as C  # noqa: E402
import progressions as P  # noqa: E402
from doclib import U, Node, lsx, stats_file  # noqa: E402

MOD_NAME = "Classe Phénix"
FOLDER = "ClassePhenix"
AUTHOR = "Evans"
DESCRIPTION = ("Ajoute la classe Phénix : un lanceur de sorts au Charisme dont le feu épargne les alliés et les "
               "soigne, qui renaît de ses cendres. Trois voies : Brasier, Cendre et Serres.")
VERSION64 = "36028797018963968"  # 1.0.0.0
MOD_UUID = U("mod:" + FOLDER)

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", FOLDER))


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def meta_lsx():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="0" revision="9" build="331"/>
    <region id="Config">
        <node id="root">
            <children>
                <node id="Dependencies"/>
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="{AUTHOR}"/>
                    <attribute id="CharacterCreationLevelName" type="FixedString" value=""/>
                    <attribute id="Description" type="LSString" value="{DESCRIPTION}"/>
                    <attribute id="Folder" type="LSString" value="{FOLDER}"/>
                    <attribute id="LobbyLevelName" type="FixedString" value=""/>
                    <attribute id="MD5" type="LSString" value=""/>
                    <attribute id="MainMenuBackgroundVideo" type="FixedString" value=""/>
                    <attribute id="MenuLevelName" type="FixedString" value=""/>
                    <attribute id="Name" type="LSString" value="{MOD_NAME}"/>
                    <attribute id="NumPlayers" type="uint8" value="4"/>
                    <attribute id="PhotoBooth" type="FixedString" value=""/>
                    <attribute id="StartupLevelName" type="FixedString" value=""/>
                    <attribute id="Tags" type="LSString" value=""/>
                    <attribute id="Type" type="FixedString" value="Add-on"/>
                    <attribute id="UUID" type="FixedString" value="{MOD_UUID}"/>
                    <attribute id="Version64" type="int64" value="{VERSION64}"/>
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="{VERSION64}"/>
                        </node>
                        <node id="TargetModes">
                            <children>
                                <node id="Target">
                                    <attribute id="Object" type="FixedString" value="Story"/>
                                </node>
                            </children>
                        </node>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
"""


def equipment_txt():
    items = ["WPN_Quarterstaff", "ARM_Leather_Body", "ARM_Boots_Leather", "OBJ_Potion_Healing",
             "OBJ_Potion_Healing", "ARM_Camp_Body", "ARM_Camp_Shoes", "OBJ_Keychain", "OBJ_Bag_AlchemyPouch",
             "OBJ_Backpack_CampSupplies", "OBJ_Scroll_Revivify"]
    out = [f'new equipment "{P.EQUIPMENT}"', 'add initialweaponset "Melee"']
    for it in items:
        out += ["add equipmentgroup", f'add equipment entry "{it}"']
    return "\n".join(out) + "\n"


def build():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    pub = f"Public/{FOLDER}"
    write(f"Mods/{FOLDER}/meta.lsx", meta_lsx())

    # --- stats
    groups = {"PHX_Passifs.txt": "PassiveData", "PHX_Etats.txt": "StatusData", "PHX_Sorts.txt": "SpellData",
              "PHX_Reactions.txt": "InterruptData"}
    for fname, typ in groups.items():
        write(f"{pub}/Stats/Generated/Data/{fname}", stats_file([e for e in C.STATS if e.type == typ]))
    write(f"{pub}/Stats/Generated/Equipment.txt", equipment_txt())

    # --- classe, voies, progressions
    write(f"{pub}/ClassDescriptions/ClassDescriptions.lsx", lsx("ClassDescriptions", P.CLASSDESCS))
    write(f"{pub}/Progressions/Progressions.lsx", lsx("Progressions", P.PROGRESSIONS))
    write(f"{pub}/Progressions/ProgressionDescriptions.lsx", lsx("ProgressionDescriptions", [
        Node("ProgressionDescription", [
            ("Description", "TranslatedString", C.L.add(f"selector:{sid}:desc", desc)),
            ("DisplayName", "TranslatedString", C.L.add(f"selector:{sid}:nom", titre)),
            ("SelectorId", "FixedString", sid), ("UUID", "guid", U("progdesc:" + sid))])
        for sid, titre, desc in C.SELECTOR_LABELS]))

    # --- listes
    write(f"{pub}/Lists/SpellLists.lsx", lsx("SpellLists", [
        Node("SpellList", [("Comment", "LSString", com), ("Spells", "LSString", ";".join(spells)),
                           ("UUID", "guid", U("spelllist:" + name))])
        for name, com, spells in C.SPELLLISTS]))
    write(f"{pub}/Lists/SkillLists.lsx", lsx("SkillLists", [
        Node("SkillList", [("Skills", "LSString", ", ".join(sk)), ("UUID", "guid", U("skilllist:" + name))])
        for name, sk in C.SKILLLISTS]))

    # --- ressource (Braises)
    write(f"{pub}/ActionResourceDefinitions/ActionResourceDefinitions.lsx", lsx(
        "ActionResourceDefinitions", [Node("ActionResourceDefinition", [
            ("Description", "TranslatedString", C.L.add(f"resource:{n}:desc", d)),
            ("DisplayName", "TranslatedString", C.L.add(f"resource:{n}:nom", t)),
            ("IsSpellResource", "bool", "false"), ("MaxLevel", "uint32", 0), ("MaxValue", "uint32", 0),
            ("Name", "FixedString", n), ("PartyActionResource", "bool", "false"), ("ReplenishType", "FixedString", r),
            ("ShowOnActionResourcePanel", "bool", "true"), ("UUID", "guid", U("resource:" + n)),
            ("UpdatesSpellPowerLevel", "bool", "false")]) for n, t, d, r in C.RESOURCES]))

    # --- paliers de puissance
    write(f"{pub}/Levelmaps/LevelMapValues.lsx", lsx("LevelMapValues", [
        Node("LevelMapSeries", [(f"Level{lv}", "LSString", v) for lv, v in sorted(vals.items())] +
             [("Name", "FixedString", name), ("UUID", "guid", U("levelmap:" + name))])
        for name, vals in C.LEVELMAPS]))

    # --- répartition de caractéristiques conseillée
    write(f"{pub}/CharacterCreationPresets/AbilityDistributionPresets.lsx", lsx(
        "AbilityDistributionPresets", [Node("AbilityDistributionPreset",
            [(k, "int32", v) for k, v in P.DIST.items()] +
            [("ClassUUID", "guid", U("class:" + C.PHENIX)), ("UUID", "guid", U("abilitypreset:" + C.PHENIX))])]))

    # --- textes : français ; l'anglais reprend le français en attendant la traduction
    loca = C.L.xml()
    write(f"Localization/French/{FOLDER}.loca.xml", loca)
    write(f"Localization/English/{FOLDER}.loca.xml", loca)


# ====================================================================== VÉRIFICATIONS
VANILLA_HINTS = os.environ.get("PHX_VANILLA_HINTS")  # fichier optionnel de noms connus du jeu


def check():
    problems, warnings = [], []
    # 1. tous les XML se lisent
    for dirpath, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith((".lsx", ".xml")):
                try:
                    ET.parse(os.path.join(dirpath, f))
                except ET.ParseError as e:
                    problems.append(f"XML invalide : {f} : {e}")

    entries = {e.name: e for e in C.STATS}
    if len(entries) != len(C.STATS):
        problems.append("Deux entrées de stats portent le même nom")
    resources = {r[0] for r in C.RESOURCES}
    levelmaps = {m[0] for m in C.LEVELMAPS}
    classes = {a[2] for n in P.CLASSDESCS for a in n.attrs if a[0] == "Name"}
    defined = set(entries) | resources | levelmaps | classes

    # 2. chaque nom PHX_ cité existe
    token = re.compile(r"\b((?:Target|Shout|Projectile|Zone|Interrupt)_PHX_\w+|PHX_\w+)")
    for e in C.STATS:
        for k, v in e.data.items():
            if k in ("DisplayName", "Description", "StackId", "Stack"):
                continue
            for t in token.findall(v):
                if t not in defined:
                    problems.append(f"{e.name}.{k} cite {t}, qui n'existe pas")
        if e.using and "PHX_" in e.using and e.using not in entries:
            problems.append(f"{e.name} dérive de {e.using}, qui n'existe pas")
    for name, _, spells in C.SPELLLISTS:
        for s in spells:
            if "PHX_" in s and s not in entries:
                problems.append(f"Liste {name} : sort {s} inexistant")
    for node in P.PROGRESSIONS:
        attrs = {a[0]: str(a[2]) for a in node.attrs}
        for key in ("PassivesAdded", "PassivesRemoved"):
            for p in filter(None, attrs.get(key, "").split(";")):
                if p.startswith("PHX_") and p not in entries:
                    problems.append(f"Progression {attrs['Name']} niv. {attrs['Level']} : passif {p} inexistant")
        for t in re.findall(r"ActionResource\((\w+)", attrs.get("Boosts", "")):
            if t.startswith("PHX_") and t not in resources:
                problems.append(f"Progression {attrs['Name']} : ressource {t} inexistante")

    # 3. chaque liste citée par une progression existe (listes du mod ou du jeu)
    known_lists = ({U("spelllist:" + n) for n, _, _ in C.SPELLLISTS} | {U("skilllist:" + n) for n, _ in C.SKILLLISTS} |
                   {C.ALL_ABILITIES_LIST})
    for node in P.PROGRESSIONS:
        attrs = {a[0]: str(a[2]) for a in node.attrs}
        for g in re.findall(r"Select\w+\(([0-9a-f-]{36})|AddSpells\(([0-9a-f-]{36})", attrs.get("Selectors", "")):
            g = g[0] or g[1]
            if g not in known_lists:
                problems.append(f"Progression {attrs['Name']} : liste {g} inconnue")

    # 4. UUID uniques
    uuids = re.findall(r'id="UUID" type="(?:guid|FixedString)" value="([0-9a-f-]{36})"',
                       "".join(open(os.path.join(dp, f), encoding="utf-8").read()
                               for dp, _, fs in os.walk(ROOT) for f in fs if f.endswith(".lsx")))
    dup = {u for u in uuids if uuids.count(u) > 1}
    if dup:
        problems.append(f"UUID en double : {sorted(dup)[:5]}")

    # 5. aucun lien avec un autre mod
    for e in C.STATS:
        if "DOC_" in e.text():
            problems.append(f"{e.name} cite un nom d'un autre mod (DOC_)")

    # 6. (optionnel) noms du jeu de base connus
    if VANILLA_HINTS and os.path.exists(VANILLA_HINTS):
        known = set(open(VANILLA_HINTS, encoding="utf-8").read().split())
        for e in C.STATS:
            if e.using and "PHX_" not in e.using and e.using not in known:
                warnings.append(f"Base non vérifiée : {e.name} dérive de {e.using}")
            icon = e.data.get("Icon")
            if icon and icon not in known:
                warnings.append(f"Icône non vérifiée : {e.name} -> {icon}")
        for name, _, spells in C.SPELLLISTS:
            for sp in spells:
                if "PHX_" not in sp and sp not in known:
                    warnings.append(f"Sort du jeu non vérifié dans {name} : {sp}")
    return problems, warnings


def main():
    if "--check" not in sys.argv:
        build()
        print(f"Mod généré dans {ROOT}")
    problems, warnings = check()
    print(f"{len(C.STATS)} entrées de stats, {len(P.PROGRESSIONS)} progressions, "
          f"{len(C.SPELLLISTS)} listes de sorts, {len(C.L.texts)} textes.")
    for w in warnings:
        print("  avertissement :", w)
    for p in problems:
        print("  ERREUR :", p)
    if problems:
        sys.exit(1)
    print("Vérifications : OK")


if __name__ == "__main__":
    main()
