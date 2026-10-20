"""Classe Chronomancien : progression niveau par niveau et description de classe (pas de sous-classe)."""
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
ARMOR = ["Proficiency(LightArmor)", "Proficiency(SimpleWeapons)"]
DIST = dict(Strength=8, Dexterity=14, Constitution=13, Intelligence=15, Wisdom=12, Charisma=10)
EQUIPMENT = "EQP_CC_CHR_Chronomancien"
# Tenue de l'ensorceleur, Sceptre du Continuum et une teinture (le jeu n'a pas de teinture blanche pure :
# la plus proche est « noir et blanc arlequin », à appliquer soi-même en combinant les objets).
EQUIPMENT_ITEMS = [C.SCEPTRE, "ARM_Robe_Body_Sorcerer", "ARM_Boots_Leather", "OBJ_Dye_WhiteBlack"]
INTELLIGENCE = 4


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
    ("CHR_TourChrono", "Tours de magie du Chronomancien", "Choisissez vos tours de magie : espace, temps et entropie."),
]
SKILLS = U("skilllist:chronomancien")
C.SKILLLISTS.append(("chronomancien", ["Arcana", "History", "Insight", "Investigation", "Medicine", "Perception",
                                       "Religion", "Deception"]))
LISTS = C.feature_spelllists()
TOURS, SORTS = C.sorts_a_preparer()
EMPTY = {"passives": [], "removed": [], "spells": [], "boosts": []}


def level_features(lv):
    """(boosts, passives, removed, selectors) de la classe au niveau lv."""
    f = C.FEATURES.get(lv, EMPTY)
    b, p, r = list(f["boosts"]), list(f["passives"]), list(f["removed"])
    s = [f"AddSpells({LISTS[lv]},,,,AlwaysPrepared)"] if lv in LISTS else []
    # sorts du jeu à préparer (espace et temps) : la liste de chaque niveau de sort s'ouvre avec lui
    n = NEW_SPELL_LEVEL.get(lv)
    if n in SORTS:
        s += [f"AddSpells({SORTS[n]})"]
    if lv == 1:
        s += [f"SelectSpells({TOURS},3,0,CHR_TourChrono,,,AlwaysPrepared)"]
    if lv in (4, 10):
        s += [f"SelectSpells({TOURS},1,0,CHR_TourChrono,,,AlwaysPrepared)"]
    return b, p, r, s


# ================================================================== CLASSE
TABLE = U("table:" + C.CHRONO)
for lv in range(1, MAX_LEVEL + 1):
    b, p, r, s = level_features(lv)
    boosts = slot_boosts(lv) + b
    passives = unlock_passive(lv) + p
    if lv == 1:
        boosts = ["ProficiencyBonus(SavingThrow,Intelligence)", "ProficiencyBonus(SavingThrow,Dexterity)"] + \
                 ARMOR + boosts
        s = [f"SelectSkills({SKILLS},2)", f"SelectAbilityBonus({C.ALL_ABILITIES_LIST},AbilityBonus,2,1)"] + s
    progression(C.CHRONO, TABLE, lv, 0, boosts=boosts, passives=passives, removed=r, selectors=s,
                improvement=lv in FEATS)
# niveau 1 en multiclasse (sans sauvegardes ni compétences)
b, p, r, s = level_features(1)
progression(C.CHRONO, TABLE, 1, 0, boosts=ARMOR[:1] + slot_boosts(1) + b, passives=unlock_passive(1) + p,
            selectors=s, multiclass=True)

CLASSDESCS.append(Node("ClassDescription", [
    ("BaseHp", "int32", 8),
    ("CanLearnSpells", "bool", "false"),
    ("CharacterCreationPose", "guid", C.CC_POSE),
    ("ClassEquipment", "FixedString", EQUIPMENT),
    ("ClassHotbarColumns", "int32", 5),
    ("CommonHotbarColumns", "int32", 9),
    ("Description", "TranslatedString", L.add(f"class:{C.CHRONO}:desc",
        "Un mage qui plie le temps et l'espace : il accélère ses propres actions, rembobine les coups qui allaient "
        "tomber, ouvre des failles, écrase ses ennemis sous la gravité et les fait vieillir en un instant. À partir "
        "du niveau 14, il réécrit la réalité elle-même. Lanceur de sorts complet (Intelligence) qui prépare des "
        "sorts d'espace et de temps, plus ses propres sorts de dégâts.")),
    ("DisplayName", "TranslatedString", L.add(f"class:{C.CHRONO}:nom", "Chronomancien")),
    ("HpPerLevel", "int32", 5),
    ("ItemsHotbarColumns", "int32", 2),
    ("LearningStrategy", "uint8", 1),
    ("MulticlassSpellcasterModifier", "double", 1),
    ("MustPrepareSpells", "bool", "true"),
    ("Name", "FixedString", C.CHRONO),
    ("PrimaryAbility", "uint8", INTELLIGENCE),
    ("ProgressionTableUUID", "guid", TABLE),
    ("SoundClassType", "FixedString", "Wizard"),
    ("SpellCastingAbility", "uint8", INTELLIGENCE),
    ("UUID", "guid", U("class:" + C.CHRONO)),
]))
