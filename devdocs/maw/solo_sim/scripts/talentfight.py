"""Real-group fights with the solo run's talents (tree v1 or v2), keystones, and range.

Built on realfight.py (monster actions, damage-taken grid, resistances, leech, regeneration, Mana Shield, the class
heals) with:
- Range: each group starts RANGE_START units away. Monsters whose attacks are mostly missiles or spells stop at
  RANGED_STAND and shoot; the rest walk in at their speed (monsters.json, units per second) and strike only when
  adjacent. A melee solo walks in too (PARTY_SPEED) and has to walk to a monster standing off; Charge does it at once.
  A bow, breath or spell solo shoots from where it stands; once a walker is adjacent it can only get away with
  Blink, Disengage or Binding Circle then Blink (no free back-pedalling: a conservative assumption).
- Talents (talents_v2.py ranks): Cleave, Whirlwind, Sweeping Blows, Frenzy, Charge, Shield Wall, Volley, Piercing
  Arrows, Pinning Shot, Disengage, Blink, Binding Circle, Spell Surge, Mana Font, Overload, Bloodthirst. The passives
  that the game code has (Weapon Training, Marksman, Attunement, Resolve) and Lone Discipline come in the harness
  rows (pool_out_<variant>_<difficulty>.jsonl).
- Keystones: Unbroken, the class Oath, Warlord, Deadeye, Archon. Everything after the floor together stays at or
  above CLAMP.
- Usage: per talent, uses per minute of fighting and share of the damage dealt.

Usage: python3 talentfight.py <difficulties> <stages> <configs> [out.json]
  configs: today, v1, v2, and v2-<talent or keystone>[+...] ablations. Prints Markdown tables.
"""
import json, os, sys, math, copy, collections, statistics, multiprocessing

CODE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CODE)
from simdir import S
import talents_v2 as T

_src = open(CODE + '/realfight.py').read().split("if __name__ == '__main__':")[0]
_argv = sys.argv
sys.argv = ['realfight.py', S, 'unused.jsonl']
RF = {'__name__': 'realfight'}
exec(compile(_src, CODE + '/realfight.py', 'exec'), RF)
sys.argv = _argv
MON, FIGHTS, meta = RF['MON'], RF['FIGHTS'], RF['meta']
monster_actions, divisor, TYPE_INDEX = RF['monster_actions'], RF['divisor'], RF['TYPE_INDEX']
SPELL_TYPE, MS_FRAC = RF['SPELL_TYPE'], RF['MS_FRAC']

DT = 0.1
AOE_SHARE = 0.75            # share of the other monsters an area spell or a ±60° sweep reaches
CONE_SHARE = 0.6            # Volley's ±30° cone
LINE_SHARE = 0.5            # a monster stands behind the target for Piercing Arrows
RANGE_START = 1200
RANGED_STAND = 600
PARTY_SPEED = 384
REACH = 0
CLAMP = T.CLAMP

# Talent numbers per rank (TALENT_TREE_V2.md; existing ones from talents.yml).
CD = {'cleave': [12, 10, 8], 'whirlwind': [20, 17, 14], 'frenzy': [30, 30, 30], 'charge': [25, 22, 19],
      'shield_wall': [60, 50, 40], 'volley': [12, 10, 8], 'multishot': [12, 10, 8], 'disengage': [15, 13, 11], 'pinning_shot': [10, 10, 10],
      'blink': [15, 13, 11], 'spell_surge': [45, 40, 35], 'binding_circle': [20, 18, 16]}
FRENZY_DUR = [6, 7, 8]
PIN_DUR = [4, 5, 6]
ROOT_DUR = [2, 2.5, 3]
SWEEP_TARGETS = [1, 2, 3]
ONSLAUGHT_SECONDS = 30    # Onslaught: +1 % attack speed per kill, at most 10/20/30 stacks, 30 s, kills refresh (user)
PULL_GAP = 5              # seconds from one pull of four to the next
SWEEP_CAP = 0.5           # Sweeping Blows' share: 30 % + 0.25 % per weapon-skill point, at most 50 %
CLEAVE_SHARE = 1.5        # Cleave, the burst: 150 % to everything in the arc and a 1 s stagger
PIERCE_TARGETS = [1, 2, 3]
LEECH_DIV = [5, 4, 3, 2.5]


def rank(cfg, tid):
    return cfg['ranks'].get(tid, 0)


def cd(cfg, tid):
    return CD[tid][rank(cfg, tid) - 1]


def monster_profile(actor, d, tp, tm, unbroken, full):
    """(melee dps, missile dps) the character takes from this monster with after-floor multipliers tp/tm."""
    m = MON[str(actor[0])]
    grid = d['grid'].get(str(max(1, actor[1])))
    if grid is None:
        grid = d['grid'][min(d['grid'], key=lambda k: abs(int(k) - actor[1]))]
    hit = grid[0]
    flat = d['flat_cut']
    melee = missile = 0.0
    for p, dmg, t, is_missile in monster_actions(actor):
        if dmg <= 0:
            continue
        after = dmg*grid[1 + TYPE_INDEX[t]]/100
        if flat > 0:
            after = max(after - flat, 0.25*after)
        after *= tp if t == 'Phys' else tm
        if unbroken and after > 0.3*full:
            after = 0.3*full + (after - 0.3*full)/2
        chance = (hit*hit if is_missile else hit)*(1 - d['dodge'])
        if is_missile:
            missile += p*after*chance
        else:
            melee += p*after*chance
    interval = max(m['rec'], 10)/60*1.05
    return melee/interval, missile/interval


def stands_off(actor):
    """A monster whose attack 1 is a missile (or that mostly casts) shoots from range."""
    m = MON[str(actor[0])]
    casts = (m['s1c'] or 0) + (m['s2c'] or 0)
    return bool(m['a1m']) or casts >= 50


def setup(group, cfg):
    d0, m0 = next(iter(group.values()))
    build = m0['build']
    r = T.role(build)
    ks = cfg['keystones']
    oath = T.OATH[build] if 'oath' in ks and build in T.OATH else (None, 1.0, 1.0, 1.0)
    warding = 1.0
    dmg_mult = oath[3]
    speed_mult = 1.0
    full = d0['hp']
    return dict(d0=d0, m0=m0, build=build, role=r, oath=oath, warding=warding, dmg_mult=dmg_mult,
                speed_mult=speed_mult, full=full)


def attacks_of(group, cfg, st):
    """Basic attacks with their numbers after Ferocity, Alacrity, Deadeye."""
    atks = RF['player_attacks'](group)
    deadeye = 1.3 if 'deadeye' in cfg['keystones'] else 1.0
    bt = rank(cfg, 'bloodthirst')
    for a in atks:
        a['dmg'] *= st['dmg_mult']*(deadeye if a['kind'] == 'bow' else 1.0)   # Archery never touches a dragon's breath
        a['rec'] /= st['speed_mult']
        a['leech'] = a['leech'] + 0.02*bt if a['kind'] != 'breath' else a['leech']
        a['ranged'] = a['kind'] != 'melee'
    return atks


class Fight:
    def __init__(self, group, cfg, use_range=True):
        self.group = group; self.cfg = cfg; self.use_range = use_range
        st = setup(group, cfg); self.st = st
        self.d0, self.m0, self.build, self.role = st['d0'], st['m0'], st['build'], st['role']
        d0, m0, build = self.d0, self.m0, self.build
        self.full = st['full']
        self.regen = d0['regen_full']*self.full/d0['hp']
        self.gm = d0['regen_full'] > 0 and d0['regen_half']/d0['regen_full'] > 1.2
        self.regen_pot = d0['regen_potion']   # the regeneration potion's aura (realfight: potions or not)
        self.sp_full = d0['sp']
        self.sp_regen = d0['sp_per_s'] + rank(cfg, 'mana_font')*(m0['actual_level']/10)/5
        self.ms = None
        sk = m0['skills'].get('ManaShield')
        if sk:
            s, mastery = sk
            ratio = 5 if s >= 50 else 1 + min(s, 50)**1.4/60
            if 'archon' in cfg['keystones'] and s >= 50:
                ratio = 10
            self.ms = (MS_FRAC[mastery], ratio)
        self.atks = attacks_of(group, cfg, st)
        self.melee_atk = next(a for a in self.atks if a['kind'] == 'melee')
        self.ranged_atks = [a for a in self.atks if a['ranged']]
        self.is_ranged = self.role in ('ranged', 'caster') or build == 'dragon'
        self.class_heal = d0['seraph_heal'] if build == 'seraph' else d0['shaman_heal'] if build == 'shaman' else 0
        self.unbroken = 'unbroken' in cfg['keystones']
        ws = max([v[0] for k, v in m0['skills'].items()
                  if k in ('Sword', 'Axe', 'Mace', 'Spear', 'Staff', 'Dagger', 'Unarmed', 'Armsmaster')] + [0])
        self.sweep_share = SWEEP_CAP if 'warlord' in cfg['keystones'] else min(SWEEP_CAP, 0.30 + 0.0025*ws)
        sr = rank(cfg, 'sweeping_blows')
        self.sweep_n = (SWEEP_TARGETS[sr - 1] + (1 if 'warlord' in cfg['keystones'] else 0)) if sr else 0
        self.pierce_share = 0.75 if 'deadeye' in cfg['keystones'] else 0.5
        pr = rank(cfg, 'piercing_arrows')
        self.pierce_n = PIERCE_TARGETS[pr - 1] if pr else 0
        self.leech_div = LEECH_DIV[rank(cfg, 'bloodthirst')]
        self.overload = 0.1*rank(cfg, 'overload')
        self.cache = {}

    def mults(self, shield_wall, adjacent_any):
        tp, tm = self.st['oath'][1], self.st['oath'][2]
        if self.build == 'archer' and adjacent_any:
            tp = tm = 1.0
        f = self.st['warding']*(0.5 if shield_wall else 1.0)
        return max(CLAMP, tp*f), max(CLAMP, tm*f)

    def profile(self, a, shield_wall, adjacent_any):
        key = (id(a), shield_wall, adjacent_any)
        if key not in self.cache:
            tp, tm = self.mults(shield_wall, adjacent_any)
            self.cache[key] = monster_profile(a, self.d0, tp, tm, self.unbroken, self.full)
        return self.cache[key]

    # --- the player's blows -------------------------------------------------------------------------------------
    def strike(self, a, targets, shares, source):
        """Deal a blow to targets at shares; leech per target (proportional) and once per swing (floor)."""
        dealt = 0.0
        for x, sh in zip(targets, shares):
            landed = a['dmg']*sh/divisor(x['a'], a)
            if self.surge and a['cost']:
                landed *= 1.5
            dealt += max(0.0, min(landed, x['hp'])); x['hp'] -= landed
        self.dmg_by[source] += dealt
        if a['leech'] > 0 and dealt > 0:
            heal = max(dealt/self.ref_hp*a['leech']*self.full,
                       self.full*a['leech']/self.leech_div*a['rec']*60/100/(2.5 if a.get('aoe') else 1))
            self.hp = min(self.full, self.hp + heal)
        if a['kind'] == 'melee' and self.class_heal:
            self.hp = min(self.full, self.hp + self.class_heal*self.d0['my_hit_melee']*sum(shares))
        return dealt

    def order(self, pool):
        return sorted(pool, key=lambda x: -(sum(self.profile(x['a'], False, True))/max(1, x['hp'])))

    def melee_action(self, t, adj, haste):
        cfg = self.cfg; a = self.melee_atk
        rec = a['rec']/haste
        if not adj:
            # Walk (or Charge) to the next monster.
            target = self.order(self.mons)[0]
            if rank(cfg, 'charge') and t >= self.ready['charge']:
                target['dist'] = 0; target['stun_until'] = t + 1.5
                self.ready['charge'] = t + cd(cfg, 'charge'); self.use['charge'] += 1
                self.strike(a, [target], [1.0], 'charge')
                self.nxt = t + rec
                return True
            if target['far']:
                target['dist'] = max(0, target['dist'] - PARTY_SPEED*DT)
            return False
        pool = self.order(adj)
        main, others = pool[0], pool[1:]
        reach_others = others[:max(0, math.ceil(AOE_SHARE*len(others)))]
        options = []
        if rank(cfg, 'whirlwind') and t >= self.ready['whirlwind'] and len(adj) >= 2:
            options.append(('whirlwind', pool, [0.5]*len(pool)))
        if rank(cfg, 'cleave') and t >= self.ready['cleave']:
            tg = [main] + reach_others
            options.append(('cleave', tg, [CLEAVE_SHARE]*len(tg)))
        tg = [main] + reach_others[:self.sweep_n]
        options.append(('swing' if len(tg) == 1 else 'sweeping_blows', tg, [1.0] + [self.sweep_share]*(len(tg) - 1)))
        def worth(o):
            return sum(min(a['dmg']*sh/divisor(x['a'], a), x['hp']) for x, sh in zip(o[1], o[2]))
        name, tg, shares = max(options, key=worth)
        if name in ('whirlwind', 'cleave'):
            self.ready[name] = t + cd(cfg, name)
        if name == 'cleave':
            for x in tg:
                x['stun_until'] = max(x['stun_until'], t + 1.0)
        self.use[name] += 1
        self.strike(a, tg, shares, name)
        self.nxt = t + rec
        return True

    def ranged_action(self, t, adj, haste):
        cfg = self.cfg
        usable = [a for a in self.ranged_atks if not a['cost'] or a['cost'] <= self.sp or self.surge]
        if not usable:
            if adj:
                return self.melee_action(t, adj, haste)
            return False
        pool = self.order(self.mons)
        main, others = pool[0], pool[1:]

        def value(a):
            n = 1
            if a.get('aoe') and others:
                n += math.ceil(AOE_SHARE*len(others))
            if a['kind'] == 'bow' and self.pierce_n:
                n += self.pierce_share*min(self.pierce_n, len(others))*LINE_SHARE
            ov = 1 + self.overload*min(3, n - 1) if a.get('aoe') and a['cost'] else 1
            v = a['dmg']*n*ov/divisor(main['a'], a)/a['rec']
            if a['cost'] and self.sp < 0.5*self.sp_full and not self.surge:
                v *= min(1.0, self.sp_regen*a['rec']/a['cost'])
            return v
        a = max(usable, key=value)
        rec = a['rec']/haste
        # Volley in place of a bow shot, Pinning Shot on the nearest walker.
        # Multishot (tree v2): 2/3/4 bow attacks at once over a ±30° cone, 75 % each; every arrow hits the first monster
        # in its line, so point-blank they all land on the target and against a spread group they split.
        if a['kind'] == 'bow' and rank(cfg, 'multishot') and t >= self.ready['multishot']:
            cone = [main] + others[:math.ceil(CONE_SHARE*len(others))]
            arrows = rank(cfg, 'multishot') + 1
            tg = [cone[i % len(cone)] for i in range(arrows)]
            self.strike(a, tg, [0.75]*arrows, 'multishot')
            self.ready['multishot'] = t + cd(cfg, 'multishot'); self.use['multishot'] += 1
            self.nxt = t + rec
            return True
        if a['kind'] == 'bow' and rank(cfg, 'volley') and t >= self.ready['volley'] and others:
            tg = [main] + others[:min(4, math.ceil(CONE_SHARE*len(others)))]
            self.strike(a, tg, [0.6]*len(tg), 'volley')
            self.ready['volley'] = t + cd(cfg, 'volley'); self.use['volley'] += 1
            self.nxt = t + rec
            return True
        if a['kind'] == 'bow' and rank(cfg, 'pinning_shot') and t >= self.ready['pinning_shot']:
            walkers = [x for x in self.mons if not x['far'] and x['dist'] > 0]
            if walkers:
                w = min(walkers, key=lambda x: x['dist'])
                w['slow_until'] = t + PIN_DUR[rank(cfg, 'pinning_shot') - 1]
                self.ready['pinning_shot'] = t + cd(cfg, 'pinning_shot'); self.use['pinning_shot'] += 1
        tg = [main]; shares = [1.0]
        if a.get('aoe') and others:
            extra = others[:math.ceil(AOE_SHARE*len(others))]
            tg += extra; shares += [1.0]*len(extra)
            if a['cost'] and self.overload:
                bonus = 1 + self.overload*min(3, len(extra))
                shares = [s*bonus for s in shares]
        elif a['kind'] == 'bow' and self.pierce_n and others:
            k = int(round(min(self.pierce_n, len(others))*LINE_SHARE))
            tg += others[:k]; shares += [self.pierce_share]*k
        source = a['kind'] if a['kind'] in ('bow', 'breath', 'melee') else 'spell'
        if a['kind'] == 'bow' and len(tg) > 1:
            source = 'piercing_arrows'
        if a['cost'] and len(tg) > 1 and self.overload:
            source = 'overload'
        if a['cost']:
            if self.surge:
                self.surge_used = True
            else:
                self.sp -= a['cost']
        self.use[source] += 1
        self.strike(a, tg, shares, source)
        if self.surge_used:
            self.surge = False; self.surge_used = False; self.dmg_by['spell_surge'] += 0
        self.nxt = t + rec
        return True

    def run(self, actors, carry=None):
        """carry: Onslaught (stacks, seconds left) from the previous pull of the same group."""
        cfg = self.cfg
        self.mons = []
        for a in actors:
            self.mons.append(dict(hp=a[2], max=a[2], a=a, far=stands_off(a),
                                  dist=RANGE_START if self.use_range else 0, slow_until=0, root_until=0,
                                  stun_until=0, speed=max(50, MON[str(a[0])]['speed'] or 200)))
        self.ref_hp = statistics.median(x['max'] for x in self.mons)
        self.ready = {k: 0.0 for k in CD}
        self.use = collections.Counter(); self.dmg_by = collections.Counter()
        self.hp = self.full; self.sp = self.sp_full
        self.surge = False; self.surge_used = False
        frenzy_until = sw_until = 0.0
        self.fz_stacks, self.fz_until = carry if carry else (0, 0.0)
        t = 0.0; self.nxt = 0.0; dead = False; minhp = 1.0
        while self.mons and t < 1800:
            for x in self.mons:
                if x['dist'] <= REACH or t < x['root_until']:
                    continue
                if x['far'] and x['dist'] <= RANGED_STAND:
                    continue
                goal = RANGED_STAND if x['far'] else REACH
                v = x['speed']*(0.5 if t < x['slow_until'] else 1.0)
                if not self.is_ranged:
                    v += PARTY_SPEED*0.5
                x['dist'] = max(goal, x['dist'] - v*DT)
            adj = [x for x in self.mons if x['dist'] <= REACH]
            sw = t < sw_until
            dmg = 0.0
            for x in self.mons:
                if t < x['stun_until']:
                    continue
                mel, mis = self.profile(x['a'], sw, bool(adj))
                dmg += mis + (mel if x['dist'] <= REACH else 0.0)
            dmg *= DT
            if self.ms and self.sp > 0:
                absorb = dmg*self.ms[0]; cost = absorb/self.ms[1]
                if cost > self.sp:
                    absorb = self.sp*self.ms[1]; cost = self.sp
                self.sp -= cost; dmg -= absorb
            self.hp -= dmg
            rg = self.regen*(1 + (1 - max(self.hp/self.full, -1))**2) if self.gm else self.regen
            self.hp = min(self.full, self.hp + (rg + self.regen_pot)*DT)
            self.sp = min(self.sp_full, self.sp + self.sp_regen*DT)
            if self.hp <= 0:
                dead = True; minhp = 0; break
            minhp = min(minhp, self.hp/self.full)
            # Tree v1: Frenzy is an active (+25 % for 6/7/8 s every 30 s). Tree v2: a passive, below.
            if cfg.get('tree') != 'v2' and rank(cfg, 'frenzy') and t >= self.ready['frenzy'] and adj:
                frenzy_until = t + FRENZY_DUR[rank(cfg, 'frenzy') - 1]
                self.ready['frenzy'] = t + cd(cfg, 'frenzy'); self.use['frenzy'] += 1
            if rank(cfg, 'shield_wall') and self.build in T.SHIELD and t >= self.ready['shield_wall'] \
                    and (len(adj) >= 2 or self.hp < 0.7*self.full):
                sw_until = t + 6; self.ready['shield_wall'] = t + cd(cfg, 'shield_wall'); self.use['shield_wall'] += 1
            if rank(cfg, 'spell_surge') and not self.surge and t >= self.ready['spell_surge'] \
                    and any(a['cost'] for a in self.ranged_atks):
                self.surge = True; self.ready['spell_surge'] = t + cd(cfg, 'spell_surge')
                self.use['spell_surge'] += 1
            if self.nxt <= t:
                if cfg.get('tree') == 'v2':
                    # Onslaught, tree v2: each kill stacks +1 % attack speed, at most 10/20/30 stacks, 30 s.
                    haste = 1 + self.fz_stacks/100 if t < self.fz_until else 1.0
                else:
                    haste = 1.25 if t < frenzy_until else 1.0
                done = False
                walkers_adj = [x for x in adj if not x['far']]
                if self.is_ranged and walkers_adj:
                    if rank(cfg, 'binding_circle') and t >= self.ready['binding_circle'] and rank(cfg, 'blink') \
                            and t + 0.5 >= self.ready['blink']:
                        for x in self.mons:
                            if x['dist'] <= 500:
                                x['root_until'] = t + ROOT_DUR[rank(cfg, 'binding_circle') - 1]
                        self.ready['binding_circle'] = t + cd(cfg, 'binding_circle'); self.use['binding_circle'] += 1
                        self.nxt = t + 0.5; done = True
                    elif rank(cfg, 'blink') and t >= self.ready['blink']:
                        for x in self.mons:
                            if not x['far'] and x['dist'] <= 500:
                                x['dist'] += 1600
                        self.ready['blink'] = t + cd(cfg, 'blink'); self.use['blink'] += 1
                        self.nxt = t + 0.5; done = True
                    elif rank(cfg, 'disengage') and t >= self.ready['disengage']:
                        for x in walkers_adj:
                            x['dist'] = 420
                        self.ready['disengage'] = t + cd(cfg, 'disengage'); self.use['disengage'] += 1
                        self.nxt = t + 0.5; done = True
                if not done:
                    done = self.ranged_action(t, adj, haste) if self.is_ranged else self.melee_action(t, adj, haste)
            alive_before = len(self.mons)
            self.mons = [x for x in self.mons if x['hp'] > 1e-9]
            kills = alive_before - len(self.mons)
            if kills and rank(cfg, 'frenzy') and cfg.get('tree') == 'v2':
                self.fz_stacks = min(10*rank(cfg, 'frenzy'), (self.fz_stacks if t < self.fz_until else 0) + kills)
                self.fz_until = t + ONSLAUGHT_SECONDS; self.use['frenzy'] += kills
            t += DT
        left = self.fz_until - t - PULL_GAP
        return dict(dead=dead, time=t, use=self.use, dmg=self.dmg_by, minhp=minhp,
                    carry=(self.fz_stacks, left) if left > 0 else None)


# --- configurations ---------------------------------------------------------------------------------------------------
def config(name, build, level, skills):
    """(pool variant, cfg) for a named configuration."""
    if name == 'today':
        return '', dict(ranks={}, keystones=[])
    if name == 'v1':
        return 'v1', T.allocation(build, level, skills, 'v1')
    if name == 'v2':
        return 'v2', T.allocation(build, level, skills, 'v2')
    if name.startswith('v2-'):     # ablations: v2 without one or more keystones or talents (joined by +)
        cut = name[3:].split('+')
        c = T.allocation(build, level, skills, 'v2')
        c['keystones'] = [k for k in c['keystones'] if k not in cut]
        c['ranks'] = {k: v for k, v in c['ranks'].items() if k not in cut}
        return 'v2', c
    raise ValueError(name)


POOLS = {}


def pool_rows(variant, diff):
    key = (variant, diff)
    if key not in POOLS:
        f = f'{S}/pool_out_{variant + "_" if variant else ""}{diff}.jsonl'
        rows = collections.defaultdict(dict)
        for line in open(f):
            d = json.loads(line); m = meta[d['id']]
            rows[(m['build'], m['Lc'], m['diff'], m['seed'])][m['spell'] or 'none'] = (d, m)
        POOLS[key] = rows
    return POOLS[key]


def groups_of(diff, seed, Lc):
    gs = []
    for mp in FIGHTS.get(f'{diff}|{seed}|{Lc}', []):
        g = collections.defaultdict(list)
        for a in mp['actors']:
            g[a[4]].append(a)
        gs.extend(g.values())
    return gs


def job(args):
    case, cname, use_range = args
    build, Lc, diff, seed = case
    any_row = next(iter(pool_rows('', diff)[case].values()))
    variant, cfg = config(cname, build, any_row[1]['actual_level'], any_row[1]['skills'])
    group = pool_rows(variant, diff).get(case)
    if group is None:
        return case, cname, None
    gs = groups_of(diff, seed, Lc)
    total = sum(len(a) for a in gs)
    res = {}; use = collections.Counter(); dmg = collections.Counter(); ftime = 0.0
    for metric in ('ok4', 'ok'):
        won = 0; t = 0.0
        for actors in gs:
            if metric == 'ok4':
                fs = []; carry = None
                for i in range(0, len(actors), 4):      # Onslaught's stacks carry into the next pull of the group
                    f = Fight(group, cfg, use_range).run(actors[i:i + 4], carry)
                    fs.append(f); carry = f['carry']
            else:
                fs = [Fight(group, cfg, use_range).run(actors)]
            dead = any(f['dead'] for f in fs); tt = sum(f['time'] for f in fs)
            if metric == 'ok4':
                for f in fs:
                    use.update(f['use']); dmg.update(f['dmg']); ftime += f['time']
            if not dead:
                won += len(actors); t += tt
        res[metric] = won/total if total else 0
        res['spm4' if metric == 'ok4' else 'spm'] = t/won if won else None
    res['use_per_min'] = {k: v/(ftime/60) for k, v in use.items()} if ftime else {}
    tot = sum(dmg.values()) or 1
    res['dmg_share'] = {k: v/tot for k, v in dmg.items()}
    res['cfg'] = dict(ranks=cfg['ranks'], keystones=cfg['keystones'],
                      points=cfg.get('points', 0))
    return case, cname, res


def main():
    diffs = sys.argv[1].split(',')
    stages = [int(x) for x in sys.argv[2].split(',')]
    cnames = sys.argv[3].split(',')
    out = sys.argv[4] if len(sys.argv) > 4 else f'{S}/talentfight.json'
    use_range = os.environ.get('NO_RANGE') is None
    jobs = []
    for diff in diffs:
        for case in pool_rows('', diff):
            if case[1] in stages:
                for c in cnames:
                    jobs.append((case, c, use_range))
    with multiprocessing.Pool() as pool:
        results = pool.map(job, jobs, chunksize=2)
    agg = collections.defaultdict(list)
    for case, c, res in results:
        if res is not None:
            agg[(case[2], case[1], case[0], c)].append(res)
    summary = {}
    for (diff, Lc, build, c), rs in agg.items():
        med = lambda k: statistics.median([r[k] for r in rs if r[k] is not None]) if any(
            r[k] is not None for r in rs) else None
        uses = collections.defaultdict(list); shares = collections.defaultdict(list)
        for r in rs:
            for k, v in r['use_per_min'].items():
                uses[k].append(v)
            for k, v in r['dmg_share'].items():
                shares[k].append(v)
        summary[f'{diff}|{Lc}|{build}|{c}'] = dict(
            ok4=med('ok4'), ok=med('ok'), spm4=med('spm4'), spm=med('spm'),
            use_per_min={k: statistics.median(v + [0]*(len(rs) - len(v))) for k, v in uses.items()},
            dmg_share={k: statistics.median(v + [0]*(len(rs) - len(v))) for k, v in shares.items()},
            cfg=rs[0]['cfg'])
    json.dump(summary, open(out, 'w'), indent=1)
    builds = sorted({k.split('|')[2] for k in summary})
    for diff in diffs:
        for Lc in stages:
            print(f'\n### {diff}, stage {Lc}: pulls of four % / s per monster; whole groups %\n')
            print('| Build | ' + ' | '.join(cnames) + ' |')
            print('|---|' + '---|'*len(cnames))
            for b in builds:
                cells = []
                for c in cnames:
                    r = summary.get(f'{diff}|{Lc}|{b}|{c}')
                    if not r:
                        cells.append('–'); continue
                    s = f"{r['spm4']:.1f}" if r['spm4'] else '–'
                    cells.append(f"{r['ok4']*100:.0f} / {s}; {r['ok']*100:.0f}")
                print(f'| {b} | ' + ' | '.join(cells) + ' |')


if __name__ == '__main__':
    main()
