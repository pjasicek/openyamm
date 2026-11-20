"""Measure the concrete solo rules of SOLO_RULES.md with realfight.py against the route's real monster groups.

Loads realfight.py (everything before its main block) with two source patches that the rules need:
  - the leech floor's divisor 5 becomes LEECH_DIV (MAW: heal >= max HP x leech / 5 x recovery / 100, Damage.lua:1250);
  - after the flat cut, each landed monster hit passes GUARD(after, d) (the one-shot guard).
Each rule set is a per-build transform of the harness rows (pool_out_<difficulty>.jsonl). Potions are off.

Usage: python3 solo_rules_check.py [difficulty,...] [stage]   -> prints a Markdown table, writes solo_rules_check.json
Default: madness,insanity,doom at stage 500.
"""
import json, os, sys, copy, collections, statistics, multiprocessing

H = os.environ.get('SOLO_SIM_DIR') or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'output', 'maw_solo_sim'))

_src = open(H + '/realfight.py').read().split("if __name__ == '__main__':")[0]
_old_floor = "full*a['leech']/5*a['rec']"
_old_flat = "            after = max(after - flat, 0.25*after)\n"
assert _src.count(_old_floor) == 1 and _src.count(_old_flat) == 1
_src = _src.replace(_old_floor, "full*a['leech']/LEECH_DIV*a['rec']")
_src = _src.replace(_old_flat, _old_flat + "        after = GUARD(after, d)\n")
# A sweeping blow is still the melee blow: it carries the Seraph's heal on hit.
_old_heal = "if a['kind'] == 'melee' and class_heal:"
assert _src.count(_old_heal) == 1
_src = _src.replace(_old_heal, "if a['kind'] in ('melee', 'sweep') and class_heal:")
_argv = sys.argv
sys.argv = ['realfight.py', H, 'unused.jsonl']
RF = {'__name__': 'realfight', 'LEECH_DIV': 5, 'GUARD': lambda after, d: after}
exec(compile(_src, H + '/realfight.py', 'exec'), RF)
sys.argv = _argv
meta, FIGHTS, fight = RF['meta'], RF['FIGHTS'], RF['fight']

BUILDS = ['knight_sns', 'knight_2h', 'minotaur_dual', 'troll_knight', 'vamp_knight', 'monk', 'dk_vampire',
          'dk_minotaur_dual', 'seraph', 'troll', 'dragon', 'archer']

# R1 Lone Discipline: Bodybuilding to Grandmaster. HP multipliers from TALENTS_AND_PROGRESSION.md M2 (stage 500,
# the classes MAW caps at Expert); every other build here already has Grandmaster.
BB_GM = {'dk_vampire': 2.4, 'dk_minotaur_dual': 2.4, 'dk_minotaur': 2.4, 'seraph': 2.4, 'archmage': 1.6}
# Legend points (TALENTS M5): 150 points at stage 500, 300 at the end of Beyond Madness.
LP = {0: (1, 1, 1), 150: (1.5, 1.5, 0.78), 300: (2.0, 2.0, 0.61)}


def guard_30(after, d):
    """R3 Unbroken: the part of one landed hit above 30 % of max HP is halved."""
    cap = 0.30*d['hp']
    return after if after <= cap else cap + (after - cap)/2


# Cumulative rule sets: (Bodybuilding GM, leech add, floor divisor, guard, Lone Guard, Sweeping Blows, Legend points).
_BASE = dict(bb=False, leech=0.0, div=5, guard=None, lone_guard=False, sweep=False, lp=0)
RULES = {}
for name, change in [('today', {}), ('R1', dict(bb=True)), ('+R2', dict(leech=0.05, div=2.5)),
                     ('+R3', dict(guard=guard_30)), ('+R4', dict(lone_guard=True)), ('+R5', dict(sweep=True)),
                     ('+LP150', dict(lp=150)), ('+LP300', dict(lp=300))]:
    _BASE = dict(_BASE, **change)
    RULES[name] = _BASE

# R4 Lone Guard (TALENTS M1): a class's own earned cuts act after the floor. (physical, magic) taken multipliers.
LONE_GUARD = {'dk_vampire': (0.59, 0.59), 'dk_minotaur_dual': (0.59, 0.59), 'knight_sns': (0.85, 0.85)}
# R5 Sweeping Blows (TALENTS M3): a melee blow also strikes the others near the target for C of its damage.
SWEEP_C = 0.6


def transform(group, build, rule):
    r = RULES[rule]
    h_lp, d_lp, t_lp = LP[r['lp']]
    tp, tm = LONE_GUARD.get(build, (1, 1)) if r['lone_guard'] else (1, 1)
    out = {}
    for spell, (d, m) in group.items():
        d = copy.deepcopy(d)
        h = (BB_GM.get(build, 1.0) if r['bb'] else 1.0)*h_lp
        d['hp'] *= h; d['regen_full'] *= h; d['regen_half'] *= h
        for f in ('emp_melee_per_attack', 'breath_per_attack', 'ranged_dps', 'spell_dps', 'seraph_heal'):
            d[f] *= d_lp
        if t_lp != 1 or tp != 1 or tm != 1:
            d['grid'] = {lv: [g[0], g[1]*t_lp*tp] + [x*t_lp*tm for x in g[2:]] for lv, g in d['grid'].items()}
        for f in ('leech_melee', 'leech_ranged', 'leech_spell'):
            d[f] += r['leech']
        out[spell] = (d, m)
    return out


_player_attacks = RF['player_attacks']


def _attacks_with_sweep(group):
    attacks = _player_attacks(group)
    if SWEEP_ON[0]:
        melee = next(a for a in attacks if a['kind'] == 'melee')
        attacks.append(dict(melee, kind='sweep', aoe=True, dmg=melee['dmg']*(1 + 2*SWEEP_C)/3))
    return attacks


SWEEP_ON = [False]
RF['player_attacks'] = _attacks_with_sweep


def groups_of(diff, seed, Lc):
    gs = []
    for mp in FIGHTS.get(f'{diff}|{seed}|{Lc}', []):
        g = collections.defaultdict(list)
        for a in mp['actors']:
            g[a[4]].append(a)
        gs.extend(g.values())
    return gs


def job(args):
    case, rule, group = args
    build, Lc, diff, seed = case
    RF['LEECH_DIV'] = RULES[rule]['div']
    RF['GUARD'] = RULES[rule]['guard'] or (lambda after, d: after)
    SWEEP_ON[0] = RULES[rule]['sweep'] and build not in ('archer', 'dragon')
    g = transform(group, build, rule)
    gs = groups_of(diff, seed, Lc)
    total = sum(len(a) for a in gs)
    res = {}
    for metric in ('ok4', 'ok'):
        won = 0; t = 0.0
        for actors in gs:
            if metric == 'ok4':
                pulls = [fight(g, actors[i:i + 4], False) for i in range(0, len(actors), 4)]
                dead = any(p['dead'] for p in pulls); tt = sum(p['time'] for p in pulls)
            else:
                f = fight(g, actors, False); dead = f['dead']; tt = f['time']
            if not dead:
                won += len(actors); t += tt
        res[metric] = won/total if total else 0
        res['spm' if metric == 'ok' else 'spm4'] = t/won if won else None
    return case, rule, res


def main():
    diffs = (sys.argv[1] if len(sys.argv) > 1 else 'madness,insanity,doom').split(',')
    stage = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    cases = collections.defaultdict(dict)
    for diff in diffs:
        for line in open(f'{H}/pool_out_{diff}.jsonl'):
            d = json.loads(line); m = meta[d['id']]
            if m['build'] in BUILDS and m['Lc'] == stage:
                cases[(m['build'], m['Lc'], m['diff'], m['seed'])][m['spell'] or 'none'] = (d, m)
    jobs = [(c, r, g) for c, g in cases.items() for r in RULES]
    with multiprocessing.Pool() as pool:
        results = pool.map(job, jobs, chunksize=1)
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for (build, Lc, diff, seed), rule, res in results:
        agg[(diff, build)][rule].append(res)
    out = {}
    for diff in diffs:
        print(f'\n### {diff}, stage {stage}: pulls of four % / s per monster; whole groups %\n')
        print('| Build | ' + ' | '.join(RULES) + ' |')
        print('|---|' + '---|'*len(RULES))
        for build in BUILDS:
            cells = []
            for rule in RULES:
                rs = agg[(diff, build)][rule]
                if not rs:
                    cells.append('–'); continue
                ok4 = statistics.median(r['ok4'] for r in rs); ok = statistics.median(r['ok'] for r in rs)
                spm = [r['spm4'] for r in rs if r['spm4']]
                s = f'{statistics.median(spm):.1f}' if spm else '–'
                cells.append(f'{ok4*100:.0f} / {s}; {ok*100:.0f}')
                out[f'{diff}|{build}|{rule}'] = dict(ok4=ok4, ok=ok, spm4=statistics.median(spm) if spm else None)
            print(f'| {build} | ' + ' | '.join(cells) + ' |')
    json.dump(out, open(f'{H}/solo_rules_check.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
