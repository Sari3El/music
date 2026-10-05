"""Les 10 domaines (sous-classes) : affinité divine, contrepoids, capacités et sorts."""
from contenu import (DOMAINES, TYPE_FR, TYPE_NOM, ICONE_TYPE, SCHOOLS, ORDRE, CHAOS, NO_UPCAST,
                     METAMAGIC_LIST, passive, hidden, status, spell, interrupt, palier, degats,
                     ally_aura, keep_applied, outcome, slot)

# Sorts de domaine toujours préparés (niveaux de personnage 1, 3, 5, 7, 9)
DOMAIN_SPELLS = {}
# Capacités par domaine : {niveau: {"passives": [...], "removed": [...], "spells": [...], "boosts": [...],
#                                   "selectors": [...]}}
FEATURES = {}


def feat(dom, level, passives=(), removed=(), spells=(), boosts=(), selectors=()):
    f = FEATURES.setdefault(dom, {}).setdefault(level, {"passives": [], "removed": [], "spells": [],
                                                         "boosts": [], "selectors": []})
    f["passives"] += list(passives)
    f["removed"] += list(removed)
    f["spells"] += list(spells)
    f["boosts"] += list(boosts)
    f["selectors"] += list(selectors)


# ================================================================== AFFINITÉ DIVINE + CONTREPOIDS
for dom, (cls, titre, dt, opp, fr) in DOMAINES.items():
    nom = TYPE_NOM[dt]
    hidden(f"DOC_{dom}_Marqueur")
    passive(f"DOC_{dom}_Resistance", f"Affinité divine : {nom}",
            f"Vous êtes résistant aux dégâts {fr}.", ICONE_TYPE[dt], Boosts=f"Resistance({dt},Resistant)")
    passive(f"DOC_{dom}_Immunite", f"Affinité divine : {nom} (immunité)",
            f"Vous êtes immunisé contre les dégâts {fr}.", ICONE_TYPE[dt], Boosts=f"Resistance({dt},Immune)")
    passive(f"DOC_{dom}_Absorption", f"Affinité divine : {nom} (absorption)",
            f"Les dégâts {fr} vous soignent au lieu de vous blesser : chaque fois qu'ils vous atteignent "
            f"(sorts, attaques, états ou surfaces), vous récupérez 3d8 PV.",
            ICONE_TYPE[dt], props="Highlighted;OncePerAttack",
            StatsFunctorContext="OnDamagedPrevented;OnDamaged",
            Conditions=f"IsDamageType{dt}()", StatsFunctors="RegainHitPoints(3d8)")
    status(f"DOC_CONTREPOIDS_{dom.upper()}", f"Contrepoids : {TYPE_NOM[opp]}",
           f"Vous êtes vulnérable aux dégâts {TYPE_FR[opp]}, l'élément de votre domaine opposé.",
           ICONE_TYPE[opp], Boosts=f"Resistance({opp},Vulnerable)",
           StatusPropertyFlags="IgnoreResting;DisableOverhead", StatusGroups="SG_RemoveOnRespec",
           StackId=f"DOC_CONTREPOIDS_{dom.upper()}")
    passive(f"DOC_{dom}_Contrepoids", f"Contrepoids : {TYPE_NOM[opp]}",
            f"(Optionnel, activé par défaut.) Vous êtes vulnérable aux dégâts {TYPE_FR[opp]}, l'élément "
            f"de votre domaine opposé. Désactivez ce passif pour jouer sans contrepoids.",
            ICONE_TYPE[opp], props="IsToggled;ToggledDefaultOn;ToggledDefaultAddToHotbar;Highlighted",
            ToggleOnFunctors=f"ApplyStatus(DOC_CONTREPOIDS_{dom.upper()},100,-1)",
            ToggleOffFunctors=f"RemoveStatus(DOC_CONTREPOIDS_{dom.upper()})",
            ToggleGroup=f"DOC_Contrepoids_{dom}")
    feat(dom, 1, passives=[f"DOC_{dom}_Marqueur", f"DOC_{dom}_Resistance", f"DOC_{dom}_Contrepoids"])
    feat(dom, 6, passives=[f"DOC_{dom}_Immunite"], removed=[f"DOC_{dom}_Resistance"])
    feat(dom, 10, passives=[f"DOC_{dom}_Absorption"])

CRIT_SPELL_FLAGS = "HasVerbalComponent;HasSomaticComponent;IsSpell;IsHarmful"
FEATURE_SPELL = dict(Level="0", **NO_UPCAST)


# ================================================================== ORDRE : VIE (radiant)
passive("DOC_Vie_VieDebordante", "Vie débordante",
        "Vos sorts de soins (hors tours de magie) rendent en plus autant de PV que votre niveau "
        "de Divinité de l'Ordre, et la cible gagne autant de PV temporaires.",
        "PassiveFeature_DiscipleOfLife", StatsFunctorContext="OnHeal",
        Conditions="HealDoneGreaterThan(0) and IsSpell() and not IsCantrip()",
        StatsFunctors=f"RegainHitPoints(ClassLevel({ORDRE}));GainTemporaryHitPoints(ClassLevel({ORDRE}))")
status("DOC_FIL_DE_VIE", "Fil de vie",
       "Si vous tombez à 0 PV, vous restez à 1 PV à la place (une fois).",
       "PassiveFeature_RelentlessEndurance", using="RELENTLESS_ENDURANCE", StackId="DOC_FIL_DE_VIE")
spell("Target_DOC_FilDeVie", "Target", "Fil de vie",
      "Action bonus, une fois par repos court : tissez un fil de vie autour d'un allié pendant 10 tours. "
      "S'il tombe à 0 PV pendant ce temps, il reste à 1 PV.",
      using="Target_Bless", AmountOfTargets="1", Icon="Action_Cleric_PreserveLife",
      Cooldown="OncePerShortRest", UseCosts="BonusActionPoint:1",
      SpellProperties="ApplyStatus(DOC_FIL_DE_VIE,100,10)", TooltipStatusApply="ApplyStatus(DOC_FIL_DE_VIE,100,10)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell", **FEATURE_SPELL)
status("DOC_AURA_VITALE_SOIN", "Aura vitale", "Vous récupérez 1d4 PV au début de votre tour.",
       "Spell_Evocation_AuraOfVitality", TickType="StartTurn", TickFunctors="RegainHitPoints(1d4)",
       StackId="DOC_AURA_VITALE_SOIN")
ally_aura("DOC_AURA_VITALE", "Aura vitale", "Les alliés à 3 m récupèrent 1d4 PV au début de leur tour.",
          "Spell_Evocation_AuraOfVitality", 3, "DOC_AURA_VITALE_SOIN", "DOC_AURA_VITALE", 1)
keep_applied("DOC_Vie_AuraVitale", "Aura vitale",
             "Les alliés à 3 m ou moins récupèrent 1d4 PV au début de leur tour.",
             "Spell_Evocation_AuraOfVitality", "DOC_AURA_VITALE")
spell("Shout_DOC_Renaissance", "Shout", "Renaissance",
      "Une fois par repos long : tous les alliés inconscients à 9 m se relèvent avec la moitié de leurs PV.",
      using="Shout_HealingWord_Mass", Icon="Action_DivineIntervention_Heal", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", AreaRadius="9", TargetConditions="Ally() and not Dead()",
      SpellProperties="IF(IsDowned()):RegainHitPoints(MaxHP/2)", DescriptionParams="", **FEATURE_SPELL)
lm = palier("DOC_LM_SouffleDeVie", "2d8", "3d8", "4d8", "5d8")
spell("Shout_DOC_SouffleDeVie", "Shout", "Souffle de vie",
      "Action bonus : les alliés proches récupèrent 2d8 + votre modificateur de Sagesse PV "
      "(+1d8 aux niveaux 5, 9 et 12) et sont débarrassés des états Empoisonné, Aveuglé et des maladies.",
      using="Shout_HealingWord_Mass", Level="1", UseCosts="BonusActionPoint:1;SpellSlotsGroup:1:1:1",
      SpellProperties=f"RegainHitPoints({lm}+SpellCastingAbilityModifier);RemoveStatus(SG_Poisoned);"
                      f"RemoveStatus(SG_Blinded);RemoveStatus(SG_Disease)",
      DescriptionParams="", TooltipDamageList=f"RegainHitPoints({lm}+SpellCastingAbilityModifier)", **NO_UPCAST)
lm = palier("DOC_LM_EclatDeVie", "4d10", "4d10", "5d10", "6d10")
spell("Target_DOC_EclatDeVie", "Target", "Éclat de vie",
      "Une flamme de vie brûle la cible : 4d10 dégâts radiants (augmente aux paliers), moitié en cas "
      "de sauvegarde de Dextérité réussie. Vous récupérez 2d8 PV.",
      using="Target_SacredFlame", Level="3", UseCosts=slot(3), Icon="Action_Paladin_HealingRadiance",
      SpellSuccess=f"DealDamage({lm},Radiant,Magical)", SpellFail=f"DealDamage(({lm})/2,Radiant,Magical)",
      SpellProperties="RegainHitPoints(SELF,2d8)", TooltipDamageList=f"DealDamage({lm},Radiant)", **NO_UPCAST)
feat("Vie", 1, passives=["DOC_Vie_VieDebordante"])
feat("Vie", 3, spells=["Target_DOC_FilDeVie"])
feat("Vie", 6, passives=["DOC_Vie_AuraVitale"])
feat("Vie", 10, spells=["Shout_DOC_Renaissance"])
DOMAIN_SPELLS["Vie"] = {1: ["Shout_DOC_SouffleDeVie", "Target_Bless"], 3: ["Target_Sanctuary"],
                        5: ["Target_DOC_EclatDeVie", "Shout_HealingWord_Mass"], 7: ["Target_Banishment"],
                        9: ["Target_FlameStrike"]}


# ================================================================== ORDRE : JUSTICE (foudre)
hidden("DOC_Justice_Juge")
status("DOC_MARQUE_JUGEMENT", "Marque du jugement",
       "Marqué par une divinité de la Justice : ses attaques vous infligent 1d6 dégâts de foudre "
       "supplémentaires, et vous subissez 1d6 dégâts de foudre si vous attaquez quelqu'un d'autre qu'elle.",
       "Action_Paladin_HolyRebuke", Passives="DOC_Justice_MarqueRiposte", StackId="DOC_MARQUE_JUGEMENT")
hidden("DOC_Justice_MarqueRiposte", StatsFunctorContext="OnAttack",
       Conditions="not HasPassive('DOC_Justice_Juge',context.Target)",
       StatsFunctors="DealDamage(SELF,1d6,Lightning,Magical)")
passive("DOC_Justice_MarqueBonus", "Marque du jugement",
        "Action bonus : marquez une créature pendant 10 tours. Vos attaques contre elle infligent "
        "1d6 dégâts de foudre supplémentaires ; elle subit 1d6 dégâts de foudre si elle attaque "
        "quelqu'un d'autre que vous.",
        "Action_Paladin_HolyRebuke", props="Highlighted;OncePerAttack", StatsFunctorContext="OnDamage",
        Conditions="HasStatus('DOC_MARQUE_JUGEMENT',context.Target) and not IsKillingBlow()",
        StatsFunctors="DealDamage(1d6,Lightning,Magical)")
spell("Target_DOC_MarqueJugement", "Target", "Marque du jugement",
      "Action bonus : marquez une créature pendant 10 tours. Vos attaques contre elle infligent 1d6 dégâts "
      "de foudre supplémentaires ; elle subit 1d6 dégâts de foudre si elle attaque quelqu'un d'autre que vous.",
      using="Target_SacredFlame", Icon="Action_Paladin_HolyRebuke", UseCosts="BonusActionPoint:1",
      SpellRoll="", SpellSuccess="", SpellFail="", TooltipDamageList="",
      SpellProperties="ApplyStatus(DOC_MARQUE_JUGEMENT,100,10)",
      TooltipStatusApply="ApplyStatus(DOC_MARQUE_JUGEMENT,100,10)", **FEATURE_SPELL)
keep_applied("DOC_Justice_VisionVeritable", "Vision véritable",
             "Rien n'échappe à la Justice : vous voyez les créatures invisibles.",
             "Spell_Divination_SeeInvisibility", "SEE_INVISIBILITY")
spell("Target_DOC_Retribution", "Target", "Rétribution",
      "La foudre frappe celui qui a osé toucher votre allié : 2d8 dégâts de foudre.",
      using="Target_CallLightning", UseCosts="", SpellProperties="DealDamage(2d8,Lightning,Magical)",
      SpellRoll="", SpellSuccess="", SpellFail="", AreaRadius="1", TargetRadius="30",
      TooltipDamageList="DealDamage(2d8,Lightning)", **FEATURE_SPELL)
interrupt("Interrupt_DOC_Retribution", "Rétribution",
          "Réaction : quand un ennemi touche un allié à 9 m ou moins, la foudre le frappe (2d8 dégâts de foudre).",
          "PassiveFeature_ThunderboltStrike",
          InterruptContext="OnCastHit", InterruptContextScope="Nearby", Container="YesNoDecision",
          Conditions="IsAbleToReact(context.Observer) and Ally(context.Target,context.Observer) and "
                     "not Self(context.Target,context.Observer) and Enemy(context.Source,context.Observer) and "
                     "IsHit() and not AnyEntityIsItem() and "
                     "not DistanceToEntityGreaterThan(9,context.ObserverPosition,context.Target)",
          Properties="UseSpell(OBSERVER_SOURCE,Target_DOC_Retribution,true,true,true)",
          Cost="ReactionActionPoint:1", Stack="DOC_Retribution", InterruptDefaultValue="Ask;Enabled")
passive("DOC_Justice_Retribution", "Rétribution",
        "Réaction : quand un ennemi touche un allié à 9 m ou moins, il subit 2d8 dégâts de foudre.",
        "PassiveFeature_ThunderboltStrike", Boosts="UnlockInterrupt(Interrupt_DOC_Retribution)")
spell("Target_DOC_VerdictFinal", "Target", "Verdict final",
      "Une fois par repos long. La cible fait un jet de sauvegarde de Constitution. Échec : si elle a "
      "moins de 25 % de ses PV, elle est exécutée ; sinon elle subit 10d10 dégâts de foudre. "
      "Réussite : 6d10 dégâts de foudre.",
      using="Target_CallLightning", Icon="Action_DivineIntervention_Attack", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", AreaRadius="1", SpellProperties="",
      SpellRoll="not SavingThrow(Ability.Constitution, SourceSpellDC())",
      SpellSuccess="IF(HasHPPercentageLessThan(25)):Kill();IF(not HasHPPercentageLessThan(25)):DealDamage(10d10,Lightning,Magical)",
      SpellFail="DealDamage(6d10,Lightning,Magical)", TooltipDamageList="DealDamage(10d10,Lightning)",
      **FEATURE_SPELL)
lm = palier("DOC_LM_JugementCeleste", "2d10", "3d10", "4d10", "5d10")
spell("Target_DOC_JugementCeleste", "Target", "Jugement céleste",
      "La foudre divine frappe : 2d10 dégâts de foudre (+1d10 aux niveaux 5, 9 et 12), doublés si la cible "
      "porte votre Marque du jugement. Moitié en cas de sauvegarde de Dextérité réussie.",
      using="Target_CallLightning", Level="1", UseCosts=slot(1), SpellProperties="GROUND:SurfaceChange(Electrify)",
      SpellSuccess=f"IF(HasStatus('DOC_MARQUE_JUGEMENT')):DealDamage(({lm})*2,Lightning,Magical);"
                   f"IF(not HasStatus('DOC_MARQUE_JUGEMENT')):DealDamage({lm},Lightning,Magical)",
      SpellFail=f"DealDamage(({lm})/2,Lightning,Magical)", TooltipDamageList=f"DealDamage({lm},Lightning)",
      **NO_UPCAST)
lm = palier("DOC_LM_GlaiveSentence", "3d8", "3d8", "4d8", "5d8")
spell("Target_DOC_GlaiveSentence", "Target", "Glaive de la sentence",
      "Une attaque d'arme chargée de foudre : dégâts de l'arme + 3d8 dégâts de foudre (augmente aux paliers). "
      "La cible doit réussir un jet de sauvegarde de Force ou tomber À terre.",
      using="Target_Smite_Thunderous", Level="3", UseCosts=slot(3),
      SpellProperties=f"GROUND:DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);"
                      f"GROUND:ExecuteWeaponFunctors(MainHand);GROUND:DealDamage({lm}, Lightning)",
      SpellSuccess=f"DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);ExecuteWeaponFunctors(MainHand);"
                   f"DealDamage({lm},Lightning,Magical);"
                   f"ApplyStatus(PRONE_THUNDEROUS_SMITE,100,1,,,,not SavingThrow(Ability.Strength, SourceSpellDC()))",
      TooltipDamageList=f"DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);DealDamage({lm},Lightning)",
      **NO_UPCAST)
feat("Justice", 1, passives=["DOC_Justice_Juge", "DOC_Justice_MarqueBonus"], spells=["Target_DOC_MarqueJugement"])
feat("Justice", 3, passives=["DOC_Justice_VisionVeritable"])
feat("Justice", 6, passives=["DOC_Justice_Retribution"])
feat("Justice", 10, spells=["Target_DOC_VerdictFinal"])
DOMAIN_SPELLS["Justice"] = {1: ["Target_DOC_JugementCeleste", "Projectile_GuidingBolt"], 3: ["Target_HoldPerson"],
                            5: ["Target_DOC_GlaiveSentence", "Target_CallLightning"], 7: ["Target_Banishment"],
                            9: ["Target_HoldMonster"]}


# ================================================================== ORDRE : MAGIE (force)
passive("DOC_Magie_Codex", "Codex",
        "Comme un magicien, vous pouvez apprendre des sorts à partir des parchemins.",
        "PassiveFeature_ArcaneBattery")
interrupt("Interrupt_DOC_ArbitreTrame", "Arbitre de la Trame",
          "Réaction, une fois par repos court : contrez un sort lancé par un ennemi, sans emplacement de sort.",
          "PassiveFeature_ProjectedWard", using="Interrupt_Counterspell",
          Conditions="CanSee(context.Observer, context.Source) and "
                     "not DistanceToEntityGreaterThan(18, context.ObserverPosition, context.Source) and "
                     "IsAbleToReact(context.Observer) and not Self(context.Source, context.Observer) and "
                     "Enemy(context.Source, context.Observer) and IsSpell() and not Uninterruptible() and "
                     "not HasStringInSpellRoll('WeaponAttack') and not AnyEntityIsItem()",
          Cost="ReactionActionPoint:1;DOC_PouvoirDivin:1", Stack="DOC_ArbitreTrame")
passive("DOC_Magie_ArbitreTrame", "Arbitre de la Trame",
        "Réaction, une fois par repos court : contrez un sort ennemi sans dépenser d'emplacement de sort.",
        "PassiveFeature_ProjectedWard", Boosts="UnlockInterrupt(Interrupt_DOC_ArbitreTrame)")
passive("DOC_Magie_FocalisationAbsolue", "Focalisation absolue",
        "Les dégâts ne brisent plus votre concentration.", "PassiveFeature_WarCaster_Bonuses",
        Boosts=";".join(f"ConcentrationIgnoreDamage({s})" for s in SCHOOLS))
passive("DOC_Magie_MaitriseSorts", "Maîtrise des sorts",
        "Choisissez un sort de niveau 1 et un sort de niveau 2 : vous pouvez les lancer sans emplacement "
        "de sort, une fois par tour.", "PassiveFeature_ArcaneWard")
lm_salve = "DealDamage(1d4+1,Force)"
spell("Projectile_DOC_SalveOrdre", "Projectile", "Salve de l'Ordre",
      "5 projectiles de force qui touchent toujours : 1d4+1 dégâts de force chacun.",
      using="Projectile_MagicMissile", Level="1", UseCosts=slot(1), AmountOfTargets="5",
      DescriptionParams=f"{lm_salve};5", **NO_UPCAST)
lm = palier("DOC_LM_PulsationArcanique", "5d8", "5d8", "6d8", "7d8")
s, f = degats(lm, "Force")
spell("Target_DOC_PulsationArcanique", "Target", "Pulsation arcanique",
      "Une onde de pure magie dans une zone de 5 m : 5d8 dégâts de force (augmente aux paliers), moitié en "
      "cas de sauvegarde de Constitution réussie.",
      using="Target_Shatter", Level="3", UseCosts=slot(3), AreaRadius="5", SpellSuccess=s, SpellFail=f,
      TooltipDamageList=f"DealDamage({lm},Force)", **NO_UPCAST)
feat("Magie", 1, passives=["DOC_Magie_Codex"])
feat("Magie", 3, passives=["DOC_Magie_ArbitreTrame"], boosts=["ActionResource(DOC_PouvoirDivin,1,0)"])
feat("Magie", 6, passives=["DOC_Magie_FocalisationAbsolue"])
feat("Magie", 10, passives=["DOC_Magie_MaitriseSorts"])  # sélecteurs ajoutés dans progressions.py
DOMAIN_SPELLS["Magie"] = {1: ["Projectile_DOC_SalveOrdre", "Target_Command_Container"], 3: ["Shout_MirrorImage"],
                          5: ["Target_DOC_PulsationArcanique", "Target_Counterspell"], 7: ["Target_Confusion"],
                          9: ["Target_HoldMonster"]}


# ================================================================== ORDRE : SOLEIL (feu)
passive("DOC_Soleil_FeuSolaire", "Feu solaire",
        "Vos dégâts de feu ignorent la résistance au feu.", "PassiveFeature_ElementalAdept_Fire",
        Boosts="IgnoreResistance(Fire,Resistant)")
lm = palier("DOC_LM_EruptionSolaire", "3d6", "4d6", "5d6", "6d6")
spell("Zone_DOC_EruptionSolaire", "Zone", "Éruption solaire",
      "Une fois par repos court : un cône de 12 m de lumière brûlante. 3d6 dégâts de feu (augmente aux "
      "paliers) ; en cas d'échec à la sauvegarde de Constitution, les cibles sont Aveuglées et En feu "
      "pendant 2 tours.",
      using="Zone_BurningHands", Icon="Spell_Evocation_Sunbeam", Cooldown="OncePerShortRest",
      UseCosts="ActionPoint:1", Range="12",
      SpellRoll="not SavingThrow(Ability.Constitution, SourceSpellDC())",
      SpellSuccess=f"DealDamage({lm},Fire,Magical);ApplyStatus(BLINDED,100,2);ApplyStatus(BURNING,100,2)",
      SpellFail=f"DealDamage(({lm})/2,Fire,Magical)", TooltipDamageList=f"DealDamage({lm},Fire)", **FEATURE_SPELL)
status("DOC_HALO_BRULURE", "Brûlure du halo", "Vous subissez 1d6 dégâts radiants au début de votre tour.",
       "Spell_Evocation_Daylight", TickType="StartTurn", TickFunctors="DealDamage(1d6,Radiant,Magical)",
       StackId="DOC_HALO_BRULURE")
ally_aura("DOC_HALO", "Halo", "Les ennemis à 9 m subissent 1d6 dégâts radiants au début de leur tour.",
          "Spell_Evocation_Daylight", 9, "DOC_HALO_BRULURE", "DOC_HALO", 1, enemies=True)
keep_applied("DOC_Soleil_Halo", "Halo",
             "Une aura solaire de 9 m vous entoure : les ennemis qui s'y trouvent subissent 1d6 dégâts "
             "radiants au début de leur tour. Vos alliés ne sont pas affectés.",
             "Spell_Evocation_Daylight", "DOC_HALO")
spell("Projectile_DOC_Supernova", "Projectile", "Supernova",
      "Une fois par repos long : une explosion de 12d6 dégâts de feu (moitié en cas de sauvegarde de "
      "Dextérité réussie) qui laisse le sol en flammes. Grâce à votre absorption, ces flammes vous soignent.",
      using="Projectile_Fireball", Icon="Spell_Evocation_WallOfFire", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", SpellProperties="GROUND:CreateSurface(6,3,Fire)",
      SpellSuccess="DealDamage(12d6,Fire,Magical)", SpellFail="DealDamage((12d6)/2,Fire,Magical)",
      TooltipDamageList="DealDamage(12d6,Fire)", **FEATURE_SPELL)
lm = palier("DOC_LM_LanceSolaire", "2d6", "3d6", "4d6", "5d6")
spell("Projectile_DOC_LanceSolaire", "Projectile", "Lance solaire",
      "Un trait de soleil : 2d6 dégâts de feu + 2d6 dégâts radiants (augmente aux paliers). La cible prend "
      "feu et le sol s'embrase sous elle.",
      using="Projectile_GuidingBolt", Level="1", UseCosts=slot(1), Icon="Spell_Evocation_Sunbeam",
      SpellSuccess=f"DealDamage({lm},Fire,Magical);DealDamage({lm},Radiant,Magical);ApplyStatus(BURNING,100,2);"
                   f"CreateSurface(1.5,2,Fire)",
      TooltipDamageList=f"DealDamage({lm},Fire);DealDamage({lm},Radiant)", **NO_UPCAST)
lm = palier("DOC_LM_ColonneSolaire", "4d6", "4d6", "5d6", "6d6")
spell("Target_DOC_ColonneSolaire", "Target", "Colonne solaire",
      "Une colonne de feu solaire : 4d6 dégâts de feu + 4d6 dégâts radiants (augmente aux paliers), "
      "moitié en cas de sauvegarde de Dextérité réussie.",
      using="Target_FlameStrike", Level="3", UseCosts=slot(3),
      SpellSuccess=f"DealDamage({lm},Fire,Magical);DealDamage({lm},Radiant,Magical)",
      SpellFail=f"DealDamage(({lm})/2,Fire,Magical);DealDamage(({lm})/2,Radiant,Magical)",
      TooltipDamageList=f"DealDamage({lm},Fire);DealDamage({lm},Radiant)", **NO_UPCAST)
feat("Soleil", 1, passives=["DOC_Soleil_FeuSolaire"])
feat("Soleil", 3, spells=["Zone_DOC_EruptionSolaire"])
feat("Soleil", 6, passives=["DOC_Soleil_Halo"])
feat("Soleil", 10, spells=["Projectile_DOC_Supernova"])
DOMAIN_SPELLS["Soleil"] = {1: ["Projectile_DOC_LanceSolaire", "Zone_BurningHands"], 3: ["Projectile_ScorchingRay"],
                           5: ["Target_DOC_ColonneSolaire", "Projectile_Fireball"], 7: ["Target_FlameStrike"],
                           9: ["Zone_Sunbeam"]}


# ================================================================== ORDRE : PAIX (psychique)
status("DOC_LIEN_PAIX", "Lien de paix", "+1d4 aux attaques, tests et jets de sauvegarde.",
       "Spell_Abjuration_WardingBond",
       Boosts="RollBonus(Attack,1d4);RollBonus(SkillCheck,1d4);RollBonus(RawAbility,1d4);RollBonus(SavingThrow,1d4)",
       StackId="DOC_LIEN_PAIX")
spell("Target_DOC_LienDePaix", "Target", "Lien de paix",
      "Liez jusqu'à 3 alliés : ils ajoutent 1d4 à leurs attaques, tests et jets de sauvegarde. "
      "Le lien dure jusqu'à votre prochain repos long.",
      using="Target_Bless", AmountOfTargets="3", Icon="Spell_Abjuration_WardingBond", UseCosts="ActionPoint:1",
      SpellProperties="ApplyStatus(DOC_LIEN_PAIX,100,-1)", TooltipStatusApply="ApplyStatus(DOC_LIEN_PAIX,100,-1)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;IgnorePreviouslyPickedEntities", **FEATURE_SPELL)
status("DOC_APAISE", "Apaisé",
       "Vous ne pouvez plus attaquer ni agir. L'effet cesse si vous subissez des dégâts.",
       "Spell_Enchantment_CalmEmotions", Boosts="ActionResourceBlock(ActionPoint)", RemoveEvents="OnDamage",
       StackId="DOC_APAISE")
spell("Target_DOC_Apaisement", "Target", "Apaisement",
      "Une fois par repos court : la cible doit réussir un jet de sauvegarde de Sagesse ou ne plus pouvoir "
      "agir pendant 2 tours. L'effet cesse si elle subit des dégâts.",
      using="Target_HoldPerson", Icon="Spell_Enchantment_CalmEmotions", Cooldown="OncePerShortRest",
      UseCosts="ActionPoint:1", TargetConditions="Character() and not Self() and not Dead() and not Ally()",
      SpellSuccess="ApplyStatus(DOC_APAISE,100,2)", TooltipStatusApply="ApplyStatus(DOC_APAISE,100,2)",
      SpellFlags=CRIT_SPELL_FLAGS, **FEATURE_SPELL)
interrupt("Interrupt_DOC_LienProtecteur", "Lien protecteur",
          "Réaction : quand un allié porteur de votre Lien de paix est touché, vous encaissez une partie du "
          "coup : ses dégâts sont divisés par deux.",
          "Spell_Abjuration_WardingBond", InterruptContext="OnPreDamage", InterruptContextScope="Nearby",
          Container="YesNoDecision",
          Conditions="IsAbleToReact(context.Observer) and not Self(context.Target,context.Observer) and "
                     "HasStatus('DOC_LIEN_PAIX',context.Target) and HasDamageEffectFlag(DamageFlags.Hit)",
          Properties="ApplyStatus(UNCANNY_DODGE_REDUCE_DAMAGE,100,0)", Cost="ReactionActionPoint:1",
          Stack="DOC_LienProtecteur", InterruptDefaultValue="Ask;Enabled")
passive("DOC_Paix_LienProtecteur", "Lien protecteur",
        "Réaction : quand un allié lié est touché, ses dégâts sont divisés par deux.",
        "Spell_Abjuration_WardingBond", Boosts="UnlockInterrupt(Interrupt_DOC_LienProtecteur)")
status("DOC_ARMISTICE", "Armistice", "Vous ne pouvez pas attaquer ni agir.", "Spell_Enchantment_CalmEmotions",
       Boosts="ActionResourceBlock(ActionPoint)", StackId="DOC_ARMISTICE")
spell("Shout_DOC_Armistice", "Shout", "Armistice",
      "Une fois par repos long : les ennemis à 9 m doivent réussir un jet de sauvegarde de Sagesse ou ne plus "
      "pouvoir agir pendant 2 tours ; vos alliés dans la zone récupèrent 3d8 PV.",
      using="Shout_HealingWord_Mass", Icon="Spell_Enchantment_CalmEmotions", Cooldown="OncePerRest",
      UseCosts="ActionPoint:1", AreaRadius="9", TargetConditions="Character() and not Dead()",
      SpellRoll="not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellProperties="IF(Ally()):RegainHitPoints(3d8)", SpellSuccess="IF(Enemy()):ApplyStatus(DOC_ARMISTICE,100,2)",
      DescriptionParams="", **FEATURE_SPELL)
hidden("DOC_Paix_TreveRiposte", StatsFunctorContext="OnDamaged",
       Conditions="HasDamageEffectFlag(DamageFlags.Hit) and not Self(context.Source)",
       StatsFunctors="DealDamage(SWAP,2d6,Psychic,Magical)")
status("DOC_TREVE", "Trêve sacrée", "Quiconque vous frappe subit 2d6 dégâts psychiques.",
       "Spell_Abjuration_Sanctuary", Passives="DOC_Paix_TreveRiposte", StackId="DOC_TREVE")
spell("Target_DOC_TreveSacree", "Target", "Trêve sacrée",
      "Protégez jusqu'à 3 alliés (Sanctuaire) pendant 10 tours ; un ennemi qui les frappe subit 2d6 dégâts "
      "psychiques.",
      using="Target_Sanctuary", Level="1", UseCosts="BonusActionPoint:1;SpellSlotsGroup:1:1:1", AmountOfTargets="3",
      SpellProperties="ApplyStatus(SANCTUARY,100,10);ApplyStatus(DOC_TREVE,100,10)",
      TooltipStatusApply="ApplyStatus(DOC_TREVE,100,10)", **NO_UPCAST)
lm = palier("DOC_LM_OndeApaisement", "5d8", "5d8", "6d8", "7d8")
spell("Target_DOC_OndeApaisement", "Target", "Onde d'apaisement",
      "Une vague psychique dans une zone de 4 m : 5d8 dégâts psychiques (augmente aux paliers) et Hébété "
      "1 tour ; moitié des dégâts et pas d'effet en cas de sauvegarde de Sagesse réussie.",
      using="Target_Shatter", Level="3", UseCosts=slot(3), AreaRadius="4", Icon="Spell_Enchantment_CalmEmotions",
      SpellRoll="not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellSuccess=f"DealDamage({lm},Psychic,Magical);ApplyStatus(DAZED,100,1)",
      SpellFail=f"DealDamage(({lm})/2,Psychic,Magical)", TooltipDamageList=f"DealDamage({lm},Psychic)", **NO_UPCAST)
feat("Paix", 1, spells=["Target_DOC_LienDePaix"])
feat("Paix", 3, spells=["Target_DOC_Apaisement"])
feat("Paix", 6, passives=["DOC_Paix_LienProtecteur"])
feat("Paix", 10, spells=["Shout_DOC_Armistice"])
DOMAIN_SPELLS["Paix"] = {1: ["Target_DOC_TreveSacree", "Target_Sanctuary"], 3: ["Target_HoldPerson"],
                         5: ["Target_DOC_OndeApaisement", "Shout_HealingWord_Mass"], 7: ["Target_Banishment"],
                         9: ["Target_HoldMonster"]}


# ================================================================== CHAOS : MORT (nécrotique)
status("DOC_TRIBUT_FAUCHEUR", "Tribut du faucheur", "Points de vie temporaires arrachés à vos victimes.",
       "PassiveFeature_DarkOnesBlessing", Boosts=f"TemporaryHP(CharismaModifier+ClassLevel({CHAOS}))",
       StackId="DOC_TRIBUT_FAUCHEUR")
passive("DOC_Mort_TributFaucheur", "Tribut du faucheur",
        "Quand vous éliminez un ennemi, vous gagnez des PV temporaires égaux à votre modificateur de "
        "Charisme + votre niveau de Divinité du Chaos.",
        "PassiveFeature_DarkOnesBlessing", StatsFunctorContext="OnDamage",
        Conditions="IsKillingBlow() and Enemy() and Character()",
        StatsFunctors="ApplyStatus(SELF,DOC_TRIBUT_FAUCHEUR,100,-1)")
spell("Target_DOC_LeverMorts", "Target", "Lever les morts",
      "Une fois par repos court, sans emplacement : relevez un cadavre en serviteur mort-vivant "
      "(squelette ou zombie).",
      using="Target_AnimateDead", Cooldown="OncePerShortRest", UseCosts="ActionPoint:1",
      ContainerSpells="Target_DOC_LeverMorts_Skeleton;Target_DOC_LeverMorts_Zombie", **FEATURE_SPELL)
for kind, fr in (("Skeleton", "squelette"), ("Zombie", "zombie")):
    spell(f"Target_DOC_LeverMorts_{kind}", "Target", f"Lever les morts : {fr}",
          f"Relevez un cadavre en {fr} à votre service. Une fois par repos court.",
          using=f"Target_AnimateDead_{kind}", SpellContainerID="Target_DOC_LeverMorts",
          Cooldown="OncePerShortRest", UseCosts="ActionPoint:1", **FEATURE_SPELL)
status("DOC_FLETRI", "Flétri", "Vous ne pouvez pas récupérer de PV.", "Spell_Necromancy_Blight",
       Boosts="BlockRegainHP()", StackId="DOC_FLETRI")
passive("DOC_Mort_ToucherFletrissant", "Toucher flétrissant",
        "Les créatures à qui vous infligez des dégâts nécrotiques ne peuvent pas être soignées jusqu'à votre "
        "prochain tour.", "Spell_Necromancy_Blight", StatsFunctorContext="OnDamage",
        Conditions="IsDamageTypeNecrotic() and not Self()", StatsFunctors="ApplyStatus(DOC_FLETRI,100,1)")
status("DOC_OUTRE_TOMBE", "Outre-tombe", "La prochaine fois que vous tombez à 0 PV, vous restez à 1 PV.",
       "PassiveFeature_UndeadThralls_BetterSummons", using="RELENTLESS_ENDURANCE", StackId="DOC_OUTRE_TOMBE")
status("DOC_AURA_OUTRE_TOMBE_MAL", "Souffle d'outre-tombe", "Vous subissez 2d6 dégâts nécrotiques au début de votre tour.",
       "Spell_Necromancy_Harm", TickType="StartTurn", TickFunctors="DealDamage(2d6,Necrotic,Magical)",
       StackId="DOC_AURA_OUTRE_TOMBE_MAL")
ally_aura("DOC_AURA_OUTRE_TOMBE", "Aura d'outre-tombe",
          "Les ennemis à 3 m subissent 2d6 dégâts nécrotiques au début de leur tour.",
          "Spell_Necromancy_Harm", 3, "DOC_AURA_OUTRE_TOMBE_MAL", "DOC_AURA_OUTRE_TOMBE", 1, enemies=True)
passive("DOC_Mort_OutreTombe", "Outre-tombe",
        "Une fois par repos long, quand vous devriez mourir, vous restez à 1 PV puis vous vous relevez "
        "aussitôt avec la moitié de vos PV et une aura nécrotique (2d6 par tour aux ennemis à 3 m) pendant 3 tours.",
        "PassiveFeature_UndeadThralls_BetterSummons", props="Highlighted;OncePerLongRest",
        StatsFunctorContext="OnCreate;OnLongRest", StatsFunctors="ApplyStatus(SELF,DOC_OUTRE_TOMBE,100,-1)")
hidden("DOC_Mort_OutreTombe_Releve", StatsFunctorContext="OnStatusRemoved",
       Conditions="StatusId('DOC_OUTRE_TOMBE') and HasHPLessThan(2)",
       StatsFunctors="RegainHitPoints(MaxHP/2);ApplyStatus(SELF,DOC_AURA_OUTRE_TOMBE,100,3)")
lm = palier("DOC_LM_MoissonAmes", "2d8", "3d8", "4d8", "5d8")
spell("Target_DOC_MoissonAmes", "Target", "Moisson des âmes",
      "Une vague nécrotique dans une zone de 4 m : 2d8 dégâts nécrotiques (+1d8 aux niveaux 5, 9 et 12), "
      "moitié en cas de sauvegarde de Dextérité réussie. Vous récupérez la moitié des dégâts infligés.",
      using="Target_FlameStrike", Level="1", UseCosts=slot(1), AreaRadius="4", SpellProperties="",
      Icon="Spell_Necromancy_Blight",
      SpellSuccess=f"DealDamage({lm},Necrotic,Magical);RegainHitPoints(SELF,(DamageDone)/2)",
      SpellFail=f"DealDamage(({lm})/2,Necrotic,Magical)", TooltipDamageList=f"DealDamage({lm},Necrotic)",
      **NO_UPCAST)
lm = palier("DOC_LM_EtreinteTombeau", "4d8", "4d8", "5d8", "6d8")
spell("Target_DOC_EtreinteTombeau", "Target", "Étreinte du tombeau",
      "Un toucher qui draine la vie : 4d8 dégâts nécrotiques (augmente aux paliers) ; vous récupérez autant "
      "de PV que les dégâts infligés. Pas de concentration.",
      using="Target_VampiricTouch", Level="3", UseCosts=slot(3), SpellProperties="",
      SpellSuccess=f"DealDamage({lm},Necrotic,Magical);RegainHitPoints(SELF,DamageDone)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;IsMelee;IsHarmful",
      TooltipDamageList=f"DealDamage({lm},Necrotic)", **NO_UPCAST)
feat("Mort", 1, passives=["DOC_Mort_TributFaucheur"])
feat("Mort", 3, spells=["Target_DOC_LeverMorts"])
feat("Mort", 6, passives=["DOC_Mort_ToucherFletrissant"])
feat("Mort", 10, passives=["DOC_Mort_OutreTombe", "DOC_Mort_OutreTombe_Releve"])
DOMAIN_SPELLS["Mort"] = {1: ["Target_DOC_MoissonAmes", "Shout_FalseLife"], 3: ["Target_Darkness"],
                         5: ["Target_DOC_EtreinteTombeau", "Target_AnimateDead"], 7: ["Target_Blight"],
                         9: ["Target_DominatePerson"]}


# ================================================================== CHAOS : TROMPERIE (poison)
status("DOC_DOUBLE_ILLUSOIRE", "Double illusoire", "Avantage à vos attaques au corps à corps.",
       "Action_Cleric_BlessingOfTheTrickster", Boosts="IF(IsMeleeAttack()):Advantage(AttackRoll)",
       StackId="DOC_DOUBLE_ILLUSOIRE")
spell("Shout_DOC_DoubleIllusoire", "Shout", "Double illusoire",
      "Action bonus, une fois par repos court : des doubles illusoires vous entourent (Image miroir) et "
      "vous avez l'avantage à vos attaques au corps à corps pendant 10 tours.",
      using="Shout_MirrorImage", Icon="Action_Cleric_BlessingOfTheTrickster", Cooldown="OncePerShortRest",
      UseCosts="BonusActionPoint:1",
      SpellProperties="ApplyStatus(MIRROR_IMAGE_3,100,10);ApplyStatus(MIRROR_IMAGE_2,100,10);"
                      "ApplyStatus(MIRROR_IMAGE_1,100,10);ApplyStatus(DOC_DOUBLE_ILLUSOIRE,100,10)",
      **FEATURE_SPELL)
spell("Target_DOC_EscamotagePas", "Target", "Escamotage : disparition",
      "Téléportez-vous à un endroit visible à 18 m ou moins.", using="Target_MistyStep",
      UseCosts="BonusActionPoint:1", **FEATURE_SPELL)
status("DOC_ESCAMOTAGE", "Escamotage", "Vous pouvez vous téléporter en action bonus.",
       "Action_Quasit_Invisibility", Boosts="UnlockSpell(Target_DOC_EscamotagePas)", StackId="DOC_ESCAMOTAGE")
interrupt("Interrupt_DOC_Escamotage", "Escamotage",
          "Réaction, une fois par repos court : quand vous êtes touché, vous devenez invisible et pouvez "
          "vous téléporter (6 m ou plus) en action bonus.",
          "Action_Quasit_Invisibility", InterruptContext="OnCastHit", InterruptContextScope="Self",
          Container="YesNoDecision",
          Conditions="IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and "
                     "Enemy(context.Source,context.Observer) and IsHit() and not AnyEntityIsItem() and "
                     "HasLastAttackTriggered()",
          Properties="ApplyStatus(OBSERVER_OBSERVER,INVISIBILITY,100,2);ApplyStatus(OBSERVER_OBSERVER,DOC_ESCAMOTAGE,100,1)",
          Cost="ReactionActionPoint:1;DOC_PouvoirDivin:1", Stack="DOC_Escamotage",
          InterruptDefaultValue="Ask;Enabled")
passive("DOC_Tromperie_Escamotage", "Escamotage",
        "Réaction, une fois par repos court : quand vous êtes touché, vous devenez invisible et pouvez vous "
        "téléporter en action bonus.", "Action_Quasit_Invisibility",
        Boosts="UnlockInterrupt(Interrupt_DOC_Escamotage)")
passive("DOC_Tromperie_LangueArgent", "Langue d'argent",
        "Vos tests de Tromperie et de Persuasion ne peuvent pas donner moins de 15 au dé.",
        "Action_Bard_Countercharm",
        Boosts="IF(IsSkillChecked(Skill.Deception)):MinimumRollResult(SkillCheck,15);"
               "IF(IsSkillChecked(Skill.Persuasion)):MinimumRollResult(SkillCheck,15)")
spell("Target_DOC_Marionnettiste", "Target", "Marionnettiste",
      "Une fois par repos long : la cible doit réussir un jet de sauvegarde de Sagesse ou passer sous votre "
      "contrôle pendant 3 tours. Pas de concentration.",
      using="Target_DominatePerson", Cooldown="OncePerRest", UseCosts="ActionPoint:1",
      TargetConditions="Character() and not Ally() and not Dead() and not (Party(context.Target) and Party(context.Source))",
      SpellSuccess="ApplyStatus(DOMINATE_PERSON,100,3)",
      SpellFlags="HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
      **FEATURE_SPELL)
lm = palier("DOC_LM_BaiserTraitre", "2d8", "3d8", "4d8", "5d8")
spell("Projectile_DOC_BaiserTraitre", "Projectile", "Baiser du traître",
      "Un rayon empoisonné : 2d8 dégâts de poison (+1d8 aux niveaux 5, 9 et 12) ; la cible est Charmée "
      "pendant 1 tour.",
      using="Projectile_RayOfSickness", Level="1", UseCosts=slot(1),
      SpellSuccess=f"DealDamage({lm},Poison,Magical);ApplyStatus(CHARMED,100,1)",
      TooltipDamageList=f"DealDamage({lm},Poison)", **NO_UPCAST)
lm = palier("DOC_LM_NueeVenin", "5d8", "5d8", "6d8", "7d8")
spell("Target_DOC_NueeVenin", "Target", "Nuée de venin",
      "Un nuage de venin dans une zone de 4 m : 5d8 dégâts de poison (augmente aux paliers) et Empoisonné "
      "2 tours ; moitié des dégâts et pas d'effet en cas de sauvegarde de Constitution réussie.",
      using="Target_Shatter", Level="3", UseCosts=slot(3), AreaRadius="4", Icon="Action_DippedPoison_Melee",
      SpellSuccess=f"DealDamage({lm},Poison,Magical);ApplyStatus(POISONED,100,2)",
      SpellFail=f"DealDamage(({lm})/2,Poison,Magical)", TooltipDamageList=f"DealDamage({lm},Poison)", **NO_UPCAST)
feat("Tromperie", 1, spells=["Shout_DOC_DoubleIllusoire"])
feat("Tromperie", 3, passives=["DOC_Tromperie_Escamotage"], boosts=["ActionResource(DOC_PouvoirDivin,1,0)"])
feat("Tromperie", 6, passives=["DOC_Tromperie_LangueArgent"])
feat("Tromperie", 10, spells=["Target_DOC_Marionnettiste"])
DOMAIN_SPELLS["Tromperie"] = {1: ["Projectile_DOC_BaiserTraitre", "Target_CharmPerson"], 3: ["Shout_MirrorImage"],
                              5: ["Target_DOC_NueeVenin", "Shout_Blink"], 7: ["Target_Confusion"],
                              9: ["Target_DominatePerson"]}


# ================================================================== CHAOS : SORCELLERIE (acide)
status("DOC_FAILLE_ACIDE", "Faille acide", "Vous subissez 2d4 dégâts d'acide au début de votre tour.",
       "PassiveFeature_ElementalAdept_Acid", TickType="StartTurn", TickFunctors="DealDamage(2d4,Acid,Magical)",
       StackId="DOC_FAILLE_ACIDE")
passive("DOC_Sorcellerie_EntropieSorcellaire", "Métamagie chaotique",
        "Vous apprenez 2 options de Métamagie et gagnez des points de sorcellerie (2, puis 4 au niveau 6 et "
        "6 au niveau 10). Chaque coup critique ou ennemi éliminé vous rend 1 point de sorcellerie : votre "
        "métamagie se nourrit du chaos.",
        "PassiveFeature_WildMagicSurge", props="Highlighted;OncePerAttack", StatsFunctorContext="OnDamage",
        Conditions="(IsCritical() or IsKillingBlow()) and not Self()",
        StatsFunctors="RestoreResource(SELF,SorceryPoint,1,0)")
passive("DOC_Sorcellerie_ChaosMaitrise", "Chaos maîtrisé",
        "Vos Déferlements de chaos ne tirent plus dans la table de magie sauvage : seulement dans la table "
        "des effets divins, bien plus favorable.", "PassiveFeature_WildMagicRage")
hidden("DOC_Sorcellerie_FailleDeferlement", StatsFunctorContext="OnCast",
       Conditions="SpellId('Projectile_DOC_FailleAcide')", StatsFunctors="TriggerRandomCast(1,,DOC_DeferlementDivin)")
status("DOC_TEMPETE_ARCANIQUE", "Tempête arcanique", "Chacun de vos sorts en déclenche un autre au hasard.",
       "Action_Barbarian_Rage_WildMagic", StackId="DOC_TEMPETE_ARCANIQUE")
spell("Shout_DOC_TempeteArcanique", "Shout", "Tempête arcanique",
      "Une fois par repos long, pendant 3 tours : chaque sort que vous lancez déclenche en plus une explosion "
      "aléatoire (feu, foudre ou froid, 3d6 dégâts aux ennemis à 6 m).",
      using="Shout_DivineSense", Icon="Action_Barbarian_Rage_WildMagic", Cooldown="OncePerRest",
      UseCosts="BonusActionPoint:1", SpellProperties="ApplyStatus(SELF,DOC_TEMPETE_ARCANIQUE,100,3)",
      TooltipStatusApply="ApplyStatus(DOC_TEMPETE_ARCANIQUE,100,3)")
hidden("DOC_Sorcellerie_TempeteArcanique", StatsFunctorContext="OnCast",
       Conditions="HasStatus('DOC_TEMPETE_ARCANIQUE',context.Source) and HasSpellFlag(SpellFlags.Spell)",
       StatsFunctors="TriggerRandomCast(1,,DOC_TempeteArcanique)")
lm = palier("DOC_LM_FailleAcide", "4d4", "5d4", "6d4", "8d4")
spell("Projectile_DOC_FailleAcide", "Projectile", "Faille acide",
      "Une flèche d'acide primordial : 4d4 dégâts d'acide (augmente aux paliers) et 2d4 dégâts d'acide au "
      "début des 2 tours suivants (moitié des dégâts initiaux si l'attaque rate). Déclenche un Déferlement de "
      "chaos.",
      using="Projectile_AcidArrow", Level="1", UseCosts=slot(1),
      SpellSuccess=f"DealDamage({lm},Acid,Magical);ApplyStatus(DOC_FAILLE_ACIDE,100,2)",
      SpellFail=f"DealDamage(({lm})/2,Acid,Magical)", TooltipDamageList=f"DealDamage({lm},Acid)", **NO_UPCAST)
lm = palier("DOC_LM_PluieCorrosive", "5d8", "5d8", "6d8", "7d8")
spell("Target_DOC_PluieCorrosive", "Target", "Pluie corrosive",
      "Une pluie d'acide sur une zone : 5d8 dégâts d'acide (augmente aux paliers) et Faille acide ; moitié "
      "des dégâts et pas d'effet en cas de sauvegarde de Dextérité réussie.",
      using="Target_IceStorm", Level="3", UseCosts=slot(3), SpellProperties="",
      Icon="Spell_Transmutation_ElementalWeapon_Acid",
      SpellSuccess=f"DealDamage({lm},Acid,Magical);ApplyStatus(DOC_FAILLE_ACIDE,100,2)",
      SpellFail=f"DealDamage(({lm})/2,Acid,Magical)", TooltipDamageList=f"DealDamage({lm},Acid)", **NO_UPCAST)
feat("Sorcellerie", 1, passives=["TidesOfChaos", "DOC_Sorcellerie_FailleDeferlement"],
     boosts=["ActionResource(TidesOfChaos,1,0)"])
feat("Sorcellerie", 3, passives=["DOC_Sorcellerie_EntropieSorcellaire"], boosts=["ActionResource(SorceryPoint,2,0)"],
     selectors=[f"SelectPassives({METAMAGIC_LIST},2,Metamagic)"])
feat("Sorcellerie", 6, passives=["DOC_Sorcellerie_ChaosMaitrise"], boosts=["ActionResource(SorceryPoint,2,0)"])
feat("Sorcellerie", 10, passives=["DOC_Sorcellerie_TempeteArcanique"], spells=["Shout_DOC_TempeteArcanique"],
     boosts=["ActionResource(SorceryPoint,2,0)"])
DOMAIN_SPELLS["Sorcellerie"] = {1: ["Projectile_DOC_FailleAcide", "Zone_ColorSpray"], 3: ["Target_CloudOfDaggers"],
                                5: ["Target_DOC_PluieCorrosive", "Target_Counterspell"], 7: ["Target_Confusion"],
                                9: ["Target_HoldMonster"]}

for t, fr in (("Fire", "Nova de feu"), ("Lightning", "Nova de foudre"), ("Cold", "Nova de givre")):
    outcome("DOC_TempeteArcanique", f"Shout_DOC_TempeteArcanique_{t}", f"Tempête arcanique : {fr}",
            f"Les ennemis à 6 m subissent 3d6 dégâts {TYPE_FR[t]}.", AreaRadius="6",
            TargetConditions="Enemy() and not Dead()", SpellProperties=f"DealDamage(3d6,{t},Magical)")


# ================================================================== CHAOS : LUNE (froid)
PHASES = {
    "NOUVELLE": ("Nouvelle lune", "Avantage aux tests de Discrétion.", "Advantage(Skill,Stealth)"),
    "CROISSANTE": ("Lune croissante", "+3 m de déplacement.", "ActionResource(Movement,3,0)"),
    "PLEINE": ("Pleine lune", "Vos attaques au corps à corps infligent 1d6 dégâts de froid supplémentaires.",
               "IF(IsMeleeAttack()):CharacterWeaponDamage(1d6,Cold);CharacterUnarmedDamage(1d6,Cold)"),
    "DECROISSANTE": ("Lune décroissante", "+1d4 aux dégâts de vos sorts.",
                     "RollBonus(MeleeSpellDamage,1d4);RollBonus(RangedSpellDamage,1d4)"),
}
for key, (titre, desc, boosts) in PHASES.items():
    status(f"DOC_PHASE_{key}", titre, desc, "Spell_Evocation_Moonbeam", Boosts=boosts, StackId="DOC_PHASE_LUNAIRE",
           StatusPropertyFlags="IgnoreResting", StatusGroups="SG_RemoveOnRespec")
    outcome("DOC_PhasesLunaires", f"Shout_DOC_Phase_{key.capitalize()}", f"Phase lunaire : {titre}", desc,
            TargetConditions="Self()",
            SpellProperties=";".join(f"RemoveStatus(DOC_PHASE_{k})" for k in PHASES) + f";ApplyStatus(DOC_PHASE_{key},100,-1)")
passive("DOC_Lune_PhasesLunaires", "Phases lunaires",
        "À chaque repos long, la lune prend une phase au hasard : nouvelle lune (avantage en Discrétion), "
        "croissante (+3 m de déplacement), pleine (+1d6 dégâts de froid au corps à corps) ou décroissante "
        "(+1d4 aux dégâts des sorts).",
        "Spell_Evocation_Moonbeam", StatsFunctorContext="OnCreate;OnLongRest",
        StatsFunctors="TriggerRandomCast(1,,DOC_PhasesLunaires)")
spell("Shout_DOC_BeteLunaire", "Shout", "Bête lunaire",
      "Une fois par repos court, en action bonus : vous prenez la forme d'un loup lunaire (loup sanguinaire).",
      using="Shout_WildShape_Wolf_Dire", Icon="Action_AspectOfTheWolf", Cooldown="OncePerShortRest",
      UseCosts="BonusActionPoint:1", **FEATURE_SPELL)
status("DOC_ECLIPSE_FROID", "Froid de l'éclipse",
       "Vous subissez 2d8 dégâts de froid au début de votre tour et avez un désavantage à vos attaques.",
       "Spell_Evocation_Darkness", TickType="StartTurn", TickFunctors="DealDamage(2d8,Cold,Magical)",
       Boosts="Disadvantage(AttackRoll)", StackId="DOC_ECLIPSE_FROID")
add_eclipse = ally_aura("DOC_ECLIPSE", "Éclipse",
                        "Vous récupérez 2d8 PV au début de votre tour ; les ennemis à 9 m subissent 2d8 dégâts "
                        "de froid par tour et ont un désavantage à leurs attaques.",
                        "Spell_Evocation_Darkness", 9, "DOC_ECLIPSE_FROID", "DOC_ECLIPSE", 1, enemies=True)
add_eclipse.set(TickType="StartTurn", TickFunctors="RegainHitPoints(2d8)", Boosts="StatusImmunity(SG_Blinded)")
spell("Shout_DOC_Eclipse", "Shout", "Éclipse",
      "Une fois par repos long, pendant 10 tours : des ténèbres magiques vous entourent. Vous y voyez, vous "
      "récupérez 2d8 PV par tour, et les ennemis à 9 m subissent 2d8 dégâts de froid par tour.",
      using="Shout_DivineSense", Icon="Spell_Evocation_Darkness", Cooldown="OncePerRest", UseCosts="ActionPoint:1",
      SpellProperties="ApplyStatus(SELF,DOC_ECLIPSE,100,10);CreateSurface(5,10,DarknessCloud)",
      TooltipStatusApply="ApplyStatus(DOC_ECLIPSE,100,10)")
status("DOC_GLACE", "Glacé", "Votre vitesse est réduite de moitié.", "Spell_Evocation_IceStorm",
       Boosts="ActionResourceMultiplier(Movement,50,0)", StackId="DOC_GLACE")
lm = palier("DOC_LM_ClairDeLune", "2d8", "3d8", "4d8", "5d8")
spell("Target_DOC_ClairDeLune", "Target", "Clair de lune glacé",
      "Un rayon de lune glacé frappe une zone de 3 m : 2d8 dégâts de froid (+1d8 aux niveaux 5, 9 et 12) et "
      "vitesse réduite de moitié pendant 2 tours ; moitié des dégâts et pas de ralentissement en cas de "
      "sauvegarde de Dextérité réussie.",
      using="Target_IceStorm", Level="1", UseCosts=slot(1), AreaRadius="3", Icon="Spell_Evocation_Moonbeam",
      SpellProperties="GROUND:SurfaceChange(Freeze)",
      SpellSuccess=f"DealDamage({lm},Cold,Magical);ApplyStatus(DOC_GLACE,100,2)",
      SpellFail=f"DealDamage(({lm})/2,Cold,Magical)", TooltipDamageList=f"DealDamage({lm},Cold)", **NO_UPCAST)
lm = palier("DOC_LM_EclatLunaire", "3d8", "3d8", "4d8", "5d8")
spell("Target_DOC_EclatLunaire", "Target", "Éclat lunaire",
      "La lumière froide de la lune : 3d8 dégâts de froid + 3d8 dégâts radiants (augmente aux paliers), "
      "moitié en cas de sauvegarde de Dextérité réussie.",
      using="Target_SacredFlame", Level="3", UseCosts=slot(3), Icon="Spell_Evocation_Moonbeam",
      SpellSuccess=f"DealDamage({lm},Cold,Magical);DealDamage({lm},Radiant,Magical)",
      SpellFail=f"DealDamage(({lm})/2,Cold,Magical);DealDamage(({lm})/2,Radiant,Magical)",
      TooltipDamageList=f"DealDamage({lm},Cold);DealDamage({lm},Radiant)", **NO_UPCAST)
feat("Lune", 1, passives=["DOC_Lune_PhasesLunaires"])
feat("Lune", 3, spells=["Target_ShadowStep"])
feat("Lune", 6, spells=["Shout_DOC_BeteLunaire"])
feat("Lune", 10, spells=["Shout_DOC_Eclipse"])
DOMAIN_SPELLS["Lune"] = {1: ["Target_DOC_ClairDeLune", "Shout_ArmorOfAgathys"], 3: ["Target_Moonbeam"],
                         5: ["Target_DOC_EclatLunaire", "Target_SleetStorm"], 7: ["Target_IceStorm"],
                         9: ["Target_HoldMonster"]}


# ================================================================== CHAOS : GUERRE (tonnerre)
status("DOC_CRI_GUERRE", "Cri de guerre", "+2 aux dégâts.", "Action_DireWolfPack_Howl", Boosts="DamageBonus(2)",
       StackId="DOC_CRI_GUERRE")
spell("Shout_DOC_CriDeGuerre", "Shout", "Cri de guerre",
      "Action bonus, une fois par repos court : les ennemis à 6 m doivent réussir un jet de sauvegarde de "
      "Sagesse ou être Effrayés pendant 2 tours ; vos alliés dans la zone gagnent +2 aux dégâts.",
      using="Shout_DivineSense", Icon="Action_DireWolfPack_Howl", Cooldown="OncePerShortRest",
      UseCosts="BonusActionPoint:1", AreaRadius="6", TargetConditions="Character() and not Dead()",
      SpellRoll="not SavingThrow(Ability.Wisdom, SourceSpellDC())",
      SpellProperties="IF(not Enemy()):ApplyStatus(DOC_CRI_GUERRE,100,2)",
      SpellSuccess="IF(Enemy()):ApplyStatus(FRIGHTENED,100,2)", TooltipStatusApply="ApplyStatus(FRIGHTENED,100,2)")
passive("DOC_Guerre_Carnage", "Carnage",
        "Quand vous éliminez un ennemi, vous pouvez faire une attaque supplémentaire en action bonus.",
        "PassiveFeature_WarPriest", StatsFunctorContext="OnDamage",
        Conditions="IsKillingBlow() and Enemy() and not Self()",
        StatsFunctors="ApplyStatus(SELF,GREAT_WEAPON_MASTER_BONUS_ATTACK,100,1)")
status("DOC_INCARNATION_GUERRE", "Incarnation de la guerre",
       "Une action supplémentaire par tour, résistance aux dégâts physiques, immunité à la peur.",
       "PassiveFeature_WarGodsBlessing",
       Boosts="ActionResource(ActionPoint,1,0);Resistance(Slashing,Resistant);Resistance(Piercing,Resistant);"
              "Resistance(Bludgeoning,Resistant);StatusImmunity(SG_Frightened)",
       StackId="DOC_INCARNATION_GUERRE")
spell("Shout_DOC_IncarnationGuerre", "Shout", "Incarnation de la guerre",
      "Une fois par repos long, pendant 3 tours : une action supplémentaire par tour (pour une 3e attaque et "
      "plus), résistance aux dégâts tranchants, perforants et contondants, immunité à la peur.",
      using="Shout_DivineSense", Icon="PassiveFeature_WarGodsBlessing", Cooldown="OncePerRest",
      UseCosts="BonusActionPoint:1", SpellProperties="ApplyStatus(SELF,DOC_INCARNATION_GUERRE,100,3)",
      TooltipStatusApply="ApplyStatus(DOC_INCARNATION_GUERRE,100,3)")
lm = palier("DOC_LM_FracasGuerre", "2d8", "3d8", "4d8", "5d8")
spell("Zone_DOC_FracasGuerre", "Zone", "Fracas de guerre",
      "Une onde de tonnerre : 2d8 dégâts de tonnerre (+1d8 aux niveaux 5, 9 et 12) ; en cas d'échec à la "
      "sauvegarde de Constitution, les ennemis sont repoussés et tombent À terre.",
      using="Zone_Thunderwave", Level="1", UseCosts=slot(1),
      SpellSuccess=f"DealDamage({lm},Thunder,Magical);Force(4);ApplyStatus(PRONE,100,1)",
      SpellFail=f"DealDamage(({lm})/2,Thunder,Magical)", TooltipDamageList=f"DealDamage({lm},Thunder)", **NO_UPCAST)
lm = palier("DOC_LM_TonnerreBataille", "4d6", "4d6", "5d6", "6d6")
spell("Target_DOC_TonnerreBataille", "Target", "Tonnerre de bataille",
      "Une attaque d'arme qui gronde comme l'orage : dégâts de l'arme + 4d6 dégâts de tonnerre (augmente aux "
      "paliers). La cible doit réussir un jet de sauvegarde de Force ou tomber À terre.",
      using="Target_Smite_Thunderous", Level="3", UseCosts=slot(3),
      SpellProperties=f"GROUND:DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);"
                      f"GROUND:ExecuteWeaponFunctors(MainHand);GROUND:DealDamage({lm}, Thunder)",
      SpellSuccess=f"DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);ExecuteWeaponFunctors(MainHand);"
                   f"DealDamage({lm},Thunder,Magical);"
                   f"ApplyStatus(PRONE_THUNDEROUS_SMITE,100,1,,,,not SavingThrow(Ability.Strength, SourceSpellDC()))",
      TooltipDamageList=f"DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);DealDamage({lm},Thunder)",
      **NO_UPCAST)
passive("DOC_Guerre_NePourLaGuerre", "Né pour la guerre",
        "Vous maîtrisez les armures lourdes et les armes de guerre. Au niveau 5, vous gagnez une attaque "
        "supplémentaire.", "PassiveFeature_WarPriest")
feat("Guerre", 1, passives=["DOC_Guerre_NePourLaGuerre"],
     boosts=["Proficiency(HeavyArmor)", "Proficiency(MartialWeapons)"])
feat("Guerre", 3, spells=["Shout_DOC_CriDeGuerre"])
feat("Guerre", 5, passives=["ExtraAttack"])
feat("Guerre", 6, passives=["DOC_Guerre_Carnage"])
feat("Guerre", 10, spells=["Shout_DOC_IncarnationGuerre"])
DOMAIN_SPELLS["Guerre"] = {1: ["Zone_DOC_FracasGuerre", "Target_Smite_Thunderous"], 3: ["Target_Shatter"],
                           5: ["Target_DOC_TonnerreBataille", "Shout_CrusadersMantle"], 7: ["Target_HoldMonster"],
                           9: ["Target_FlameStrike"]}
