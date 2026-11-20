import re, sys, os, glob
src = open('/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/General/zzMaw-Maps.lua', encoding='latin1').read().replace('\r','')
lines = src.split('\n')[284:751]
cur = None
entries = []
custom = []
for ln in lines:
    m = re.search(r'Map\.Name\s*==\s*"([^"]+)"', ln)
    if m:
        cur = m.group(1).lower(); continue
    m = re.search(r'addDungeonEntrance\((\d+),\s*"([^"]+)"\s*,\s*\{([^}]*)\}\s*(?:,\s*\{([^}]*)\})?', ln)
    if m:
        args = m.group(3)
        name = re.search(r'Name\s*=\s*"([^"]+)"', args)
        entries.append((cur, int(m.group(1)), m.group(2), name.group(1) if name else '', (m.group(4) or '').strip()))
        continue
    m = re.search(r'evt\.map\[(\d+)\]\s*=', ln)
    if m and cur:
        custom.append((cur, int(m.group(1))))
# load our events
base = '/home/pjasicek/github/OpenYAMM/assets_dev/worlds'
def find_lua(mapname):
    stem = mapname.rsplit('.',1)[0]
    for w in ('mm6','mm7','mm8'):
        p = f'{base}/{w}/events/maps/{stem}.lua'
        if os.path.exists(p): return w, p
    return None, None
def event_body(path, ev):
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'Register(?:Event|NoOpEvent)\(%d,.*?\n(?:.*?\n)*?end(?:, "[^"]*")?\)\n' % ev, txt)
    if not m:
        m2 = re.search(r'RegisterNoOpEvent\(%d,[^\n]*\n' % ev, txt)
        return m2.group(0) if m2 else None
    return m.group(0)
def overlays(path, ev):
    d = os.path.dirname(path); stem = os.path.basename(path)[:-4]
    hits = []
    for p in glob.glob(f'{d}/{stem}_*.lua'):
        t = open(p, encoding='utf-8', errors='replace').read()
        if re.search(r'(Replace|Append|Remove)MapEvent\(%d\b' % ev, t): hits.append(os.path.basename(p))
    return hits
out = []
for mapn, ev, dun, target, label in entries:
    w, p = find_lua(mapn)
    body = event_body(p, ev) if p else None
    flags = []
    if body is None: flags.append('NO-EVENT')
    else:
        stmts = [l.strip() for l in body.split('\n')[1:-2] if l.strip() and not l.strip().startswith('--')]
        nonmove = [s for s in stmts if not s.startswith('evt.MoveToMap') and s not in ('return','end')]
        if nonmove: flags.append('COND: ' + ' | '.join(nonmove)[:220])
        mt = re.findall(r'evt\.MoveToMap\(([^\n]*)\)', body)
        if mt and dun.split('.')[0].lower() not in ' '.join(mt).lower(): flags.append('TARGET-DIFF base=' + ';'.join(mt)[:120])
    ov = overlays(p, ev) if p else []
    if ov: flags.append('OVERLAY ' + ','.join(ov))
    out.append((mapn, ev, dun, target, label, w, flags))
for o in out:
    print('%-11s %4d %-12s %-4s %s' % (o[0], o[1], o[2], o[5], ' ; '.join(o[6])))
print('entries', len(entries), 'maps', len(set(e[0] for e in entries)))
print('custom evt.map in block:', custom)
print('---- coordinate comparison')
for ln in lines:
    pass
cur=None
for ln in lines:
    m = re.search(r'Map\.Name\s*==\s*"([^"]+)"', ln)
    if m: cur=m.group(1).lower(); continue
    m = re.search(r'addDungeonEntrance\((\d+),\s*"([^"]+)"\s*,\s*\{([^}]*)\}', ln)
    if not m: continue
    ev=int(m.group(1)); a=m.group(3)
    g=lambda k: (re.search(k+r'\s*=\s*(-?\d+)', a) or [None,None])[1]
    maw=(g('X'),g('Y'),g('Z'),g('Direction'),g('HouseId'),g('Icon'),(re.search(r'Name\s*=\s*"([^"]+)"',a) or [None,''])[1].lower())
    w,p=find_lua(cur); body=event_body(p,ev) if p else ''
    mt=re.findall(r'evt\.MoveToMap\(([^)]*)\)', body or '')
    if not mt: print(cur, ev, "no base move", p, len(body or "")); continue
    parts=[x.strip().strip('"') for x in mt[-1].split(',')]
    basev=(parts[0],parts[1],parts[2],parts[3],parts[6],parts[7],parts[8].lower())
    if tuple(map(str,maw))!=tuple(basev):
        print('%-10s %4d maw=%s base=%s' % (cur, ev, maw, basev))
