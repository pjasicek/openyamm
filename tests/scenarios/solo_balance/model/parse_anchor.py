import os
import re, glob, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
res = []
for f in sorted(glob.glob(ROOT + '/output/solo_balance/logs/anchor_*.log')):
    txt = re.sub(r'\x1b\[[0-9;]*m', '', open(f, errors='replace').read())
    diff, stage = re.match(r'.*anchor_(\w+?)_(\w+)\.log', f).groups()
    ok = 'Scenario passed' in txt
    blocks = re.split(r'RUN step \d+/\d+ load_map yaml_line=\d+ map=', txt)[1:]
    for b in blocks:
        m = b.split()[0]
        sheet = re.search(r'level (\d+), might (\d+).*?attack (\d+) damage ([\d -]+), shoot', b)
        rep = re.search(r'attacks=(\d+) hits=(\d+) crits=(\d+) weapon_attacks=\d+ average_damage=([\d.]+) average_applied=([\d.]+) average_recovery=([\d.]+)', b)
        if rep is None: continue
        hps = [tuple(map(int, x)) for x in re.findall(r'Lone HP (-?\d+)/(\d+)', b)]
        # hp shows: [0] sheet show, then 5 windows (1,1,1,3,3)
        wins = hps[1:6]
        maxhp = hps[0][1]
        lost = [maxhp - h if h > 0 else None for h, _ in wins]  # None: died (censored)
        res.append(dict(diff=diff, stage=stage, map=m, ok=ok, level=int(sheet.group(1)) if sheet else None,
                        sheet=sheet.group(4).strip() if sheet else None, maxhp=maxhp,
                        attacks=int(rep.group(1)), hits=int(rep.group(2)), crits=int(rep.group(3)),
                        dmg=float(rep.group(4)), applied=float(rep.group(5)), rec=float(rep.group(6)),
                        win1=lost[:3], win3=lost[3:5]))
json.dump(res, open(os.path.join(ROOT, 'output/solo_balance/anchors.json'), 'w'), indent=1)
for r in res:
    dps = r['applied'] * r['hits'] / r['attacks'] / r['rec']
    def rate(ws, s):
        v = [x for x in ws if x is not None]
        dead = sum(1 for x in ws if x is None)
        return (sum(v) / len(v) / s if v else float('nan')), dead
    i1, d1 = rate(r['win1'], 1); i3, d3 = rate(r['win3'], 3)
    print(f"{r['diff']:9} {r['stage']:8} {r['map']:10} L{r['level']} HP{r['maxhp']:6} hit {r['hits']/r['attacks']:.2f} dmg {r['applied']:7.0f} rec {r['rec']:.2f} DPS {dps:7.0f} | in1 {i1:7.0f}/s dead{d1} in3 {i3:7.0f}/s dead{d3} | win1 {r['win1']} win3 {r['win3']}")
