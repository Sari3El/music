"""Progressions niveau par niveau, définitions de race et de classes, listes."""
import contenu as C
import contenu_domaines as D
from contenu import L, U, Node, guid_list_node, spelllist, passivelist

PROGRESSIONS = []
CLASSDESCS = []

# Emplacements de sort d'un lanceur complet : niveau -> {niveau de sort: emplacements gagnés}
SLOTS = {1: {1: 2}, 2: {1: 1}, 3: {1: 1, 2: 2}, 4: {2: 1}, 5: {3: 2}, 6: {3: 1}, 7: {4: 1},
         8: {4: 1}, 9: {4: 1, 5: 1}, 10: {5: 1}, 11: {6: 1}, 12: {}}
NEW_SPELL_LEVEL = {1: 1, 3: 2, 5: 3, 7: 4, 9: 5, 11: 6}   # niveau où un nouveau niveau de sort s'ouvre
MAX_SPELL_LEVEL = {lv: max(v for k, v in NEW_SPELL_LEVEL.items() if k <= lv) for lv in range(1, 13)}


def progression(name, table, level, ptype, boosts=(), passives=(), removed=(), selectors=(),
                improvement=False, multiclass=False, subclasses=None, key=None):
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
    attrs.append(("UUID", "guid", U(f"progression:{key or name}:{level}{':mc' if multiclass else ''}")))
    children = [guid_list_node("SubClasses", "SubClass", subclasses)] if subclasses else []
    PROGRESSIONS.append(Node("Progression", attrs, children))


def slot_boosts(level):
    return [f"ActionResource(SpellSlot,{n},{lvl})" for lvl, n in SLOTS[level].items()]


def unlock_passive(level):
    lvl = NEW_SPELL_LEVEL.get(level)
    return [f"UnlockedSpellSlotLevel{lvl}"] if lvl else []


def selector_label(selector_id, titre, desc):
    C.SELECTOR_LABELS.append((selector_id, titre, desc))


selector_label("DOC_TourOrdre", "Tours de magie de l'Ordre", "Choisissez vos tours de magie (liste du clerc).")
selector_label("DOC_TourChaos", "Tours de magie du Chaos", "Choisissez vos tours de magie (liste de l'ensorceleur).")
selector_label("DOC_TourOcculte", "Tour de magie occulte", "Choisissez un tour de magie d'occultiste.")
selector_label("DOC_SortChaos", "Sorts du Chaos", "Choisissez de nouveaux sorts (liste de l'ensorceleur).")
selector_label("DOC_MaitriseSorts", "Maîtrise des sorts",
               "Choisissez un sort que vous pourrez lancer sans emplacement, une fois par tour.")

# ================================================================== RACES : une Divinité par peuple du jeu
# Le jeu choisit visages et coiffures selon la RACE : chaque peuple a donc sa propre race « Divinité … »,
# copiée sur la race du jeu (couleurs, visages, corps), avec les mêmes sous-races que le jeu.
import json  # noqa: E402
import os  # noqa: E402

DONNEES_JEU = json.load(open(os.path.join(os.path.dirname(__file__), "donnees_jeu.json"), encoding="utf-8"))
ZERO = "00000000-0000-0000-0000-000000000000"
NOMS_RACES = {"Humain": "Divinité humaine", "Elfe": "Divinité elfe", "Drow": "Divinité drow",
              "DemiElfe": "Divinité demi-elfe", "Nain": "Divinité naine", "Halfelin": "Divinité halfeline",
              "Gnome": "Divinité gnome", "Tieffelin": "Divinité tieffeline", "Githyanki": "Divinité githyanki",
              "Drakeide": "Divinité drakéide", "DemiOrque": "Divinité demi-orque"}
LIST_NODES = ["SkinColors", "EyeColors", "HairColors", "HairHighlightColors", "HairGrayingColors",
              "TattooColors", "MakeupColors", "LipsMakeupColors", "HornColors", "HornTipColors", "Visuals", "Tags"]
CC_SLOTS = {"0": "Head", "1": "Hair", "2": "Horns", "3": "Beard", "5": "DragonbornTop", "6": "DragonbornChin",
            "7": "DragonbornJaw", "8": "Tail", "9": "Private Parts"}
RACE_DESC = L.add("race:desc",
    "Les Divinités sont de vrais dieux, tombés sur Faerûn. Ni mortels, ni esprits enfermés dans un corps : "
    "des dieux arrachés à leur royaume, privés de l'essentiel de leur puissance. Leur quête pour la "
    "retrouver les mène à la Porte de Baldur, là où la Couronne de Karsus – l'artefact de l'archimage "
    "qui osa voler la divinité de Mystryl – attire à elle tout ce qui touche au divin.\n\n"
    "Un dieu peut s'incarner sous les traits de n'importe quel peuple : choisissez la Divinité dont vous "
    "voulez l'apparence. Les pouvoirs divins sont les mêmes pour toutes ; les traits raciaux du peuple "
    "imité ne sont pas accordés.\n\n"
    "Vue divine, Volonté divine, Étincelle immortelle, Présence ; Injonction divine au niveau 3 ; "
    "Forme divine au niveau 5.")
FORME_DESC = L.add("race:forme:desc",
    "Variante d'apparence de ce peuple. Apparence uniquement : les pouvoirs divins sont les mêmes pour "
    "toutes les variantes.")

RACE_NODES, PRESET_NODES, APPEARANCE_NODES = [], [], []


def race_children(lists):
    return [Node(k, [("Object", "guid", g)]) for k in LIST_NODES for g in lists.get(k, [])]


def add_visuals(rows, race_uuid, key):
    for v in rows:
        if v["SlotName"] not in CC_SLOTS:
            continue
        attrs = [("BodyShape", "uint8", v.get("BodyShape", "0")), ("BodyType", "uint8", v.get("BodyType", "0"))]
        if v.get("DefaultSkinColor"):
            attrs.append(("DefaultSkinColor", "guid", v["DefaultSkinColor"]))
        attrs.append(("DisplayName", "TranslatedString", v["DisplayName"]))
        if v.get("IconIdOverride"):
            attrs.append(("IconIdOverride", "FixedString", v["IconIdOverride"]))
        attrs.append(("RaceUUID", "guid", race_uuid))
        if v.get("RootTemplate"):
            attrs.append(("RootTemplate", "guid", v["RootTemplate"]))
        attrs += [("SlotName", "FixedString", CC_SLOTS[v["SlotName"]]), ("UUID", "guid", U(f"ccav:{key}:{v['UUID']}")),
                  ("VisualResource", "guid", v["VisualResource"])]
        APPEARANCE_NODES.append(Node("CharacterCreationAppearanceVisual", attrs))


def add_presets(bodies, race_uuid, sub_uuid, key):
    for c in bodies:
        PRESET_NODES.append(Node("CharacterCreationPreset", [
            ("BodyShape", "uint8", c.get("BodyShape", "0")), ("BodyType", "uint8", c["BodyType"]),
            ("CloseUpA", "LSString", c["CloseUpA"]), ("CloseUpB", "LSString", c["CloseUpB"]),
            ("Overview", "LSString", c["Overview"]), ("RaceUUID", "guid", race_uuid),
            ("RootTemplate", "guid", c["RootTemplate"]), ("SubRaceUUID", "guid", sub_uuid),
            ("UUID", "guid", U(f"preset:{key}:{c['BodyType']}:{c.get('BodyShape', '0')}")),
            ("VOLinesTableUUID", "guid", c["VOLinesTableUUID"]),
        ]))


def optional(data):
    out = []
    if data.get("RaceEquipment"):
        out.append(("RaceEquipment", "FixedString", data["RaceEquipment"]))
    if data.get("RaceSoundSwitch"):
        out.append(("RaceSoundSwitch", "FixedString", data["RaceSoundSwitch"]))
    return out


for bnom, data in DONNEES_JEU.items():
    name = f"{C.RACE}_{bnom}"
    race_uuid = U("race:" + name)
    table = U("table:race:" + bnom)
    progression(name, table, 1, 2,
                boosts=["ActionResource(Movement,9,0)", "ProficiencyBonus(Skill,Religion)",
                        "ProficiencyBonus(Skill,Intimidation)"],
                passives=["DOC_Race_Marqueur", "DOC_Race_VueDivine", "DOC_Race_VolonteDivine",
                          "DOC_Race_EtincelleImmortelle"],
                selectors=[f"AddSpells({C.RACE_L1},,,,AlwaysPrepared)",
                           f"SelectAbilityBonus({C.ALL_ABILITIES_LIST},AbilityBonus,2,1)"])
    progression(name, table, 3, 2, selectors=[f"AddSpells({C.RACE_L3},,,,AlwaysPrepared)"])
    progression(name, table, 5, 2, selectors=[f"AddSpells({C.RACE_L5},,,,AlwaysPrepared)"])
    RACE_NODES.append(Node("Race", [
        ("Description", "TranslatedString", RACE_DESC),
        ("DisplayName", "TranslatedString", L.add(f"race:{bnom}:nom", NOMS_RACES[bnom])),
        ("DisplayTypeUUID", "guid", C.HUMANOID), ("Name", "FixedString", name),
        ("ParentGuid", "guid", C.HUMANOID), ("ProgressionTableUUID", "guid", table),
    ] + optional(data) + [("UUID", "guid", race_uuid)], race_children(data["listes"])))
    add_visuals(data["visuels"], race_uuid, bnom)
    add_presets(data["corps"], race_uuid, ZERO, bnom)
    for sub in data["sous_races"]:
        sname = f"{name}_{sub['code']}"
        sub_uuid = U("race:" + sname)
        RACE_NODES.append(Node("Race", [
            ("Description", "TranslatedString", FORME_DESC),
            ("DisplayName", "TranslatedString", sub["nom_jeu"]),  # nom du jeu, traduit automatiquement
            ("DisplayTypeUUID", "guid", C.HUMANOID), ("Name", "FixedString", sname),
            ("ParentGuid", "guid", race_uuid),
        ] + optional(sub) + [("UUID", "guid", sub_uuid)], race_children(sub["listes"])))
        add_visuals(sub["visuels"], sub_uuid, sname)
        add_presets(sub["corps"], race_uuid, sub_uuid, sname)

# ================================================================== LISTES COMMUNES
ORDRE_SKILLS = U("skilllist:ordre")
CHAOS_SKILLS = U("skilllist:chaos")
C.SKILLLISTS.append(("ordre", ["History", "Insight", "Medicine", "Persuasion", "Religion", "Intimidation"]))
C.SKILLLISTS.append(("chaos", ["Arcana", "Deception", "Intimidation", "Insight", "Persuasion", "Religion"]))

CREATRICE_SKILLS = U("skilllist:creatrice")
C.SKILLLISTS.append(("creatrice", ["Acrobatics", "AnimalHandling", "Arcana", "Athletics", "Deception", "History",
                                   "Insight", "Intimidation", "Investigation", "Medicine", "Nature", "Perception",
                                   "Performance", "Persuasion", "Religion", "SleightOfHand", "Stealth", "Survival"]))

MAITRISE_RES = U("resource:DOC_MaitriseSorts")


import functools  # noqa: E402


@functools.lru_cache(maxsize=None)
def domain_lists(dom):
    """Listes des sorts de domaine toujours préparés, par niveau de personnage."""
    return {lv: spelllist(f"DOC_{dom}_Domaine_{lv}", f"{dom} : sorts de domaine (niveau {lv})", spells)
            for lv, spells in D.DOMAIN_SPELLS[dom].items()}


@functools.lru_cache(maxsize=None)
def feature_lists(dom):
    out = {}
    for lv, f in D.FEATURES[dom].items():
        if f["spells"]:
            out[lv] = spelllist(f"DOC_{dom}_Capacites_{lv}", f"{dom} : capacités (niveau {lv})", f["spells"])
    return out


# ================================================================== CLASSES
CLASSES = {
    C.ORDRE: dict(
        titre="Divinité de l'Ordre", ability=5, saves=("Wisdom", "Constitution"),
        desc="Un dieu de la loi, de la protection et de la certitude. L'Ordre élève le plancher : vos jets ne "
             "tombent jamais trop bas, vos décrets protègent vos alliés et enchaînent vos ennemis. Lanceur de "
             "sorts complet (Sagesse) avec les sorts du clerc et du paladin, plus des sorts exclusifs.",
        armor=["Proficiency(LightArmor)", "Proficiency(MediumArmor)", "Proficiency(Shields)",
               "Proficiency(SimpleWeapons)"],
        equipment="EQP_CC_DOC_DiviniteOrdre", sound="Cleric", skills=ORDRE_SKILLS,
        prepare=True, excl=C.ORDRE_EXCL_LISTS, l12=C.ORDRE_L12,
        dist=dict(Strength=13, Dexterity=10, Constitution=14, Intelligence=8, Wisdom=15, Charisma=12)),
    C.CHAOS: dict(
        titre="Divinité du Chaos", ability=6, saves=("Charisma", "Dexterity"),
        desc="Un dieu du changement, de la ruine et du hasard. Le Chaos élève le plafond : coups critiques "
             "fréquents, déferlements de magie imprévisibles, dégâts dévastateurs. Lanceur de sorts complet "
             "(Charisme) avec les sorts de l'ensorceleur et les tours de l'occultiste, plus des sorts exclusifs.",
        armor=["Proficiency(LightArmor)", "Proficiency(SimpleWeapons)", "Proficiency(Rapiers)",
               "Proficiency(Shortswords)", "Proficiency(Scimitars)"],
        equipment="EQP_CC_DOC_DiviniteChaos", sound="Sorcerer", skills=CHAOS_SKILLS,
        prepare=False, excl=C.CHAOS_EXCL_LISTS, l12=C.CHAOS_L12,
        dist=dict(Strength=8, Dexterity=14, Constitution=13, Intelligence=10, Wisdom=12, Charisma=15)),
    C.CREATRICE: dict(
        titre="Divinité Créatrice", ability=6, saves=("Strength", "Dexterity", "Constitution", "Intelligence",
                                                     "Wisdom", "Charisma"),
        desc="Le dieu d'avant l'Ordre et le Chaos, celui qui a tout façonné. La Créatrice réunit les pouvoirs "
             "des deux sans leurs contreparties : la fiabilité de l'Ordre (Loi absolue, Décrets, Inébranlable), "
             "la puissance du Chaos (critiques étendus, Entropie, Indomptable), toutes les armures et toutes les "
             "armes. Elle peut préparer n'importe quel sort du jeu, toutes classes confondues, et dispose de "
             "5 emplacements dès qu'un niveau de sort s'ouvre. Lanceur de sorts complet (Charisme).",
        armor=["Proficiency(LightArmor)", "Proficiency(MediumArmor)", "Proficiency(HeavyArmor)",
               "Proficiency(Shields)", "Proficiency(SimpleWeapons)", "Proficiency(MartialWeapons)"],
        equipment="EQP_CC_DOC_DiviniteCreatrice", sound="Cleric", skills=CREATRICE_SKILLS, nskills=4,
        prepare=True, excl=None, l12=None, hp=(12, 7), slots=5, contrepoids=False,
        dist=dict(Strength=13, Dexterity=12, Constitution=14, Intelligence=8, Wisdom=10, Charisma=15)),
}
SUBCLASS_SELECTION_LEVEL = 1


def class_level_features(cls, lv):
    """(boosts, passives, removed, selectors) propres à la classe au niveau lv."""
    b, p, r, s = [], [], [], []
    if cls == C.ORDRE:
        if lv == 1:
            p += ["DOC_Classe_Marqueur", "DOC_Ordre_LoiAbsolue_5", "DOC_Ordre_DivinitePure"]
        if lv == 2:
            b += ["ActionResource(DOC_Decret,2,0)"]
            p += ["DOC_Ordre_Decrets"]
            s += [f"AddSpells({C.ORDRE_DECRETS},,,,AlwaysPrepared)"]
        if lv == 6:
            b += ["ActionResource(DOC_Decret,1,0)"]
            p += ["DOC_Ordre_LoiAbsolue_8", "DOC_Ordre_Aura_1"]
            r += ["DOC_Ordre_LoiAbsolue_5"]
        if lv == 7:
            p += ["DOC_Ordre_Inebranlable"]
        if lv == 10:
            b += ["ActionResource(DOC_Decret,1,0)"]
            p += ["DOC_Ordre_Aura_2"]
            r += ["DOC_Ordre_Aura_1"]
        if lv == 11:
            p += ["DOC_Ordre_LoiAbsolue_10", "DOC_Ordre_Aura_3"]
            r += ["DOC_Ordre_LoiAbsolue_8", "DOC_Ordre_Aura_2"]
        # sorts : listes du clerc et du paladin (à préparer) + exclusifs toujours préparés
        if lv in NEW_SPELL_LEVEL:
            n = NEW_SPELL_LEVEL[lv]
            s += [f"AddSpells({C.CLERIC_SPELLS[n]})"]
            if n in C.PALADIN_SPELLS:
                s += [f"AddSpells({C.PALADIN_SPELLS[n]})"]
        if lv == 1:
            s += [f"SelectSpells({C.CLERIC_CANTRIPS},3,0,DOC_TourOrdre,,,AlwaysPrepared)"]
        if lv in (4, 10):
            s += [f"SelectSpells({C.CLERIC_CANTRIPS},1,0,DOC_TourOrdre,,,AlwaysPrepared)"]
    elif cls == C.CREATRICE:
        return creatrice_level_features(lv)
    else:
        if lv == 1:
            p += ["DOC_Classe_Marqueur", "DOC_Chaos_Critique_19", "DOC_Chaos_Deferlement", "DOC_Chaos_UnNaturel",
                  "DOC_Chaos_DivinitePure"]
        if lv == 2:
            b += ["ActionResource(DOC_Entropie,3,0)"]
            p += ["DOC_Chaos_EntropieGain", "DOC_Chaos_EntropieReset"]
            s += [f"AddSpells({C.CHAOS_ENTROPIE},,,,AlwaysPrepared)"]
        if lv == 6:
            b += ["ActionResource(DOC_Entropie,1,0)"]
            p += ["DOC_Chaos_Critique_18", "DOC_Chaos_Aura_1"]
            r += ["DOC_Chaos_Critique_19"]
        if lv == 7:
            p += ["DOC_Chaos_Indomptable"]
        if lv == 10:
            b += ["ActionResource(DOC_Entropie,1,0)"]
            p += ["DOC_Chaos_Aura_2"]
            r += ["DOC_Chaos_Aura_1"]
        if lv == 11:
            p += ["DOC_Chaos_Critique_17"]
            r += ["DOC_Chaos_Critique_18"]
        if lv == 12:
            p += ["DOC_Chaos_TempetePrimordiale"]
        # sorts connus : liste de l'ensorceleur (cumulative jusqu'au niveau de sort maximum)
        sl = C.SORCERER_SPELLS[MAX_SPELL_LEVEL[lv]]
        if lv == 1:
            s += [f"SelectSpells({sl},2,0,DOC_SortChaos)",
                  f"SelectSpells({C.SORCERER_CANTRIPS},4,0,DOC_TourChaos,,,AlwaysPrepared)",
                  f"SelectSpells({C.WARLOCK_CANTRIPS},1,0,DOC_TourOcculte,,,AlwaysPrepared)"]
        elif lv <= 11:
            s += [f"SelectSpells({sl},1,1,DOC_SortChaos)"]
        if lv in (4, 10):
            s += [f"SelectSpells({C.SORCERER_CANTRIPS},1,0,DOC_TourChaos,,,AlwaysPrepared)"]
    if lv in NEW_SPELL_LEVEL:
        excl = CLASSES[cls]["excl"][NEW_SPELL_LEVEL[lv]]
        s += [f"AddSpells({excl},,,,AlwaysPrepared)"]
    if lv == 12:
        s += [f"AddSpells({CLASSES[cls]['l12']},,,,AlwaysPrepared)"]
    return b, p, r, s


def creatrice_level_features(lv):
    """Divinité Créatrice : socles de l'Ordre ET du Chaos, sans malus (ni Contrepoids, ni magie sauvage)."""
    b, p, r, s = [], [], [], []
    for cls in (C.ORDRE, C.CHAOS):
        cb, cp, cr, cs = class_level_features(cls, lv)
        b += cb
        r += cr
        p += [x for x in cp if x not in ("DOC_Chaos_Deferlement", "DOC_Chaos_UnNaturel", "DOC_Ordre_DivinitePure",
                                         "DOC_Chaos_DivinitePure") and x not in p]
        # on garde les capacités de classe (Décrets, Entropie, sorts exclusifs, niveau 12),
        # mais pas les sorts de clerc/ensorceleur : la Créatrice a sa propre liste, plus large
        s += [x for x in cs if "DOC_Tour" not in x and "DOC_SortChaos" not in x
              and not any(g in x for g in list(C.CLERIC_SPELLS.values()) + list(C.PALADIN_SPELLS.values()))]
    if lv == 1:
        p += ["DOC_Creatrice_Deferlement", "DOC_Creatrice_DivinitePure"]
    # n'importe quel sort du jeu : toutes les listes de toutes les classes, à préparer
    if lv in NEW_SPELL_LEVEL:
        s += [f"AddSpells({g})" for g in C.all_class_lists(NEW_SPELL_LEVEL[lv])]
    if lv == 1:
        s += [f"SelectSpells({g},{2 if g == C.WIZARD_CANTRIPS else 1},0,DOC_TourCreation,,,AlwaysPrepared)"
              for g in C.ALL_CANTRIP_LISTS]
    if lv in (4, 10):
        s += [f"SelectSpells({C.WIZARD_CANTRIPS},1,0,DOC_TourCreation,,,AlwaysPrepared)",
              f"SelectSpells({C.SORCERER_CANTRIPS},1,0,DOC_TourCreation,,,AlwaysPrepared)"]
    return b, p, r, s


def class_slot_boosts(info, lv):
    """Lanceur complet ; la Créatrice a d'emblée 5 emplacements à chaque nouveau niveau de sort."""
    if not info.get("slots"):
        return slot_boosts(lv)
    n = NEW_SPELL_LEVEL.get(lv)
    return [f"ActionResource(SpellSlot,{info['slots']},{n})"] if n else []


selector_label("DOC_TourCreation", "Tours de magie de la Création",
               "Choisissez vos tours de magie, dans les listes de toutes les classes.")

for cls, info in CLASSES.items():
    table = U("table:" + cls)
    if cls == C.CREATRICE:
        subclass_uuids = [U("class:DOC_Creatrice_" + d) for d in C.DOMAINES]
    else:
        subclass_uuids = [U("class:DOC_" + d) for d, v in C.DOMAINES.items() if v[0] == cls]
    for lv in range(1, 13):
        b, p, r, s = class_level_features(cls, lv)
        boosts = class_slot_boosts(info, lv) + b
        passives = unlock_passive(lv) + p
        if lv == 1:
            boosts = [f"ProficiencyBonus(SavingThrow,{sv})" for sv in info["saves"]] + info["armor"] + boosts
            sel = [f"SelectSkills({info['skills']},{info.get('nskills', 2)})",
                   f"SelectAbilityBonus({C.ALL_ABILITIES_LIST},AbilityBonus,2,1)"] + s
        else:
            sel = s
        progression(cls, table, lv, 0, boosts=boosts, passives=passives, removed=r, selectors=sel,
                    improvement=lv in (4, 8, 12),
                    subclasses=subclass_uuids if lv == SUBCLASS_SELECTION_LEVEL else None)
    # niveau 1 en multiclasse (sans sauvegardes ni compétences)
    b, p, r, s = class_level_features(cls, 1)
    progression(cls, table, 1, 0, boosts=info["armor"][:3] + class_slot_boosts(info, 1) + b, passives=unlock_passive(1) + p,
                selectors=s, multiclass=True, subclasses=subclass_uuids)

    CLASSDESCS.append(Node("ClassDescription", [
        ("BaseHp", "int32", info.get("hp", (10, 6))[0]),
        ("CanLearnSpells", "bool", "true" if cls == C.CREATRICE else "false"),
        ("CharacterCreationPose", "guid", C.CC_POSE),
        ("ClassEquipment", "FixedString", info["equipment"]),
        ("ClassHotbarColumns", "int32", 5),
        ("CommonHotbarColumns", "int32", 9),
        ("Description", "TranslatedString", L.add(f"class:{cls}:desc", info["desc"])),
        ("DisplayName", "TranslatedString", L.add(f"class:{cls}:nom", info["titre"])),
        ("HpPerLevel", "int32", info.get("hp", (10, 6))[1]),
        ("ItemsHotbarColumns", "int32", 2),
        ("LearningStrategy", "uint8", 1),
        ("MulticlassSpellcasterModifier", "double", 1),
        ("MustPrepareSpells", "bool", "true" if info["prepare"] else "false"),
        ("Name", "FixedString", cls),
        ("PrimaryAbility", "uint8", info["ability"]),
        ("ProgressionTableUUID", "guid", table),
        ("SoundClassType", "FixedString", info["sound"]),
        ("SpellCastingAbility", "uint8", info["ability"]),
        ("SubclassTitle", "TranslatedString", L.add(f"class:{cls}:subtitle", "Domaine divin")),
        ("UUID", "guid", U("class:" + cls)),
    ]))

# ================================================================== DOMAINES (sous-classes)
DOMAIN_DESC = {
    "Vie": "La vie déborde de vous : soins renforcés, fil de vie qui retient vos alliés, aura de guérison et "
           "renaissance de groupe. Affinité : radiant.",
    "Justice": "Vous marquez les coupables et la foudre les juge : marque du jugement, vision véritable, "
               "rétribution et verdict final. Affinité : foudre.",
    "Magie": "Vous êtes l'arbitre de la Trame : codex, contresort gratuit, concentration inébranlable et sorts "
             "maîtrisés. Affinité : force.",
    "Soleil": "Le feu du soleil vous obéit : il ignore les résistances, aveugle, brûle les ennemis autour de "
              "vous et finit en supernova. Affinité : feu.",
    "Paix": "Vous liez vos alliés et désarmez vos ennemis : lien de paix, apaisement, lien protecteur et "
            "armistice. Affinité : psychique.",
    "Mort": "Vous moissonnez les âmes : PV volés aux morts, serviteurs mort-vivants, soins empêchés et retour "
            "d'outre-tombe. Affinité : nécrotique.",
    "Tromperie": "Mensonges, illusions et poisons : double illusoire, escamotage, langue d'argent et "
                 "marionnettiste. Affinité : poison.",
    "Sorcellerie": "Le chaos à l'état pur : marées du chaos, métamagie nourrie par l'entropie, déferlements "
                   "maîtrisés et tempête arcanique. Affinité : acide.",
    "Lune": "Les phases de la lune guident vos pouvoirs : pas de l'ombre, bête lunaire et éclipse glacée. "
            "Affinité : froid.",
    "Guerre": "Vous êtes né pour la guerre : armures lourdes, attaque supplémentaire, cri de guerre, carnage et "
              "incarnation de la guerre. Affinité : tonnerre.",
}

for dom, (cls, titre, dt, opp, fr) in C.DOMAINES.items():
    name = f"DOC_{cls.split('Divinite')[1]}_{dom}"
    table = U("table:sub:" + dom)
    dlists = domain_lists(dom)
    flists = feature_lists(dom)
    levels = sorted(set(dlists) | set(D.FEATURES[dom]))
    for lv in levels:
        f = D.FEATURES[dom].get(lv, {"passives": [], "removed": [], "spells": [], "boosts": [], "selectors": []})
        sel = []
        if lv in dlists:
            sel.append(f"AddSpells({dlists[lv]},,,,AlwaysPrepared)")
        if lv in flists:
            sel.append(f"AddSpells({flists[lv]},,,,AlwaysPrepared)")
        sel += f["selectors"]
        if dom == "Magie" and lv == 10:
            sel += [f"SelectSpells({C.CLERIC_SPELLS[1]},1,0,DOC_MaitriseSorts,,{MAITRISE_RES},AlwaysPrepared)",
                    f"SelectSpells({C.CLERIC_SPELLS[2]},1,0,DOC_MaitriseSorts,,{MAITRISE_RES},AlwaysPrepared)"]
            f = dict(f, boosts=f["boosts"] + ["ActionResource(DOC_MaitriseSorts,1,0)"])
        progression(name, table, lv, 1, boosts=f["boosts"], passives=f["passives"], removed=f["removed"],
                    selectors=sel, key=name)
    CLASSDESCS.append(Node("ClassDescription", [
        ("CanLearnSpells", "bool", "true" if dom == "Magie" else "false"),
        ("CharacterCreationPose", "guid", C.CC_POSE),
        ("Description", "TranslatedString", L.add(f"class:{name}:desc", DOMAIN_DESC[dom])),
        ("DisplayName", "TranslatedString", L.add(f"class:{name}:nom", titre)),
        ("LearningStrategy", "uint8", 1),
        ("MustPrepareSpells", "bool", "true" if cls == C.ORDRE else "false"),
        ("Name", "FixedString", name),
        ("ParentGuid", "guid", U("class:" + cls)),
        ("PrimaryAbility", "uint8", CLASSES[cls]["ability"]),
        ("ProgressionTableUUID", "guid", table),
        ("ShortName", "TranslatedString", L.add(f"class:{name}:court", dom)),
        ("SoundClassType", "FixedString", CLASSES[cls]["sound"]),
        ("SpellCastingAbility", "uint8", CLASSES[cls]["ability"]),
        ("UUID", "guid", U("class:DOC_" + dom)),
    ]))

# ================================================================== DOMAINES DE LA CRÉATRICE
# Les 10 domaines, mêmes capacités, sans le Contrepoids (aucun malus).
for dom, (cls, titre, dt, opp, fr) in C.DOMAINES.items():
    name = f"DOC_Creatrice_{dom}"
    table = U("table:sub:creatrice:" + dom)
    dlists = domain_lists(dom)
    flists = feature_lists(dom)
    for lv in sorted(set(dlists) | set(D.FEATURES[dom])):
        f = D.FEATURES[dom].get(lv, {"passives": [], "removed": [], "spells": [], "boosts": [], "selectors": []})
        sel = []
        if lv in dlists:
            sel.append(f"AddSpells({dlists[lv]},,,,AlwaysPrepared)")
        if lv in flists:
            sel.append(f"AddSpells({flists[lv]},,,,AlwaysPrepared)")
        sel += f["selectors"]
        boosts = f["boosts"]
        if dom == "Magie" and lv == 10:
            sel += [f"SelectSpells({C.CLERIC_SPELLS[1]},1,0,DOC_MaitriseSorts,,{MAITRISE_RES},AlwaysPrepared)",
                    f"SelectSpells({C.CLERIC_SPELLS[2]},1,0,DOC_MaitriseSorts,,{MAITRISE_RES},AlwaysPrepared)"]
            boosts = boosts + ["ActionResource(DOC_MaitriseSorts,1,0)"]
        passives = [x for x in f["passives"] if not x.endswith("_Contrepoids")]
        progression(name, table, lv, 1, boosts=boosts, passives=passives, removed=f["removed"],
                    selectors=sel, key=name)
    CLASSDESCS.append(Node("ClassDescription", [
        ("CanLearnSpells", "bool", "true"),
        ("CharacterCreationPose", "guid", C.CC_POSE),
        ("Description", "TranslatedString", L.add(f"class:{name}:desc",
                                                  DOMAIN_DESC[dom] + " Sans contrepoids.")),
        ("DisplayName", "TranslatedString", L.add(f"class:{name}:nom", titre)),
        ("LearningStrategy", "uint8", 1),
        ("MustPrepareSpells", "bool", "true"),
        ("Name", "FixedString", name),
        ("ParentGuid", "guid", U("class:" + C.CREATRICE)),
        ("PrimaryAbility", "uint8", CLASSES[C.CREATRICE]["ability"]),
        ("ProgressionTableUUID", "guid", table),
        ("ShortName", "TranslatedString", L.add(f"class:{name}:court", dom)),
        ("SoundClassType", "FixedString", CLASSES[C.CREATRICE]["sound"]),
        ("SpellCastingAbility", "uint8", CLASSES[C.CREATRICE]["ability"]),
        ("UUID", "guid", U("class:" + name)),
    ]))
