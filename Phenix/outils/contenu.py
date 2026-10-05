"""Contenu du mod « Classe Phénix » : capacités, sorts, états, ressources.

Mod indépendant. Tout ce qu'il crée porte le préfixe PHX_ (sorts : <Type>_PHX_<Nom>).
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
# Sorts du jeu que le Phénix peut apprendre : uniquement le feu et la lumière (radiant).
# Source : bg3.wiki (sorts de classe dont les dégâts sont de feu ou radiants, plus les sorts de lumière).
TOURS_FEU_LUMIERE = ["Projectile_FireBolt", "Shout_ProduceFlame", "Target_SacredFlame", "Target_Light",
                     "Target_DancingLights"]
SORTS_FEU_LUMIERE = {
    1: ["Zone_BurningHands", "Projectile_GuidingBolt", "Target_HellishRebuke", "Target_Smite_Searing",
        "Shout_DivineFavor", "Target_FaerieFire"],
    2: ["Projectile_ScorchingRay", "Target_FlamingSphere", "Target_HeatMetal", "Shout_FlameBlade",
        "Target_Moonbeam", "Target_Smite_Branding_Container"],
    3: ["Projectile_Fireball", "Shout_SpiritGuardians", "Shout_CrusadersMantle", "Target_Daylight_Container",
        "Target_Smite_Blinding"],
    4: ["Wall_WallOfFire", "Shout_FireShield", "Target_GuardianOfFaith"],
    5: ["Target_FlameStrike"],
    6: ["Zone_Sunbeam"],
}


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


# ================================================================== PHÉNIX
PHENIX = "PHX_Phenix"
FEATURE_SPELL = dict(Level="0", **NO_UPCAST)
ENNEMI = "Enemy() and not Dead()"

# Capacités par niveau : FEATURES[voie][niveau] = {"passives", "removed", "spells", "boosts"}
# (voie None = classe de base)
FEATURES = {}


def feat(voie, level, passives=(), removed=(), spells=(), boosts=()):
    f = FEATURES.setdefault(voie, {}).setdefault(level, {"passives": [], "removed": [], "spells": [], "boosts": []})
    f["passives"] += list(passives)
    f["removed"] += list(removed)
    f["spells"] += list(spells)
    f["boosts"] += list(boosts)


def explosion(name, titre, desc, radius, success, fail=None, save=True, targets="not Dead()", **data):
    """Explosion déclenchée par CreateExplosion (sans coût, ne se lance pas à la main)."""
    extra = dict(SpellRoll="not SavingThrow(Ability.Dexterity, SourceSpellDC())", SpellSuccess=success,
                 SpellFail=fail or success) if save else dict(SpellRoll="", SpellSuccess=success, SpellFail="")
    return spell(name, "Projectile", titre, desc, using="Projectile_Fireball", Level="0", UseCosts="",
                 AreaRadius=str(radius), ExplodeRadius=str(radius), TargetConditions=targets,
                 SpellProperties="", Icon="Spell_Evocation_FlameStrike", **extra, **NO_UPCAST, **data)


# ================================================================== RESSOURCE : BRAISES
resource("PHX_Braise", "Braises",
         "Feu accumulé par le Phénix : +1 quand il inflige ou subit des dégâts de feu (une fois par tour). "
         "Se dépense pour Attiser, Propager ou Purifier.", "Never")

# ================================================================== NIVEAU 1
hidden("PHX_Marqueur")
passive("PHX_FlammeLoyale", "Flamme loyale",
        "Votre feu ne blesse jamais vos alliés ni vous-même : les dégâts de feu que vous leur infligez "
        "leur sont rendus aussitôt en PV, et ils ne prennent pas feu. Vos sorts de Phénix ne visent de "
        "toute façon que les ennemis.",
        "PassiveFeature_ElementalAdept_Fire", StatsFunctorContext="OnDamage",
        Conditions="IsDamageTypeFire() and (Self() or Ally()) and not Enemy()",
        StatsFunctors="RegainHitPoints(DamageDone);RemoveStatus(BURNING)")

FB_TICK = palier("PHX_LM_FlammeBienfaitrice_Tour", "1d6", "2d6", "3d6", "4d6", "5d6", "6d6", "8d6")
FB_SOIN = palier("PHX_LM_FlammeBienfaitrice", "2d8", "3d8", "4d8", "5d8", "6d8", "7d8", "9d8")
status("PHX_FLAMME_BIENFAITRICE", "Flamme bienfaitrice",
       "Ces flammes soignent au lieu de brûler : des PV au début de chaque tour (1d6, puis 2d6 au niveau 5, "
       "3d6 au 9, 4d6 au 12, 5d6 au 15, 6d6 au 17, 8d6 au 20).",
       "Status_Burning", using="BURNING", StackId="PHX_FLAMME_BIENFAITRICE",
       TickType="StartTurn", TickFunctors=f"RegainHitPoints({FB_TICK})", OnApplyFunctors="", Boosts="",
       StatusGroups="")
spell("Target_PHX_FlammeBienfaitrice", "Target", "Flamme bienfaitrice",
      "Enveloppe un allié de flammes bienfaitrices : il récupère 2d8 + votre modificateur de Charisme PV, "
      "puis 1d6 PV au début de chacun de ses tours pendant 3 tours. Il a l'air en feu, mais ce feu le soigne. "
      "Les soins augmentent avec votre niveau (jusqu'à 9d8 et 8d6 par tour au niveau 20).",
      using="Target_CureWounds", Level="1", UseCosts=slot(1), Icon="Spell_HarmonyOfFireAndWater",
      TargetConditions="not Enemy() and not Dead()",
      SpellProperties=f"RegainHitPoints({FB_SOIN}+SpellCastingAbilityModifier);"
                      "ApplyStatus(PHX_FLAMME_BIENFAITRICE,100,3)",
      TooltipStatusApply="ApplyStatus(PHX_FLAMME_BIENFAITRICE,100,3)", **NO_UPCAST)

status("PHX_CENDRES_ARDENTES", "Cendres ardentes",
       "Vos cendres couvent : au bout de 2 tours à terre, vous vous relevez avec 1/6 de vos PV maximum.",
       "statIcons_FireInfusion", StackId="PHX_CENDRES_ARDENTES",
       OnRemoveFunctors="IF(HasStatus('DOWNED')):RegainHitPoints(MaxHP/6,Guaranteed)",
       StatusPropertyFlags="DisableCombatlog")
passive("PHX_CendresArdentes", "Cendres ardentes",
        "Quand vous tombez à terre (0 PV), vos cendres couvent : au bout de 2 tours, si personne ne vous a "
        "relevé, vous vous relevez seul avec 1/6 de vos PV maximum.",
        "statIcons_FireInfusion", StatsFunctorContext="OnStatusApplied",
        Conditions="StatusId('DOWNED')", StatsFunctors="ApplyStatus(SELF,PHX_CENDRES_ARDENTES,100,2)")

# Tour de magie : Plume ardente (une 2e version rebondit à partir du niveau 5)
PLUME = dict(using="Projectile_FireBolt", Level="0", Icon="Spell_Transmutation_FeatherFall",
             TargetConditions="not Self() and not Dead()",
             SpellSuccess="DealDamage(LevelMapValue(D10Cantrip),Fire,Magical)",
             TooltipDamageList="DealDamage(LevelMapValue(D10Cantrip),Fire)")
spell("Projectile_PHX_PlumeArdente", "Projectile", "Plume ardente",
      "Tour de magie. Une plume de feu frappe une cible : 1d10 dégâts de feu (2d10 au niveau 5, 3d10 au "
      "niveau 10).", AmountOfTargets="1", **PLUME)
spell("Projectile_PHX_PlumeArdente_Rebond", "Projectile", "Plume ardente",
      "Tour de magie. La plume rebondit : deux plumes de feu, choisissez deux cibles (ou deux fois la même). "
      "Chacune inflige 1d10 dégâts de feu (2d10 au niveau 5, 3d10 au niveau 10).", AmountOfTargets="2", **PLUME)
# Le sort est donné par un passif invisible : au niveau 5, le passif est retiré (et le sort à 1 cible
# avec lui) et remplacé par celui qui donne la version qui rebondit. Une progression ne sait pas retirer
# un sort directement.
hidden("PHX_PlumeArdente_Sort", Boosts="UnlockSpell(Projectile_PHX_PlumeArdente,,,,Charisma)")
hidden("PHX_PlumeArdente_Rebond_Sort", Boosts="UnlockSpell(Projectile_PHX_PlumeArdente_Rebond,,,,Charisma)")

# ================================================================== NIVEAU 2 : BRAISES
passive("PHX_Braises", "Braises",
        "Une fois par tour, quand vous infligez des dégâts de feu, vous gagnez 1 Braise (maximum 3, puis 5 "
        "au niveau 9). Dépensez-les avec Attiser, Propager ou Purifier.",
        "statIcons_GlowingFlask", props="Highlighted;OncePerTurn", StatsFunctorContext="OnDamage",
        Conditions="IsDamageTypeFire() and not Self()", StatsFunctors="RestoreResource(SELF,PHX_Braise,1,0)")
hidden("PHX_BraisesAbsorbees", props="IsHidden;OncePerTurn",
       StatsFunctorContext="OnDamagedPrevented;OnDamaged", Conditions="IsDamageTypeFire()",
       StatsFunctors="RestoreResource(SELF,PHX_Braise,1,0)")

BRAISE_COST = "BonusActionPoint:1;PHX_Braise:1"
hidden("PHX_Attiser_Effet", props="IsHidden;OncePerAttack", StatsFunctorContext="OnDamage",
       Conditions="IsDamageTypeFire() and Enemy()",
       StatsFunctors="DealDamage(1d6,Fire,Magical);RemoveStatus(SELF,PHX_ATTISER)")
status("PHX_ATTISER", "Attiser", "Votre prochaine attaque ou votre prochain sort de feu inflige 1d6 dégâts de feu "
       "supplémentaires.", "statIcons_Hellfire", StackId="PHX_ATTISER", Passives="PHX_Attiser_Effet")
spell("Shout_PHX_Attiser", "Shout", "Braises : Attiser",
      "Action bonus, 1 Braise : votre prochaine attaque ou votre prochain sort de feu contre un ennemi "
      "inflige 1d6 dégâts de feu supplémentaires (dans les 2 tours).",
      using="Shout_DivineSense", Icon="statIcons_Hellfire", UseCosts=BRAISE_COST, Cooldown="",
      SpellProperties="ApplyStatus(SELF,PHX_ATTISER,100,2)", TooltipStatusApply="ApplyStatus(PHX_ATTISER,100,2)",
      **FEATURE_SPELL)

explosion("Projectile_PHX_Propagation", "Propagation", "Le feu se propage aux ennemis proches.", 3,
          "IF(Enemy()):DealDamage(2d6,Fire,Magical)", "IF(Enemy()):DealDamage((2d6)/2,Fire,Magical)")
hidden("PHX_Propager_Effet", props="IsHidden;OncePerAttack", StatsFunctorContext="OnDamage",
       Conditions="IsDamageTypeFire() and IsSpell() and Enemy()",
       StatsFunctors="CreateExplosion(Projectile_PHX_Propagation);RemoveStatus(SELF,PHX_PROPAGER)")
status("PHX_PROPAGER", "Propager", "Votre prochain sort de feu se propage autour de sa cible.",
       "Spell_Evocation_WallOfFire", StackId="PHX_PROPAGER", Passives="PHX_Propager_Effet")
spell("Shout_PHX_Propager", "Shout", "Braises : Propager",
      "Action bonus, 1 Braise : votre prochain sort de feu qui touche un ennemi se propage : les ennemis à "
      "3 m de lui subissent 2d6 dégâts de feu (moitié en cas de sauvegarde de Dextérité réussie).",
      using="Shout_DivineSense", Icon="Spell_Evocation_WallOfFire", UseCosts=BRAISE_COST, Cooldown="",
      SpellProperties="ApplyStatus(SELF,PHX_PROPAGER,100,2)", TooltipStatusApply="ApplyStatus(PHX_PROPAGER,100,2)",
      **FEATURE_SPELL)

PURGE = ";".join(f"RemoveStatus({g})" for g in ("SG_Poisoned", "SG_Blinded", "SG_Frightened", "SG_Charmed",
                                                  "SG_Paralyzed", "SG_Disease"))
spell("Shout_PHX_Purifier", "Shout", "Braises : Purifier",
      "Action bonus, 1 Braise : une onde de feu purificateur libère vos alliés à 9 m (et vous-même) des états "
      "Empoisonné, Aveuglé, Effrayé, Charmé, Paralysé et des maladies.",
      using="Shout_HealingWord_Mass", Icon="Action_Paladin_LayOnHands_Cure", UseCosts=BRAISE_COST,
      AreaRadius="9", TargetConditions="not Enemy() and not Dead()", SpellProperties=PURGE,
      SpellRoll="", SpellSuccess="", SpellFail="", TooltipDamageList="", **FEATURE_SPELL)

# ================================================================== NIVEAU 3 : BOND DE FLAMME (sort de niveau 2)
explosion("Projectile_PHX_GerbeBond", "Gerbe de flammes", "Gerbe de feu au départ et à l'arrivée du bond.", 3,
          "IF(Enemy()):DealDamage(2d6,Fire,Magical)", "IF(Enemy()):DealDamage((2d6)/2,Fire,Magical)")
spell("Target_PHX_BondDeFlamme", "Target", "Bond de flamme",
      "Vous vous téléportez jusqu'à 9 m dans une gerbe de feu : les ennemis à 3 m de votre point de départ "
      "et de votre point d'arrivée subissent 2d6 dégâts de feu (moitié si sauvegarde de Dextérité réussie).",
      using="Target_MistyStep", Level="2", UseCosts="BonusActionPoint:1;SpellSlotsGroup:1:1:2", Range="9",
      Icon="Action_Monk_StepOfTheWind_Dash",
      SpellProperties="CreateExplosion(Projectile_PHX_GerbeBond);GROUND:TeleportSource();"
                      "GROUND:CreateExplosion(Projectile_PHX_GerbeBond)", **NO_UPCAST)

# ================================================================== NIVEAU 5
passive("PHX_Ignifuge", "Ignifugé",
        "Le feu ne vous atteint plus : immunité aux dégâts de feu et à l'état En feu.",
        "Spell_Abjuration_ProtectionFromEnergy_Fire",
        Boosts="Resistance(Fire,Immune);StatusImmunity(BURNING)")

lm = palier("PHX_LM_PluieDePlumes", "4d6", "4d6", "5d6", "6d6", "7d6", "8d6", "10d6")
PP_SOIN = palier("PHX_LM_PluieDePlumes_Soin", "3d8", "3d8", "4d8", "5d8", "6d8", "7d8", "9d8")
spell("Projectile_PHX_PluieDePlumes", "Projectile", "Pluie de plumes",
      "Une pluie de plumes enflammées sur une zone de 6 m : les ennemis subissent 4d6 dégâts de feu (moitié "
      "si sauvegarde de Dextérité réussie), les alliés pris dedans récupèrent 3d8 PV. Dégâts et soins "
      "augmentent avec votre niveau (jusqu'à 10d6 et 9d8 au niveau 20).",
      using="Projectile_Fireball", Level="3", UseCosts=slot(3), Icon="Spell_Transmutation_FeatherFall",
      AreaRadius="6", ExplodeRadius="6", TargetConditions="not Dead()", SpellProperties="",
      SpellRoll="not SavingThrow(Ability.Dexterity, SourceSpellDC())",
      SpellSuccess=f"IF(Enemy()):DealDamage({lm},Fire,Magical);IF(not Enemy()):RegainHitPoints({PP_SOIN})",
      SpellFail=f"IF(Enemy()):DealDamage(({lm})/2,Fire,Magical);IF(not Enemy()):RegainHitPoints({PP_SOIN})",
      TooltipDamageList=f"DealDamage({lm},Fire)", **NO_UPCAST)
LARMES = palier("PHX_LM_LarmesDePhenix", "5d8", "5d8", "6d8", "7d8", "8d8", "9d8", "10d8")
spell("Target_PHX_LarmesDePhenix", "Target", "Larmes de phénix",
      "Des larmes de feu guérisseur : un allié récupère 5d8 + votre modificateur de Charisme PV, gagne autant "
      "de PV temporaires que votre niveau, et est libéré des poisons, des maladies et des malédictions. Les "
      "soins augmentent avec votre niveau (jusqu'à 10d8 au niveau 20).",
      using="Target_CureWounds", Level="3", UseCosts=slot(3), Icon="Spell_Evocation_Heal",
      TargetConditions="not Enemy() and not Dead()",
      SpellProperties=f"RegainHitPoints({LARMES}+SpellCastingAbilityModifier);GainTemporaryHitPoints(Level);"
                      "RemoveStatus(SG_Poisoned);"
                      "RemoveStatus(SG_Disease);RemoveStatus(SG_Cursed)", **NO_UPCAST)

# ================================================================== NIVEAUX 6 et 11 : BOUCLIER DE FLAMMES
for dmg, suffix in (("1d8", "1"), ("2d8", "2"), ("3d8", "3")):
    passive(f"PHX_BouclierFlammes_{suffix}", "Bouclier de flammes" + ("" if suffix == "1" else f" ({dmg})"),
            f"Un ennemi qui vous frappe au corps à corps subit {dmg} dégâts de feu.",
            "Spell_Evocation_FireShield_Warm", StatsFunctorContext="OnDamaged",
            Conditions="IsMeleeAttack()", StatsFunctors=f"DealDamage(SWAP,{dmg},Fire,Magical)")

# ================================================================== NIVEAU 7 : FEU SACRÉ + BÛCHER SACRÉ
passive("PHX_FeuSacre", "Feu sacré",
        "Vos dégâts de feu ignorent la résistance au feu de vos cibles.",
        "statIcons_Hellfire", Boosts="IF(not Self()):IgnoreResistance(Fire,Resistant)")
passive("PHX_FeuSacre_2", "Feu sacré (immunité)",
        "Vos dégâts de feu ignorent aussi l'immunité au feu de vos cibles.",
        "statIcons_Hellfire", Boosts="IF(not Self()):IgnoreResistance(Fire,Immune)")


def aura_double(name, titre, desc, icon, radius, enemy_status, ally_status):
    return status(name, titre, desc, icon, StackId=name, AuraRadius=str(radius),
                  AuraStatuses=f"IF(Enemy() and not Dead()):ApplyStatus({enemy_status});"
                               f"IF(not Enemy() and not Dead()):ApplyStatus({ally_status})",
                  StatusPropertyFlags="IgnoreResting", StatusGroups="SG_RemoveOnRespec")


BU_DGT = palier("PHX_LM_Bucher", "2d8", "2d8", "3d8", "4d8", "5d8", "6d8", "7d8")
BU_SOIN = palier("PHX_LM_Bucher_Soin", "2d8", "2d8", "3d8", "4d8", "5d8", "6d8", "7d8")
status("PHX_BUCHER_BRULURE", "Bûcher sacré", "Vous subissez des dégâts de feu au début de votre tour.",
       "Spell_Evocation_FlameStrike", TickType="StartTurn", TickFunctors=f"DealDamage({BU_DGT},Fire,Magical)",
       StackId="PHX_BUCHER_BRULURE")
status("PHX_BUCHER_SOIN", "Bûcher sacré", "Vous récupérez des PV au début de votre tour.",
       "Spell_Evocation_FlameStrike", TickType="StartTurn", TickFunctors=f"RegainHitPoints({BU_SOIN})",
       StackId="PHX_BUCHER_SOIN")
aura_double("PHX_BUCHER", "Bûcher sacré", "Un bûcher sacré brûle autour de vous.", "Spell_Evocation_FlameStrike",
            6, "PHX_BUCHER_BRULURE", "PHX_BUCHER_SOIN")
spell("Shout_PHX_BucherSacre", "Shout", "Bûcher sacré",
      "Pendant 4 tours, un bûcher sacré de 6 m brûle autour de vous : au début de leur tour, les ennemis "
      "subissent 2d8 dégâts de feu et vos alliés récupèrent 2d8 PV (3d8 au niveau 9, 4d8 au 12, jusqu'à 7d8 au "
      "niveau 20).",
      # Esprits gardiens est un conteneur de variantes : on part d'Aura du croisé (aura simple) et on vide
      # tout ce qui pourrait en être hérité (variantes, jet de sauvegarde, dégâts affichés).
      using="Shout_CrusadersMantle", Level="4", UseCosts=slot(4), Icon="Spell_Evocation_FlameStrike",
      ContainerSpells="", SpellContainerID="", SpellRoll="", SpellSuccess="", SpellFail="",
      TooltipDamageList="", TooltipAttackSave="", DescriptionParams="",
      SpellProperties="ApplyStatus(SELF,PHX_BUCHER,100,4)", TooltipStatusApply="ApplyStatus(PHX_BUCHER,100,4)",
      **NO_UPCAST)

# ================================================================== NIVEAU 9 : CŒUR DE PHÉNIX + PLUME DE RENAISSANCE
passive("PHX_CoeurDePhenix", "Cœur de phénix",
        "Le feu vous soigne au lieu de vous blesser, y compris le vôtre : chaque fois que du feu vous "
        "atteint, vous récupérez 3d8 PV (4d8 au niveau 12, 5d8 au 15, 6d8 au 20).",
        "statIcons_AbsorbElement_Fire", props="Highlighted;OncePerAttack",
        StatsFunctorContext="OnDamagedPrevented;OnDamaged", Conditions="IsDamageTypeFire()",
        StatsFunctors=f"RegainHitPoints({palier('PHX_LM_Coeur', '3d8', '3d8', '3d8', '4d8', '5d8', '5d8', '6d8')})")

explosion("Projectile_PHX_GerbePlume", "Gerbe de renaissance", "Gerbe de feu d'une Plume de renaissance.", 4,
          "IF(Enemy()):DealDamage(3d6,Fire,Magical)", "IF(Enemy()):DealDamage((3d6)/2,Fire,Magical)")
status("PHX_PLUME_RENAISSANCE_DOWNED", "Renaissance", "Vous renaissez de vos cendres.", "Status_Fly",
       using="RELENTLESS_ENDURANCE_DOWNED", stype="DOWNED",
       OnApplyFunctors="RemoveStatus(PHX_PLUME_RENAISSANCE);RegainHitPoints(MaxHP/2,Guaranteed);"
                       "CreateExplosion(Projectile_PHX_GerbePlume)")
status("PHX_PLUME_RENAISSANCE", "Plume de renaissance",
       "Si vous tombez à 0 PV, vous renaissez aussitôt avec la moitié de vos PV dans une gerbe de feu (une fois).",
       "Spell_Transmutation_FeatherFall", StackId="PHX_PLUME_RENAISSANCE",
       Boosts="DownedStatus(PHX_PLUME_RENAISSANCE_DOWNED,7)",
       StatusPropertyFlags="ApplyToDead;IgnoreResting")
PLUME_RENAISSANCE = dict(using="Target_CureWounds", Icon="Spell_Transmutation_FeatherFall",
                         TargetConditions="not Enemy() and not Dead()",
                         SpellProperties="ApplyStatus(PHX_PLUME_RENAISSANCE,100,-1)",
                         TooltipStatusApply="ApplyStatus(PHX_PLUME_RENAISSANCE,100,-1)")
spell("Target_PHX_PlumeDeRenaissance", "Target", "Plume de renaissance",
      "Un allié reçoit une plume de phénix jusqu'à son prochain repos long : s'il tombe à 0 PV, il renaît "
      "aussitôt avec la moitié de ses PV dans une gerbe de feu (3d6 dégâts aux ennemis à 4 m). Une seule fois.",
      Level="5", UseCosts=slot(5), **PLUME_RENAISSANCE, **NO_UPCAST)

# ================================================================== NIVEAU 10 : RENAISSANCE DU PHÉNIX
hidden("PHX_Renouveau_Effet", props="IsHidden;OncePerAttack", StatsFunctorContext="OnDamage",
       Conditions="Enemy()", StatsFunctors="DealDamage(1d6,Fire,Magical)")
status("PHX_RENOUVEAU", "Renouveau", "Vos attaques et vos sorts infligent 1d6 dégâts de feu supplémentaires.",
       "statIcons_FireInfusion", StackId="PHX_RENOUVEAU", Passives="PHX_Renouveau_Effet")
explosion("Projectile_PHX_ExplosionRenaissance", "Renaissance du phénix",
          "Explosion de feu de la renaissance du Phénix.", 6,
          "IF(Enemy()):DealDamage(6d6,Fire,Magical);"
          "IF(not Enemy() and HasStatus('DOWNED') and HasPassive('PHX_Cendre_RenaissanceCollective',context.Source)):"
          "RegainHitPoints(MaxHP/2,Guaranteed)",
          "IF(Enemy()):DealDamage((6d6)/2,Fire,Magical);"
          "IF(not Enemy() and HasStatus('DOWNED') and HasPassive('PHX_Cendre_RenaissanceCollective',context.Source)):"
          "RegainHitPoints(MaxHP/2,Guaranteed)")
status("PHX_RENAISSANCE_DOWNED", "Renaissance du phénix", "Vous renaissez de vos cendres.", "Status_Fly",
       using="RELENTLESS_ENDURANCE_DOWNED", stype="DOWNED",
       OnApplyFunctors="RemoveStatus(PHX_RENAISSANCE_PRETE);RegainHitPoints(MaxHP,Guaranteed);"
                       "CreateExplosion(Projectile_PHX_ExplosionRenaissance);ApplyStatus(PHX_RENOUVEAU,100,2)")
status("PHX_RENAISSANCE_PRETE", "Renaissance du phénix",
       "La prochaine fois que vous tombez à 0 PV, vous renaissez avec tous vos PV.",
       "Status_Fly", StackId="PHX_RENAISSANCE_PRETE", Boosts="DownedStatus(PHX_RENAISSANCE_DOWNED,8)",
       StatusPropertyFlags="DisableOverhead;ApplyToDead;IgnoreResting", StatusGroups="SG_RemoveOnRespec")
passive("PHX_Renaissance", "Renaissance du phénix",
        "Une fois par repos long, quand vous tombez à 0 PV, vous ne tombez pas : vous renaissez aussitôt avec "
        "tous vos PV dans une grande explosion de feu (6d6 dégâts aux ennemis à 6 m, aucun aux alliés). "
        "Renouveau : pendant 2 tours, vos attaques et sorts infligent 1d6 dégâts de feu supplémentaires. "
        "Ensuite, Cendres ardentes reprend le relais.",
        "Status_Fly", props="Highlighted;OncePerLongRest", StatsFunctorContext="OnCreate;OnLongRest",
        StatsFunctors="ApplyStatus(SELF,PHX_RENAISSANCE_PRETE,100,-1)")

# ================================================================== NIVEAU 11 : ENVOL DU PHÉNIX (sort de niveau 6)
explosion("Projectile_PHX_ExplosionEnvol", "Envol du phénix : explosion",
          "Le phénix invoqué explose en disparaissant.", 6,
          "IF(Enemy()):DealDamage(4d6,Fire,Magical);IF(not Enemy()):RegainHitPoints(2d8)",
          "IF(Enemy()):DealDamage((4d6)/2,Fire,Magical);IF(not Enemy()):RegainHitPoints(2d8)")
status("PHX_ENVOL_EXPLOSION", "Phénix invoqué",
       "Quand cette créature meurt ou disparaît, elle explose : 4d6 dégâts de feu aux ennemis à 6 m, "
       "2d8 PV aux alliés.", "Spell_Conjuration_ConjureElemental_HigherLevel_Fire",
       StackId="PHX_ENVOL_EXPLOSION", OnRemoveFunctors="CreateExplosion(Projectile_PHX_ExplosionEnvol)",
       StatusPropertyFlags="IgnoreResting;ApplyToDead")
# Version de base de l'élémentaire de feu (la version « _6 » n'existe que dans le conteneur du jeu
# et ne peut pas se lancer seule) ; on la détache du conteneur comme le fait le jeu pour sa version PNJ.
FIRE_ELEMENTAL = "88a6c664-877c-4d6e-81ad-dd377df2634e"
spell("Target_PHX_EnvolDuPhenix", "Target", "Envol du phénix",
      "Invoque une créature de feu qui combat à vos côtés (le jeu n'a pas de modèle de phénix : c'est un "
      "élémentaire de feu). Quand elle meurt ou disparaît, elle explose : 4d6 dégâts de feu aux ennemis à 6 m "
      "(moitié si sauvegarde de Dextérité réussie) et 2d8 PV aux alliés.",
      using="Target_ConjureElemental_Elemental_Fire", SpellContainerID="", Level="6", UseCosts=slot(6),
      Icon="Spell_Conjuration_ConjureElemental_HigherLevel_Fire",
      SpellProperties=f"GROUND:Summon({FIRE_ELEMENTAL}, -1,Projectile_AiHelper_Summon_Strong,,"
                      f"'ConjureElemetnalStack',UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK,PHX_ENVOL_EXPLOSION)",
      **NO_UPCAST)

# ================================================================== NIVEAUX 12 et 20 : AVATAR DU PHÉNIX
AV_DGT = palier("PHX_LM_Avatar", "3d6", "3d6", "3d6", "3d6", "4d6", "5d6", "6d6")
AV_SOIN = palier("PHX_LM_Avatar_Soin", "3d8", "3d8", "3d8", "3d8", "4d8", "5d8", "6d8")
status("PHX_AVATAR_BRULURE", "Avatar du phénix", "Vous subissez des dégâts de feu au début de votre tour.",
       "Status_Burning", TickType="StartTurn", TickFunctors=f"DealDamage({AV_DGT},Fire,Magical)",
       StackId="PHX_AVATAR_BRULURE")
status("PHX_AVATAR_SOIN", "Avatar du phénix", "Vous récupérez des PV au début de votre tour.",
       "Spell_Evocation_Heal", TickType="StartTurn", TickFunctors=f"RegainHitPoints({AV_SOIN})",
       StackId="PHX_AVATAR_SOIN")
for n, rayon in ((1, 3), (2, 6)):
    aura_double(f"PHX_AVATAR_{n}", "Avatar du phénix", f"Vous êtes un phénix : vous volez, et une aura de feu de "
                f"{rayon} m brûle les ennemis et soigne les alliés.", "Spell_Transmutation_Fly", rayon,
                "PHX_AVATAR_BRULURE", "PHX_AVATAR_SOIN")
AVATAR = {1: ("Une fois par repos long, pendant 5 tours", "OncePerRest", 5, 3),
          2: ("Une fois par repos court, pendant 10 tours", "OncePerShortRest", 10, 6)}
for n, (quand, cd, tours, rayon) in AVATAR.items():
    spell(f"Shout_PHX_AvatarDuPhenix_{n}", "Shout", "Avatar du phénix",
          f"{quand} : vous prenez la forme d'un phénix. Vous volez, et une aura de feu de {rayon} m inflige "
          f"3d6 dégâts de feu aux ennemis et rend 3d8 PV aux alliés au début de leur tour (jusqu'à 6d6 et 6d8 "
          f"au niveau 20).",
          using="Shout_DivineSense", Icon="Spell_Transmutation_Fly", UseCosts="BonusActionPoint:1", Cooldown=cd,
          SpellProperties=f"ApplyStatus(SELF,PHX_AVATAR_{n},100,{tours});ApplyStatus(SELF,FLY,100,{tours})",
          TooltipStatusApply=f"ApplyStatus(PHX_AVATAR_{n},100,{tours})", **FEATURE_SPELL)
    hidden(f"PHX_Avatar_{n}_Sort", Boosts=f"UnlockSpell(Shout_PHX_AvatarDuPhenix_{n})")


# ================================================================== RÉACTIONS (s'améliorent avec les niveaux)
# Chaque réaction existe en plusieurs rangs ; un passif débloque le rang, et la progression retire le
# passif du rang précédent quand le suivant arrive.
REACT = dict(InterruptDefaultValue="Ask;Enabled", Container="YesNoDecision")


def rang(passif, titre, desc, icon, interrupt_name):
    passive(passif, titre, desc, icon, Boosts=f"UnlockInterrupt({interrupt_name})")


# --- Aspiration des flammes : un allié proche va subir du feu -> le feu est annulé et aspiré
status("PHX_FEU_ASPIRE", "Feu aspiré", "Le Phénix a aspiré le feu : vous n'en subissez pas les dégâts.",
       "statIcons_AbsorbElement_Fire", StackId="PHX_FEU_ASPIRE", Boosts="Resistance(Fire,Immune)",
       StatusPropertyFlags="DisableOverhead;DisableCombatlog")
ASPIRATION = {1: ("9", "1d8", "ReactionActionPoint:1", ""),
              2: ("18", "2d8", "ReactionActionPoint:1", "ApplyStatus(PHX_FLAMME_BIENFAITRICE,100,2);"),
              3: ("18", "3d8", "", "ApplyStatus(PHX_FLAMME_BIENFAITRICE,100,2);")}
for n, (dist, soin, cout, bonus) in ASPIRATION.items():
    status(f"PHX_ASPIRATION_GAIN_{n}", "Flammes aspirées", f"Le Phénix aspire le feu : +1 Braise et {soin} PV.",
           "statIcons_AbsorbElement_Fire", StackId=f"PHX_ASPIRATION_GAIN_{n}",
           OnApplyFunctors=f"RegainHitPoints({soin});RestoreResource(PHX_Braise,1,0)",
           StatusPropertyFlags="DisableOverhead;DisableCombatlog")
    gratuit = " Elle ne coûte plus de réaction : elle se déclenche à chaque fois." if not cout else ""
    soin_allie = " L'allié est en plus enveloppé de Flamme bienfaitrice (1d6 PV par tour, 2 tours)." if bonus else ""
    desc = (f"Réaction : quand vous-même ou un allié à {dist} m ou moins allez subir des dégâts de feu (sort, "
            f"attaque ou surface, ennemi ou allié), vous aspirez les flammes : il ne subit aucun dégât de feu, "
            f"et vous gagnez 1 Braise et {soin} PV.{soin_allie}{gratuit}")
    nom = "Aspiration des flammes" + ("" if n == 1 else " " + "I" * n)
    interrupt(f"Interrupt_PHX_Aspiration_{n}", nom, desc, "statIcons_AbsorbElement_Fire",
              InterruptContext="OnPreDamage", InterruptContextScope="Nearby",
              Conditions="IsAbleToReact(context.Observer) and IsDamageTypeFire() and "
                         "(Self(context.Target,context.Observer) or Ally(context.Target,context.Observer)) and "
                         f"not DistanceToEntityGreaterThan({dist},context.ObserverPosition,context.Target)",
              Properties=f"ApplyStatus(PHX_FEU_ASPIRE,100,0);{bonus}"
                         f"ApplyStatus(OBSERVER_OBSERVER,PHX_ASPIRATION_GAIN_{n},100,0)",
              Cost=cout, Stack="PHX_Aspiration", **REACT)
    rang(f"PHX_Aspiration_{n}", nom, desc, "statIcons_AbsorbElement_Fire", f"Interrupt_PHX_Aspiration_{n}")

# --- Riposte ardente : quand un ennemi vous touche, le feu lui répond
for n, dmg in ((1, "2d8"), (2, "3d8"), (3, "5d8")):
    spell(f"Target_PHX_RiposteArdente_{n}", "Target", "Riposte ardente",
          f"Des flammes frappent l'attaquant : {dmg} dégâts de feu (moitié si sauvegarde de Dextérité réussie).",
          using="Target_HellishRebuke", Level="0", UseCosts="", Cooldown="", Icon="Spell_HellishRebuke",
          SpellRoll="not SavingThrow(Ability.Dexterity, SourceSpellDC())",
          SpellSuccess=f"DealDamage({dmg},Fire,Magical)", SpellFail=f"DealDamage(({dmg})/2,Fire,Magical)",
          TooltipDamageList=f"DealDamage({dmg},Fire)", **NO_UPCAST)
    nom = "Riposte ardente" + ("" if n == 1 else " " + "I" * n)
    desc = (f"Réaction : quand un ennemi vous touche avec une attaque, il subit {dmg} dégâts de feu (moitié si "
            f"sauvegarde de Dextérité réussie).")
    interrupt(f"Interrupt_PHX_RiposteArdente_{n}", nom, desc, "Spell_HellishRebuke",
              InterruptContext="OnCastHit", InterruptContextScope="Self",
              Conditions="IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and "
                         "Enemy(context.Source,context.Observer) and IsHit() and not AnyEntityIsItem()",
              Properties=f"UseSpell(OBSERVER_SOURCE,Target_PHX_RiposteArdente_{n},true,true,true)",
              Cost="ReactionActionPoint:1", Stack="PHX_RiposteArdente", **REACT)
    rang(f"PHX_RiposteArdente_{n}", nom, desc, "Spell_HellishRebuke", f"Interrupt_PHX_RiposteArdente_{n}")

# --- Contre-feu : le Phénix dévore un sort ennemi (contresort payé en Braises)
status("PHX_CONTREFEU_GAIN", "Contre-feu", "Le sort dévoré nourrit le Phénix : +1 Braise.",
       "Spell_Abjuration_ProtectionFromEnergy_Fire", StackId="PHX_CONTREFEU_GAIN",
       OnApplyFunctors="RestoreResource(PHX_Braise,1,0)", StatusPropertyFlags="DisableOverhead;DisableCombatlog")
for n, niv in ((1, 3), (2, 5), (3, 9)):
    nom = "Contre-feu" + ("" if n == 1 else " " + "I" * n)
    auto = (f"Les sorts de niveau {niv} ou moins sont annulés automatiquement ; au-delà, test de Charisme."
            if niv < 9 else "Tous les sorts sont annulés automatiquement.")
    desc = (f"Réaction, 2 Braises : quand un ennemi à 18 m lance un sort, vous le dévorez dans les flammes et "
            f"l'annulez, sans emplacement de sort. {auto} Le sort dévoré vous rend 1 Braise.")
    interrupt(f"Interrupt_PHX_ContreFeu_{n}", nom, desc, "Spell_Abjuration_ProtectionFromEnergy_Fire",
              using="Interrupt_Counterspell",
              Conditions="CanSee(context.Observer, context.Source) and "
                         "not DistanceToEntityGreaterThan(18, context.ObserverPosition, context.Source) and "
                         "IsAbleToReact(context.Observer) and not Self(context.Source, context.Observer) and "
                         "Enemy(context.Source, context.Observer) and IsSpell() and not Uninterruptible() and "
                         "not HasStringInSpellRoll('WeaponAttack') and not AnyEntityIsItem()",
              Roll=f"TryCounterspellHigherLevel({niv})",
              Success="Counterspell();UseSpell(OBSERVER_SOURCE,Target_Counterspell_Success,true,true,true);"
                      "ApplyStatus(OBSERVER_OBSERVER,PHX_CONTREFEU_GAIN,100,0)",
              Cost="ReactionActionPoint:1;PHX_Braise:2", Stack="PHX_ContreFeu")
    rang(f"PHX_ContreFeu_{n}", nom, desc, "Spell_Abjuration_ProtectionFromEnergy_Fire",
         f"Interrupt_PHX_ContreFeu_{n}")


# ================================================================== NIVEAUX 13 à 20 (avec un mod niveau 20)
# Les emplacements de sort de niveau 7 à 9 et les passifs UnlockedSpellSlotLevel7-9 sont fournis par le
# mod qui débloque le niveau 20.
def sort_centre(name, titre, desc, level, icon, explosion_name):
    """Sort lancé sur soi qui déclenche une explosion centrée sur le Phénix."""
    return spell(name, "Shout", titre, desc, using="Shout_DivineSense", Level=str(level), UseCosts=slot(level),
                 Cooldown="", Icon=icon, SpellProperties=f"CreateExplosion({explosion_name})", **NO_UPCAST)


AUBE = palier("PHX_LM_Aube", "8d8", "8d8", "8d8", "8d8", "9d8", "10d8", "12d8")
explosion("Projectile_PHX_Aube", "Aube du phénix", "Lumière guérisseuse du Phénix.", 18,
          f"RegainHitPoints({AUBE}+SpellCastingAbilityModifier);GainTemporaryHitPoints(Level);{PURGE}",
          save=False, targets="not Enemy() and not Dead()")
sort_centre("Shout_PHX_AubeDuPhenix", "Aube du phénix",
            "Sort de niveau 7. Une aube de feu doré se lève : vous et vos alliés à 18 m récupérez 8d8 + votre "
            "modificateur de Charisme PV (9d8 au niveau 15, 10d8 au 17, 12d8 au 20), gagnez autant de PV "
            "temporaires que votre niveau, et êtes libérés des états Empoisonné, Aveuglé, Effrayé, Charmé, "
            "Paralysé et des maladies.", 7, "Spell_Evocation_MassCureWounds", "Projectile_PHX_Aube")

explosion("Projectile_PHX_ResurrectionArdente", "Résurrection ardente", "Les cendres des alliés se rallument.", 18,
          "IF(Dead() and Tagged('PLAYABLE')):Resurrect(100,100);IF(not Dead()):RegainHitPoints(6d8)",
          save=False, targets="not Enemy()")
sort_centre("Shout_PHX_ResurrectionArdente", "Résurrection ardente",
            "Sort de niveau 8. Vos alliés morts à 18 m renaissent de leurs cendres avec tous leurs PV ; les "
            "alliés vivants (et vous) récupèrent 6d8 PV.", 8, "Status_Fly", "Projectile_PHX_ResurrectionArdente")

SOLEIL = palier("PHX_LM_SoleilRenaissant", "10d6", "10d6", "10d6", "10d6", "10d6", "10d6", "12d6")
SOLEIL_SOIN = palier("PHX_LM_SoleilRenaissant_Soin", "10d8", "10d8", "10d8", "10d8", "10d8", "10d8", "12d8")
explosion("Projectile_PHX_SoleilRenaissant", "Soleil renaissant", "Un soleil naît autour du Phénix.", 12,
          f"IF(Enemy()):DealDamage({SOLEIL},Fire,Magical);IF(Enemy()):DealDamage({SOLEIL},Radiant,Magical);"
          f"IF(not Enemy()):RegainHitPoints({SOLEIL_SOIN})",
          f"IF(Enemy()):DealDamage(({SOLEIL})/2,Fire,Magical);IF(Enemy()):DealDamage(({SOLEIL})/2,Radiant,Magical);"
          f"IF(not Enemy()):RegainHitPoints({SOLEIL_SOIN})")
sort_centre("Shout_PHX_SoleilRenaissant", "Soleil renaissant",
            "Sort de niveau 9. Un soleil naît autour de vous : les ennemis à 12 m subissent 10d6 dégâts de feu et "
            "10d6 dégâts radiants (moitié si sauvegarde de Dextérité réussie ; 12d6 + 12d6 au niveau 20), et vos "
            "alliés récupèrent 10d8 PV (12d8 au niveau 20).", 9, "Spell_Evocation_Sunbeam",
            "Projectile_PHX_SoleilRenaissant")

passive("PHX_BrasierEternel", "Brasier éternel",
        "Votre feu ne s'éteint jamais : vous gagnez 1 Braise au début de chacun de vos tours, et vous avez "
        "2 Braises de plus.", "statIcons_GlowingFlask", StatsFunctorContext="OnTurn",
        StatsFunctors="RestoreResource(SELF,PHX_Braise,1,0)")
passive("PHX_Renaissance_2", "Renaissance du phénix (repos court)",
        "Votre Renaissance du phénix se recharge aussi à chaque repos court.",
        "Status_Fly", StatsFunctorContext="OnCreate;OnLongRest;OnShortRest",
        StatsFunctors="ApplyStatus(SELF,PHX_RENAISSANCE_PRETE,100,-1)")
passive("PHX_PhenixImmortel", "Phénix immortel",
        "Vous êtes devenu un phénix véritable : +2 en Charisme et en Constitution (maximum 22), et votre "
        "Avatar du phénix se recharge à chaque repos court, dure 10 tours et son aura s'étend à 6 m.",
        "Spell_Transmutation_Fly", Boosts="Ability(Charisma,2,22);Ability(Constitution,2,22)")

# ================================================================== CLASSE DE BASE : niveau -> capacités
feat(None, 1, passives=["PHX_Marqueur", "PHX_FlammeLoyale", "PHX_CendresArdentes", "PHX_PlumeArdente_Sort"],
     spells=["Target_PHX_FlammeBienfaitrice"])
feat(None, 2, passives=["PHX_Braises", "PHX_BraisesAbsorbees", "PHX_Aspiration_1"],
     boosts=["ActionResource(PHX_Braise,3,0)"],
     spells=["Shout_PHX_Attiser", "Shout_PHX_Propager", "Shout_PHX_Purifier"])
feat(None, 3, passives=["PHX_RiposteArdente_1"], spells=["Target_PHX_BondDeFlamme"])
feat(None, 5, passives=["PHX_Ignifuge", "PHX_PlumeArdente_Rebond_Sort", "PHX_ContreFeu_1"],
     removed=["PHX_PlumeArdente_Sort"],
     spells=["Projectile_PHX_PluieDePlumes", "Target_PHX_LarmesDePhenix"])
feat(None, 6, passives=["PHX_BouclierFlammes_1"])
feat(None, 7, passives=["PHX_FeuSacre", "PHX_Aspiration_2"], removed=["PHX_Aspiration_1"],
     spells=["Shout_PHX_BucherSacre"])
feat(None, 9, passives=["PHX_CoeurDePhenix", "PHX_RiposteArdente_2"], removed=["PHX_RiposteArdente_1"],
     boosts=["ActionResource(PHX_Braise,2,0)"],
     spells=["Target_PHX_PlumeDeRenaissance"])
feat(None, 10, passives=["PHX_Renaissance"])
feat(None, 11, passives=["PHX_BouclierFlammes_2", "PHX_FeuSacre_2", "PHX_ContreFeu_2"],
     removed=["PHX_BouclierFlammes_1", "PHX_ContreFeu_1"], spells=["Target_PHX_EnvolDuPhenix"])
feat(None, 12, passives=["PHX_Avatar_1_Sort"])
feat(None, 13, spells=["Shout_PHX_AubeDuPhenix"])
feat(None, 14, passives=["PHX_Aspiration_3"], removed=["PHX_Aspiration_2"])
feat(None, 15, passives=["PHX_RiposteArdente_3"], removed=["PHX_RiposteArdente_2"],
     spells=["Shout_PHX_ResurrectionArdente"])
feat(None, 16, passives=["PHX_BrasierEternel"], boosts=["ActionResource(PHX_Braise,2,0)"])
feat(None, 17, passives=["PHX_ContreFeu_3"], removed=["PHX_ContreFeu_2"], spells=["Shout_PHX_SoleilRenaissant"])
feat(None, 18, passives=["PHX_Renaissance_2"], removed=["PHX_Renaissance"])
feat(None, 19, passives=["PHX_BouclierFlammes_3"], removed=["PHX_BouclierFlammes_2"])
feat(None, 20, passives=["PHX_PhenixImmortel", "PHX_Avatar_2_Sort"], removed=["PHX_Avatar_1_Sort"])

# ================================================================== VOIE DU PHÉNIX ÉTERNEL
# Une seule voie qui réunit le Brasier (dégâts), la Cendre (soins) et les Serres (corps à corps).
VOIE = "Eternel"

# --- Brasier (dégâts)
passive("PHX_Brasier_Brasier", "Cœur du brasier",
        "Vos sorts de feu brûlent plus fort : une fois par attaque, ils infligent en plus votre modificateur "
        "de Charisme en dégâts de feu. Vous avez 2 Braises de plus.",
        "Spell_Evocation_WallOfFire", props="Highlighted;OncePerAttack", StatsFunctorContext="OnDamage",
        Conditions="IsDamageTypeFire() and IsSpell() and Enemy()",
        StatsFunctors="DealDamage(max(1,CharismaModifier),Fire,Magical)")
explosion("Projectile_PHX_Nova", "Nova", "Explosion géante centrée sur le Phénix.", 9,
          "IF(Enemy()):DealDamage(8d6,Fire,Magical)", "IF(Enemy()):DealDamage((8d6)/2,Fire,Magical)")
spell("Shout_PHX_Nova", "Shout", "Nova",
      "Une fois par repos long : une explosion géante de 9 m centrée sur vous. Les ennemis subissent 8d6 dégâts "
      "de feu (moitié si sauvegarde de Dextérité réussie), aucun dégât aux alliés, et le feu vous soigne de "
      "4d8 PV (Cœur de phénix).",
      using="Shout_DivineSense", Icon="Spell_Evocation_FlameStrike", UseCosts="ActionPoint:1",
      Cooldown="OncePerRest", SpellProperties="CreateExplosion(Projectile_PHX_Nova);RegainHitPoints(4d8)",
      **FEATURE_SPELL)
feat(VOIE, 3, passives=["PHX_Brasier_Brasier"], boosts=["ActionResource(PHX_Braise,2,0)"])
feat(VOIE, 10, spells=["Shout_PHX_Nova"])

# --- Cendre (soins)
passive("PHX_Cendre_SoinsArdents", "Soins ardents",
        "Vos sorts de soins (hors tours de magie) rendent en plus votre niveau de Phénix en PV.",
        "Spell_HarmonyOfFireAndWater", StatsFunctorContext="OnHeal",
        Conditions="HealDoneGreaterThan(0) and IsSpell() and not IsCantrip()",
        StatsFunctors=f"RegainHitPoints(ClassLevel({PHENIX}))")
spell("Target_PHX_PlumeDeRenaissance_Cendre", "Target", "Plume de renaissance (gratuite)",
      "Une fois par repos long, sans emplacement de sort : un allié reçoit une Plume de renaissance. S'il tombe "
      "à 0 PV, il renaît aussitôt avec la moitié de ses PV dans une gerbe de feu. Une seule fois.",
      Level="0", UseCosts="ActionPoint:1", Cooldown="OncePerRest", **PLUME_RENAISSANCE, **NO_UPCAST)
passive("PHX_Cendre_RenaissanceCollective", "Renaissance collective",
        "L'explosion de votre Renaissance du phénix relève aussi les alliés à terre à 6 m, avec la moitié "
        "de leurs PV.", "Status_Fly")
feat(VOIE, 3, passives=["PHX_Cendre_SoinsArdents"], spells=["Target_PHX_PlumeDeRenaissance_Cendre"])
feat(VOIE, 10, passives=["PHX_Cendre_RenaissanceCollective"])

# --- Serres (corps à corps)
explosion("Projectile_PHX_ImpactCharge", "Charge ardente", "Impact de feu de la Charge ardente.", 3,
          "IF(Enemy()):DealDamage(2d8,Fire,Magical)", "IF(Enemy()):DealDamage((2d8)/2,Fire,Magical)")
spell("Target_PHX_ChargeArdente", "Target", "Charge ardente",
      "Action bonus, une fois par tour : vous bondissez jusqu'à 9 m. À l'impact, les ennemis à 3 m subissent "
      "2d8 dégâts de feu (moitié si sauvegarde de Dextérité réussie). Aucun dégât aux alliés.",
      using="Target_MistyStep", UseCosts="BonusActionPoint:1", Range="9", Cooldown="OncePerTurn",
      Icon="Action_Monk_FangsOfTheFireSnake",
      SpellProperties="GROUND:TeleportSource();GROUND:CreateExplosion(Projectile_PHX_ImpactCharge)",
      **FEATURE_SPELL)
feat(VOIE, 3, boosts=["Proficiency(MediumArmor)", "Proficiency(Shields)", "Proficiency(MartialWeapons)"],
     spells=["Target_PHX_ChargeArdente"])
feat(VOIE, 5, passives=["ExtraAttack"])

VOIES = {
    VOIE: ("Voie du Phénix éternel",
           "Les trois visages du phénix réunis. Brasier : vos sorts de feu brûlent plus fort (+Charisme) et "
           "vous avez 2 Braises de plus. Cendre : soins renforcés et une Plume de renaissance gratuite par repos "
           "long. Serres : armures intermédiaires, boucliers, armes de guerre, Charge ardente et Attaque "
           "supplémentaire au niveau 5. Au niveau 10 : Nova, et votre Renaissance relève aussi les alliés à "
           "terre autour de vous."),
}


def sorts_appris():
    """Listes de sorts à apprendre : tours, et sorts cumulés jusqu'au niveau de sort n."""
    tours = spelllist("PHX_ToursFeuLumiere", "Phénix : tours de magie de feu et de lumière", TOURS_FEU_LUMIERE)
    cumul, sorts = [], {}
    for n in sorted(SORTS_FEU_LUMIERE):
        cumul = cumul + SORTS_FEU_LUMIERE[n]
        sorts[n] = spelllist(f"PHX_SortsFeuLumiere_{n}", f"Phénix : sorts de feu et de lumière (niveaux 1 à {n})",
                             list(cumul))
    return tours, sorts


def feature_spelllists():
    """Listes de sorts accordés (toujours préparés) : {voie: {niveau: uuid}}."""
    out = {}
    for voie, levels in FEATURES.items():
        for lv, f in levels.items():
            if f["spells"]:
                out.setdefault(voie, {})[lv] = spelllist(f"PHX_{voie or 'Base'}_{lv}",
                                                         f"Phénix {voie or ''} : capacités (niveau {lv})",
                                                         f["spells"])
    return out
