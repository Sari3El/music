"""Classe Phénix : progression niveau par niveau, voies (sous-classes) et descriptions de classe."""
import contenu as C
from contenu import L, U
from doclib import Node, guid_list_node

PROGRESSIONS = []
CLASSDESCS = []

# Emplacements de sort d'un lanceur complet : niveau -> {niveau de sort: emplacements gagnés}
# Niveaux 13 à 20 : nécessitent un mod qui débloque le niveau 20 (il fournit les emplacements 7 à 9).
MAX_LEVEL = 20
SLOTS = {1: {1: 2}, 2: {1: 1}, 3: {1: 1, 2: 2}, 4: {2: 1}, 5: {3: 2}, 6: {3: 1}, 7: {4: 1},
         8: {4: 1}, 9: {4: 1, 5: 1}, 10: {5: 1}, 11: {6: 1}, 12: {},
         13: {7: 1}, 14: {}, 15: {8: 1}, 16: {}, 17: {9: 1}, 18: {5: 1}, 19: {6: 1}, 20: {7: 1}}
NEW_SPELL_LEVEL = {1: 1, 3: 2, 5: 3, 7: 4, 9: 5, 11: 6, 13: 7, 15: 8, 17: 9}   # nouveau niveau de sort
MAX_SPELL_LEVEL = {lv: max(v for k, v in NEW_SPELL_LEVEL.items() if k <= lv) for lv in range(1, MAX_LEVEL + 1)}
FEATS = (4, 8, 12, 16, 19)
SUBCLASS_LEVEL = 3
ARMOR = ["Proficiency(LightArmor)", "Proficiency(SimpleWeapons)"]
DIST = dict(Strength=8, Dexterity=13, Constitution=14, Intelligence=10, Wisdom=12, Charisma=15)
EQUIPMENT = "EQP_CC_PHX_Phenix"


def progression(name, table, level, ptype, boosts=(), passives=(), removed=(), selectors=(),
                improvement=False, multiclass=False, subclasses=None):
    attrs = []
    if improvement:
        attrs.append(("AllowImprovement", "bool", "true"))
    if boosts:
        attrs.append(("Boosts", "LSString", ";".join(boosts)))
    if multiclass:
        attrs.append(("IsMulticlass", "bool", "true"))
    attrs.append(("Level", "uint8", level))
    attrs.append(("Name", "LSString", name))
    if passives:
        attrs.append(("PassivesAdded", "LSString", ";".join(passives)))
    if removed:
        attrs.append(("PassivesRemoved", "LSString", ";".join(removed)))
    attrs.append(("ProgressionType", "uint8", ptype))
    if selectors:
        attrs.append(("Selectors", "LSString", ";".join(selectors)))
    attrs.append(("TableUUID", "guid", table))
    attrs.append(("UUID", "guid", U(f"progression:{name}:{level}{':mc' if multiclass else ''}")))
    children = [guid_list_node("SubClasses", "SubClass", subclasses)] if subclasses else []
    PROGRESSIONS.append(Node("Progression", attrs, children))


def slot_boosts(level):
    return [f"ActionResource(SpellSlot,{n},{lvl})" for lvl, n in SLOTS[level].items()]


def unlock_passive(level):
    lvl = NEW_SPELL_LEVEL.get(level)
    return [f"UnlockedSpellSlotLevel{lvl}"] if lvl else []


C.SELECTOR_LABELS += [
    ("PHX_TourPhenix", "Tours de magie du Phénix", "Choisissez vos tours de magie : feu et lumière uniquement."),
    ("PHX_SortPhenix", "Sorts du Phénix", "Choisissez de nouveaux sorts : feu et lumière uniquement."),
]
SKILLS = U("skilllist:phenix")
C.SKILLLISTS.append(("phenix", ["Arcana", "Insight", "Intimidation", "Medicine", "Performance", "Persuasion",
                                "Religion", "Survival"]))
LISTS = C.feature_spelllists()
TOURS, SORTS = C.sorts_appris()
EMPTY = {"passives": [], "removed": [], "spells": [], "boosts": []}


def level_features(lv):
    """(boosts, passives, removed, selectors) de la classe au niveau lv."""
    f = C.FEATURES[None].get(lv, EMPTY)
    b, p, r = list(f["boosts"]), list(f["passives"]), list(f["removed"])
    s = [f"AddSpells({LISTS[None][lv]},,,,AlwaysPrepared)"] if lv in LISTS[None] else []
    # sorts connus : uniquement feu et lumière (liste cumulative jusqu'au niveau de sort maximum)
    sl = SORTS[min(MAX_SPELL_LEVEL[lv], max(SORTS))]   # le jeu n'a pas de sort de feu de niveau 7+
    if lv == 1:
        s += [f"SelectSpells({sl},2,0,PHX_SortPhenix)",
              f"SelectSpells({TOURS},2,0,PHX_TourPhenix,,,AlwaysPrepared)"]
    elif lv <= 11 or lv in (13, 15, 17):
        s += [f"SelectSpells({sl},1,1,PHX_SortPhenix)"]
    if lv in (4, 10):
        s += [f"SelectSpells({TOURS},1,0,PHX_TourPhenix,,,AlwaysPrepared)"]
    return b, p, r, s


# ================================================================== CLASSE
TABLE = U("table:" + C.PHENIX)
SUBCLASSES = [U(f"class:{C.PHENIX}_{v}") for v in C.VOIES]
for lv in range(1, MAX_LEVEL + 1):
    b, p, r, s = level_features(lv)
    boosts = slot_boosts(lv) + b
    passives = unlock_passive(lv) + p
    if lv == 1:
        boosts = ["ProficiencyBonus(SavingThrow,Constitution)", "ProficiencyBonus(SavingThrow,Charisma)"] + \
                 ARMOR + boosts
        s = [f"SelectSkills({SKILLS},2)", f"SelectAbilityBonus({C.ALL_ABILITIES_LIST},AbilityBonus,2,1)"] + s
    progression(C.PHENIX, TABLE, lv, 0, boosts=boosts, passives=passives, removed=r, selectors=s,
                improvement=lv in FEATS, subclasses=SUBCLASSES if lv == SUBCLASS_LEVEL else None)
# niveau 1 en multiclasse (sans sauvegardes ni compétences)
b, p, r, s = level_features(1)
progression(C.PHENIX, TABLE, 1, 0, boosts=ARMOR[:1] + slot_boosts(1) + b, passives=unlock_passive(1) + p,
            selectors=s, multiclass=True)

CLASSDESCS.append(Node("ClassDescription", [
    ("BaseHp", "int32", 8),
    ("CanLearnSpells", "bool", "false"),
    ("CharacterCreationPose", "guid", C.CC_POSE),
    ("ClassEquipment", "FixedString", EQUIPMENT),
    ("ClassHotbarColumns", "int32", 5),
    ("CommonHotbarColumns", "int32", 9),
    ("Description", "TranslatedString", L.add(f"class:{C.PHENIX}:desc",
        "Un être de feu qui ne meurt jamais vraiment. Ses flammes épargnent ses alliés et peuvent même les "
        "soigner ; quand il tombe, ses cendres couvent, et il finit par renaître dans une explosion de feu. "
        "Lanceur de sorts complet (Charisme) qui n'apprend que des sorts de feu et de lumière, plus ses propres sorts.")),
    ("DisplayName", "TranslatedString", L.add(f"class:{C.PHENIX}:nom", "Phénix")),
    ("HpPerLevel", "int32", 5),
    ("ItemsHotbarColumns", "int32", 2),
    ("LearningStrategy", "uint8", 1),
    ("MulticlassSpellcasterModifier", "double", 1),
    ("MustPrepareSpells", "bool", "false"),
    ("Name", "FixedString", C.PHENIX),
    ("PrimaryAbility", "uint8", 6),
    ("ProgressionTableUUID", "guid", TABLE),
    ("SoundClassType", "FixedString", "Sorcerer"),
    ("SpellCastingAbility", "uint8", 6),
    ("SubclassTitle", "TranslatedString", L.add(f"class:{C.PHENIX}:subtitle", "Voie du Phénix")),
    ("UUID", "guid", U("class:" + C.PHENIX)),
]))

# ================================================================== VOIES (sous-classes)
for voie, (titre, desc) in C.VOIES.items():
    name = f"{C.PHENIX}_{voie}"
    table = U("table:sub:" + voie)
    for lv, f in sorted(C.FEATURES[voie].items()):
        sel = [f"AddSpells({LISTS[voie][lv]},,,,AlwaysPrepared)"] if lv in LISTS.get(voie, {}) else []
        progression(name, table, lv, 1, boosts=f["boosts"], passives=f["passives"], removed=f["removed"],
                    selectors=sel)
    CLASSDESCS.append(Node("ClassDescription", [
        ("CanLearnSpells", "bool", "false"),
        ("CharacterCreationPose", "guid", C.CC_POSE),
        ("Description", "TranslatedString", L.add(f"class:{name}:desc", desc)),
        ("DisplayName", "TranslatedString", L.add(f"class:{name}:nom", titre)),
        ("LearningStrategy", "uint8", 1),
        ("MustPrepareSpells", "bool", "false"),
        ("Name", "FixedString", name),
        ("ParentGuid", "guid", U("class:" + C.PHENIX)),
        ("PrimaryAbility", "uint8", 6),
        ("ProgressionTableUUID", "guid", table),
        ("ShortName", "TranslatedString", L.add(f"class:{name}:court", voie)),
        ("SoundClassType", "FixedString", "Sorcerer"),
        ("SpellCastingAbility", "uint8", 6),
        ("UUID", "guid", U("class:" + name)),
    ]))
