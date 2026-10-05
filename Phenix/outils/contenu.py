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
SORCERER_CANTRIPS = "485a68b4-c678-4888-be63-4a702efbe391"
SORCERER_SPELLS = {1: "92c4751f-6255-4f67-822c-a75d53830b27", 2: "f80396e2-cb76-4694-b0db-5c34da61a478",
                   3: "dcbaf2ae-1f45-453e-ab83-cd154f8277a4", 4: "5fe40622-1d3e-4cc1-8d89-e66fe51d8c5c",
                   5: "3276fcfe-e143-4559-b6e0-7d7aa0ffcb53", 6: "1270a6db-980b-4e3b-bf26-2924da61dfd5"}


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


def palier(name, l1, l5, l9, l12):
    """Valeur qui grandit aux niveaux 5, 9 et 12 du personnage."""
    LEVELMAPS.append((name, {1: l1, 5: l5, 9: l9, 12: l12}))
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


def explosion(name, titre, desc, radius, success, fail=None, save=True, **data):
    """Explosion déclenchée par CreateExplosion (sans coût, ne se lance pas à la main)."""
    extra = dict(SpellRoll="not SavingThrow(Ability.Dexterity, SourceSpellDC())", SpellSuccess=success,
                 SpellFail=fail or success) if save else dict(SpellRoll="", SpellSuccess=success, SpellFail="")
    return spell(name, "Projectile", titre, desc, using="Projectile_Fireball", Level="0", UseCosts="",
                 AreaRadius=str(radius), ExplodeRadius=str(radius), TargetConditions="not Dead()",
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

status("PHX_FLAMME_BIENFAITRICE", "Flamme bienfaitrice",
       "Ces flammes soignent au lieu de brûler : 1d6 PV au début de chaque tour.",
       "Status_Burning", using="BURNING", StackId="PHX_FLAMME_BIENFAITRICE",
       TickType="StartTurn", TickFunctors="RegainHitPoints(1d6)", OnApplyFunctors="", Boosts="",
       StatusGroups="")
spell("Target_PHX_FlammeBienfaitrice", "Target", "Flamme bienfaitrice",
      "Enveloppe un allié de flammes bienfaitrices : il récupère 1d8 + votre modificateur de Charisme PV, "
      "puis 1d6 PV au début de chacun de ses tours pendant 3 tours. Il a l'air en feu, mais ce feu le soigne.",
      using="Target_CureWounds", Level="1", UseCosts=slot(1), Icon="Spell_HarmonyOfFireAndWater",
      TargetConditions="not Enemy() and not Dead()",
      SpellProperties="RegainHitPoints(1d8+SpellCastingAbilityModifier);"
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
spell("Projectile_PHX_PlumeArdente_Rebond", "Projectile", "Plume ardente (rebond)",
      "Tour de magie. Deux plumes de feu : choisissez deux cibles (ou deux fois la même). Chacune inflige "
      "1d10 dégâts de feu (2d10 au niveau 5, 3d10 au niveau 10).", AmountOfTargets="2", **PLUME)

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

lm = palier("PHX_LM_PluieDePlumes", "4d6", "4d6", "5d6", "6d6")
spell("Projectile_PHX_PluieDePlumes", "Projectile", "Pluie de plumes",
      "Une pluie de plumes enflammées sur une zone de 6 m : les ennemis subissent 4d6 dégâts de feu (moitié "
      "si sauvegarde de Dextérité réussie ; augmente aux niveaux 9 et 12), les alliés pris dedans récupèrent "
      "2d8 PV.",
      using="Projectile_Fireball", Level="3", UseCosts=slot(3), Icon="Spell_Transmutation_FeatherFall",
      AreaRadius="6", ExplodeRadius="6", TargetConditions="not Dead()", SpellProperties="",
      SpellRoll="not SavingThrow(Ability.Dexterity, SourceSpellDC())",
      SpellSuccess=f"IF(Enemy()):DealDamage({lm},Fire,Magical);IF(not Enemy()):RegainHitPoints(2d8)",
      SpellFail=f"IF(Enemy()):DealDamage(({lm})/2,Fire,Magical);IF(not Enemy()):RegainHitPoints(2d8)",
      TooltipDamageList=f"DealDamage({lm},Fire)", **NO_UPCAST)
spell("Target_PHX_LarmesDePhenix", "Target", "Larmes de phénix",
      "Des larmes de feu guérisseur : un allié récupère 4d8 + votre modificateur de Charisme PV et est libéré "
      "des poisons, des maladies et des malédictions.",
      using="Target_CureWounds", Level="3", UseCosts=slot(3), Icon="Spell_Evocation_Heal",
      TargetConditions="not Enemy() and not Dead()",
      SpellProperties="RegainHitPoints(4d8+SpellCastingAbilityModifier);RemoveStatus(SG_Poisoned);"
                      "RemoveStatus(SG_Disease);RemoveStatus(SG_Cursed)", **NO_UPCAST)

# ================================================================== NIVEAUX 6 et 11 : BOUCLIER DE FLAMMES
for dmg, suffix in (("1d8", "1"), ("2d8", "2")):
    passive(f"PHX_BouclierFlammes_{suffix}", "Bouclier de flammes" + ("" if suffix == "1" else " (2d8)"),
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


status("PHX_BUCHER_BRULURE", "Bûcher sacré", "Vous subissez 2d8 dégâts de feu au début de votre tour.",
       "Spell_Evocation_FlameStrike", TickType="StartTurn", TickFunctors="DealDamage(2d8,Fire,Magical)",
       StackId="PHX_BUCHER_BRULURE")
status("PHX_BUCHER_SOIN", "Bûcher sacré", "Vous récupérez 1d8 PV au début de votre tour.",
       "Spell_Evocation_FlameStrike", TickType="StartTurn", TickFunctors="RegainHitPoints(1d8)",
       StackId="PHX_BUCHER_SOIN")
aura_double("PHX_BUCHER", "Bûcher sacré", "Un bûcher sacré brûle autour de vous.", "Spell_Evocation_FlameStrike",
            6, "PHX_BUCHER_BRULURE", "PHX_BUCHER_SOIN")
spell("Shout_PHX_BucherSacre", "Shout", "Bûcher sacré",
      "Pendant 4 tours, un bûcher sacré de 6 m brûle autour de vous : au début de leur tour, les ennemis "
      "subissent 2d8 dégâts de feu et vos alliés récupèrent 1d8 PV.",
      using="Shout_SpiritGuardians", Level="4", UseCosts=slot(4), Icon="Spell_Evocation_FlameStrike",
      SpellProperties="ApplyStatus(SELF,PHX_BUCHER,100,4)", TooltipStatusApply="ApplyStatus(PHX_BUCHER,100,4)",
      **NO_UPCAST)

# ================================================================== NIVEAU 9 : CŒUR DE PHÉNIX + PLUME DE RENAISSANCE
passive("PHX_CoeurDePhenix", "Cœur de phénix",
        "Le feu vous soigne au lieu de vous blesser, y compris le vôtre : chaque fois que du feu vous "
        "atteint, vous récupérez 3d8 PV.",
        "statIcons_AbsorbElement_Fire", props="Highlighted;OncePerAttack",
        StatsFunctorContext="OnDamagedPrevented;OnDamaged", Conditions="IsDamageTypeFire()",
        StatsFunctors="RegainHitPoints(3d8)")

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
spell("Target_PHX_EnvolDuPhenix", "Target", "Envol du phénix",
      "Invoque une créature de feu pure qui combat à vos côtés (le jeu n'a pas de modèle de phénix : c'est un "
      "élémentaire de feu).",
      using="Target_ConjureElemental_Elemental_Fire_6", Level="6", UseCosts=slot(6),
      Icon="Spell_Conjuration_ConjureElemental_HigherLevel_Fire", **NO_UPCAST)

# ================================================================== NIVEAU 12 : AVATAR DU PHÉNIX
status("PHX_AVATAR_BRULURE", "Avatar du phénix", "Vous subissez 2d6 dégâts de feu au début de votre tour.",
       "Status_Burning", TickType="StartTurn", TickFunctors="DealDamage(2d6,Fire,Magical)",
       StackId="PHX_AVATAR_BRULURE")
status("PHX_AVATAR_SOIN", "Avatar du phénix", "Vous récupérez 2d6 PV au début de votre tour.",
       "Spell_Evocation_Heal", TickType="StartTurn", TickFunctors="RegainHitPoints(2d6)",
       StackId="PHX_AVATAR_SOIN")
aura_double("PHX_AVATAR", "Avatar du phénix", "Vous êtes un phénix : vous volez, et une aura de feu de 3 m "
            "brûle les ennemis et soigne les alliés.", "Spell_Transmutation_Fly", 3,
            "PHX_AVATAR_BRULURE", "PHX_AVATAR_SOIN")
spell("Shout_PHX_AvatarDuPhenix", "Shout", "Avatar du phénix",
      "Une fois par repos long, pendant 5 tours : vous prenez la forme d'un phénix. Vous volez, et une aura "
      "de feu de 3 m inflige 2d6 dégâts de feu aux ennemis et rend 2d6 PV aux alliés au début de leur tour.",
      using="Shout_DivineSense", Icon="Spell_Transmutation_Fly", UseCosts="BonusActionPoint:1",
      Cooldown="OncePerRest",
      SpellProperties="ApplyStatus(SELF,PHX_AVATAR,100,5);ApplyStatus(SELF,FLY,100,5)",
      TooltipStatusApply="ApplyStatus(PHX_AVATAR,100,5)", **FEATURE_SPELL)

# ================================================================== CLASSE DE BASE : niveau -> capacités
feat(None, 1, passives=["PHX_Marqueur", "PHX_FlammeLoyale", "PHX_CendresArdentes"],
     spells=["Target_PHX_FlammeBienfaitrice", "Projectile_PHX_PlumeArdente"])
feat(None, 2, passives=["PHX_Braises", "PHX_BraisesAbsorbees"],
     boosts=["ActionResource(PHX_Braise,3,0)"],
     spells=["Shout_PHX_Attiser", "Shout_PHX_Propager", "Shout_PHX_Purifier"])
feat(None, 3, spells=["Target_PHX_BondDeFlamme"])
feat(None, 5, passives=["PHX_Ignifuge"],
     spells=["Projectile_PHX_PluieDePlumes", "Target_PHX_LarmesDePhenix", "Projectile_PHX_PlumeArdente_Rebond"])
feat(None, 6, passives=["PHX_BouclierFlammes_1"])
feat(None, 7, passives=["PHX_FeuSacre"], spells=["Shout_PHX_BucherSacre"])
feat(None, 9, passives=["PHX_CoeurDePhenix"], boosts=["ActionResource(PHX_Braise,2,0)"],
     spells=["Target_PHX_PlumeDeRenaissance"])
feat(None, 10, passives=["PHX_Renaissance"])
feat(None, 11, passives=["PHX_BouclierFlammes_2", "PHX_FeuSacre_2"],
     removed=["PHX_BouclierFlammes_1"], spells=["Target_PHX_EnvolDuPhenix"])
feat(None, 12, spells=["Shout_PHX_AvatarDuPhenix"])

# ================================================================== VOIE DU BRASIER (dégâts)
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
feat("Brasier", 3, passives=["PHX_Brasier_Brasier"], boosts=["ActionResource(PHX_Braise,2,0)"])
feat("Brasier", 10, spells=["Shout_PHX_Nova"])

# ================================================================== VOIE DE LA CENDRE (soins)
passive("PHX_Cendre_SoinsArdents", "Soins ardents",
        "Vos sorts de soins (hors tours de magie) rendent en plus votre niveau de Phénix en PV.",
        "Spell_HarmonyOfFireAndWater", StatsFunctorContext="OnHeal",
        Conditions="HealDoneGreaterThan(0) and IsSpell() and not IsCantrip()",
        StatsFunctors=f"RegainHitPoints(ClassLevel({PHENIX}))")
spell("Target_PHX_PlumeDeRenaissance_Cendre", "Target", "Plume de renaissance (Cendre)",
      "Une fois par repos long, sans emplacement de sort : un allié reçoit une Plume de renaissance. S'il tombe "
      "à 0 PV, il renaît aussitôt avec la moitié de ses PV dans une gerbe de feu. Une seule fois.",
      Level="0", UseCosts="ActionPoint:1", Cooldown="OncePerRest", **PLUME_RENAISSANCE, **NO_UPCAST)
passive("PHX_Cendre_RenaissanceCollective", "Renaissance collective",
        "L'explosion de votre Renaissance du phénix relève aussi les alliés à terre à 6 m, avec la moitié "
        "de leurs PV.", "Status_Fly")
feat("Cendre", 3, passives=["PHX_Cendre_SoinsArdents"], spells=["Target_PHX_PlumeDeRenaissance_Cendre"])
feat("Cendre", 10, passives=["PHX_Cendre_RenaissanceCollective"])

# ================================================================== VOIE DES SERRES (corps à corps)
explosion("Projectile_PHX_ImpactCharge", "Charge ardente", "Impact de feu de la Charge ardente.", 3,
          "IF(Enemy()):DealDamage(2d8,Fire,Magical)", "IF(Enemy()):DealDamage((2d8)/2,Fire,Magical)")
spell("Target_PHX_ChargeArdente", "Target", "Charge ardente",
      "Action bonus, une fois par tour : vous bondissez jusqu'à 9 m. À l'impact, les ennemis à 3 m subissent "
      "2d8 dégâts de feu (moitié si sauvegarde de Dextérité réussie). Aucun dégât aux alliés.",
      using="Target_MistyStep", UseCosts="BonusActionPoint:1", Range="9", Cooldown="OncePerTurn",
      Icon="Action_Monk_FangsOfTheFireSnake",
      SpellProperties="GROUND:TeleportSource();GROUND:CreateExplosion(Projectile_PHX_ImpactCharge)",
      **FEATURE_SPELL)
feat("Serres", 3, boosts=["Proficiency(MediumArmor)", "Proficiency(Shields)", "Proficiency(MartialWeapons)"],
     spells=["Target_PHX_ChargeArdente"])
feat("Serres", 5, passives=["ExtraAttack"])

VOIES = {
    "Brasier": ("Voie du Brasier",
                "Le feu destructeur : vos sorts de feu brûlent plus fort, vous avez 2 Braises de plus, et au "
                "niveau 10 vous libérez Nova, une explosion géante qui vous soigne."),
    "Cendre": ("Voie de la Cendre",
               "Le feu qui guérit : soins renforcés, une Plume de renaissance gratuite par repos long, et au "
               "niveau 10 votre Renaissance du phénix relève aussi les alliés à terre autour de vous."),
    "Serres": ("Voie des Serres",
               "Le phénix guerrier : armures intermédiaires, boucliers, armes de guerre, Charge ardente, et "
               "Attaque supplémentaire au niveau 5."),
}


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
