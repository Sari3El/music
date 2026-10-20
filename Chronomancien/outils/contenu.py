"""Contenu du mod « Classe Chronomancien » : capacités, sorts, états, réactions, ressources.

Mod indépendant. Tout ce qu'il crée porte le préfixe CHR_ (sorts : <Type>_CHR_<Nom>).
Les sorts dérivent (« using ») de sorts du jeu de base pour en reprendre les animations.
Tout est fait en données, sans Script Extender : voir CONCEPTION.md pour les écarts avec le
cahier des charges.
"""
from doclib import Entry, Loca, U

L = Loca()
STATS = []           # toutes les entrées de stats
LEVELMAPS = []       # (nom, {niveau: valeur})
SPELLLISTS = []      # (nom, commentaire, [sorts])
SKILLLISTS = []      # (nom, [compétences])
RESOURCES = []       # (nom, titre, description, recharge)
SELECTOR_LABELS = []  # (SelectorId, titre, description)

# ------------------------------------------------------------------ jeu de base
ALL_ABILITIES_LIST = "b9149c8e-52c8-46e5-9cb6-fc39301c05fe"
CC_POSE = "0f07ec6e-4ef0-434e-9a51-1353260ccff8"

# ------------------------------------------------------------------ fabriques
def add(e):
    STATS.append(e)
    return e


def passive(name, titre, desc, icon, props="Highlighted", **data):
    return add(Entry(name, "PassiveData", DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, Properties=props, **data))


def hidden(name, props="IsHidden", **data):
    return add(Entry(name, "PassiveData", DisplayName=L.ref(name + ":nom", name), Properties=props, **data))


def status(name, titre, desc, icon, using=None, stype="BOOST", **data):
    if data.get("StatusPropertyFlags") == "":
        del data["StatusPropertyFlags"]
    return add(Entry(name, "StatusData", using, StatusType=stype, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, **data))


def spell(name, stype, titre, desc, using=None, **data):
    return add(Entry(name, "SpellData", using, SpellType=stype, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), **data))


def interrupt(name, titre, desc, icon, using=None, **data):
    return add(Entry(name, "InterruptData", using, DisplayName=L.ref(name + ":nom", titre),
                     Description=L.ref(name + ":desc", desc), Icon=icon, **data))


def palier(name, l1, l5, l9, l12, l15=None, l17=None, l20=None):
    """Valeur qui grandit avec le niveau du personnage (5, 9, 12, puis 15, 17 et 20 avec un mod niveau 20)."""
    vals = {1: l1, 5: l5, 9: l9, 12: l12}
    for lv, v in ((15, l15), (17, l17), (20, l20)):
        if v is not None:
            vals[lv] = v
    LEVELMAPS.append((name, vals))
    return f"LevelMapValue({name})"


def spelllist(name, comment, spells):
    SPELLLISTS.append((name, comment, spells))
    return U("spelllist:" + name)


def resource(name, titre, desc, replenish):
    RESOURCES.append((name, titre, desc, replenish))


def slot(level):
    return f"ActionPoint:1;SpellSlotsGroup:1:1:{level}"


NO_UPCAST = dict(TooltipUpcastDescription="", TooltipUpcastDescriptionParams="")



# ================================================================== CHRONOMANCIEN
CHRONO = "CHR_Chronomancien"
FEATURE_SPELL = dict(Level="0", **NO_UPCAST)
SANS_CONCENTRATION = "HasVerbalComponent;HasSomaticComponent;IsSpell;IsHarmful"
TYPES = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison",
         "Psychic", "Radiant", "Slashing", "Thunder"]

# Capacités par niveau : FEATURES[niveau] = {"passives", "removed", "spells", "boosts"}
FEATURES = {}


def feat(level, passives=(), removed=(), spells=(), boosts=()):
    f = FEATURES.setdefault(level, {"passives": [], "removed": [], "spells": [], "boosts": []})
    f["passives"] += list(passives)
    f["removed"] += list(removed)
    f["spells"] += list(spells)
    f["boosts"] += list(boosts)


# Sorts du jeu que le Chronomancien peut préparer : espace, temps, entropie (vieillissement) et réalité.
TOURS_JEU = ["Target_MageHand", "Target_TrueStrike", "Shout_BladeWard", "Target_MinorIllusion", "Target_ChillTouch"]
SORTS_JEU = {
    1: ["Projectile_MagicMissile", "Shout_Shield_Wizard", "Shout_FeatherFall", "Shout_ExpeditiousRetreat",
        "Target_Longstrider", "Target_Jump"],
    2: ["Target_MistyStep", "Shout_Blur", "Target_HoldPerson", "Shout_MirrorImage", "Projectile_RayOfEnfeeblement",
        "Target_Darkness"],
    3: ["Target_Haste", "Target_Slow", "Shout_Blink", "Target_Counterspell", "Target_GaseousForm"],
    4: ["Teleportation_DimensionDoor", "Target_Banishment", "Target_ResilientSphere", "Target_Blight"],
    5: ["Target_HoldMonster", "Throw_Telekinesis"],
    6: ["Teleportation_ArcaneGate", "Target_GlobeOfInvulnerability", "Projectile_Disintegrate",
        "Target_CircleOfDeath"],
}

# ================================================================== RESSOURCE : SABLIER
resource("CHR_Sablier", "Sablier",
         "Le temps que le Chronomancien peut plier : Accélération, Rembobinage, Ralentir, Faille, Prison "
         "temporelle, Réécrire l'instant. Se recharge au repos court.", "ShortRest")
SABLIER = "CHR_Sablier"

# ================================================================== ÉTATS COMMUNS
status("CHR_RALENTI_LEGER", "Temps ralenti", "Votre temps s'écoule plus lentement : mouvement réduit de moitié.",
       "Spell_Transmutation_Slow", StackId="CHR_RALENTI_LEGER", Boosts="ActionResourceMultiplier(Movement,50,0)")
status("CHR_RALENTI", "Ralenti", "Le temps vous retient : mouvement réduit de moitié, -2 à la CA, ni action bonus "
       "ni réaction.", "Spell_Transmutation_Slow", StackId="CHR_RALENTI",
       Boosts="ActionResourceMultiplier(Movement,50,0);AC(-2);ActionResourceBlock(BonusActionPoint);"
              "ActionResourceBlock(ReactionActionPoint)")
IMMUNE_TOUT = ";".join(f"Resistance({t},Immune)" for t in TYPES)

# ================================================================== NIVEAU 1
passive("CHR_Prescience", "Prescience",
        "Vous voyez quelques secondes dans l'avenir : +5 à l'initiative, et vous ne pouvez pas être surpris.",
        "PassiveFeature_Portent", Boosts="Initiative(5);StatusImmunity(SURPRISED)")
passive("CHR_Resonance", "Résonance temporelle",
        "Vos tours de magie frappent deux fois dans le temps : une fois par attaque, ils infligent en plus votre "
        "modificateur d'Intelligence en dégâts de force.", "PassiveFeature_AgonizingBlast",
        props="Highlighted;OncePerAttack", StatsFunctorContext="OnDamage",
        Conditions="IsCantrip() and Enemy()", StatsFunctors="DealDamage(max(1,IntelligenceModifier),Force,Magical)")

spell("Shout_CHR_Acceleration", "Shout", "Accélération",
      "1 Sablier, une fois par tour, sans action : vous accélérez votre propre temps et gagnez une action "
      "supplémentaire ce tour-ci.", using="Shout_ActionSurge", UseCosts=f"{SABLIER}:1", Cooldown="OncePerTurn",
      **FEATURE_SPELL)

status("CHR_REMBOBINE", "Rembobiné", "Le temps est revenu en arrière : ce coup n'a jamais eu lieu.",
       "Spell_Transmutation_Haste", StackId="CHR_REMBOBINE", Boosts=IMMUNE_TOUT,
       StatusPropertyFlags="DisableOverhead;DisableCombatlog")
interrupt("Interrupt_CHR_Rembobinage", "Rembobinage",
          "Réaction, 1 Sablier : quand un ennemi va infliger des dégâts à vous-même ou à un allié à 9 m ou moins, "
          "vous rembobinez le temps : ce coup n'a jamais eu lieu, la cible ne subit aucun dégât.",
          "Spell_Transmutation_Haste", InterruptContext="OnPreDamage", InterruptContextScope="Nearby",
          Conditions="IsAbleToReact(context.Observer) and "
                     "(Self(context.Target,context.Observer) or Ally(context.Target,context.Observer)) and "
                     "Enemy(context.Source,context.Observer) and not AnyEntityIsItem() and "
                     "not DistanceToEntityGreaterThan(9,context.ObserverPosition,context.Target)",
          Properties="ApplyStatus(CHR_REMBOBINE,100,0)", Cost=f"ReactionActionPoint:1;{SABLIER}:1",
          Stack="CHR_Rembobinage", InterruptDefaultValue="Ask;Enabled", Container="YesNoDecision")
passive("CHR_Rembobinage", "Rembobinage",
        "Réaction, 1 Sablier : un coup qui allait vous toucher, vous ou un allié proche, n'a jamais eu lieu.",
        "Spell_Transmutation_Haste", Boosts="UnlockInterrupt(Interrupt_CHR_Rembobinage)")

spell("Projectile_CHR_EclatTemporel", "Projectile", "Éclat temporel",
      "Tour de magie. Un éclat de temps figé frappe la cible : 1d10 dégâts de force (2d10 au niveau 5, 3d10 au "
      "niveau 10, 4d10 au niveau 17) et son mouvement est réduit de moitié jusqu'à son prochain tour.",
      using="Projectile_EldritchBlast", Level="0", AmountOfTargets="1", Icon="Spell_Transmutation_Slow",
      SpellSuccess="DealDamage(LevelMapValue(D10Cantrip),Force,Magical);ApplyStatus(CHR_RALENTI_LEGER,100,1)",
      TooltipDamageList="DealDamage(LevelMapValue(D10Cantrip),Force)", **NO_UPCAST)

ENTROPIE = palier("CHR_LM_RayonEntropie", "3d10", "4d10", "5d10", "6d10", "7d10", "8d10", "10d10")
spell("Projectile_CHR_RayonEntropie", "Projectile", "Rayon d'entropie",
      "Sort de niveau 1. Un rayon qui fait vieillir tout ce qu'il touche : 3d10 dégâts nécrotiques (jusqu'à "
      "10d10 au niveau 20) et la cible est ralentie (mouvement réduit de moitié) pendant 2 tours.",
      using="Projectile_RayOfSickness", Level="1", UseCosts=slot(1), Icon="Spell_Necromancy_Blight",
      SpellSuccess=f"DealDamage({ENTROPIE},Necrotic,Magical);ApplyStatus(CHR_RALENTI_LEGER,100,2)",
      TooltipDamageList=f"DealDamage({ENTROPIE},Necrotic)", **NO_UPCAST)

# ================================================================== NIVEAU 2
spell("Target_CHR_Ralentir", "Target", "Ralentir",
      "Action bonus, 1 Sablier : la cible fait un jet de sauvegarde de Sagesse. Échec : elle est ralentie "
      "pendant 2 tours (mouvement réduit de moitié, -2 à la CA, ni action bonus ni réaction).",
      using="Target_HoldPerson", UseCosts=f"BonusActionPoint:1;{SABLIER}:1", Icon="Spell_Transmutation_Slow",
      SpellFlags=SANS_CONCENTRATION, TargetConditions="Character() and not Self() and not Dead()",
      SpellRoll="not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellSuccess="ApplyStatus(CHR_RALENTI,100,2)", SpellFail="", **FEATURE_SPELL)
for n, niv in ((1, 1), (2, 2), (3, 3), (4, 4)):
    passive(f"CHR_Memoire_{n}", "Mémoire du temps" + ("" if n == 1 else f" ({niv})"),
            f"À chaque repos court, vous rembobinez votre magie : vous récupérez un emplacement de sort de "
            f"niveau {niv}.", "Skill_Wizard_ArcaneRecovery", StatsFunctorContext="OnShortRest",
            StatsFunctors=f"RestoreResource(SELF,SpellSlot,1,{niv})")

# ================================================================== NIVEAU 3 : FAILLE + FRACTURE SPATIALE
spell("Target_CHR_Faille", "Target", "Faille",
      "Action bonus, 1 Sablier, une fois par tour : vous ouvrez une faille jusqu'à 18 m. Visez le sol pour vous "
      "y téléporter, ou une créature (alliée ou ennemie) pour échanger vos places.",
      using="Target_BenignTransposition_Teleport", UseCosts=f"BonusActionPoint:1;{SABLIER}:1", Range="18",
      Cooldown="OncePerTurn", RequirementConditions="", TargetConditions="not Self()",
      Icon="Spell_Conjuration_MistyStep",
      SpellProperties="GROUND:IF(CanStand('')):TeleportSource();IF(Character() and not Self()):SwapPlaces()",
      **FEATURE_SPELL)
FRACTURE = palier("CHR_LM_Fracture", "4d8", "5d8", "6d8", "7d8", "8d8", "9d8", "11d8")
spell("Target_CHR_FractureSpatiale", "Target", "Fracture spatiale",
      "Sort de niveau 2. L'espace se brise à un point choisi : les créatures à 3 m subissent 4d8 dégâts de force "
      "(jusqu'à 11d8 au niveau 20) et tombent à terre (moitié des dégâts et pas de chute si sauvegarde de "
      "Constitution réussie).",
      using="Target_Shatter", Level="2", UseCosts=slot(2), Icon="Spell_Evocation_Shatter",
      SpellRoll="not SavingThrow(Ability.Constitution, SourceSpellDC())",
      SpellSuccess=f"DealDamage({FRACTURE},Force,Magical);ApplyStatus(PRONE,100,1)",
      SpellFail=f"DealDamage(({FRACTURE})/2,Force,Magical)", TooltipDamageList=f"DealDamage({FRACTURE},Force)",
      **NO_UPCAST)

# ================================================================== NIVEAU 5 : EFFONDREMENT GRAVITATIONNEL
GRAVITE = palier("CHR_LM_Effondrement", "6d8", "6d8", "7d8", "8d8", "9d8", "10d8", "12d8")
spell("Target_CHR_Effondrement", "Target", "Effondrement gravitationnel",
      "Sort de niveau 3. Un puits de gravité de 6 m : les créatures sont attirées vers son centre, subissent 6d8 "
      "dégâts de force (jusqu'à 12d8 au niveau 20) et tombent à terre (moitié des dégâts, ni attraction ni chute "
      "si sauvegarde de Force réussie).",
      using="Target_Shatter", Level="3", UseCosts=slot(3), AreaRadius="6", Icon="Spell_Evocation_Shatter",
      SpellRoll="not SavingThrow(Ability.Strength, SourceSpellDC())",
      SpellSuccess=f"DealDamage({GRAVITE},Force,Magical);Force(-6, OriginToEntity, Neutral, false, true);"
                   "ApplyStatus(PRONE,100,1)",
      SpellFail=f"DealDamage(({GRAVITE})/2,Force,Magical)", TooltipDamageList=f"DealDamage({GRAVITE},Force)",
      **NO_UPCAST)

# ================================================================== NIVEAU 6 : ÉCHO TEMPOREL
ECHO = palier("CHR_LM_Echo", "2d8", "2d8", "2d8", "3d8", "4d8", "4d8", "5d8")
status("CHR_ECHO", "Écho temporel", "Le sort vous frappe une seconde fois : dégâts de force au début de votre tour.",
       "Spell_Transmutation_Haste", StackId="CHR_ECHO", TickType="StartTurn",
       TickFunctors=f"DealDamage({ECHO},Force,Magical)")
passive("CHR_EchoTemporel", "Écho temporel",
        "Une fois par tour, quand un de vos sorts (hors tours de magie) blesse un ennemi, son écho le frappe à "
        "nouveau au début de son tour : 2d8 dégâts de force (3d8 au niveau 12, 4d8 au 15, 5d8 au 20).",
        "Spell_Transmutation_Haste", props="Highlighted;OncePerTurn", StatsFunctorContext="OnDamage",
        Conditions="IsSpell() and not IsCantrip() and Enemy()", StatsFunctors="ApplyStatus(CHR_ECHO,100,1)")

# ================================================================== NIVEAU 7 : VIEILLISSEMENT ACCÉLÉRÉ
status("CHR_VIEILLI", "Vieilli", "Des années ont passé en un instant : désavantage aux attaques et -2 à la CA.",
       "Spell_Necromancy_Blight", StackId="CHR_VIEILLI", Boosts="Disadvantage(AttackRoll);AC(-2)")
VIEUX = palier("CHR_LM_Vieillissement", "8d8", "8d8", "9d8", "10d8", "11d8", "12d8", "14d8")
spell("Target_CHR_Vieillissement", "Target", "Vieillissement accéléré",
      "Sort de niveau 4. Vous faites défiler des décennies sur la cible : 8d8 dégâts nécrotiques (jusqu'à 14d8 au "
      "niveau 20), et elle est vieillie pendant 3 tours (désavantage aux attaques, -2 à la CA). Moitié des "
      "dégâts et pas de vieillissement si sauvegarde de Constitution réussie.",
      using="Target_Blight", Level="4", UseCosts=slot(4), Icon="Spell_Necromancy_Blight",
      SpellRoll="not SavingThrow(Ability.Constitution, SourceSpellDC())",
      SpellSuccess=f"DealDamage({VIEUX},Necrotic,Magical);ApplyStatus(CHR_VIEILLI,100,3)",
      SpellFail=f"DealDamage(({VIEUX})/2,Necrotic,Magical)", TooltipDamageList=f"DealDamage({VIEUX},Necrotic)",
      **NO_UPCAST)

# ================================================================== NIVEAU 9 : PRISON TEMPORELLE + ONDE CHRONIQUE
status("CHR_PRISON", "Prison temporelle", "Figé hors du temps : vous ne pouvez rien faire, mais rien ne peut "
       "vous blesser.", "statIcons_END_Netherbrain_Slow", StackId="CHR_PRISON",
       Boosts="ActionResourceBlock(ActionPoint);ActionResourceBlock(BonusActionPoint);ActionResourceBlock(Movement);"
              "ActionResourceBlock(ReactionActionPoint);" + IMMUNE_TOUT)
spell("Target_CHR_PrisonTemporelle", "Target", "Prison temporelle",
      "Action, 2 Sabliers, une fois par repos court : la cible fait un jet de sauvegarde de Sagesse. Échec : elle "
      "est figée hors du temps pendant 2 tours (aucune action, aucun mouvement, mais immunisée à tous les "
      "dégâts). Sur un allié, aucun jet : il est mis à l'abri.",
      using="Target_HoldPerson", UseCosts=f"ActionPoint:1;{SABLIER}:2", Cooldown="OncePerShortRest",
      SpellFlags=SANS_CONCENTRATION, TargetConditions="Character() and not Dead()",
      Icon="Spell_Enchantment_HoldPerson",
      SpellRoll="not Enemy() or not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellSuccess="ApplyStatus(CHR_PRISON,100,2)", SpellFail="", **FEATURE_SPELL)
ONDE = palier("CHR_LM_Onde", "10d8", "10d8", "10d8", "11d8", "12d8", "13d8", "15d8")
spell("Zone_CHR_OndeChronique", "Zone", "Onde chronique",
      "Sort de niveau 5. Un cône de 9 m où le temps se déchire : 10d8 dégâts de force (jusqu'à 15d8 au niveau "
      "20), et les créatures sont ralenties pendant 2 tours (moitié des dégâts et pas de ralentissement si "
      "sauvegarde de Constitution réussie).",
      using="Zone_ConeOfCold", Level="5", UseCosts=slot(5), Icon="Spell_Transmutation_Slow",
      SpellRoll="not SavingThrow(Ability.Constitution, SourceSpellDC())",
      SpellSuccess=f"DealDamage({ONDE},Force,Magical);ApplyStatus(CHR_RALENTI,100,2)",
      SpellFail=f"DealDamage(({ONDE})/2,Force,Magical)", TooltipDamageList=f"DealDamage({ONDE},Force)",
      **NO_UPCAST)

# ================================================================== NIVEAU 10
passive("CHR_DoubleTemporel", "Double temporel",
        "Un vous-même décalé d'une seconde veille sur vous : vous avez 2 réactions par round.",
        "PassiveFeature_Portent", Boosts="ActionResource(ReactionActionPoint,1,0)")
passive("CHR_MaitreEntropie", "Maître de l'entropie",
        "Vos dégâts de force et nécrotiques ignorent la résistance de vos cibles.", "PassiveFeature_Portent",
        Boosts="IF(not Self()):IgnoreResistance(Force,Resistant);IF(not Self()):IgnoreResistance(Necrotic,Resistant)")

# ================================================================== NIVEAUX 11 et 19 : ARRÊT DU TEMPS
for n, (cd, quand) in ((1, ("OncePerRest", "Une fois par repos long")),
                       (2, ("OncePerShortRest", "Une fois par repos court"))):
    spell(f"Shout_CHR_ArretDuTemps_{n}", "Shout", "Arrêt du temps",
          f"{quand}, sans action : le temps s'arrête pour tous sauf vous. Vous récupérez votre action, votre "
          f"action bonus, votre réaction et tout votre mouvement : vous jouez un nouveau tour complet. Utilisez-le "
          f"à la fin de votre tour.",
          using="Shout_ActionSurge", UseCosts="", Cooldown=cd, Icon="statIcons_END_Netherbrain_Slow_Aura",
          SpellProperties="RestoreResource(ActionPoint,100%,0);RestoreResource(BonusActionPoint,100%,0);"
                          "RestoreResource(Movement,100%,0);RestoreResource(ReactionActionPoint,100%,0)",
          **FEATURE_SPELL)
    hidden(f"CHR_ArretDuTemps_{n}_Sort", Boosts=f"UnlockSpell(Shout_CHR_ArretDuTemps_{n})")
NEANT = palier("CHR_LM_Neant", "12d10", "12d10", "12d10", "12d10", "13d10", "14d10", "16d10")
spell("Projectile_CHR_RayonDuNeant", "Projectile", "Rayon du néant",
      "Sort de niveau 6. Un rayon qui efface la matière : 12d10 dégâts de force (jusqu'à 16d10 au niveau 20). "
      "Une sauvegarde de Dextérité réussie l'évite entièrement. Une créature réduite à 0 PV est réduite en "
      "poussière.",
      using="Projectile_Disintegrate", Level="6", UseCosts=slot(6), Icon="Spell_Transmutation_Disintegrate",
      SpellSuccess=f"DealDamage({NEANT},Force,Magical)", TooltipDamageList=f"DealDamage({NEANT},Force)",
      **NO_UPCAST)

# ================================================================== NIVEAU 12
passive("CHR_SablierDeCombat", "Sablier inépuisable",
        "Au début de chaque combat, vous récupérez 1 Sablier.", "PassiveFeature_Portent",
        StatsFunctorContext="OnCombatStarted", StatsFunctors=f"RestoreResource(SELF,{SABLIER},1,0)")

# ================================================================== NIVEAUX 13 à 20 (avec un mod niveau 20)
SING = palier("CHR_LM_Singularite", "14d8", "14d8", "14d8", "14d8", "14d8", "15d8", "16d8")
spell("Target_CHR_Singularite", "Target", "Singularité",
      "Sort de niveau 7. Un trou noir s'ouvre : les créatures à 9 m sont aspirées vers son centre, subissent "
      "14d8 dégâts de force (16d8 au niveau 20) et tombent à terre (moitié des dégâts, ni attraction ni chute si "
      "sauvegarde de Force réussie).",
      using="Target_Shatter", Level="7", UseCosts=slot(7), AreaRadius="9", Icon="Spell_Evocation_Shatter",
      SpellRoll="not SavingThrow(Ability.Strength, SourceSpellDC())",
      SpellSuccess=f"DealDamage({SING},Force,Magical);Force(-9, OriginToEntity, Neutral, false, true);"
                   "ApplyStatus(PRONE,100,1)",
      SpellFail=f"DealDamage(({SING})/2,Force,Magical)", TooltipDamageList=f"DealDamage({SING},Force)", **NO_UPCAST)

# --- Réalité (niveau 14 et plus)
for cible, roll, desc in (("Allie", 20, "un allié (ou vous) à 18 m rate un jet de sauvegarde : il devient un 20"),
                          ("Ennemi", 1, "un ennemi à 18 m réussit un jet de sauvegarde : il devient un 1")):
    rel = ("(Ally(context.Target,context.Observer) or Self(context.Target,context.Observer))" if roll == 20
           else "Enemy(context.Target,context.Observer)")
    interrupt(f"Interrupt_CHR_Reecrire_{cible}", "Réécrire l'instant",
              f"Réaction, 1 Sablier : quand {desc}. La réalité se plie à votre volonté.",
              "PassiveFeature_Portent_20", InterruptContext="OnPostRoll", InterruptContextScope="Nearby",
              Conditions=f"IsAbleToReact(context.Observer) and HasInterruptedSavingThrow() and {rel} and "
                         f"not AnyEntityIsItem() and IsSetInterruptInteresting({roll}) and "
                         "not DistanceToEntityGreaterThan(18,context.ObserverPosition,context.Target)",
              Properties=f"SetRoll({roll})", Cost=f"ReactionActionPoint:1;{SABLIER}:1",
              Stack=f"CHR_Reecrire_{cible}", InterruptDefaultValue="Ask;Enabled", Container="YesNoDecision")
passive("CHR_ReecrireInstant", "Réécrire l'instant",
        "Réaction, 1 Sablier : un jet de sauvegarde raté par un allié à 18 m devient un 20, ou un jet réussi par un "
        "ennemi devient un 1.", "PassiveFeature_Portent_20",
        Boosts="UnlockInterrupt(Interrupt_CHR_Reecrire_Allie);UnlockInterrupt(Interrupt_CHR_Reecrire_Ennemi)")
for n, (seuil, bonus) in ((1, ("19", 1)), (2, ("18", 2))):
    passive(f"CHR_RealiteBrisee_{n}", f"Réalité brisée (critique {seuil}-20)",
            f"La réalité cède sous vos coups : vos attaques, y compris vos sorts d'attaque, infligent un coup "
            f"critique sur {seuil}-20.", "PassiveFeature_Portent_20", Boosts=f"ReduceCriticalAttackThreshold({bonus})")

status("CHR_REALITE_ALTEREE", "Réalité altérée", "Votre réalité est réécrite : vulnérable à tous les dégâts.",
       "PassiveFeature_Portent_20", StackId="CHR_REALITE_ALTEREE",
       Boosts=";".join(f"Resistance({t},Vulnerable)" for t in TYPES))
spell("Target_CHR_Alteration", "Target", "Altération",
      "Sort de niveau 8. Vous réécrivez la réalité dans une zone de 6 m : les ennemis subissent 8d8 dégâts "
      "psychiques et deviennent vulnérables à tous les dégâts pendant 3 tours (moitié des dégâts et pas de "
      "vulnérabilité si sauvegarde de Sagesse réussie).",
      using="Target_Shatter", Level="8", UseCosts=slot(8), AreaRadius="6", Icon="PassiveFeature_Portent_20",
      TargetConditions="Enemy() and not Dead()",
      SpellRoll="not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellSuccess="DealDamage(8d8,Psychic,Magical);ApplyStatus(CHR_REALITE_ALTEREE,100,3)",
      SpellFail="DealDamage((8d8)/2,Psychic,Magical)", TooltipDamageList="DealDamage(8d8,Psychic)", **NO_UPCAST)
spell("Projectile_CHR_Effacement", "Projectile", "Effacement",
      "Sort de niveau 9. Vous effacez une créature de la réalité : si elle a 150 PV ou moins, elle cesse "
      "d'exister. Sinon, elle subit 16d10 dégâts de force. Aucun jet de sauvegarde.",
      using="Projectile_Disintegrate", Level="9", UseCosts=slot(9), Icon="Spell_Transmutation_Disintegrate",
      SpellRoll="", SpellSuccess="", SpellFail="",
      SpellProperties="IF(HasHPLessThan(151)):Kill();IF(not HasHPLessThan(151)):DealDamage(16d10,Force,Magical)",
      TooltipDamageList="DealDamage(16d10,Force)", **NO_UPCAST)

passive("CHR_Ancrage", "Ancrage temporel",
        "Vous êtes ancré dans le temps et l'espace : immunité aux états Ralenti, Paralysé, Étourdi, Entravé, Banni "
        "et À terre.", "PassiveFeature_Portent",
        Boosts="StatusImmunity(SLOW);StatusImmunity(CHR_RALENTI);StatusImmunity(SG_Paralyzed);"
               "StatusImmunity(SG_Stunned);StatusImmunity(SG_Restrained);StatusImmunity(BANISHED);"
               "StatusImmunity(SG_Prone)")
PARADOXE = ";".join(["RegainHitPoints(MaxHP)"] + [f"RestoreResource(SpellSlot,100%,{n})" for n in range(1, 10)] +
                    ["ResetCooldowns(UntilRest)", f"RestoreResource({SABLIER},100%,0)"])
spell("Shout_CHR_Paradoxe", "Shout", "Paradoxe",
      "Une fois par repos long : le temps revient en arrière pour vous et vos alliés à 18 m. Tous retrouvent la "
      "totalité de leurs PV, de leurs emplacements de sort et de leurs capacités à recharge.",
      using="Shout_HealingWord_Mass", UseCosts="ActionPoint:1", Cooldown="OncePerRest", AreaRadius="18",
      Icon="PassiveFeature_ArcaneWard", TargetConditions="not Enemy() and not Dead()",
      SpellRoll="", SpellSuccess="", SpellFail="", SpellProperties=PARADOXE, TooltipDamageList="",
      **FEATURE_SPELL)

# ================================================================== PROGRESSION (capacités)
feat(1, passives=["CHR_Prescience", "CHR_Resonance", "CHR_Rembobinage"], boosts=[f"ActionResource({SABLIER},2,0)"],
     spells=["Shout_CHR_Acceleration", "Projectile_CHR_EclatTemporel", "Projectile_CHR_RayonEntropie"])
feat(2, passives=["CHR_Memoire_1"], spells=["Target_CHR_Ralentir"])
feat(3, spells=["Target_CHR_Faille", "Target_CHR_FractureSpatiale"])
feat(5, boosts=[f"ActionResource({SABLIER},1,0)"], spells=["Target_CHR_Effondrement"])
feat(6, passives=["CHR_EchoTemporel", "CHR_Memoire_2"])
feat(7, spells=["Target_CHR_Vieillissement"])
feat(9, boosts=[f"ActionResource({SABLIER},1,0)"], spells=["Target_CHR_PrisonTemporelle", "Zone_CHR_OndeChronique"])
feat(10, passives=["CHR_DoubleTemporel", "CHR_MaitreEntropie", "CHR_Memoire_3"])
feat(11, passives=["CHR_ArretDuTemps_1_Sort"], spells=["Projectile_CHR_RayonDuNeant"])
feat(12, passives=["CHR_SablierDeCombat"])
feat(13, boosts=[f"ActionResource({SABLIER},1,0)"], spells=["Target_CHR_Singularite"])
feat(14, passives=["CHR_ReecrireInstant", "CHR_RealiteBrisee_1", "CHR_Memoire_4"])
feat(15, spells=["Target_CHR_Alteration"])
feat(17, boosts=[f"ActionResource({SABLIER},1,0)"], spells=["Projectile_CHR_Effacement"])
feat(18, passives=["CHR_Ancrage", "CHR_RealiteBrisee_2"], removed=["CHR_RealiteBrisee_1"])
feat(19, passives=["CHR_ArretDuTemps_2_Sort"], removed=["CHR_ArretDuTemps_1_Sort"])
feat(20, spells=["Shout_CHR_Paradoxe"])


def feature_spelllists():
    """Listes de sorts accordés (toujours préparés) : {niveau: uuid}."""
    return {lv: spelllist(f"CHR_Capacites_{lv}", f"Chronomancien : capacités (niveau {lv})", f["spells"])
            for lv, f in FEATURES.items() if f["spells"]}


def sorts_a_preparer():
    """Tours de magie à choisir, et sorts du jeu à préparer par niveau de sort."""
    tours = spelllist("CHR_ToursEspaceTemps", "Chronomancien : tours de magie", TOURS_JEU)
    sorts = {n: spelllist(f"CHR_SortsEspaceTemps_{n}", f"Chronomancien : sorts de niveau {n}", lst)
             for n, lst in SORTS_JEU.items()}
    return tours, sorts
