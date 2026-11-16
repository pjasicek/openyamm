"""Power-gap sweeps over realfight.py: how much more power a solo needs to clear Beyond Madness.

Loads realfight.py's functions (everything before its `if __name__ == '__main__':`), scales fields of the harness
rows (pool_out_<difficulty>.jsonl) and replays the fights against the real monster groups (fights.json) of the
case's stage. Potions are off throughout (ok4 and ok as in agg_real.py).

Per case (build, stage, difficulty, seed) and lever, the multiplier at which the seed reaches a target is found by
log-space bisection. Each seed's share of monsters beaten is (near enough) monotone in the multiplier, so the
multiplier at which the median over the five seeds reaches the target is the median of the per-seed thresholds.

Levers (k >= 1 always means "stronger"):
  hp       max HP x k (regeneration, potions stay absolute; leech heals scale with max HP as in realfight)
  dmg      every damage source x k (melee per attack, breath, bow, spells)
  magic    damage taken from every non-physical type x 1/k (grid columns Fire..Energy)
  phys     physical damage taken x 1/k
  sustain  existing regeneration and leech x k (no effect on builds without either)
  regen    adds regeneration of k % of max HP per second (k is a percentage here, not a multiplier)
  comboA   hp x k, dmg x k, magic taken x 1/k
  comboB   hp x k, dmg x k, magic and physical taken x 1/k
  comboC   magic taken x 1/2 fixed (magic hits at physical parity), hp x k, dmg x k
  mon      dmg x k, every damage taken x 1/k: the same as dividing the monsters' HP and damage by k
Targets: ok4 (pulled four at a time, resting between pulls) >= 90 %, ok (whole groups at once) >= 90 %, and for the
combos also "mash" = ok >= 90 % with <= 1 s of fighting per monster (whole groups, surviving groups only) and
"mashR" = ok >= 90 % with <= max(1 s, 1.1 x the fastest attack's recovery) per monster (one swing per monster: a
single-target attack slower than 1 s can never reach 1 s per monster).

Usage: python3 power_gap_sweep.py sweep   -> power_gap_sweep.json
       python3 power_gap_sweep.py probe   -> power_gap_probe.json (fixed multipliers on other difficulties)
       python3 power_gap_sweep.py gap     -> power_gap_gap.json (baseline incoming mix, time to kill / time to die)
       python3 power_gap_sweep.py tables  -> prints the Markdown tables of POWER_GAP.md from the three JSON files
The probe takes PROBE='[["A2.75","comboA",2.75], ...]' (tag, lever, k) and optional PROBE_DIFFS / PROBE_OUT.

Effective power P = EHP multiplier x DPS multiplier, with EHP from the case's physical share s of the incoming damage:
hp k -> P = k; dmg k -> k; magic k -> 1/(s + (1-s)/k); phys k -> 1/(s/k + 1-s); comboA -> k^2/(s + (1-s)/k);
comboB -> k^3; comboC -> k^2/(s + (1-s)/2); mon -> k^2.
"""
import json, os, sys, math, copy, collections, statistics, multiprocessing

# The solo-sim work directory (realfight.py, pool_out_*.jsonl, pool_meta.json, fights.json, monsters.json); results are
# written there too. Default: <repo>/output/maw_solo_sim, as devdocs/maw/solo_sim/scripts/simdir.py.
H = os.environ.get('SOLO_SIM_DIR') or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'output', 'maw_solo_sim'))

_src = open(H + '/realfight.py').read().split("if __name__ == '__main__':")[0]
_argv = sys.argv
sys.argv = ['realfight.py', H, 'unused.jsonl']
RF = {'__name__': 'realfight'}
exec(compile(_src, H + '/realfight.py', 'exec'), RF)
sys.argv = _argv
fight, monster_dps, monster_actions, MON, FIGHTS, meta = (RF['fight'], RF['monster_dps'], RF['monster_actions'],
                                                          RF['MON'], RF['FIGHTS'], RF['meta'])
TYPE_INDEX = RF['TYPE_INDEX']

FOCUS = ['knight_sns', 'knight_2h', 'minotaur_dual', 'vamp_knight', 'dk_vampire', 'dk_minotaur_dual', 'archer',
         'archmage', 'dragon', 'seraph', 'troll']
TARGETS = [('madness', 500), ('insanity', 500), ('doom', 500), ('madness', 200)]
SINGLE = ['hp', 'dmg', 'magic', 'phys', 'sustain', 'regen']
COMBOS = ['comboA', 'comboB', 'comboC', 'mon']
CAP = {'regen': 1000.0}            # bisection upper bound per lever (default 1000)
LO = {'regen': 0.01}               # lower bound (regen is additive % of HP/s)
ITER = 11


def load_cases(diffs):
    cases = collections.defaultdict(dict)
    for diff in diffs:
        for line in open(f'{H}/pool_out_{diff}.jsonl'):
            d = json.loads(line)
            m = meta[d['id']]
            cases[(m['build'], m['Lc'], m['diff'], m['seed'])][m['spell'] or 'none'] = (d, m)
    return cases


def scale(group, lever, k):
    out = {}
    for spell, (d, m) in group.items():
        d = copy.copy(d)
        hp_k = dmg_k = magic_k = phys_k = 1.0
        if lever in ('hp', 'comboA', 'comboB', 'comboC'):
            hp_k = k
        if lever in ('dmg', 'comboA', 'comboB', 'comboC', 'mon'):
            dmg_k = k
        if lever in ('magic', 'comboA', 'comboB', 'mon'):
            magic_k = 1/k
        if lever == 'comboC':
            magic_k = 0.5
        if lever in ('phys', 'comboB', 'mon'):
            phys_k = 1/k
        d['hp'] = d['hp']*hp_k
        for f in ('emp_melee_per_attack', 'breath_per_attack', 'ranged_dps', 'spell_dps'):
            d[f] = d[f]*dmg_k
        if magic_k != 1 or phys_k != 1:
            d['grid'] = {lv: [g[0], g[1]*phys_k] + [x*magic_k for x in g[2:]] for lv, g in d['grid'].items()}
        if lever == 'sustain':
            for f in ('regen_full', 'regen_half', 'leech_melee', 'leech_ranged', 'leech_spell'):
                d[f] = d[f]*k
        if lever == 'regen':
            add = d['hp']*k/100
            if d['regen_full'] > 0:
                ratio = d['regen_half']/d['regen_full']
                d['regen_full'] += add; d['regen_half'] = d['regen_full']*ratio
            else:
                d['regen_full'] = d['regen_half'] = add
        out[spell] = (d, m)
    return out


def case_groups(case):
    build, Lc, diff, seed = case
    gs = []
    for mp in FIGHTS.get(f'{diff}|{seed}|{Lc}', []):
        groups = collections.defaultdict(list)
        for a in mp['actors']:
            groups[a[4]].append(a)
        gs.extend(groups.values())
    return gs


def run(group, gs, metric, stop_fail=None):
    """Share of monsters beaten (no potions) and seconds per monster of the beaten groups.
    metric 'ok4': pulled four at a time; 'ok': whole group. stop_fail: stop once this share has failed."""
    total = sum(len(a) for a in gs)
    failed = 0; won = 0; t = 0.0
    for actors in sorted(gs, key=len, reverse=True):
        if metric == 'ok4':
            pulls = [fight(group, actors[i:i + 4], False) for i in range(0, len(actors), 4)]
            dead = any(p['dead'] for p in pulls); tt = sum(p['time'] for p in pulls)
        else:
            f = fight(group, actors, False)
            dead = f['dead']; tt = f['time']
        if dead:
            failed += len(actors)
            if stop_fail is not None and failed > stop_fail*total:
                return 1 - failed/total, None
        else:
            won += len(actors); t += tt
    return won/total, (t/won if won else None)


def pace_floor(group):
    return max(1.0, 1.1*min(a['rec'] for a in RF['player_attacks'](group)))


def passes(group, gs, target):
    if target in ('mash', 'mashR'):
        share, spm = run(group, gs, 'ok', 0.10 + 1e-9)
        return share >= 0.9 and spm is not None and spm <= (1.0 if target == 'mash' else pace_floor(group))
    share, _ = run(group, gs, target, 0.10 + 1e-9)
    return share >= 0.9


def bisect_job(job):
    case, lever, target, group = job
    gs = case_groups(case)
    lo, hi = LO.get(lever, 1.0), CAP.get(lever, 1000.0)
    if lever != 'regen' and passes(group, gs, target):
        return (case, lever, target, 1.0)
    if not passes(scale(group, lever, hi), gs, target):
        return (case, lever, target, math.inf)
    if lever == 'regen' and passes(scale(group, lever, lo), gs, target):
        return (case, lever, target, lo)
    for _ in range(ITER):
        mid = math.sqrt(lo*hi)
        if passes(scale(group, lever, mid), gs, target):
            hi = mid
        else:
            lo = mid
    return (case, lever, target, hi)


def eval_job(job):
    """Full metrics of one case at one setting: ok, ok4, spm (whole), spm4."""
    case, tag, lever, k, group = job
    gs = case_groups(case)
    g = scale(group, lever, k) if lever else group
    ok, spm = run(g, gs, 'ok')
    ok4, spm4 = run(g, gs, 'ok4')
    return (case, tag, dict(ok=ok, spm=spm, ok4=ok4, spm4=spm4))


def gap_job(job):
    """Baseline decomposition: incoming physical/magic share, time to kill vs time to die per group."""
    case, group = job
    d0, m0 = next(iter(group.values()))
    gs = case_groups(case)
    phys = magic = 0.0
    rows = []
    immortal = scale(group, 'hp', 1e9)
    for actors in gs:
        inc = 0.0
        for a in actors:
            tot = monster_dps(a, d0)
            # physical part: same formula with every magic column zeroed
            dz = dict(d0); dz['grid'] = {lv: [g[0], g[1]] + [0.0]*10 for lv, g in d0['grid'].items()}
            p = monster_dps(a, dz)
            phys += p; magic += tot - p; inc += tot
        ttk = fight(immortal, actors, False)['time']
        ttd = d0['hp']/inc if inc > 0 else math.inf
        rows.append(dict(n=len(actors), ttk=ttk, ttd=ttd, inc=inc/d0['hp']))
    n = sum(r['n'] for r in rows)
    # pulls of four: the first pull's incoming
    big = [r for r in rows if r['n'] >= 5]
    return (case, dict(phys_share=phys/(phys + magic) if phys + magic else 0, n=n,
                       ttk_per_mon=sum(r['ttk'] for r in rows)/n,
                       ratio_med=statistics.median(r['ttk']/r['ttd'] for r in rows),
                       ratio_big=statistics.median([r['ttk']/r['ttd'] for r in big]) if big else None,
                       ttd_med=statistics.median(r['ttd'] for r in rows),
                       inc_pct_med=statistics.median(100*r['inc'] for r in rows),
                       hp=d0['hp']))


def pool_map(fn, jobs):
    multiprocessing.set_start_method('fork', force=True)
    with multiprocessing.Pool(24) as p:
        return p.map(fn, jobs, chunksize=1)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'sweep'
    if mode == 'sweep':
        cases = load_cases(sorted({d for d, _ in TARGETS}))
        jobs = []
        for (b, Lc, diff, seed), g in cases.items():
            if b in FOCUS and (diff, Lc) in TARGETS:
                for lever in SINGLE:
                    for target in ('ok4', 'ok'):
                        jobs.append(((b, Lc, diff, seed), lever, target, g))
                for lever in COMBOS:
                    for target in ('ok4', 'ok', 'mash', 'mashR'):
                        jobs.append(((b, Lc, diff, seed), lever, target, g))
        jobs.sort(key=lambda j: j[0][1] != 500)    # heavy L500 first
        print(len(jobs), 'bisections', flush=True)
        res = pool_map(bisect_job, jobs)
        json.dump([[list(c), l, t, (None if math.isinf(k) else k)] for c, l, t, k in res],
                  open(H + '/power_gap_sweep.json', 'w'))
    elif mode == 'gap':
        cases = load_cases(sorted({d for d, _ in TARGETS} | {'nightmare'}))
        jobs = [(c, g) for c, g in cases.items() if c[0] in FOCUS and ((c[2], c[1]) in TARGETS or
                                                                       (c[2], c[1]) == ('nightmare', 500))]
        res = pool_map(gap_job, jobs)
        json.dump([[list(c), r] for c, r in res], open(H + '/power_gap_gap.json', 'w'))
    elif mode == 'probe':
        # settings: list of [tag, lever, k] in PROBE env (JSON); applied on all focus builds and listed difficulties
        settings = json.loads(os.environ['PROBE'])
        diffs = json.loads(os.environ.get('PROBE_DIFFS', '[["nightmare",500],["doom",500],["insanity",500],'
                                                         '["madness",500],["madness",200],["nightmare",200]]'))
        diffs = [tuple(x) for x in diffs]
        cases = load_cases(sorted({d for d, _ in diffs}))
        jobs = [(c, tag, lever, k, g) for c, g in cases.items() if c[0] in FOCUS and (c[2], c[1]) in diffs
                for tag, lever, k in settings]
        res = pool_map(eval_job, jobs)
        json.dump([[list(c), tag, r] for c, tag, r in res],
                  open(H + '/' + os.environ.get('PROBE_OUT', 'power_gap_probe.json'), 'w'))
    elif mode == 'tables':
        tables()


def tables():
    med = lambda v: sorted(v)[len(v)//2]
    inf = math.inf
    by = collections.defaultdict(list)
    for c, l, t, k in json.load(open(H + '/power_gap_sweep.json')):
        by[(c[0], c[2], c[1], l, t)].append(inf if k is None else k)
    gap = collections.defaultdict(list)
    for c, r in json.load(open(H + '/power_gap_gap.json')):
        gap[(c[0], c[2], c[1])].append(r)
    share = lambda b, d, L: statistics.median(x['phys_share'] for x in gap[(b, d, L)])

    def num(x):
        return f'{x:.2f}' if x < 10 else f'{x:.1f}' if x < 100 else f'{x:.0f}'

    def single(x, regen=False):
        return '—' if math.isinf(x) else 'ok' if x <= (0.011 if regen else 1.0001) else num(x)

    def power(l, k, s):
        return {'hp': k, 'dmg': k, 'magic': 1/(s + (1 - s)/k), 'phys': 1/(s/k + 1 - s),
                'comboA': k*k/(s + (1 - s)/k), 'comboB': k**3, 'comboC': k*k/(s + (1 - s)/2), 'mon': k*k}[l]

    for d, L in TARGETS:
        print(f'\n#### {d} L{L}: single levers\n')
        print('| build | phys share | HP ok4 | HP ok | dmg ok4 | dmg ok | magic ok4 | magic ok | phys ok4 | phys ok | '
              'sustain ok4 | sustain ok | regen %/s ok4 | regen %/s ok |')
        print('|' + '---|'*14)
        for b in FOCUS:
            cells = [single(med(by[(b, d, L, l, t)]), l == 'regen') for l in SINGLE for t in ('ok4', 'ok')]
            print(f'| {b} | {round(100*share(b, d, L))} % | ' + ' | '.join(cells) + ' |')
        print(f'\n#### {d} L{L}: combinations, k (P)\n')
        print('| build | A ok4 | A ok | A mash 1 s | A mash 1 swing | B ok4 | B ok | C ok4 | C ok | mon ok4 | mon ok | '
              'mon mash 1 swing |')
        print('|' + '---|'*12)
        for b in FOCUS:
            s = share(b, d, L)

            def c(l, t):
                k = med(by[(b, d, L, l, t)])
                if math.isinf(k):
                    return '—'
                if k <= 1.0001:
                    return 'ok'
                return f'{num(k)} ({power(l, k, s):.0f})' if power(l, k, s) >= 10 else f'{num(k)} ({power(l, k, s):.1f})'
            print(f'| {b} | ' + ' | '.join([c('comboA', 'ok4'), c('comboA', 'ok'), c('comboA', 'mash'),
                                            c('comboA', 'mashR'), c('comboB', 'ok4'), c('comboB', 'ok'),
                                            c('comboC', 'ok4'), c('comboC', 'ok'), c('mon', 'ok4'), c('mon', 'ok'),
                                            c('mon', 'mashR')]) + ' |')
    print('\n#### Time to kill vs time to die (today)\n')
    print('| difficulty | build | phys share | HP | incoming %HP/s (median group) | time to die, s | '
          'time to kill, s per monster | TTK/TTD median group | TTK/TTD groups of 5+ |')
    print('|' + '---|'*9)
    for d, L in [('madness', 500), ('insanity', 500), ('nightmare', 500), ('madness', 200)]:
        for b in FOCUS:
            l = gap[(b, d, L)]
            m = lambda k: statistics.median(x[k] for x in l if x[k] is not None)
            print(f"| {d} L{L} | {b} | {round(100*m('phys_share'))} % | {round(m('hp'))} | {m('inc_pct_med'):.0f} | "
                  f"{m('ttd_med'):.1f} | {m('ttk_per_mon'):.1f} | {m('ratio_med'):.1f} | {m('ratio_big'):.1f} |")
    probe = H + '/power_gap_probe.json'
    if os.path.exists(probe):
        pb = collections.defaultdict(list)
        tags = []
        for c, tag, r in json.load(open(probe)):
            pb[(c[0], c[2], c[1], tag)].append(r)
            if tag not in tags:
                tags.append(tag)
        for d, L in [('nightmare', 500), ('doom', 500), ('insanity', 500), ('madness', 500), ('nightmare', 200),
                     ('madness', 200)]:
            print(f'\n#### Probe {d} L{L}: ok4 % / ok % / s per monster (whole groups, beaten groups)\n')
            print('| build | ' + ' | '.join(tags) + ' |')
            print('|' + '---|'*(len(tags) + 1))
            for b in FOCUS:
                cells = []
                for t in tags:
                    l = pb[(b, d, L, t)]
                    spm = statistics.median([x['spm'] for x in l if x['spm'] is not None] or [0])
                    cells.append(f"{round(100*statistics.median(x['ok4'] for x in l))}/"
                                 f"{round(100*statistics.median(x['ok'] for x in l))}/{spm:.1f}")
                print(f'| {b} | ' + ' | '.join(cells) + ' |')


if __name__ == '__main__':
    main()
