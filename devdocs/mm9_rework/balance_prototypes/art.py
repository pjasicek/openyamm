import csv,re,collections,statistics as st
S='/home/pjasicek/github/OpenYAMM/output/mm9_balance/'
E='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
M='/home/pjasicek/github/OpenYAMM/assets_dev/worlds/mm9/data_tables/'
# weights: crude "stat-point equivalents"
W=dict(stat=1, hpsp=0.5, ac=1, res=0.3, skill=3, halfskill=12, rec_tick=1.25, regen_hp=25, regen_sp=25, dmg=2, atk=0.5)
FLAG={'halfMissile':25,'immunity':8,'vampiric':25,'waterwalk':5,'feather':5,'fullimmune':40,
 'BreakAfterFirstAttack':-30,'PoisonWeaponDamage':5,'PoisonOnHit40Grandmaster':10,'PerfectAccuracy':20,'TripleProjectile':40,
 'DiseaseWeaponDamage':5,'HalveTargetArmor':15,'BreakChance2SelfDamage':-10,'BypassArmorChance20':10,'Vampiric':25,
 'WeeklyInsanityChance10':-10,'WeeklyHealthLossChance10':-10,'EnrageOnHit5Grandmaster':5,'StunOnHit5':5,'SelfKnockoutOnFailedStun70':-15,
 'KillOnHit10':30,'ReelOnHit':5,'DisableDivineIntervention':-5,'FearOnHit10':5,'MeleeArmor40':30,'RangedArmorMinus10':-8,'MagicArmor20':10,
 'Amelioration':15,'Everlasting':5,'MissileArmor30':20,'WeeklyGold1000':10,'PartyEnduranceMinus40':-40,'PhysicalDamageReduction3Percent':10,
 'CarriedPartyEffect':0,'EncounterChancePlus15Percent':-5,'AllConditionImmunity':40,'ExperienceGainMinus15Percent':-15}
def rd(p,skip=0):
    return list(csv.DictReader(open(p,encoding='latin-1').read().splitlines()[skip:],delimiter='\t'))
def dice(s):
    m=re.fullmatch(r'(\d+)d(\d+)',s.strip()); return int(m.group(1))*(int(m.group(2))+1)/2 if m else 0
def num(s):
    try: return float(s)
    except: return 0
def slot(r):
    es=r['Equip Stat']
    return 'weapon' if es in('Weapon','Weapon2','Weapon1or2','Missile') else ('body' if es in ('Armor','Shield','Helm','Boots','Gauntlets','Cloak','Belt') else 'jewel')
def base(r):
    if slot(r)=='weapon': return dice(r['Mod1'])+num(r['Mod2']), num(r['Mod2'])
    return num(r['Mod1'])+num(r['Mod2']),0
# --- engine rare effects
txt=open(S+'rare.txt').read().split('void applyRareItemBonus')[1]
blocks=collections.defaultdict(list); cur=[]
for line in txt.splitlines():
    m=re.match(r'\s*case (\d+):',line)
    if m:
        if cur and cur[-1][1]: cur=[]
        cur.append([m.group(1),[]]); 
        for c in cur: blocks.setdefault(c[0],[])
        continue
    for c in cur: blocks[c[0]].append(line); 
    if cur: cur[-1][1].append(line)
elem={}
for m in re.finditer(r'case (\d+): result\.\w+ = (\d+)',open('/home/pjasicek/github/OpenYAMM/game/items/ItemEnchantRuntime.cpp').read()): elem[m.group(1)]=int(m.group(2))
def score_engine(iid):
    s=0; parts=[]
    for l in blocks.get(iid,[]):
        if m:=re.search(r'magicalBonuses\.(might|intellect|personality|endurance|speed|accuracy|luck) ([+-])= (-?\d+)',l):
            v=int(m.group(3))*(1 if m.group(2)=='+' else -1); s+=v*W['stat']; parts.append(f'{m.group(1)[:3]}{v:+}')
        elif m:=re.search(r'addAllPrimaryStats\(member, (-?\d+)\)',l): v=int(m.group(1)); s+=7*v; parts.append(f'all7{v:+}')
        elif m:=re.search(r'(maxHealth|maxSpellPoints) ([+-])= (\d+)',l): v=int(m.group(3))*(1 if m.group(2)=='+' else -1); s+=v*W['hpsp']; parts.append(f'{m.group(1)[:5]}{v:+}')
        elif m:=re.search(r'armorClass ([+-])= (\d+)',l): v=int(m.group(2))*(1 if m.group(1)=='+' else -1); s+=v; parts.append(f'AC{v:+}')
        elif m:=re.search(r'resistances\.\w+ ([+-])= (\d+)',l): v=min(int(m.group(2)),100)*(1 if m.group(1)=='+' else -1); s+=v*W['res']; parts.append(f'res{v:+}')
        elif m:=re.search(r'addAllMagicResistances\(member, (-?\d+)\)',l): v=int(m.group(1)); s+=v*7*W['res']; parts.append(f'allres{v:+}')
        elif m:=re.search(r'addAllElementalResistances\(member, (-?\d+)\)',l): v=int(m.group(1)); s+=v*4*W['res']; parts.append(f'elemres{v:+}')
        elif m:=re.search(r'addSkillBonus\(member, "(\w+)", (\d+)\)',l): v=int(m.group(2)); s+=v*W['skill']; parts.append(f'{m.group(1)}+{v}')
        elif m:=re.search(r'addHalfLearnedSkillBonus\(member, "(\w+)"\)',l): s+=W['halfskill']; parts.append(f'{m.group(1)}+50%')
        elif m:=re.search(r'attackRecoveryReductionTicks \+= (\d+)',l): v=int(m.group(1)); s+=v*W['rec_tick']; parts.append(f'recov-{v}')
        elif m:=re.search(r'healthRegenPerSecond ([+-])= ([\d.]+)',l): v=float(m.group(2))*(1 if m.group(1)=='+' else -1); s+=v*W['regen_hp']; parts.append(f'hpregen{v:+}/s')
        elif m:=re.search(r'spellRegenPerSecond \+= ([\d.]+)',l): v=float(m.group(1)); s+=v*W['regen_sp']; parts.append(f'spregen+{v}/s')
        elif m:=re.search(r'weaponEnchantmentDamageBonus \+= (\d+)',l): v=int(m.group(1)); s+=v*W['dmg']; parts.append(f'dmg+{v}')
        elif 'halfMissileDamage' in l: s+=FLAG['halfMissile']; parts.append('halfMissile')
        elif 'addConditionImmunity' in l or 'addPoisonImmunity' in l or 'addDiseaseImmunity' in l: s+=FLAG['immunity']; parts.append('immune')
        elif 'addMmergeFullConditionImmunity' in l: s+=FLAG['fullimmune']; parts.append('allImmune')
        elif 'vampiricHealFraction' in l: s+=FLAG['vampiric']; parts.append('vampiric')
        elif 'waterWalking' in l: s+=5; parts.append('waterwalk')
        elif 'featherFalling' in l: s+=5; parts.append('featherfall')
        elif 'ReelOnHit' in l: s+=5; parts.append('reel')
        elif 'meleeAttack' in l: s+=10; parts.append('bless')
        elif 'resistances.fire += 65000' in l: pass
    if iid in elem: s+=elem[iid]*W['dmg']; parts.append(f'elem+{elem[iid]}')
    return s,parts
def score_mm9(e):
    s=0; parts=[]
    for k in ('might','intellect','personality','endurance','speed','accuracy','luck'):
        if e.get(k): v=num(e[k]); s+=v; parts.append(f'{k[:3]}{v:+.0f}')
    for k in ('max_health','max_sp'):
        if e.get(k): v=num(e[k]); s+=v*W['hpsp']; parts.append(f'{k}{v:+.0f}')
    if e.get('armor_class'): v=num(e['armor_class']); s+=v; parts.append(f'AC{v:+.0f}')
    if e.get('all_resistances'): v=num(e['all_resistances']); s+=v*7*W['res']; parts.append(f'allres{v:+.0f}')
    for k in ('melee_attack','ranged_attack'):
        if e.get(k): v=num(e[k]); s+=v*W['atk']; parts.append(f'{k}{v:+.0f}')
    for k in ('melee_damage','ranged_damage','weapon_damage'):
        if e.get(k): v=num(e[k]); s+=v*W['dmg']; parts.append(f'{k}{v:+.0f}')
    if e.get('skill_bonuses'):
        for sb in e['skill_bonuses'].split('|'):
            n,v=sb.split(':'); s+=int(v)*W['skill']; parts.append(f'{n}{int(v):+}')
    if e.get('recovery_reduction_ticks'): v=num(e['recovery_reduction_ticks']); s+=v*W['rec_tick']; parts.append(f'recov{-v:+.0f}')
    if e.get('health_regen_per_second'): v=num(e['health_regen_per_second']); s+=v*W['regen_hp']; parts.append(f'hpregen+{v}/s')
    if e.get('spell_regen_per_second'): v=num(e['spell_regen_per_second']); s+=v*W['regen_sp']; parts.append(f'spregen+{v}/s')
    for f in filter(None,(e.get('effect_flags') or '').split('|')): s+=FLAG.get(f,0); parts.append(f)
    return s,parts
eng=[r for r in rd(E+'items.txt',1) if r.get('Item #','').strip().isdigit() and r['material'] in('Artifact','Relic')]
mm9=[r for r in rd(M+'items.txt') if r['material'] in('Artifact','Relic','Special')]
eff={e['item_id']:e for e in rd(M+'item_effects.txt')}
out=[]
for r in eng:
    s,p=score_engine(r['Item #']); b,a=base(r); out.append(('ENG',r['material'],slot(r),r['Item #'],r['Name'],r['Equip Stat'],r['Mod1'],r['Mod2'],b,s,' '.join(p)))
for r in mm9:
    s,p=score_mm9(eff.get(r['Item #'],{})); b,a=base(r); out.append(('MM9',r['material'],slot(r),r['Item #'],r['Name'],r['Equip Stat'],r['Mod1'],r['Mod2'],b,s,' '.join(p)))
import json; json.dump(out,open(S+'art.json','w'))
for o in out: print('\t'.join(str(x) for x in o))
print()
def summ(filt):
    xs=[o for o in out if filt(o)]
    if not xs: return '-'
    return f'n={len(xs):3d} base med {st.median(o[8] for o in xs):5.1f}  effect med {st.median(o[9] for o in xs):5.1f} mean {st.mean(o[9] for o in xs):5.1f} max {max(o[9] for o in xs):5.0f}'
for src in ('ENG','MM9'):
    for mat in ('Artifact','Relic','Special'):
        for sl in ('weapon','body','jewel'):
            print(src,mat,sl,summ(lambda o: o[0]==src and o[1]==mat and o[2]==sl))
