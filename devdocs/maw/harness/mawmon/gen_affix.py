T={1:(20,0.5),2:(10,1),3:(10,1),4:(5,0.5),5:(7,0.15),6:(7,0.15),7:(1,0.1),8:(5,0.25),9:(15,0.2),10:(5,0.1),
11:(30,1),12:(30,2),13:(30,1),14:(20,1),15:(20,1.5),16:(30,0.5),17:(20,0.5),18:(15,1),19:(4,0.05),20:(10,0.2),
21:(10,0.2),22:(20,1),23:(15,0.5),24:(15,0.5),25:(15,0.5),26:(15,0.5),27:(15,0.5),28:(15,0.5),29:(15,0.5),
30:(15,0.5),31:(15,0.5),32:(15,0.5),33:(15,0.5)}
RED={13,21,22,23,24,25,26,27,28,29,30,31,32,33}
PROC={3,4,8,9,14,19,34}
def mround(x): 
    return int(x) if x==int(x) else x
def power(n,p):
    b,s=T[n]; v=b+p*s
    if n in RED: v=round((1-1/(v/100+1))*100*100)/100
    if n in PROC: v=min(v,100)
    return v
E={
1:("monster","Monsters deal +X% damage","Damage.lua:1944-1946","player pipe: x(1 + X/100) when the attacker is a monster","works"),
2:("monster","Monsters have X% critical chance","Damage.lua:1947-1951","player pipe: X% chance of x2 on ANY damage to a player (traps and falls too)","works"),
3:("monster","X% chance to cast Fireball","zzMaw-Monsters.lua:340-345","every map monster: Spell 6, SpellChance X, SpellSkill field 10","works"),
4:("monster","X% chance to cast Dragon Breath","zzMaw-Monsters.lua:346-350","every map monster: Spell 97, SpellChance X, SpellSkill field 5","works"),
5:("monster","Monsters reflect X% of physical damage","Damage.lua:1154-1158",
   "player melee damage reflected as affixCut(dealt, 5) = dealt x (1 - X/100), then ^0.85 in the player pipe","bug: reflects (100 - X)% instead of X%"),
6:("monster","Monsters reflect X% of magic damage","Damage.lua:1159-1163","same as 5 for non-physical damage","bug: reflects (100 - X)% instead of X%"),
7:("monster","Monsters regenerate X% HP per second","zzMaw-Monsters.lua:3604-3609, zzMaw-Timers.lua:91",
   "mappingRegen heals the global variable `mon` (whatever was last assigned) by X% of FullHitPoints","bug: no per-monster regeneration"),
8:("monster","X% chance to ignore status resistance","Global/zzMaw_Mapping.lua:1-6","DoBadThingToPlayer: a resisted condition is applied anyway with X% chance","works"),
9:("monster","X% chance to summon a monster on death","zzAlchemy.lua:1146-1148","on kill: one monster of the same family, tier {A 55, B 30, C 15}%, radius 128","works"),
10:("monster","Monsters deal X% of player HP as damage","Damage.lua:1952-1955","monster hits add FullHP x X/100","works"),
11:("monster","Monsters have +X% movement speed","zzMaw-Monsters.lua:3469-3490","every monster's per-frame displacement (< 100 units) is extended by X/100","works"),
12:("monster","Monster resistances +X","zzMaw-Monsters.lua:600-605","every resistance: min(base + X, 200 + X, 999)","works"),
13:("monster","X% extra chance to resist control effects","Damage.lua:346","only the Stun spell (34): hit chance x (1 - X/100)","partial: other crowd control unaffected"),
14:("monster","X% chance to deal energy damage","Damage.lua:1735-1737","`math.random() < X` without /100","bug: every monster hit becomes Energy (12)"),
15:("monster","Monsters have +X% HP","zzMaw-Monsters.lua:659-663",
   "multiplies HPtable after the templates were written; live HP comes from getMonsterHealth","bug: monster HP unchanged; only the leech reference (Damage.lua:1221) grows, i.e. leech x 1/(1 + X/100)"),
16:("boss","Boss density +X%","zzMaw-Monsters.lua:2901-2903","boss count = ceil(count x (1 + X/100))","works"),
17:("monster","X% chance to be a higher tier","zzMaw-Monsters.lua:2904-2911","each non-C monster: SetId(Id + 1) with X% chance, before boss picks","works"),
18:("boss","Bosses +X% HP and damage","zzMaw-Monsters.lua:3009-3011, 3070-3072","boss hpMult and dmgMult x (1 + X/100) (spell skill too)","works"),
19:("boss","X% chance for a monster to become a boss","zzMaw-Monsters.lua:2913-2920","each non-C, non-peaceful, unnamed monster: generateBoss with X% chance","works"),
20:("player","Player critical chance -X","zzMaw-Stats.lua:125-127","crit chance - X/100 (absolute; NOT in the hyperbolic reduction list)","works"),
21:("player","Player critical damage -X%","zzMaw-Stats.lua:128-130","crit multiplier = (m - 1) x (1 - X/100) + 1","works"),
22:("player","Player HP/SP regeneration -X%","zzMAW-Skills.lua:1388-1390","regen tick time multiplier x (1 - X/100)","works"),
23:("player","Player physical damage -X%","Damage.lua:1143-1145","DamageToMonster: physical result x (1 - X/100)","works"),
24:("player","Player magic damage -X%","Damage.lua:1146-1148","DamageToMonster: non-physical result x (1 - X/100)","works"),
25:("player","Player movement speed -X%","Global/zzMaw_Mapping.lua:7-18","each tick with the enemy detector yellow/red the party is pushed back by X% of its movement","works"),
26:("player","Player attack speed -X%","Global/zzMaw_Mapping.lua:19-23","GetAttackDelay: delay / (1 - X/100)","works"),
27:("player","Player spell recovery +X%","zzMaw-Stats.lua:240-242","spell delay / (1 - X/100)","works"),
28:("player","Player armor -X%","zzMaw-Stats.lua:1057-1059","AC x (1 - X/100)","works"),
29:("player","Player resistances -X%","zzMaw-Stats.lua:1130-1132","total resistance x (1 - X/100)","works"),
30:("player","X% chance for players to miss","Damage.lua:1149-1153","DamageToMonster result 0 with X% chance","works"),
31:("player","Healing -X%","zzMaw-Spells.lua:96-98","heal spell multiplier x (1 - X/100)","works"),
32:("player","Leech -X%","Damage.lua:1236-1237","leech heal x (1 - X/100)","works"),
33:("player","Buff effects -X%","Global/zzMaw_Mapping.lua:25-34",
   "AfterLoadMap scales buffPower Base/Scaling by (1 - X/100) in place","bug: compounds on every reload inside the map; leaving restores the Mapping table (see BALANCE_MODEL.md)"),
}
def q(s): return '"'+s.replace('"','\\"')+'"'
L=[]
A=L.append
A('# draft extracted from MAW ef23ee17')
A('# Dimension-map affixes ("mapping", item 290). Paths relative to Maw-Mod-MMMerge/Scripts/.')
A('# value = base + Power x scale (calculateAffixPower, General/zzMaw-Maps.lua:1084-1112).')
A('#   kind reduction: shown and applied as 100 x (1 - 1/(1 + value/100)) with 2 decimals (Formulas.reductionPercent)')
A('#   kind proc:      capped at 100')
A('# Power is the map item\'s MaxCharges. Effects read getMapAffixPower(n) at the listed sites; "X" is the final value.')
A('# examples: X at Power 10 / 30 / 60.')
A('format: 1')
A('source: {repo: Maw-Mod-MMMerge, commit: ef23ee17}')
A('')
A('map_item:')
A('  item_id: 290                   # renamed "Dimension Map" (zzMaw-Maps.lua:1035)')
A('  fields: {BonusStrength: target mapstats id, BonusExpireTime: affix 1, Bonus2: affix 2, "Charges % 1000": affix 3,')
A('           "floor(Charges / 1000)": affix 4, Bonus: affix count (0 means 4), MaxCharges: Power}')
A('  unlock: "vars.dimensionalMapsQuest.Done (oracle topic)"')
A('  target_pool: "completed dungeons among mapDungeons (157 mapstats ids, zzMaw-Maps.lua:791)"')
A('  drop:                          # MonsterKilled, zzMaw-Maps.lua:826-939')
A('    base_chance: 0.001')
A('    chance: "pity(0.001 x completed/157, failures) x mon.Level/100 / (mapsDropped on this map + 1) x mult"')
A('    mult: {boss: 10, broodling: "10 / (5 - tier)"}')
A('    level_required: {default: 100, madness: 70}      # getMonsterLevel(mon)')
A('    madness_map_level_required: 950  # map mean + 20 + Power x 10 must reach MADNESS_MAP_DROP_LEVEL, else no drop')
A('    seeded_roll: "mapvars.MonsterSeed[index] + 1337 when vars.seed is set"')
A('    failures: "vars.mapDropFailures += mult on a failed eligible roll; 0 on a drop"')
A('    affix_count: {4: 0.10, 3: 0.20, 2: 0.70, 1: 0.0}   # bug: `elseif bonus<=0.6` tests bonus, not roll')
A('    affixes: "distinct, uniform 1..33"')
A('    power: "round(monsterLevel/10 - U{0,1,2,3}); Road to Insanity (not Madness): at least 30"')
A('  on_completion:                 # checkMapCompletition, zzMaw-Monsters.lua:2654-2701')
A('    map_already_completed_branch: >-')
A('      (every dimension map, since targets are completed dungeons; not in Madness) no exp/gold;')
A('      grants a new map: target random completed dungeon, affix 2 always, 3 at 60%, 4 at 50%, 1 at 40%,')
A('      Bonus 0 (read as 4 slots, empty ones are 0), Power = min(round(Power + 1), 255)')
A('    madness_branch: "normal completion reward with madness formula, plus item by affix count {1: 1070, 2: 1061,')
A('      3: 1062, 4: 1065} instead of the crafting cube and gems"')
A('  entering:                      # UseMouseItem, zzMaw-Maps.lua:959-1027')
A('    refill: "target map RefillDays = 0 for this visit (restored on AfterLoadMap)"')
A('    monsters: "3 random families from possibleMonstersIn (.blv) / possibleMonstersOut (.odm) (seeded from the item)"')
A('    density: "Mon{1..3}Hi x (1 + (Power x nAff + 20 x nAff) / 300), rounded"')
A('    monster_level: "base level + map extraBolster + Power x 10 + 20 (no party bolster, no horizontal x2.5)"')
A('    shown_level: "Power x 10 + 20 + round(mean of the map band)"   # getDimensionMapLevel, zzMaw-Maps.lua:804-807')
A('    loot: "rarity mult x (1 + (Power x nAff + 20 x nAff)/400); enchant tier bonus floor(max((Power - 28)/2, 0))"')
A('    crafting_drop: "x (1 + (Power x nAff + 20 x nAff)/800 x 1.5)"   # zzAlchemy.lua:1167-1175')
A('')
A('affixes:')
for n in range(1,34):
    b,s=T[n]
    kind='reduction' if n in RED else ('proc' if n in PROC else 'flat')
    tgt,text,site,eff,status=E[n]
    ex=' / '.join(str(mround(round(power(n,p),2))) for p in (10,30,60))
    A(f'  {n}:')
    A(f'    text: {q(text)}')
    A(f'    target: {tgt}')
    A(f'    base: {mround(b)}')
    A(f'    scale: {mround(s)}')
    A(f'    kind: {kind}')
    A(f'    examples: {q(ex)}')
    A(f'    site: {q(site)}')
    A(f'    effect: {q(eff)}')
    A(f'    status: {q(status)}')
A('# Note: the proc list in calculateAffixPower also names 34, which does not exist (totalMapAffixes = 33).')
open('/home/pjasicek/github/OpenYAMM/devdocs/maw/data/dimension_affixes.yml','w').write('\n'.join(L)+'\n')
