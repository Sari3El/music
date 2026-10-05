"""Contenu du mod « Divinités de l'Ordre et du Chaos ».

Ce fichier décrit TOUT le mod : race, classes, domaines, sorts, états,
réactions et progressions. build_mod.py le transforme en fichiers de jeu.

Conventions :
- préfixe DOC_ sur tout ce qui est créé par le mod (évite les conflits) ;
- sorts : <Type>_DOC_<Nom> (Target_, Shout_, Projectile_, Zone_) ;
- états : DOC_<NOM> en majuscules ; réactions : Interrupt_DOC_<Nom>.
- les sorts exclusifs dérivent (« using ») d'un sort du jeu de base pour
  récupérer animations, sons et effets visuels.
"""
from doclib import Entry, Loca, Node, U, guid_list_node

L = Loca()
STATS = []          # toutes les entrées de stats
LEVELMAPS = []      # (nom, {niveau: valeur})
SPELLLISTS = []     # (nom, commentaire, [sorts])
PASSIVELISTS = []   # (nom, [passifs])
SKILLLISTS = []     # (nom, [compétences])
OUTCOMES = []       # (groupe, sort) pour les déferlements aléatoires
RESOURCES = []      # (nom, titre, description, recharge)
PROGRESSIONS = []   # Node
CLASSDESCS = []     # Node
SELECTOR_LABELS = []  # (SelectorId, titre, description)

# ------------------------------------------------------------------ jeu de base
HUMAN = "0eb594cb-8820-4be6-a58d-8be7a1a98fba"
HUMANOID = "899d275e-9893-490a-9cd5-be856794929f"
ALL_ABILITIES_LIST = "b9149c8e-52c8-46e5-9cb6-fc39301c05fe"
CC_POSE = "0f07ec6e-4ef0-434e-9a51-1353260ccff8"

CLERIC_CANTRIPS = "2f43a103-5bf1-4534-b14f-663decc0c525"
CLERIC_SPELLS = {1: "269d1a3b-eed8-4131-8901-a562238f5289", 2: "2968a3e6-6c8a-4c2e-882a-ad295a2ad8ac",
                 3: "21be0992-499f-4c7a-a77a-4430085e947a", 4: "37e9b20b-5fd1-45c5-b1c5-159c42397c83",
                 5: "b73aeea5-1ff9-4cac-b61d-b5aa6dfe31c2", 6: "f8ba7b05-1237-4eaa-97fa-1d3623d5862b"}
PALADIN_SPELLS = {1: "c6288ac5-c68b-40ed-bbdd-2ff388575831", 2: "c14c9564-1503-47a1-be19-98e77f22ff59"}
SORCERER_CANTRIPS = "485a68b4-c678-4888-be63-4a702efbe391"
SORCERER_SPELLS = {1: "92c4751f-6255-4f67-822c-a75d53830b27", 2: "f80396e2-cb76-4694-b0db-5c34da61a478",
                   3: "dcbaf2ae-1f45-453e-ab83-cd154f8277a4", 4: "5fe40622-1d3e-4cc1-8d89-e66fe51d8c5c",
                   5: "3276fcfe-e143-4559-b6e0-7d7aa0ffcb53", 6: "1270a6db-980b-4e3b-bf26-2924da61dfd5"}
WARLOCK_CANTRIPS = "f5c4af9c-5d8d-4526-9057-94a4b243cd40"
METAMAGIC_LIST = "49704931-e47b-4ce6-abc6-dfa7ba640752"
# Autres classes (source : BG3 Community Library, IdDictionary) — pour la Divinité Créatrice
WIZARD_CANTRIPS = "3cae2e56-9871-4cef-bba6-96845ea765fa"
WIZARD_SPELLS = {1: "11f331b0-e8b7-473b-9d1f-19e8e4178d7d", 2: "80c6b070-c3a6-4864-84ca-e78626784eb4",
                 3: "22755771-ca11-49f4-b772-13d8b8fecd93", 4: "820b1220-0385-426d-ae15-458dc8a6f5c0",
                 5: "f781a25e-d288-43b4-bf5d-3d8d98846687", 6: "bc917f22-7f71-4a25-9a77-7d2f91a96a65"}
DRUID_CANTRIPS = "b8faf12f-ca42-45c0-84f8-6951b526182a"
DRUID_SPELLS = {1: "2cd54137-2fe5-4100-aad3-df64735a8145", 2: "92126d17-7f1a-41d2-ae6c-a8d254d2b135",
                3: "3156daf5-9266-41d0-b52c-5bc559a98654", 4: "09c326c9-672c-4198-a4c0-6f07323bde27",
                5: "ff711c12-b59f-4fde-b9ea-6e5c38ec8f23", 6: "6a4e2167-55f3-4ba8-900f-14666b293e93"}
BARD_CANTRIPS = "61f79a30-2cac-4a7a-b5fe-50c89d307dd6"
BARD_SPELLS = {1: "dcb45167-86bd-4297-9b9d-c295be51af5b", 2: "7ea8f476-97a1-4256-8f10-afa76a845cce",
               3: "c213ca01-3767-457b-a5c8-fd4c1dd656e2", 4: "75e04c40-be8f-40a5-9acc-0b5d59d5f3a6",
               5: "bd71fffb-e4d2-4233-9a31-13d43fba36e3", 6: "586a8796-34f4-41f5-a3ef-95738561d55d"}
RANGER_SPELLS = {1: "458be063-60d4-4548-ae7d-50117fa0226f", 2: "e7cfb80a-f5c2-4304-8446-9b00ea6a9814",
                 3: "9a60f649-7f82-4152-90b1-0499c5c9f3e2"}
# listes complètes de l'occultiste, une par protecteur (Fée, Fiélon, Grand Ancien)
WARLOCK_SPELLS = {
    1: ["e0099b15-2599-4cba-a54b-b25ae03d6519", "4823a292-f584-4f7f-8434-6630c72e5411", "65952d48-bb16-4ad7-b173-532182bf7770"],
    2: ["0cc2c8ab-9bbc-43a7-a66d-08e47da4c172", "835aeca7-c64a-4aaa-a25c-143aa14a5cec", "fe101a94-8619-49b2-859d-a68c2c291054"],
    3: ["f18ad912-e2f4-47a9-8744-73d6a51c2941", "5dec41aa-f16a-434e-b209-50c07e64e4ed", "30e9b761-6be0-418e-bb28-5103c00c663b"],
    4: ["c3d8a4a5-9dae-4193-8322-a5d1c5b89f47", "7ad7dbd0-751b-4bcd-8034-53bcc7bfb19d", "b64e527e-1f97-4125-84f7-78376ab1440b"],
    5: ["0a9b924f-64fb-4f22-b975-5eeedc99b2fd", "deab57bf-4eec-4085-82f7-87335bce3f5d", "6d2edca9-71a7-4f3f-89f0-fccfff0bdee5"]}


def all_class_lists(n):
    """Toutes les listes de sorts de niveau n du jeu (toutes classes)."""
    out = []
    for d in (CLERIC_SPELLS, PALADIN_SPELLS, SORCERER_SPELLS, WIZARD_SPELLS, DRUID_SPELLS, BARD_SPELLS, RANGER_SPELLS):
        if n in d:
            out.append(d[n])
    return out + WARLOCK_SPELLS.get(n, [])


ALL_CANTRIP_LISTS = [CLERIC_CANTRIPS, SORCERER_CANTRIPS, WARLOCK_CANTRIPS, WIZARD_CANTRIPS, DRUID_CANTRIPS,
                     BARD_CANTRIPS]

ORDRE = "DOC_DiviniteOrdre"
CHAOS = "DOC_DiviniteChaos"
CREATRICE = "DOC_DiviniteCreatrice"
RACE = "DOC_Divinite"

# Domaines : nom interne -> (classe, titre, type de dégâts, type opposé, nom FR du type)
DOMAINES = {
    "Vie":         (ORDRE, "Domaine de la Vie",          "Radiant",   "Necrotic",  "radiants"),
    "Justice":     (ORDRE, "Domaine de la Justice",      "Lightning", "Poison",    "de foudre"),
    "Magie":       (ORDRE, "Domaine de la Magie",        "Force",     "Acid",      "de force"),
    "Soleil":      (ORDRE, "Domaine du Soleil",          "Fire",      "Cold",      "de feu"),
    "Paix":        (ORDRE, "Domaine de la Paix",         "Psychic",   "Thunder",   "psychiques"),
    "Mort":        (CHAOS, "Domaine de la Mort",         "Necrotic",  "Radiant",   "nécrotiques"),
    "Tromperie":   (CHAOS, "Domaine de la Tromperie",    "Poison",    "Lightning", "de poison"),
    "Sorcellerie": (CHAOS, "Domaine de la Sorcellerie",  "Acid",      "Force",     "d'acide"),
    "Lune":        (CHAOS, "Domaine de la Lune",         "Cold",      "Fire",      "de froid"),
    "Guerre":      (CHAOS, "Domaine de la Guerre",       "Thunder",   "Psychic",   "de tonnerre"),
}
TYPE_FR = {"Radiant": "radiants", "Necrotic": "nécrotiques", "Lightning": "de foudre", "Poison": "de poison",
           "Force": "de force", "Acid": "d'acide", "Fire": "de feu", "Cold": "de froid",
           "Psychic": "psychiques", "Thunder": "de tonnerre"}
TYPE_NOM = {"Radiant": "radiant", "Necrotic": "nécrotique", "Lightning": "foudre", "Poison": "poison",
            "Force": "force", "Acid": "acide", "Fire": "feu", "Cold": "froid",
            "Psychic": "psychique", "Thunder": "tonnerre"}
ICONE_TYPE = {"Radiant": "PassiveFeature_LathandersLight", "Necrotic": "PassiveFeature_Generic_Death",
              "Lightning": "PassiveFeature_HeartOfTheStorm_Lightning",
              "Poison": "PassiveFeature_NaturalExplorer_WastelandWanderer_Poison",
              "Force": "PassiveFeature_ArcaneWard", "Acid": "PassiveFeature_ElementalAdept_Acid",
              "Fire": "PassiveFeature_ElementalAdept_Fire", "Cold": "PassiveFeature_ElementalAdept_Cold",
              "Psychic": "PassiveFeature_ThoughtShield_PsychicResistance",
              "Thunder": "PassiveFeature_ElementalAdept_Thunder"}

SCHOOLS = ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion",
           "Necromancy", "Transmutation"]
DAMAGE_TYPES = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing",
                "Poison", "Psychic", "Radiant", "Slashing", "Thunder"]


# ------------------------------------------------------------------ fabriques
def add(e):
    STATS.append(e)
    return e


def passive(name, titre, desc, icon, props="Highlighted", **data):
    return add(Entry(name, "PassiveData", DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, Properties=props, **data))


def hidden(name, **data):
    return add(Entry(name, "PassiveData", DisplayName=L.ref(name + ":nom", name), Properties="IsHidden", **data))


def status(name, titre, desc, icon, using=None, stype="BOOST", **data):
    data.setdefault("StatusPropertyFlags", "")
    if data["StatusPropertyFlags"] == "":
        del data["StatusPropertyFlags"]
    return add(Entry(name, "StatusData", using, StatusType=stype, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, **data))


def spell(name, stype, titre, desc, using=None, **data):
    return add(Entry(name, "SpellData", using, SpellType=stype, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), **data))


def interrupt(name, titre, desc, icon, using=None, **data):
    return add(Entry(name, "InterruptData", using, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, **data))


def palier(name, l1, l5, l9, l12):
    """Valeur qui grandit aux paliers 5, 9 et 12 (niveau du personnage)."""
    LEVELMAPS.append((name, {1: l1, 5: l5, 9: l9, 12: l12}))
    return f"LevelMapValue({name})"


def spelllist(name, comment, spells):
    SPELLLISTS.append((name, comment, spells))
    return U("spelllist:" + name)


def passivelist(name, passives):
    PASSIVELISTS.append((name, passives))
    return U("passivelist:" + name)


def resource(name, titre, desc, replenish):
    RESOURCES.append((name, titre, desc, replenish))


def slot(level):
    return f"ActionPoint:1;SpellSlotsGroup:1:1:{level}"


NO_UPCAST = dict(TooltipUpcastDescription="", TooltipUpcastDescriptionParams="")


def ally_aura(name, titre, desc, icon, radius, buff, stack, prio, enemies=False):
    """État d'aura posé sur soi ; il applique `buff` aux alliés (ou ennemis) proches."""
    cible = "Enemy() and not Dead()" if enemies else "Ally() and not Dead() and not Tagged('INANIMATE')"
    return status(name, titre, desc, icon, StackId=stack, StackPriority=prio, AuraRadius=radius,
                  AuraStatuses=f"IF({cible}):ApplyStatus({buff})",
                  RemoveConditions="HasStatus('SG_Incapacitated')", RemoveEvents="OnStatusApplied",
                  StatusPropertyFlags="IgnoreResting", StatusGroups="SG_RemoveOnRespec")


def keep_applied(name, titre, desc, icon, status_name):
    """Passif qui (ré)applique un état permanent sur soi (auras, sens divins...)."""
    return passive(name, titre, desc, icon,
                   StatsFunctorContext="OnCreate;OnLongRest;OnShortRest;OnCombatStarted;OnTurn",
                   StatsFunctors=f"ApplyStatus(SELF,{status_name},100,-1)")


# ================================================================== RESSOURCES
resource("DOC_Decret", "Décrets",
         "Pouvoir de la Divinité de l'Ordre pour imposer sa loi : Protéger, Purifier, Lier. "
         "Se recharge au repos court.", "ShortRest")
resource("DOC_Entropie", "Entropie",
         "Chaos accumulé en combat : +1 à chaque coup critique et à chaque ennemi éliminé. "
         "Retombe à zéro au début et à la fin de chaque combat.", "Never")
resource("DOC_PouvoirDivin", "Pouvoir divin",
         "Charge des réactions de domaine (Escamotage, Arbitre de la Trame). Se recharge au repos court.",
         "ShortRest")
resource("DOC_MaitriseSorts", "Maîtrise des sorts",
         "Permet de lancer un sort maîtrisé sans emplacement de sort, une fois par tour.", "Default")


# ================================================================== RACE : DIVINITÉ
hidden("DOC_Race_Marqueur")
passive("DOC_Race_VueDivine", "Vue divine",
        "Vous voyez dans le noir jusqu'à 24 m, comme en pleine lumière.",
        "PassiveFeature_SuperiorDarkvision",
        Boosts="DarkvisionRangeMin(24);ActiveCharacterLight(c46e7ba8-e746-7020-5146-287474d7b9f7)")
passive("DOC_Race_VolonteDivine", "Volonté divine",
        "Vous avez l'avantage aux jets de sauvegarde contre les états Charmé et Effrayé. "
        "La magie ne peut pas vous endormir.",
        "PassiveFeature_DivineHealth",
        Boosts="StatusImmunity(SLEEP);Tag(CHARMED_ADV);Tag(FRIGHTENED_ADV)")
passive("DOC_Race_EtincelleImmortelle", "Étincelle immortelle",
        "Une fois par repos long, quand vous tombez à 0 PV, vous restez à 1 PV.",
        "PassiveFeature_RelentlessEndurance", props="Highlighted;OncePerLongRest",
        StatsFunctorContext="OnCreate;OnLongRest",
        StatsFunctors="ApplyStatus(SELF,RELENTLESS_ENDURANCE,100,-1)")

# Injonction : le sort Injonction du jeu, 1 fois par repos long, sans emplacement
INJ_CHILDREN = ["Halt", "Approach", "Drop", "Flee", "Grovel"]
INJ_FR = {"Halt": "Halte", "Approach": "Approche", "Drop": "Lâche", "Flee": "Fuis", "Grovel": "À genoux"}
spell("Target_DOC_Injonction", "Target", "Injonction divine",
      "Prononcez un ordre divin d'un seul mot. La cible doit réussir un jet de sauvegarde de Sagesse "
      "ou obéir pendant son prochain tour. Une fois par repos long, sans emplacement de sort.",
      using="Target_Command_Container", Cooldown="OncePerRest", UseCosts="ActionPoint:1",
      ContainerSpells=";".join(f"Target_DOC_Injonction_{c}" for c in INJ_CHILDREN), **NO_UPCAST)
for c in INJ_CHILDREN:
    spell(f"Target_DOC_Injonction_{c}", "Target", f"Injonction divine : {INJ_FR[c]}",
          "Ordre divin d'un seul mot (jet de sauvegarde de Sagesse). Une fois par repos long.",
          using=f"Target_Command_{c}", SpellContainerID="Target_DOC_Injonction",
          Cooldown="OncePerRest", UseCosts="ActionPoint:1", **NO_UPCAST)

# Forme divine (niv. 5) : vol + dégâts aux attaques, type selon le domaine (Divinité pure)
FORME_BOOSTS = []
for dom, (_cls, _t, dtype, _o, _f) in DOMAINES.items():
    FORME_BOOSTS.append(f"IF(HasPassive('DOC_{dom}_Marqueur',context.Source)):CharacterWeaponDamage(1d6,{dtype})")
    FORME_BOOSTS.append(f"IF(HasPassive('DOC_{dom}_Marqueur',context.Source)):CharacterUnarmedDamage(1d6,{dtype})")
FORME_BOOSTS.append("IF(not HasPassive('DOC_Classe_Marqueur',context.Source)):CharacterWeaponDamage(1d6,Force)")
FORME_BOOSTS.append("IF(not HasPassive('DOC_Classe_Marqueur',context.Source)):CharacterUnarmedDamage(1d6,Force)")
status("DOC_FORME_DIVINE", "Forme divine",
       "Votre gloire divine est revenue : vous volez et vos attaques infligent 1d6 dégâts de force "
       "supplémentaires. Si vous êtes aussi Divinité de l'Ordre ou du Chaos (Divinité pure), "
       "ces dégâts prennent le type de votre domaine.",
       "PassiveFeature_LathandersLight", Boosts=";".join(FORME_BOOSTS), StackId="DOC_FORME_DIVINE")
spell("Shout_DOC_FormeDivine", "Shout", "Forme divine",
      "Action bonus, une fois par repos long : vous retrouvez votre gloire pendant 3 tours. "
      "Vous volez et vos attaques infligent 1d6 dégâts de force supplémentaires "
      "(type de votre domaine si vous êtes une Divinité pure).",
      using="Shout_DivineSense", Icon="Action_Fly", Cooldown="OncePerRest", UseCosts="BonusActionPoint:1",
      SpellProperties="ApplyStatus(SELF,DOC_FORME_DIVINE,100,3);ApplyStatus(SELF,FLY,100,3)",
      TooltipStatusApply="ApplyStatus(DOC_FORME_DIVINE,100,3)")

RACE_L1 = spelllist("DOC_Race_Niv1", "Divinité : Présence", ["Shout_Thaumaturgy"])
RACE_L3 = spelllist("DOC_Race_Niv3", "Divinité : Injonction divine", ["Target_DOC_Injonction"])
RACE_L5 = spelllist("DOC_Race_Niv5", "Divinité : Forme divine", ["Shout_DOC_FormeDivine"])


# ================================================================== SOCLES DES CLASSES
hidden("DOC_Classe_Marqueur")

# --- Divinité de l'Ordre : Loi absolue
for v, lvl in ((5, 1), (8, 6), (10, 11)):
    passive(f"DOC_Ordre_LoiAbsolue_{v}", f"Loi absolue ({v})",
            f"Votre volonté plie le hasard : vos jets de d20 (attaques, tests, sauvegardes) "
            f"ne peuvent pas donner moins de {v}.",
            "PassiveFeature_Portent",
            Boosts=";".join(f"MinimumRollResult({r},{v})" for r in
                            ("Attack", "SkillCheck", "RawAbility", "SavingThrow", "DeathSavingThrow")))

# --- Décrets
status("DOC_LIE", "Lié par décret",
       "Un décret divin vous enchaîne : impossible de vous déplacer ou de réagir.",
       "Spell_Enchantment_HoldPerson",
       Boosts="ActionResourceBlock(Movement);ActionResourceBlock(ReactionActionPoint)",
       StackId="DOC_LIE")
spell("Target_DOC_Purifier", "Target", "Décret : Purifier",
      "Action bonus, 1 Décret : retirez d'un allié les états Empoisonné, Aveuglé, Charmé, Effrayé, "
      "Paralysé, Étourdi, Entravé et les maladies.",
      using="Target_Bless", Level="0", AmountOfTargets="1", Icon="Action_Paladin_LayOnHands_SmallHeal",
      UseCosts="BonusActionPoint:1;DOC_Decret:1",
      SpellProperties=";".join(f"RemoveStatus({g})" for g in
                               ("SG_Poisoned", "SG_Blinded", "SG_Charmed", "SG_Frightened", "SG_Paralyzed",
                                "SG_Stunned", "SG_Restrained", "SG_Disease")),
      TooltipStatusApply="", SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell", **NO_UPCAST)
spell("Target_DOC_Lier", "Target", "Décret : Lier",
      "Action, 1 Décret : la cible doit réussir un jet de sauvegarde de Sagesse ou être Liée pendant "
      "2 tours (elle ne peut ni se déplacer ni réagir).",
      using="Target_HoldPerson", Level="0", UseCosts="ActionPoint:1;DOC_Decret:1",
      TargetConditions="Character() and not Self() and not Dead() and not Ally()",
      SpellSuccess="ApplyStatus(DOC_LIE,100,2)", TooltipStatusApply="ApplyStatus(DOC_LIE,100,2)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
      **NO_UPCAST)
interrupt("Interrupt_DOC_Proteger", "Décret : Protéger",
          "Réaction, 1 Décret : quand un allié proche est touché, les dégâts qu'il subit sont divisés par deux.",
          "PassiveFeature_FightingStyle_Protection",
          InterruptContext="OnPreDamage", InterruptContextScope="Nearby", Container="YesNoDecision",
          Conditions="IsAbleToReact(context.Observer) and Ally(context.Target,context.Observer) and "
                     "not Self(context.Target,context.Observer) and HasDamageEffectFlag(DamageFlags.Hit) and "
                     "not DistanceToEntityGreaterThan(9,context.ObserverPosition,context.Target)",
          Properties="ApplyStatus(UNCANNY_DODGE_REDUCE_DAMAGE,100,0)",
          Cost="ReactionActionPoint:1;DOC_Decret:1", Stack="DOC_Proteger",
          InterruptDefaultValue="Ask;Enabled")
passive("DOC_Ordre_Decrets", "Décrets",
        "Vous imposez votre loi au monde. Vous disposez de charges de Décret (2, puis 3 au niveau 6 "
        "et 4 au niveau 10), rechargées au repos court : Protéger (réaction), Purifier (action bonus) "
        "et Lier (action).",
        "Action_Paladin_DivineGuardian", Boosts="UnlockInterrupt(Interrupt_DOC_Proteger)")
ORDRE_DECRETS = spelllist("DOC_Ordre_Decrets", "Décrets", ["Target_DOC_Purifier", "Target_DOC_Lier"])

# --- Aura d'Ordre
for n, r, v, prio in ((1, 3, 8, 1), (2, 9, 8, 2), (3, 9, 10, 3)):
    status(f"DOC_AURA_ORDRE_BUFF_{n}", "Aura d'Ordre",
           f"Vos jets de sauvegarde ne peuvent pas donner moins de {v}.",
           "Action_Paladin_AuraOfProtection", Boosts=f"MinimumRollResult(SavingThrow,{v})",
           StackId="DOC_AURA_ORDRE_BUFF", StackPriority=prio)
    ally_aura(f"DOC_AURA_ORDRE_{n}", "Aura d'Ordre",
              f"Les alliés à {r} m profitent de votre Loi absolue sur leurs sauvegardes (minimum {v}).",
              "Action_Paladin_AuraOfProtection", r, f"DOC_AURA_ORDRE_BUFF_{n}", "DOC_AURA_ORDRE", prio)
for n, r, v in ((1, 3, 8), (2, 9, 8), (3, 9, 10)):
    keep_applied(f"DOC_Ordre_Aura_{n}", "Aura d'Ordre",
                 f"Les alliés à {r} m ou moins ne peuvent pas obtenir moins de {v} à leurs jets de sauvegarde.",
                 "Action_Paladin_AuraOfProtection", f"DOC_AURA_ORDRE_{n}")

passive("DOC_Ordre_Inebranlable", "Inébranlable",
        "Rien ne fait vaciller l'Ordre : vous ne pouvez pas être renversé, bousculé ni repoussé.",
        "PassiveFeature_ShieldMaster_PassiveBonuses",
        Boosts="StatusImmunity(SG_Prone);StatusImmunity(PRONE);Attribute(Grounded)")

# --- Ordre parfait (niv. 12)
status("DOC_ORDRE_PARFAIT_BUFF", "Ordre parfait",
       "Les coups critiques ne vous touchent pas et vous ne pouvez pas tomber sous 1 PV.",
       "Action_Paladin_AuraOfDevotion",
       Boosts="CriticalHit(AttackTarget,Success,Never);DownedStatus(RELENTLESS_ENDURANCE_DOWNED,5)",
       StackId="DOC_ORDRE_PARFAIT_BUFF")
ally_aura("DOC_ORDRE_PARFAIT", "Ordre parfait",
          "Les alliés à 9 m ne subissent pas de coups critiques et ne tombent pas sous 1 PV.",
          "Action_Paladin_AuraOfDevotion", 9, "DOC_ORDRE_PARFAIT_BUFF", "DOC_ORDRE_PARFAIT", 1)
spell("Shout_DOC_OrdreParfait", "Shout", "Ordre parfait",
      "Une fois par repos long, pendant 10 tours : les alliés à 9 m ne subissent pas de coups "
      "critiques et ne peuvent pas tomber sous 1 PV.",
      using="Shout_DivineSense", Icon="Action_Paladin_AuraOfDevotion", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", SpellProperties="ApplyStatus(SELF,DOC_ORDRE_PARFAIT,100,10)",
      TooltipStatusApply="ApplyStatus(DOC_ORDRE_PARFAIT,100,10)")

# --- Divinité pure
passive("DOC_Ordre_DivinitePure", "Divinité pure (Ordre)",
        "Si vous êtes de race Divinité : +1 charge de Décret, et votre Forme divine prend "
        "le type de dégâts de votre domaine.",
        "PassiveFeature_BlessingsOfKnowledge", BoostContext="OnCreate;OnLongRest;OnShortRest",
        BoostConditions="HasPassive('DOC_Race_Marqueur',context.Source)", Boosts="ActionResource(DOC_Decret,1,0)")


# --- Divinité du Chaos : Chaos primordial
for crit, red in ((19, 1), (18, 2), (17, 3)):
    passive(f"DOC_Chaos_Critique_{crit}", f"Chaos primordial (critique {crit}-20)",
            f"Le hasard vous sert : vos attaques infligent un coup critique sur {crit}-20.",
            "PassiveFeature_WildMagicSurge", Boosts=f"ReduceCriticalAttackThreshold({red})")
SURGE = ("IF(HasStatus('TIDES_OF_CHAOS',context.Source)):TriggerRandomCast(1,,DOC_DeferlementDivin,WildMagic);"
         "IF(not HasStatus('TIDES_OF_CHAOS',context.Source) and not HasPassive('DOC_Sorcellerie_ChaosMaitrise',context.Source)):"
         "TriggerRandomCast(20,,WildMagic,DOC_DeferlementDivin);"
         "IF(not HasStatus('TIDES_OF_CHAOS',context.Source) and HasPassive('DOC_Sorcellerie_ChaosMaitrise',context.Source)):"
         "TriggerRandomCast(20,,DOC_DeferlementDivin);"
         "IF(HasStatus('TIDES_OF_CHAOS',context.Source)):RemoveStatus(SELF,TIDES_OF_CHAOS)")
passive("DOC_Chaos_Deferlement", "Déferlement de chaos",
        "Chaque sort lancé avec un emplacement a 1 chance sur 20 de déclencher un Déferlement de chaos : "
        "un effet aléatoire de magie sauvage ou un effet divin. Un 1 naturel à une attaque en déclenche "
        "un aussi.",
        "PassiveFeature_WildMagicSurge", StatsFunctorContext="OnCast",
        Conditions="not IsCantrip() and HasSpellFlag(SpellFlags.Spell)", StatsFunctors=SURGE)
hidden("DOC_Chaos_UnNaturel", StatsFunctorContext="OnAttack", Conditions="IsCriticalMiss()",
       StatsFunctors="TriggerRandomCast(1,,WildMagic,DOC_DeferlementDivin)")

# --- Entropie
passive("DOC_Chaos_EntropieGain", "Entropie",
        "Vous gagnez 1 point d'Entropie à chaque coup critique et à chaque ennemi éliminé "
        "(maximum 3, puis 4 au niveau 6 et 5 au niveau 10). L'Entropie retombe à zéro au début "
        "et à la fin de chaque combat.",
        "PassiveFeature_EntropicWard", props="Highlighted;OncePerAttack",
        StatsFunctorContext="OnDamage", Conditions="(IsCritical() or IsKillingBlow()) and not Self()",
        StatsFunctors="RestoreResource(SELF,DOC_Entropie,1,0)")
hidden("DOC_Chaos_EntropieReset", StatsFunctorContext="OnCombatStarted;OnCombatEnded;OnCreate;OnLongRest;OnShortRest",
       StatsFunctors="UseActionResource(SELF,DOC_Entropie,100%,0)")
status("DOC_DEFAIRE", "Défaire",
       "Vos dégâts ignorent les résistances de vos cibles.", "PassiveFeature_EntropicWard",
       Boosts=";".join(f"IF(not Self()):IgnoreResistance({t},Resistant)" for t in DAMAGE_TYPES), StackId="DOC_DEFAIRE")
spell("Target_DOC_PasChaotique", "Target", "Entropie : Pas chaotique",
      "Action bonus, 1 Entropie : téléportez-vous à un endroit visible à 18 m ou moins.",
      using="Target_MistyStep", Level="0", Icon="Action_Monk_ShadowStep",
      UseCosts="BonusActionPoint:1;DOC_Entropie:1", **NO_UPCAST)
spell("Shout_DOC_Defaire", "Shout", "Entropie : Défaire",
      "Action bonus, 2 Entropie : pendant 2 tours, vos dégâts ignorent les résistances de vos cibles.",
      using="Shout_DivineSense", Icon="PassiveFeature_EntropicWard", Cooldown="",
      UseCosts="BonusActionPoint:1;DOC_Entropie:2", SpellProperties="ApplyStatus(SELF,DOC_DEFAIRE,100,2)",
      TooltipStatusApply="ApplyStatus(DOC_DEFAIRE,100,2)")
spell("Shout_DOC_Detoner", "Shout", "Entropie : Détoner",
      "Action, 3 Entropie : une explosion d'un élément aléatoire (feu, froid, foudre ou acide) "
      "inflige 4d6 dégâts aux ennemis à 6 m ou moins.",
      using="Shout_DivineSense", Icon="Spell_Abjuration_GlyphOfWarding_Detonation", Cooldown="",
      UseCosts="ActionPoint:1;DOC_Entropie:3", SpellProperties="TriggerRandomCast(1,0,DOC_Detonation)")
CHAOS_ENTROPIE = spelllist("DOC_Chaos_Entropie", "Entropie",
                           ["Target_DOC_PasChaotique", "Shout_DOC_Defaire", "Shout_DOC_Detoner"])

# --- Aura de Chaos
status("DOC_AURA_CHAOS_MALUS", "Aura de Chaos",
       "Le chaos vous ronge : -1d4 à vos jets de sauvegarde.", "Action_Paladin_AuraOfHate",
       Boosts="RollBonus(SavingThrow,-1d4)", StackId="DOC_AURA_CHAOS_MALUS")
for n, r, prio in ((1, 3, 1), (2, 9, 2)):
    ally_aura(f"DOC_AURA_CHAOS_{n}", "Aura de Chaos",
              f"Les ennemis à {r} m subissent -1d4 à leurs jets de sauvegarde.",
              "Action_Paladin_AuraOfHate", r, "DOC_AURA_CHAOS_MALUS", "DOC_AURA_CHAOS", prio, enemies=True)
    keep_applied(f"DOC_Chaos_Aura_{n}", "Aura de Chaos",
                 f"Les ennemis à {r} m ou moins subissent -1d4 à leurs jets de sauvegarde.",
                 "Action_Paladin_AuraOfHate", f"DOC_AURA_CHAOS_{n}")

passive("DOC_Chaos_Indomptable", "Indomptable",
        "Le chaos ne se laisse pas enchaîner : immunité à la paralysie et aux entraves "
        "(toiles, enchevêtrement...).",
        "PassiveFeature_DivineHealth",
        Boosts="StatusImmunity(SG_Paralyzed);StatusImmunity(SG_Restrained)")

# --- Tempête primordiale (niv. 12)
status("DOC_TEMPETE_PRIMORDIALE", "Tempête primordiale",
       "Un Déferlement de chaos au début de chacun de vos tours ; coups critiques sur 15-20.",
       "Action_Barbarian_Rage_WildMagic", Boosts="ReduceCriticalAttackThreshold(2)",
       StackId="DOC_TEMPETE_PRIMORDIALE")
spell("Shout_DOC_TempetePrimordiale", "Shout", "Tempête primordiale",
      "Une fois par repos long, pendant 10 tours : un Déferlement de chaos se produit au début de "
      "chacun de vos tours et vos coups critiques passent à 15-20.",
      using="Shout_DivineSense", Icon="Action_Barbarian_Rage_WildMagic", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", SpellProperties="ApplyStatus(SELF,DOC_TEMPETE_PRIMORDIALE,100,10)",
      TooltipStatusApply="ApplyStatus(DOC_TEMPETE_PRIMORDIALE,100,10)")
hidden("DOC_Chaos_TempetePrimordiale", StatsFunctorContext="OnTurn",
       Conditions="HasStatus('DOC_TEMPETE_PRIMORDIALE',context.Source)",
       StatsFunctors="TriggerRandomCast(1,,DOC_DeferlementDivin)")

passive("DOC_Chaos_DivinitePure", "Divinité pure (Chaos)",
        "Si vous êtes de race Divinité : +1 Entropie maximum, et votre Forme divine prend "
        "le type de dégâts de votre domaine.",
        "PassiveFeature_BlessingsOfKnowledge", BoostContext="OnCreate;OnLongRest;OnShortRest",
        BoostConditions="HasPassive('DOC_Race_Marqueur',context.Source)", Boosts="ActionResource(DOC_Entropie,1,0)")

ORDRE_L12 = spelllist("DOC_Ordre_Niv12", "Ordre parfait", ["Shout_DOC_OrdreParfait"])
CHAOS_L12 = spelllist("DOC_Chaos_Niv12", "Tempête primordiale", ["Shout_DOC_TempetePrimordiale"])


# ================================================================== DÉFERLEMENTS ALÉATOIRES
def outcome(group, name, titre, desc, **data):
    spell(name, "Shout", titre, desc, using="Shout__WildMagic", **data)
    OUTCOMES.append((group, name))


outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Benediction", "Déferlement : Bénédiction chaotique",
        "Vos alliés à 9 m sont bénis pendant 3 tours.", AreaRadius="9",
        TargetConditions="Ally() and not Dead()", SpellProperties="ApplyStatus(BLESS,100,3)")
outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Eclat", "Déferlement : Éclat primordial",
        "Les ennemis à 6 m subissent 2d8 dégâts de force.", AreaRadius="6",
        TargetConditions="Enemy() and not Dead()", SpellProperties="DealDamage(2d8,Force,Magical)")
outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Ascension", "Déferlement : Ascension fugace",
        "Vous volez pendant 2 tours.", TargetConditions="Self()", SpellProperties="ApplyStatus(FLY,100,2)")
outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Vitalite", "Déferlement : Souffle vital",
        "Vous récupérez 2d8 PV.", TargetConditions="Self()", SpellProperties="RegainHitPoints(2d8)")
outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Entropie", "Déferlement : Couronne d'entropie",
        "Vous gagnez 1 point d'Entropie.", TargetConditions="Self()",
        SpellProperties="RestoreResource(DOC_Entropie,1,0)")
outcome("DOC_DeferlementDivin", "Shout_DOC_Deferlement_Contrecoup", "Déferlement : Contrecoup divin",
        "Le chaos se retourne contre vous : vous subissez 1d10 dégâts de force.", TargetConditions="Self()",
        SpellProperties="DealDamage(1d10,Force,Magical)")
# Divinité Créatrice : mêmes effets, sans le Contrecoup ni la magie sauvage du jeu (aucun malus)
for _s in ("Benediction", "Eclat", "Ascension", "Vitalite", "Entropie"):
    OUTCOMES.append(("DOC_DeferlementCreation", f"Shout_DOC_Deferlement_{_s}"))
passive("DOC_Creatrice_Deferlement", "Déferlement créateur",
        "Chaque sort lancé avec un emplacement a 1 chance sur 20 de déclencher un Déferlement créateur : un "
        "effet divin toujours favorable (bénédiction, éclat, vol, soins ou Entropie). Jamais de magie "
        "sauvage, jamais de contrecoup.",
        "PassiveFeature_WildMagicSurge", StatsFunctorContext="OnCast",
        Conditions="not IsCantrip() and HasSpellFlag(SpellFlags.Spell)",
        StatsFunctors="IF(HasStatus('TIDES_OF_CHAOS',context.Source)):TriggerRandomCast(1,,DOC_DeferlementCreation);"
                      "IF(not HasStatus('TIDES_OF_CHAOS',context.Source)):TriggerRandomCast(20,,DOC_DeferlementCreation);"
                      "IF(HasStatus('TIDES_OF_CHAOS',context.Source)):RemoveStatus(SELF,TIDES_OF_CHAOS)")
passive("DOC_Creatrice_Perfection", "Perfection créatrice",
        "Le corps d'un dieu créateur : +4 à toutes les caractéristiques (Force, Dextérité, Constitution, "
        "Intelligence, Sagesse et Charisme).",
        "PassiveFeature_BlessingsOfKnowledge",
        Boosts=";".join(f"Ability({a},4)" for a in ("Strength", "Dexterity", "Constitution", "Intelligence",
                                                     "Wisdom", "Charisma")))
passive("DOC_Creatrice_DivinitePure", "Divinité pure (Création)",
        "Si vous êtes de race Divinité : +1 charge de Décret et +1 Entropie maximum, et votre Forme divine "
        "prend le type de dégâts de votre domaine.",
        "PassiveFeature_BlessingsOfKnowledge", BoostContext="OnCreate;OnLongRest;OnShortRest",
        BoostConditions="HasPassive('DOC_Race_Marqueur',context.Source)",
        Boosts="ActionResource(DOC_Decret,1,0);ActionResource(DOC_Entropie,1,0)")

for t in ("Fire", "Cold", "Lightning", "Acid"):
    outcome("DOC_Detonation", f"Shout_DOC_Detonation_{t}", f"Détonation ({TYPE_NOM[t]})",
            f"Les ennemis à 6 m subissent 4d6 dégâts {TYPE_FR[t]}.", AreaRadius="6",
            TargetConditions="Enemy() and not Dead()", SpellProperties=f"DealDamage(4d6,{t},Magical)")


# ================================================================== SORTS EXCLUSIFS DE CLASSE
def degats(dmg, dtype, half=True):
    s = f"DealDamage({dmg},{dtype},Magical)"
    f = f"DealDamage(({dmg})/2,{dtype},Magical)" if half else None
    return s, f


# --- Ordre
lm = palier("DOC_LM_VerdictLumineux", "4d6", "5d6", "6d6", "7d6")
spell("Projectile_DOC_VerdictLumineux", "Projectile", "Verdict lumineux",
      "Un trait de lumière divine (4d6 dégâts radiants, augmente aux niveaux 5, 9 et 12). "
      "La prochaine attaque contre la cible a l'avantage.",
      using="Projectile_GuidingBolt", Level="1", UseCosts=slot(1),
      SpellSuccess=f"DealDamage({lm},Radiant,Magical);ApplyStatus(GUIDING_BOLT,100,2)",
      TooltipDamageList=f"DealDamage({lm},Radiant)", **NO_UPCAST)
lm = palier("DOC_LM_ChainesLoi", "2d8", "3d8", "4d8", "5d8")
spell("Target_DOC_ChainesLoi", "Target", "Chaînes de la Loi",
      "La cible (n'importe quelle créature) doit réussir un jet de sauvegarde de Sagesse ou être "
      "paralysée et subir 2d8 dégâts radiants (augmente aux paliers). Pas de concentration.",
      using="Target_HoldPerson", Level="2", UseCosts=slot(2),
      TargetConditions="Character() and not Self() and not Dead() and not Ally()",
      SpellSuccess=f"ApplyStatus(HOLD_PERSON,100,10);DealDamage({lm},Radiant,Magical)",
      TooltipDamageList=f"DealDamage({lm},Radiant)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
      **NO_UPCAST)
status("DOC_EGIDE_ORDRE", "Égide de l'Ordre", "+2 à la CA et +2 aux jets de sauvegarde.",
       "Spell_Abjuration_ShieldOfFaith", Boosts="AC(2);RollBonus(SavingThrow,2)", StackId="DOC_EGIDE_ORDRE")
spell("Target_DOC_EgideOrdre", "Target", "Égide de l'Ordre",
      "Jusqu'à 6 alliés gagnent +2 à la CA et +2 aux jets de sauvegarde pendant 10 tours. "
      "Pas de concentration.",
      using="Target_Bless", Level="3", UseCosts=slot(3), AmountOfTargets="6",
      Icon="Spell_Abjuration_ShieldOfFaith", SpellProperties="ApplyStatus(DOC_EGIDE_ORDRE,100,10)",
      TooltipStatusApply="ApplyStatus(DOC_EGIDE_ORDRE,100,10)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;IgnorePreviouslyPickedEntities", **NO_UPCAST)
spell("Target_DOC_BannissementAbsolu", "Target", "Bannissement absolu",
      "La cible doit réussir un jet de sauvegarde de Charisme ou être bannie pendant 3 tours. "
      "Pas de concentration.",
      using="Target_Banishment", Level="4", UseCosts=slot(4), SpellSuccess="ApplyStatus(BANISHED,100,3)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;RangeIgnoreVerticalThreshold;IsHarmful",
      **NO_UPCAST)
spell("Target_DOC_DecretImmobilite", "Target", "Décret d'immobilité",
      "Toutes les créatures dans une zone de 3 m doivent réussir un jet de sauvegarde de Sagesse "
      "ou être paralysées. Pas de concentration.",
      using="Target_HoldMonster", Level="5", UseCosts=slot(5), AreaRadius="3",
      TargetConditions="Character() and not Self() and not Dead() and not Ally()",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
      **NO_UPCAST)
lm = palier("DOC_LM_JugementOrdre", "10d8", "10d8", "10d8", "12d8")
s, f = degats(lm, "Radiant")
spell("Target_DOC_JugementOrdre", "Target", "Jugement de l'Ordre",
      "Une colonne de lumière s'abat sur une zone de 6 m : 10d8 dégâts radiants (12d8 au niveau 12), "
      "la moitié en cas de sauvegarde de Dextérité réussie.",
      using="Target_FlameStrike", Level="6", UseCosts=slot(6), AreaRadius="6", SpellProperties="",
      SpellSuccess=s, SpellFail=f, TooltipDamageList=f"DealDamage({lm},Radiant)", **NO_UPCAST)

# --- Chaos
lm = palier("DOC_LM_TraitPrimordial", "3d8", "4d8", "5d8", "6d8")
spell("Target_DOC_TraitPrimordial", "Target", "Trait primordial",
      "Un éclair de chaos pur : 3d8 dégâts de force (augmente aux niveaux 5, 9 et 12).",
      using="Target_ChillTouch", Level="1", UseCosts=slot(1), Icon="PassiveFeature_WildMagicSurge",
      SpellSuccess=f"DealDamage({lm},Force,Magical)", TooltipDamageList=f"DealDamage({lm},Force)", **NO_UPCAST)
lm = palier("DOC_LM_FractureReel", "3d8", "4d8", "5d8", "6d8")
s, f = degats(lm, "Force")
spell("Target_DOC_FractureReel", "Target", "Fracture du réel",
      "La réalité se brise dans une zone de 4 m : 3d8 dégâts de force (augmente aux paliers), "
      "moitié en cas de sauvegarde de Constitution réussie.",
      using="Target_Shatter", Level="2", UseCosts=slot(2), AreaRadius="4", SpellSuccess=s, SpellFail=f,
      TooltipDamageList=f"DealDamage({lm},Force)", **NO_UPCAST)
lm = palier("DOC_LM_FoudreChaos", "4d10", "4d10", "5d10", "6d10")
s, f = degats(lm, "Lightning")
spell("Target_DOC_FoudreChaos", "Target", "Foudre du chaos",
      "La foudre frappe une zone : 4d10 dégâts de foudre (augmente aux paliers), moitié en cas de "
      "sauvegarde de Dextérité réussie. Le sol est électrifié.",
      using="Target_CallLightning", Level="3", UseCosts=slot(3), SpellProperties="GROUND:SurfaceChange(Electrify)",
      SpellSuccess=s, SpellFail=f, TooltipDamageList=f"DealDamage({lm},Lightning)", **NO_UPCAST)
lm = palier("DOC_LM_GreleEntropie", "6d8", "6d8", "7d8", "8d8")
s, f = degats(lm, "Force")
spell("Target_DOC_GreleEntropie", "Target", "Grêle d'entropie",
      "Une pluie d'éclats chaotiques : 6d8 dégâts de force (augmente aux paliers) et Hébété 1 tour ; "
      "moitié des dégâts et pas d'effet en cas de sauvegarde de Dextérité réussie.",
      using="Target_IceStorm", Level="4", UseCosts=slot(4), SpellSuccess=s + ";ApplyStatus(DAZED,100,1)",
      SpellFail=f, TooltipDamageList=f"DealDamage({lm},Force)", **NO_UPCAST)
lm = palier("DOC_LM_FletrissureChaos", "9d8", "9d8", "9d8", "11d8")
s, f = degats(lm, "Force")
spell("Target_DOC_FletrissureChaos", "Target", "Flétrissure du chaos",
      "Le chaos défait la cible : 9d8 dégâts de force (11d8 au niveau 12), moitié en cas de "
      "sauvegarde de Constitution réussie.",
      using="Target_Blight", Level="5", UseCosts=slot(5), TargetConditions="not Self() and not Dead()",
      SpellSuccess=s, SpellFail=f, TooltipDamageList=f"DealDamage({lm},Force)", **NO_UPCAST)
lm = palier("DOC_LM_Apocalypse", "6d8", "6d8", "6d8", "7d8")
spell("Target_DOC_ApocalypsePrimordiale", "Target", "Apocalypse primordiale",
      "Le chaos originel embrase une zone de 6 m : 6d8 dégâts de feu et 6d8 dégâts de force "
      "(7d8 + 7d8 au niveau 12), moitié en cas de sauvegarde de Dextérité réussie.",
      using="Target_FlameStrike", Level="6", UseCosts=slot(6), AreaRadius="6",
      SpellSuccess=f"DealDamage({lm},Fire,Magical);DealDamage({lm},Force,Magical)",
      SpellFail=f"DealDamage(({lm})/2,Fire,Magical);DealDamage(({lm})/2,Force,Magical)",
      TooltipDamageList=f"DealDamage({lm},Fire);DealDamage({lm},Force)", **NO_UPCAST)

ORDRE_EXCL = {1: "Projectile_DOC_VerdictLumineux", 2: "Target_DOC_ChainesLoi", 3: "Target_DOC_EgideOrdre",
              4: "Target_DOC_BannissementAbsolu", 5: "Target_DOC_DecretImmobilite", 6: "Target_DOC_JugementOrdre"}
CHAOS_EXCL = {1: "Target_DOC_TraitPrimordial", 2: "Target_DOC_FractureReel", 3: "Target_DOC_FoudreChaos",
              4: "Target_DOC_GreleEntropie", 5: "Target_DOC_FletrissureChaos", 6: "Target_DOC_ApocalypsePrimordiale"}
ORDRE_EXCL_LISTS = {n: spelllist(f"DOC_Ordre_Exclusif_{n}", f"Ordre : sort exclusif de niveau {n}", [s])
                    for n, s in ORDRE_EXCL.items()}
CHAOS_EXCL_LISTS = {n: spelllist(f"DOC_Chaos_Exclusif_{n}", f"Chaos : sort exclusif de niveau {n}", [s])
                    for n, s in CHAOS_EXCL.items()}
