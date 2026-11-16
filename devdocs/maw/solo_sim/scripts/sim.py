"""Expected-value fight simulator over the harness's engine numbers (out.jsonl + meta.json).
One solo character against N B-tier monsters of level M that all attack from the first second."""
import json, math, sys, collections, os

from simdir import S as _S
S = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ('', '-') else _S
MON_INTERVAL = 80/60*1.05      # median monster recovery 80 ticks, x U(0.9, 1.2) (GameplayActorAiSystem startAttack)
DT = 0.1
AOE_SHARE = 0.75               # share of the pack an area attack (Fireball, dragon breath) catches

meta = json.load(open(S + '/' + os.environ.get('META', 'meta.json')))
rows = {}
OUT = sys.argv[2] if len(sys.argv) > 2 else 'out.jsonl'
for line in open(S + '/' + OUT):
    d = json.loads(line); rows[d['id']] = d

groups = collections.defaultdict(dict)
for cid, d in rows.items():
    m = meta[cid]
    key = (m['build'], m['Lc'], m['diff'], m['mtag'])
    groups[key][m['spell'] or 'none'] = (d, m)

MS_FRAC = {1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}

def mana_shield(m, d=None):
    sk = m['skills'].get('ManaShield')
    if not sk: return None
    s, mastery = sk
    eff = 5 if s >= 50 else 1 + min(s, 50)**1.4/60
    if d is not None and d.get('tf_archon') and s >= 50:
        eff = 10   # the Archon keystone
    return MS_FRAC[mastery], eff

import os
MAW_FLAT = os.environ.get('MAW_FLAT') == '1'
OPENER = float(os.environ.get('OPENER', '0'))
RANGED = {'archer', 'dragon', 'archmage', 'elementalist', 'priest'}

def incoming(d, magic=False):
    """Expected HP lost per second to one B monster, and the landed hit."""
    if magic:
        raw = d['mon_dmg_b_magic']
        taken = sum(d['taken_'+k] for k in ('fire', 'air', 'water', 'earth', 'mind', 'body'))/6/100
        hit = d['hit_on_me']**2   # missiles roll the Speed dodge twice
    else:
        raw = d['mon_dmg_b_phys']; taken = d['taken_phys']/100; hit = d['hit_on_me']
    after = raw*taken
    flat = d['flat_cut']*(d['flat_maw_factor'] if MAW_FLAT else 1)
    after = max(after - flat, 0.25*after) if flat > 0 else after
    # Talent tree v2 rows (talent_route.py): cuts after the floor, and Unbroken halving a hit's part above 30 % of HP.
    after *= d.get('tf_tm', 1.0) if magic else d.get('tf_tp', 1.0)
    if d.get('tf_unbroken') and after > 0.3*d['hp']:
        after = 0.3*d['hp'] + (after - 0.3*d['hp'])/2
    hit *= (1 - d['dodge'])
    return after*hit/MON_INTERVAL, after

def fight(group, N, potions=False, magic=False):
    d0, m0 = next(iter(group.values()))
    full = d0['hp']; hp = full; build = m0['build']
    sp_full = d0['sp']; sp = sp_full
    per_mon, landed = incoming(d0, magic)
    monhp = d0['mon_hp_b']
    regen_base = d0['regen_full']; gm_regen = d0['regen_full'] > 0 and d0['regen_half']/d0['regen_full'] > 1.2
    regen_pot = d0['regen_potion']
    ms = mana_shield(m0, d0)
    sweep_n = d0.get('tf_sweep_n', 0); sweep_share = d0.get('tf_sweep_share', 0)
    overload = d0.get('tf_overload', 0); leech_div = d0.get('tf_leech_div', 5)
    # attacks available
    attacks = []
    melee_dmg = d0['emp_melee_per_attack']; melee_rec = d0['emp_melee_recovery']
    if build == 'archer':
        attacks.append(dict(kind='bow', dmg=d0['ranged_dps']*d0['bow_delay_s'], rec=d0['bow_delay_s'], cost=0, aoe=False,
                            leech=d0['leech_ranged']))
    if build == 'dragon' and d0['breath_recovery'] > 0:
        attacks.append(dict(kind='breath', dmg=d0['breath_per_attack'], rec=d0['breath_recovery'], cost=0, aoe=True,
                            leech=0))
    for spell, (d, m) in group.items():
        if d.get('spell_recovery_s', 0) <= 0 or d.get('spell_dps', 0) <= 0:
            continue   # not known at this stage (the class has not got the mastery yet)
        if spell in ('Incinerate', 'Light Bolt', 'Fire Bolt', 'Lightning Bolt'):
            attacks.append(dict(kind=spell, dmg=d['spell_dps']*d['spell_recovery_s'], rec=d['spell_recovery_s'],
                                cost=d['spell_cost'], aoe=False, leech=d['leech_spell']))
        if spell == 'Fireball':
            attacks.append(dict(kind=spell, dmg=d['spell_dps']*d['spell_recovery_s'], rec=d['spell_recovery_s'],
                                cost=d['spell_cost'], aoe=True, leech=d['leech_spell']))
    attacks.append(dict(kind='melee', dmg=melee_dmg, rec=melee_rec, cost=0, aoe=False, leech=d0['leech_melee']))
    sp_regen = d0['sp_per_s']
    # assassin energy
    assassin = build == 'assassin'
    if assassin:
        sk = m0['skills']
        m_fire = sk.get('FireMagic', [0, 0])[1]; s_fire = sk.get('FireMagic', [0, 0])[0]
        m_water = sk.get('WaterMagic', [0, 0])[1]; m_air = sk.get('AirMagic', [0, 0])[1]
        e_cost = 50 - 5*m_fire; e_refund = (0.10 + 0.01*s_fire)*15; e_regen = (0.6 + 0.2*m_water)*10
        bonus = d0['assassination_bonus']
    mons = [monhp]*N
    t = 0.0; next_attack = 0.0; minhp = hp; drinks = 0; dead = False
    while mons and t < 900:
        alive = len(mons)
        # monsters (a ranged build gets OPENER seconds before the pack reaches it)
        dmg = per_mon*alive*DT if (t >= OPENER or build not in RANGED) else 0.0
        if ms and sp > 0:
            absorb = dmg*ms[0]; cost = absorb/ms[1]
            if cost > sp: absorb = sp*ms[1]; cost = sp
            sp -= cost; dmg -= absorb
        hp -= dmg
        # regeneration
        r = regen_base*(1 + (1 - max(hp/full, -1))**2) if gm_regen else regen_base
        hp = min(full, hp + (r + regen_pot)*DT)
        sp = min(sp_full, sp + sp_regen*DT)
        if assassin: sp = min(sp_full, sp + e_regen*DT)
        if potions and hp < 0.35*full and next_attack <= t:
            hp = min(full, hp + d0['pot_heal_large']); drinks += 1; next_attack = t + 1.0
        if hp <= 0:
            dead = True; minhp = min(minhp, hp); break
        minhp = min(minhp, hp)
        if next_attack <= t:
            usable = [a for a in attacks if (a['cost'] <= sp if not assassin else True)]
            def value(a):
                hits = max(1, math.ceil(AOE_SHARE*alive)) if a['aoe'] and alive > 1 else 1
                v = a['dmg']*min(hits, alive)/a['rec']
                # below half mana, weigh a spell by what regeneration can keep paying for
                if a['cost'] and not assassin and sp < 0.5*sp_full:
                    v *= min(1.0, sp_regen*a['rec']/a['cost'])
                return v
            a = max(usable, key=value)
            dmg_hit = a['dmg']
            if assassin and a['kind'] == 'melee':
                if sp >= e_cost:
                    sp -= e_cost; sp += e_refund
                    dmg_hit -= bonus*min(0.8, 0.2*(alive - 1))
                else:
                    dmg_hit -= bonus
            elif a['cost']:
                sp -= a['cost']
            hits = min(alive, max(1, math.ceil(AOE_SHARE*alive))) if a['aoe'] else 1
            shares = [1.0]*hits
            if a['kind'] == 'melee' and sweep_n and alive > 1:
                extra = min(sweep_n, math.ceil(AOE_SHARE*(alive - 1)))
                hits = 1 + extra; shares = [1.0] + [sweep_share]*extra     # Sweeping Blows (talent tree v2)
            if a['aoe'] and a['cost'] and overload and hits > 1:
                shares = [x*(1 + overload*min(3, hits - 1)) for x in shares]   # Overload (talent tree v2)
            dealt = 0
            for i in range(hits):
                take = min(dmg_hit*shares[i], mons[i]); mons[i] -= dmg_hit*shares[i]; dealt += take
            # leech: the share of a B monster's HP dealt, of full HP; floor share/5 x recovery ticks/100 of full HP
            if a['leech'] > 0:
                heal = max(dealt/monhp*a['leech']*full,
                           full*a['leech']/leech_div*a['rec']*60/100/(2.5 if a['aoe'] else 1))
                hp = min(full, hp + heal)
            if a['kind'] == 'melee':
                # Only the Seraph line heals with Body on a blow, only the Shaman line with its own Body heal
                # (MawCombatRules::applyClassHitEffects); the helpers do not check the class themselves.
                classHeal = d0['seraph_heal'] if build == 'seraph' else d0['shaman_heal'] if build == 'shaman' else 0
                hp = min(full, hp + classHeal*d0['my_hit_melee'])
            kills = sum(1 for x in mons if x <= 1e-9)
            if assassin and kills: sp = min(sp_full, sp + kills*(1 + m_air)*5)
            mons = [x for x in mons if x > 1e-9]
            next_attack = t + a['rec']
        t += DT
    return dict(dead=dead, minhp=max(minhp, 0)/full, time=t, drinks=drinks)

def summary(group):
    d0, m0 = next(iter(group.values()))
    per_mon, landed = incoming(d0)
    per_mag, _ = incoming(d0, True)
    full = d0['hp']
    r = d0['regen_full']*(1.25 if d0['regen_full'] > 0 and d0['regen_half']/d0['regen_full'] > 1.2 else 1) + d0['regen_potion']
    single = fight(group, 1)
    out = dict(build=m0['build'], label=m0['label'], Lc=m0['Lc'], diff=m0['diff'], mtag=m0['mtag'], M=m0['M'],
               P=m0['P'], hp=full, skills=m0['skills'], monhp=d0['mon_hp_b'], mondmg=d0['mon_dmg_b_phys'],
               landed=landed, inc_pct=100*per_mon/full, inc_mag_pct=100*per_mag/full, regen_pct=100*r/full,
               ttk1=single['time'], potion_heal_pct=100*d0['pot_heal_large']/full)
    for N in (4, 10):
        f = fight(group, N); fp = fight(group, N, potions=True); fm = fight(group, N, magic=True)
        out[f'n{N}'] = f; out[f'n{N}p'] = fp; out[f'n{N}m'] = fm
    lo, hi = 0, 41          # largest pack survived without drinking (binary search, deaths are monotonic in N)
    if not fight(group, 1)['dead']:
        lo = 1
        while hi - lo > 1:
            mid = (lo + hi)//2
            lo, hi = (mid, hi) if not fight(group, mid)['dead'] else (lo, mid)
    out['maxn'] = lo
    return out

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('fork')
    with multiprocessing.Pool(24) as pool:
        results = pool.map(summary, list(groups.values()))
    json.dump(results, open(S + '/results_' + ('mawflat_' if MAW_FLAT else '') + ('opener_' if OPENER else '') + OUT.replace('.jsonl', '') + '.json', 'w'))
    print(len(results), 'groups')
