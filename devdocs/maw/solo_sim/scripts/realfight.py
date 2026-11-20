"""Real-group fights: each build against the actual monster groups of the maps around its stage.

Inputs: the harness rows (out_route_<seed>.jsonl, with the per-attacker-level grid), meta_route_seeds.json (case meta)
and fights.json (per difficulty|seed|stage: the last five cleared maps and the next five, each actor
[monsterId, level, hp, attack1Damage, group, boss, physBase, magicBase]) plus monsters.json (the monster table).

A group is the actors standing together (512 units, gen in route_*.json). The whole group attacks at once; the solo
starts each group at full health and kills the monster with the most damage per HP first. Every monster attacks every
recovery/60 x 1.05 s with its own mix: spell 1 at its chance, spell 2, attack 2, else attack 1, each with its own
type, missile flag and MAW damage (attack 1 = the map's row; attack 2 = its base for its class x dice ratio;
player-school spells = base for magic x MAW's spell multiplier). Damage taken per type and the Speed hit chance come
from the character sheet against an attacker of that level. The solo's hits are cut by the monster's resistance to
their type (MAW: / 2^(res/100), resistance capped at 200).
"""
import json, math, sys, os, collections, statistics

from simdir import S as _S
S = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ('', '-') else _S
OUT = sys.argv[2]
DT = 0.1
AOE_SHARE = 0.75
MON = json.load(open(S + '/monsters.json'))
FIGHTS = json.load(open(S + '/fights.json'))
meta = json.load(open(S + '/' + os.environ.get('META', 'pool_meta.json')))

# Grid type order from the harness: Physical, Fire, Air, Water, Earth, Spirit, Mind, Body, Light, Dark, Energy.
TYPE_INDEX = {'Phys': 0, 'Fire': 1, 'Air': 2, 'Water': 3, 'Earth': 4, 'Spirit': 5, 'Mind': 6, 'Body': 7, 'Pois': 7,
              'Light': 8, 'Dark': 9, 'Ener': 10, 'Energy': 10}
# monsters.json resistance order: fire, air, water, earth, spirit, mind, body, light, dark, phys.
RES_INDEX = {'Phys': 9, 'Fire': 0, 'Air': 1, 'Water': 2, 'Earth': 3, 'Spirit': 4, 'Mind': 5, 'Body': 6, 'Light': 7,
             'Dark': 8}
SPELL_MULT = {2: 0.75, 6: 0.5, 9: 0.3, 11: 1.35, 15: 0.5, 18: 0.95, 20: 0.8, 24: 0.5, 29: 1.15, 32: 0.75, 37: 0.85,
              39: 1.1, 41: 0.6, 44: 0.4, 52: 0.65, 59: 0.8, 65: 1.25, 70: 0.75, 78: 1.1, 90: 1.15, 93: 0.4, 97: 0.7}
SCHOOL = ['Fire', 'Air', 'Water', 'Earth', 'Spirit', 'Mind', 'Body', 'Light', 'Dark']
SPELL_TYPE = {'Incinerate': 'Fire', 'Fire Bolt': 'Fire', 'Fireball': 'Fire', 'Lightning Bolt': 'Air',
              'Light Bolt': 'Light'}
MS_FRAC = {1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}


def spell_type(spell_id):
    if spell_id in (44, 93):
        return 'Phys'
    return SCHOOL[min(8, (spell_id - 1)//11)]


def monster_actions(actor):
    """[(probability, base damage before the character's defences, damage type, missile)] per attack."""
    mid, level, hp, a1dmg, group, boss, phys, magic = actor
    m = MON[str(mid)]
    base = lambda t: phys if t == 'Phys' else magic
    acts = []
    rest = 1.0
    for sid, chance in ((m['s1'], m['s1c']), (m['s2'], m['s2c'])):
        if sid and chance:
            p = rest*chance/100
            if sid in SPELL_MULT:
                t = spell_type(sid)
                acts.append((p, base(t)*SPELL_MULT[sid], t, True))
            else:
                acts.append((p, 0.0, 'Phys', False))   # a buff or curse: the turn goes without damage
            rest -= p
    a1t = m['a1'] if m['a1'] in TYPE_INDEX else 'Phys'
    if m['a2'] not in ('0', '') and m['a2c'] and m['a2avg'] > 0:
        a2t = m['a2'] if m['a2'] in TYPE_INDEX else 'Phys'
        p = rest*m['a2c']/100
        ratio = m['a2avg']/m['a1avg'] if m['a1avg'] > 0 else 1
        acts.append((p, base(a2t)*ratio, a2t, bool(m['a2m'])))
        rest -= p
    acts.append((rest, a1dmg, a1t, bool(m['a1m'])))
    return acts


def monster_dps(actor, d, maw_flat=False):
    """Expected HP the character loses per second to this monster."""
    m = MON[str(actor[0])]
    grid = d['grid'].get(str(max(1, actor[1])))
    if grid is None:
        grid = d['grid'][min(d['grid'], key=lambda k: abs(int(k) - actor[1]))]
    hit = grid[0]
    flat = d['flat_cut']*(d['flat_maw_factor'] if maw_flat else 1)
    per_attack = 0.0
    for p, dmg, t, missile in monster_actions(actor):
        if dmg <= 0:
            continue
        after = dmg*grid[1 + TYPE_INDEX[t]]/100
        if flat > 0:
            after = max(after - flat, 0.25*after)
        chance = (hit*hit if missile else hit)*(1 - d['dodge'])
        per_attack += p*after*chance
    interval = max(m['rec'], 10)/60*1.05
    return per_attack/interval


def resist_div(actor, t):
    if t is None:
        return 1.0
    res = MON[str(actor[0])]['res'][RES_INDEX.get(t, 9)]
    return 2**(min(max(0, res) % 1000, 200)/100)


def player_attacks(group):
    d0, m0 = next(iter(group.values()))
    build = m0['build']
    attacks = []
    if build == 'archer':
        attacks.append(dict(kind='bow', dmg=d0['ranged_dps']*d0['bow_delay_s'], rec=d0['bow_delay_s'], cost=0,
                            aoe=False, leech=d0['leech_ranged'], type='Phys'))
    if build == 'dragon' and d0['breath_recovery'] > 0:
        # A dragon's breath takes the monster's lowest resistance (DM:657-664).
        attacks.append(dict(kind='breath', dmg=d0['breath_per_attack'], rec=d0['breath_recovery'], cost=0, aoe=True,
                            leech=0, type='lowest'))
    for spell, (d, m) in group.items():
        if spell in SPELL_TYPE and d.get('spell_recovery_s', 0) > 0 and d.get('spell_dps', 0) > 0:
            attacks.append(dict(kind=spell, dmg=d['spell_dps']*d['spell_recovery_s'], rec=d['spell_recovery_s'],
                                cost=d['spell_cost'], aoe=spell == 'Fireball', leech=d['leech_spell'],
                                type=SPELL_TYPE[spell]))
    attacks.append(dict(kind='melee', dmg=d0['emp_melee_per_attack'], rec=d0['emp_melee_recovery'], cost=0,
                        aoe=False, leech=d0['leech_melee'], type='Phys'))
    return attacks


def divisor(actor, a):
    if a['type'] == 'lowest':
        return 2**(min(min(max(0, r) % 1000, 200) for r in MON[str(actor[0])]['res'])/100)
    return resist_div(actor, a['type'])


def fight(group, actors, potions, maw_flat=False):
    d0, m0 = next(iter(group.values()))
    build = m0['build']
    full = d0['hp']; hp = full; sp_full = d0['sp']; sp = sp_full
    regen = d0['regen_full']; gm = regen > 0 and d0['regen_half']/regen > 1.2
    regen_pot = d0['regen_potion']; sp_regen = d0['sp_per_s']
    ms = None
    sk = m0['skills'].get('ManaShield')
    if sk:
        s, mastery = sk
        ms = (MS_FRAC[mastery], 5 if s >= 50 else 1 + min(s, 50)**1.4/60)
    attacks = player_attacks(group)
    class_heal = d0['seraph_heal'] if build == 'seraph' else d0['shaman_heal'] if build == 'shaman' else 0
    assassin = build == 'assassin'
    if assassin:
        sks = m0['skills']
        s_fire, m_fire = sks.get('FireMagic', [0, 0]); m_water = sks.get('WaterMagic', [0, 0])[1]
        m_air = sks.get('AirMagic', [0, 0])[1]
        e_cost = 50 - 5*m_fire; e_refund = (0.10 + 0.01*s_fire)*15; e_regen = (0.6 + 0.2*m_water)*10
        bonus = d0['assassination_bonus']
    mons = [dict(hp=a[2], max=a[2], dps=monster_dps(a, d0, maw_flat), a=a) for a in actors]
    # Kill order: most damage per HP first.
    mons.sort(key=lambda x: -x['dps']/max(1, x['hp']))
    t = 0.0; nxt = 0.0; minhp = hp; drinks = 0; dead = False
    ref_hp = statistics.median(x['max'] for x in mons)
    while mons and t < 1800:
        alive = len(mons)
        dmg = sum(x['dps'] for x in mons)*DT
        if ms and sp > 0:
            absorb = dmg*ms[0]; cost = absorb/ms[1]
            if cost > sp:
                absorb = sp*ms[1]; cost = sp
            sp -= cost; dmg -= absorb
        hp -= dmg
        r = regen*(1 + (1 - max(hp/full, -1))**2) if gm else regen
        hp = min(full, hp + (r + regen_pot)*DT)
        sp = min(sp_full, sp + sp_regen*DT)
        if assassin:
            sp = min(sp_full, sp + e_regen*DT)
        if potions and hp < 0.35*full and nxt <= t:
            hp = min(full, hp + d0['pot_heal_large']); drinks += 1; nxt = t + 1.0
        if hp <= 0:
            dead = True; minhp = min(minhp, hp); break
        minhp = min(minhp, hp)
        if nxt <= t:
            usable = [a for a in attacks if assassin or a['cost'] <= sp]

            def value(a):
                hits = max(1, math.ceil(AOE_SHARE*alive)) if a['aoe'] and alive > 1 else 1
                v = sum(a['dmg']/divisor(x['a'], a) for x in mons[:hits])/a['rec']
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
            dealt = 0.0
            for x in mons[:hits]:
                landed = dmg_hit/divisor(x['a'], a)
                dealt += min(landed, x['hp']); x['hp'] -= landed
            if a['leech'] > 0:
                heal = max(dealt/ref_hp*a['leech']*full,
                           full*a['leech']/5*a['rec']*60/100/(2.5 if a['aoe'] else 1))
                hp = min(full, hp + heal)
            if a['kind'] == 'melee' and class_heal:
                hp = min(full, hp + class_heal*d0['my_hit_melee'])
            kills = sum(1 for x in mons if x['hp'] <= 1e-9)
            if assassin and kills:
                sp = min(sp_full, sp + kills*(1 + m_air)*5)
            mons = [x for x in mons if x['hp'] > 1e-9]
            nxt = t + a['rec']
        t += DT
    return dict(dead=dead, minhp=max(minhp, 0)/full, time=t, drinks=drinks)


def party_fight(members, actors, potions):
    """A party's fight, in the same expected values: `members` is one harness group per member.

    Every monster spreads its attacks evenly over the living members (each takes the damage its own sheet lets
    through), every member attacks on its own recovery with its best attack, and a member who knows Heal or Power Cure
    (the harness's `heals`) heals when someone is hurt. A member at 0 HP is out; the party loses when all are. Cover,
    the classes' own on-hit heals and the Assassin's energy are left out (none of the reference party uses them)."""
    st = []
    for g in members:
        d0, m0 = next(iter(g.values()))
        ms = None
        sk = m0['skills'].get('ManaShield')
        if sk:
            ms = (MS_FRAC[sk[1]], 5 if sk[0] >= 50 else 1 + min(sk[0], 50)**1.4/60)
        regen = d0['regen_full']
        st.append(dict(d=d0, full=d0['hp'], hp=d0['hp'], sp=d0['sp'], sp_full=d0['sp'], nxt=0.0,
                       attacks=player_attacks(g), alive=True, regen=regen, gm=regen > 0 and d0['regen_half']/regen > 1.2,
                       ms=ms, heals=d0.get('heals') or [[0, 0, 0], [0, 0, 0]]))
    mons = [dict(hp=a[2], max=a[2], dps=[monster_dps(a, m['d']) for m in st], a=a) for a in actors]
    mons.sort(key=lambda x: -sum(x['dps'])/max(1, x['hp']))
    ref_hp = statistics.median(x['max'] for x in mons)
    t = 0.0; drinks = 0; deaths = 0; minshare = 1.0
    while mons and t < 1800:
        living = [i for i, m in enumerate(st) if m['alive']]
        if not living:
            break
        alive = len(mons)
        for i in living:
            m = st[i]
            dmg = sum(x['dps'][i] for x in mons)/len(living)*DT
            if m['ms'] and m['sp'] > 0:
                absorb = dmg*m['ms'][0]; cost = absorb/m['ms'][1]
                if cost > m['sp']:
                    absorb = m['sp']*m['ms'][1]; cost = m['sp']
                m['sp'] -= cost; dmg -= absorb
            m['hp'] -= dmg
            r = m['regen']*(1 + (1 - max(m['hp']/m['full'], -1))**2) if m['gm'] else m['regen']
            m['hp'] = min(m['full'], m['hp'] + (r + m['d']['regen_potion'])*DT)
            m['sp'] = min(m['sp_full'], m['sp'] + m['d']['sp_per_s']*DT)
            if potions and m['hp'] < 0.35*m['full'] and m['nxt'] <= t:
                m['hp'] = min(m['full'], m['hp'] + m['d']['pot_heal_large']); drinks += 1; m['nxt'] = t + 1.0
            if m['hp'] <= 0:
                m['alive'] = False; deaths += 1
        living = [i for i in living if st[i]['alive']]
        if not living:
            break
        minshare = min(minshare, sum(st[i]['hp'] for i in living)/sum(m['full'] for m in st))
        for i in living:
            m = st[i]
            if m['nxt'] > t or not mons:
                continue
            hurt = sorted(living, key=lambda j: st[j]['hp']/st[j]['full'])
            low = st[hurt[0]]
            heal, cure = m['heals'][0], m['heals'][1]
            if low['hp'] < 0.6*low['full']:
                several = sum(1 for j in living if st[j]['hp'] < 0.75*st[j]['full']) >= 2
                if cure[0] > 0 and several and m['sp'] >= cure[1]:
                    for j in living:
                        st[j]['hp'] = min(st[j]['full'], st[j]['hp'] + cure[0])
                    m['sp'] -= cure[1]; m['nxt'] = t + max(cure[2], 0.3)
                    continue
                if heal[0] > 0 and m['sp'] >= heal[1]:
                    low['hp'] = min(low['full'], low['hp'] + heal[0])
                    m['sp'] -= heal[1]; m['nxt'] = t + max(heal[2], 0.3)
                    continue
            usable = [a for a in m['attacks'] if a['cost'] <= m['sp']]

            def value(a):
                hits = max(1, math.ceil(AOE_SHARE*len(mons))) if a['aoe'] and len(mons) > 1 else 1
                v = sum(a['dmg']/divisor(x['a'], a) for x in mons[:hits])/a['rec']
                if a['cost'] and m['sp'] < 0.5*m['sp_full']:
                    v *= min(1.0, m['d']['sp_per_s']*a['rec']/a['cost'])
                return v
            a = max(usable, key=value)
            if a['cost']:
                m['sp'] -= a['cost']
            hits = min(len(mons), max(1, math.ceil(AOE_SHARE*len(mons)))) if a['aoe'] else 1
            dealt = 0.0
            for x in mons[:hits]:
                landed = a['dmg']/divisor(x['a'], a)
                dealt += min(landed, x['hp']); x['hp'] -= landed
            if a['leech'] > 0:
                m['hp'] = min(m['full'], m['hp'] + max(dealt/ref_hp*a['leech']*m['full'],
                              m['full']*a['leech']/5*a['rec']*60/100/(2.5 if a['aoe'] else 1)))
            mons = [x for x in mons if x['hp'] > 1e-9]
            m['nxt'] = t + a['rec']
        t += DT
    wiped = not any(m['alive'] for m in st)
    return dict(dead=wiped, minhp=0.0 if wiped else minshare, time=t, drinks=drinks, deaths=deaths)


def evaluate(key_group):
    key, group = key_group
    party = key[0] == 'party'
    members = list(group.values()) if party else None
    d0, m0 = next(iter((members[0] if party else group).values()))
    run = (lambda actors, potions: party_fight(members, actors, potions)) if party else \
        (lambda actors, potions: fight(group, actors, potions))
    full = sum(next(iter(g.values()))[0]['hp'] for g in members) if party else d0['hp']
    maps = FIGHTS.get(f"{m0.get('tag', m0['diff'])}|{m0['seed']}|{m0['Lc']}", [])
    res = []
    for mp in maps:
        groups = collections.defaultdict(list)
        for a in mp['actors']:
            groups[a[4]].append(a)
        per = []
        for gi, actors in groups.items():
            f = run(actors, False)
            fp = run(actors, True) if f['dead'] or f.get('deaths') else f
            # The same group pulled four at a time, resting to full between pulls.
            chunks = [actors[i:i + 4] for i in range(0, len(actors), 4)]
            pulls = [run(c, False) for c in chunks]
            pulls_p = [run(c, True) if x['dead'] or x.get('deaths') else x for c, x in zip(chunks, pulls)]
            incoming = sum(sum(monster_dps(a, next(iter(g.values()))[0]) for g in members)/len(members)
                           if party else monster_dps(a, d0) for a in actors)
            per.append(dict(n=len(actors), dead=f['dead'], deadp=fp['dead'], time=fp['time'], drinks=fp['drinks'],
                            dead4=any(x['dead'] for x in pulls), dead4p=any(x['dead'] for x in pulls_p),
                            time4=sum(x['time'] for x in pulls_p), drinks4=sum(x['drinks'] for x in pulls_p),
                            deaths=fp.get('deaths', int(fp['dead'])),
                            deaths4=sum(x.get('deaths', int(x['dead'])) for x in pulls_p),
                            minhp=f['minhp'], names=collections.Counter(MON[str(a[0])]['name'] for a in actors).most_common(3),
                            lv=max(a[1] for a in actors), dps=incoming/full))
        res.append(dict(file=mp['file'], next=mp.get('next', 0), level=mp['level'], monsters=len(mp['actors']),
                        groups=per))
    return dict(build='party' if party else m0['build'], label='Party of five' if party else m0['label'],
                cls=m0.get('cls'), promoted=m0.get('promoted'), Lc=m0['Lc'], diff=m0['diff'], seed=m0['seed'],
                party=party, level=m0.get('actual_level', m0['Lc']), hp=full, maps=res)


if __name__ == '__main__':
    rows = {}
    for line in open(S + '/' + OUT):
        d = json.loads(line); rows[d['id']] = d
    groups = collections.defaultdict(dict)
    for cid, d in rows.items():
        m = meta[cid]
        if m.get('party'):
            # One entry per party: member build -> that member's harness group.
            groups[('party', m['Lc'], m['diff'], m['seed'])].setdefault(m['build'], {})[m['spell'] or 'none'] = (d, m)
        else:
            groups[(m['build'], m['Lc'], m['diff'], m['seed'])][m['spell'] or 'none'] = (d, m)
    import multiprocessing
    multiprocessing.set_start_method('fork')
    with multiprocessing.Pool(24) as pool:
        results = pool.map(evaluate, list(groups.items()), chunksize=4)
    json.dump(results, open(S + '/real_' + OUT.replace('.jsonl', '.json'), 'w'))
    print(len(results), 'cases')
