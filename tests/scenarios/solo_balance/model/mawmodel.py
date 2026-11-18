"""Python port of game/rules/maw/MawBalanceModel.cpp, parameterised for a solo character.

Every function mirrors the C++ one; the solo extensions are keyword arguments:
  skill_override  - the character's real skill level instead of the 5-skill estimate
  gear_level      - the level the worn gear came from (loot tier, item power) instead of the character level
  geared          - the geared fraction instead of gearedFraction(level)
  buffs           - a set of buff names that are up ('haste','heroism','bless','fate','stoneskin','shield',
                    'resist','dotg'); None = all (the expected character)
  buff_skill      - the caster skill behind the buffs (default: the estimated skill)
  vs_level        - the attacker's level for armour and resistance divisors (default: same level)
"""
import math
from functools import lru_cache

def clamp01(v): return min(max(v, 0.0), 1.0)
def maw_round(v): return math.floor(v + 0.5)

class MT:
    def __init__(self, values, zero_based):
        self.v = [None]*5
        start = 0 if zero_based else 1
        for i, x in enumerate(values): self.v[start+i] = x
    def at(self, i, fb):
        return self.v[i] if 0 <= i < 5 and self.v[i] is not None else fb

zb = lambda *a: MT(a, True)
ob = lambda *a: MT(a, False)
ArmsmasterDamage = zb(0, 0, 1, 1, 1.5)
ArmsmasterSpeed = zb(0, 0, 0, 1, 1)
ArmsmasterAttack = zb(0, 1, 1, 1, 1)
SwordAttack = zb(0, 1, 2, 3, 4)
SwordRecovery = zb(0, 0, 1, 1, 2)
ChainItemArmor = zb(0, 3, 4, 5, 6)
ChainItemResistance = zb(0, 1, 2, 3, 4)
BodybuildingHealth = zb(0, 0.5, 1, 1.5, 2)
BodybuildingFlatPerRank = ob(1, 2, 3)
FireAuraDamage = zb(0, 0.1, 0.15, 0.2, 0.25)
CoverGate = ob(0, 1, 1, 1)
EnchantsWorn = 3*13.75
BUFF = {'resist': (20, 2), 'haste': (10, 2), 'shield': (15, 3), 'stoneskin': (20, 2), 'bless': (20, 2),
        'fate': (5, 1), 'heroism': (15, 3), 'dotg': (20, 2), 'hop': (10, 2)}
ALL_BUFFS = frozenset(['resist', 'haste', 'shield', 'stoneskin', 'bless', 'fate', 'heroism', 'dotg'])
DropsDensity = [1, 0.40, 0.40, 0.40, 0.43, 0.43, 0.47, 0.59, 0.66, 0.70]
HitsChar = [0, 14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4]
HitsMon = [0, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
RarityDifficultyMult = [0, 1, 1, 1, 1.1, 1.2, 1.4, 1.6, 1.8, 2]
RarityBandMult = [(1,1,1),(1,1,1),(1,1,1),(1,1,1),(1.5,1.4,1.4),(2,1.8,1.6),(2.5,2.2,1.8),(3,2.6,2),(4,3,2.2),(5.5,3.4,2.4)]
Common, Uncommon, Rare, Epic, Ancient, Primordial, Legendary, Celestial = range(1, 9)

def legendary_ramp(L): return clamp01((L-100)/400)
def power_for(IL): return min(math.floor(max(IL, 0)/5), 100)

def weapon_damage(IL, two, flat):
    p = min(power_for(IL), 255); fp = math.floor(p/2); pf = 2*fp; pd = 4*(p-fp)
    dice, fl, ld = 16+pd, flat+pf, pf+pd/2
    if not two: dice, fl, ld = dice/2, fl/2, ld/2
    return dice, fl, ld

# MAW f1ffd3b1: the base item's ladder rung (1 at level 0, the sixth from level 100) sets the weapon's flat damage and the
# armour everyone wears; the Primordial item of the level adds its power by the geared share.
def base_tier(L): return 1 + 5*clamp01(L/100)
def weapon_flat(L): return 16*(base_tier(L)-1)/5
def armor_tier_ac(L): return 116*(0.21 + 0.79*(base_tier(L)-1)/5)

def enchant_chance(r, t):
    return {Epic: min(5+0.75*t, 20), Rare: min(20+2*t, 60), Uncommon: min(60+t, 80)}.get(r, 100)

def rarity_fraction(r):
    mean = {Celestial: 25/20, Primordial: 25/20, Ancient: 22.5/20, Legendary: 18/20}.get(r, 14/20)
    en = 0 if r == Common else 1 if r == Uncommon else 2 if r == Rare else 3
    return en/3*mean/(25/20)

def rarity_distribution(t, d):
    widths = [0]*9; total = 0; prev = 0
    for r in range(Epic, Common-1, -1):
        th = enchant_chance(r, t)
        bm = RarityBandMult[d][0] if r == Epic else RarityBandMult[d][1] if r == Rare else RarityBandMult[d][2] if r == Uncommon else 1
        widths[r] = max(th-prev, 0)*bm; total += widths[r]; prev = th
    dist = [0]*9
    for r in range(Common, Epic+1): dist[r] = widths[r]/total if total > 0 else (1 if r == Common else 0)
    epic = dist[Epic]; mult = RarityDifficultyMult[d]*enchant_chance(Uncommon, t)/80; left = 1
    for r, up in ((Celestial, .002), (Legendary, .03), (Primordial, .04), (Ancient, .12)):
        ch = min(up*mult, 1); dist[r] = epic*left*ch; left -= left*ch
    dist[Epic] = epic*left
    return dist

def drops_seen(L, density): return (L/(3.6+L/140)+1)*density

class Model:
    def __init__(self, difficulty=3, party=5, insanity=False, madness=False, doom=False, true_nightmare=False, austerity=False):
        self.d = difficulty; self.party = party; self.insanity = insanity; self.madness = madness
        self.doom = doom; self.tn = true_nightmare

    @staticmethod
    def preset(name, party=5):
        return {'maw': Model(3, party), 'hard': Model(4, party), 'hell': Model(5, party),
                'nightmare': Model(6, party, true_nightmare=True),
                'doom': Model(7, party, doom=True),
                'insanity': Model(8, party, doom=True, insanity=True),
                'madness': Model(9, party, doom=True, insanity=True, madness=True)}[name]

    def th(self, i):
        t = (0, 10, 24, 40) if self.madness else (0, 8, 16, 25) if self.insanity else (0, 4, 7, 10)
        return t[min(max(i, 1), 4)-1]
    def mastery_for(self, s):
        for m in (4, 3, 2, 1):
            if s >= self.th(m): return m
        return 1
    def ggmv(self, tbl, s, m):
        m = max(m, 0)
        if m < 1: return tbl.at(0, 0)
        i = min(m, 4); a = self.th(i); b = self.th(i+1) if i < 4 else a*1.4
        prev = tbl.at(m-1, 0); cur = tbl.at(m, prev)
        if b <= a: return cur
        return prev + (cur-prev)*clamp01((s-a)/(b-a))
    def grow(self, tbl, s, m): return tbl.at(1, 0) if m <= 1 else self.ggmv(tbl, s, m)
    def buff_ramp(self, s): return clamp01((s-self.th(2))/(self.th(3)-self.th(2)))
    def buff_flat(self, name, s, L, div=4, buffs=None):
        if isinstance(buffs, dict):
            if name not in buffs: return 0
            bs, bl = buffs[name]; b, sc = BUFF[name]
            return (b + bl/div)*(1 + sc/100*min(bs, 75 if name in ('dotg', 'hop') else 50))
        if buffs is not None and name not in buffs: return 0
        b, sc = BUFF[name]; m = self.mastery_for(s)
        cs = min(s, 75 if name in ('dotg', 'hop') else 50)
        base = self.grow(zb(0, b, b, b, b), s, m); scal = self.grow(zb(0, sc, sc, sc, sc), s, m)
        return (base + L/div)*(1+scal/100*cs)*self.buff_ramp(s)
    def buff_mult(self, name, s, buffs=None):
        if isinstance(buffs, dict):
            if name not in buffs: return 0
            bs, bl = buffs[name]; b, sc = BUFF[name]
            return b/100*(1 + 0.02*min(bs, 75 if name in ('dotg', 'hop') else 50))
        if buffs is not None and name not in buffs: return 0
        b, sc = BUFF[name]; m = self.mastery_for(s)
        cs = min(s, 75 if name in ('dotg', 'hop') else 50)
        base = self.grow(zb(0, b, b, b, b), s, m)
        return base/100*self.buff_ramp(s)*(1+0.02*cs)
    @staticmethod
    def stat_effect(v):
        st = int(v)
        if st >= 25: return st//5
        for t, e in ((21,4),(19,3),(17,2),(15,1),(13,0),(11,-1),(9,-2),(7,-3),(5,-4),(3,-5),(0,-6)):
            if st >= t: return e
        return -6
    @staticmethod
    def skill_points(L):
        if L < 2: return 0
        q = math.floor(L/10); r = L-10*q
        return 5*(L-1)+5*q*(q-1)+q*(r+1)
    @staticmethod
    def skill_from_points(p): return (math.sqrt(1+8*(p+1))-1)/2
    def skill(self, L): return self.skill_from_points(self.skill_points(L)/5)
    def loot_tier(self, L): return L/15+min(1+L/15, 6)
    def enchant_curve(self, t): return 1+t*2 if t <= 12 else 25+min((t-12)*3, 75)
    def max_enchant(self, L):
        ex = 1.2 if self.insanity else 1.1 if self.doom else 1.05 if self.tn else 1.0
        return self.enchant_curve(self.loot_tier(L))*ex*1.1
    def eef(self, t, drops, d):
        dist = rarity_distribution(t, d); n = max(drops, 1); e = 0; below = 0
        for r in (Common, Uncommon, Rare, Epic, Legendary, Ancient, Primordial, Celestial):
            cum = below+dist[r]; e += rarity_fraction(r)*(cum**n-below**n); below = cum
        return e
    def geared(self, L, drop_mult=1.0):
        t = self.loot_tier(L); anchor = (L+20)/(L+100)
        return anchor*self.eef(t, drops_seen(L, DropsDensity[self.d])*drop_mult, self.d)/self.eef(t, drops_seen(L, 1), 9)

    # --- character -------------------------------------------------------------------------------------------
    def char(self, L, skill=None, gear_level=None, geared=None, buffs=None, buff_skill=None, vs_level=None,
             two_handed=True, bodybuilding=True, armsmaster=True, armor_skill=None, arms_skill=None,
             bb_skill=None, stat_potions=True, arms_explicit=False, item_level=None):
        """Returns a dict with stat, health, ac, res, power, vitality... for a character of level L."""
        s = self.skill(L) if skill is None else skill
        m = self.mastery_for(s)
        GL = L if gear_level is None else gear_level
        IL = GL if item_level is None else item_level   # weapon and armour power (the Crafting Cube raises it)
        g = self.geared(GL) if geared is None else geared
        bs = s if buff_skill is None else buff_skill
        VL = L if vs_level is None else vs_level
        a_s = s if armor_skill is None else armor_skill
        bb_s = (s if bb_skill is None else bb_skill) if bodybuilding else 0
        ar_s = (s if arms_skill is None else arms_skill) if armsmaster else 0
        # stat
        enchant_power = EnchantsWorn*self.max_enchant(GL)
        if isinstance(buffs, dict):
            dotg = 1 + (min(10 + buffs['dotg'][0]/7, 20)/100 if 'dotg' in buffs else 0)
        else:
            dotg = 1 + (min(10+bs/7, 20)/100*self.buff_ramp(bs) if (buffs is None or 'dotg' in buffs) else 0)
        stat = (17 + (min(L, 500)*0.2 if stat_potions else 0) + enchant_power*0.2*g)*dotg
        # health
        per = min(6*L/(330 if self.madness else 210), 6)+3
        bbm = min(self.mastery_for(bb_s), 3) if bb_s > 0 else 0
        flat_bonus = EnchantsWorn*self.max_enchant(GL)*0.2*g*(1+min(self.max_enchant(GL)/50, 5))
        bb_flat = bb_s*self.grow(BodybuildingFlatPerRank, bb_s, bbm) if bb_s > 0 else 0
        bb_pct = self.ggmv(BodybuildingHealth, bb_s, bbm) if bb_s > 0 else 0
        health = (25 + per*L + (stat/5 + bb_flat)*per + flat_bonus)*(1+bb_pct*bb_s/100)*(1+stat/1000)
        # defence
        pw = power_for(IL); ch = min(max(maw_round(pw*1.2), pw+4), 255)
        worn = armor_tier_ac(GL) + 116*ch/40*g
        am = self.mastery_for(a_s)
        ac = worn*(1+0.5*legendary_ramp(GL)+self.grow(ChainItemArmor, a_s, am)*a_s/100) + self.buff_flat('stoneskin', bs, L, 4, buffs)
        res = worn*self.grow(ChainItemResistance, a_s, am)*a_s/100 + self.buff_flat('resist', bs, L, 4, buffs) + self.stat_effect(stat)
        enres = self.max_enchant(GL)*100/200*g*(1+0.5*legendary_ramp(GL))
        hit = 1/(1+stat/(100+stat)*0.5)
        phys = max(1/(ac/(200+VL)+1), 0.1)
        magic = 1/(res/(100+2*VL)+1)*max(1-self.buff_mult('shield', bs, buffs), 0.7)*1/(enres/100+1)
        magic = max(magic, 0.1)
        ramp = legendary_ramp(GL)
        leg = (1-0.10*ramp)*(1-(1-0.97**5)*ramp)
        cover = 1.0  # a solo character has nobody to cover; the expected one counts Cover below
        taken = (phys*0.5+magic*0.5)*hit*leg
        vitality = health/taken*cover
        # power (melee)
        flat = weapon_flat(GL)
        fd, ff, _ = weapon_damage(ch*5, True, flat)
        bd, bf, _ = weapon_damage(0, True, flat)
        wd, wf = bd + (fd-bd)*g, bf + (ff-bf)*g
        melee = s + 10*ramp
        wsm = 1 + 2*melee/100
        arms = ar_s if arms_explicit else ar_s*1.5
        armsm = self.mastery_for(arms) if arms > 0 else 0
        arms_base = self.ggmv(ArmsmasterDamage, arms, armsm)*arms if arms > 0 else 0
        scal = wf + 0.5*wd + arms_base
        dmg = 1.5 + scal*wsm + max(melee - scal*(wsm-1), 0)
        dmg = (dmg + self.stat_effect(stat))*(1+self.buff_mult('heroism', bs, buffs))*(1+stat/1000)
        spd = ((stat-13)/4 if stat <= 21 else math.floor(stat/10))/100
        wspd = self.ggmv(SwordRecovery, melee, self.mastery_for(melee))*melee/100
        aspd = self.ggmv(ArmsmasterSpeed, arms, armsm)*arms/100 if arms > 0 else 0
        dmg *= (1+spd+wspd+aspd)*(1+self.buff_mult('haste', bs, buffs))
        cc = stat/min(500+L*5, 3000) + 0.05 + 0.1*ramp + self.buff_mult('fate', bs, buffs)
        cd = stat/min(250+L*2.5, 3000 if self.madness else 2000) + 0.5
        critm = 1+min(cc, 1)*cd
        dmg *= critm
        enl = (1+0.5*ramp)*(1+(critm-1)*ramp)
        enc_base = self.weapon_level_damage(ch*5, True, flat)*g*enl
        dmg += enc_base*0.5*min(GL/100, 1)
        dmg += enc_base*self.ggmv(FireAuraDamage, s, m)
        dmg *= min(1+0.25*ramp, 2)*(1+0.15*ramp)
        dmg *= max(cc, 1)
        if isinstance(buffs, dict):
            bless_hit = (0.05 + 0.001*min(buffs['bless'][0], 50)) if 'bless' in buffs else 0
        else:
            bless_hit = (0.05+0.05*min(bs, 50)/50) if (buffs is None or 'bless' in buffs) else 0
        power = dmg*min(0.75+bless_hit, 1)
        return dict(skill=s, mastery=m, stat=stat, geared=g, health=health, ac=ac, res=res, phys=phys, magic=magic,
                    hit=hit, taken=taken, vitality=vitality, power=power, speed=1+spd+wspd+aspd, crit=critm)

    def weapon_level_damage(self, IL, two, flat):
        ld = weapon_damage(IL, two, flat)[2]
        arms = self.skill(IL)*1.5
        a = self.ggmv(ArmsmasterDamage, arms, self.mastery_for(arms))*arms
        sf = self.stat_effect(self.expected(IL)['stat'])
        if not two: a /= 2; sf /= 2
        return ((ld+a)*(1+0.02*self.skill(IL))+sf)*(1+self.expected(IL)['stat']/1000)

    @lru_cache(maxsize=None)
    def _expected_stat(self, L):
        s = self.skill(L); g = self.geared(L)
        dotg = 1 + min(10+s/7, 20)/100*self.buff_ramp(s)
        return (17 + min(L, 500)*0.2 + EnchantsWorn*self.max_enchant(L)*0.2*g)*dotg
    def expected(self, L):
        return {'stat': self._expected_stat(L)}

    # --- the expected character exactly as the C++ model (with Cover) -----------------------------------------
    def expected_char(self, L):
        c = self.char(L)
        s = c['skill']; m = c['mastery']
        gate = self.grow(CoverGate, s, m)
        if gate > 0:
            chance = min(0.10+0.01*s, 0.40)*gate
            ratio = 2 if self.party <= 1 else 2
            cover = 1/((1-chance)+chance/ratio)
        else:
            cover = 1
        c['vitality'] *= cover; c['cover'] = cover
        return c
    def monster_hp(self, L): return self.expected_char(L)['power']*HitsMon[self.d]
    def monster_dmg(self, L): return self.expected_char(L)['vitality']/HitsChar[self.d]

# MAW experience curve (game/rules/maw/MawExperienceCurve.cpp:14-17)
_EXP = [0.0]*2002
for _l in range(2, 2002):
    _EXP[_l] = _EXP[_l-1] + 1000*(_l-1)*max(1+((_l-1)-100)*0.005, 1)
def exp_for_level(L):
    w = int(math.floor(L)); return _EXP[w] + (L-w)*1000*w*max(1+(w-100)*0.005, 1)
def level_for_exp(x):
    lo, hi = 1.0, 2000.0
    for _ in range(60):
        mid = (lo+hi)/2
        if exp_for_level(mid) < x: lo = mid
        else: hi = mid
    return lo
