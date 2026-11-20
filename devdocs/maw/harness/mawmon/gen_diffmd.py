import json, textwrap
md=json.load(open('mon_diff.json')); mp=json.load(open('map_diff.json'))
LBL={3:'Level',4:'HP',5:'AC',6:'EXP',7:'Treasure',15:'Pref',16:'Special atk',17:'Atk1 type',18:'Atk1 dmg',
     20:'Atk2 %',21:'Atk2 type',22:'Atk2 dmg',24:'Spell1 %',25:'Spell1',26:'Spell2 %',27:'Spell2',38:'Special'}
def clean(v): 
    v=v.strip()
    return v if v else "''"
def num(s):
    s=s.strip().strip('"').strip().replace(',','')
    try: return float(s)
    except: return None
def cosmetic(i,a,b):
    if i in (4,6) and num(a)==num(b): return True
    if i in (25,27) and a.replace(' ','').lower()==b.replace(' ','').lower(): return True
    return False
def tier(i): return {1:'A',2:'B',0:'C'}[i%3]
def wrapline(prefix, text, width=118):
    return textwrap.fill(text, width=width, initial_indent=prefix, subsequent_indent=' '*len(prefix),
                         break_long_words=False, break_on_hyphens=False)
def rowline(r):
    parts=[]
    for i,c,a,b,o in r['diffs']:
        lab=LBL.get(i,c)
        s=f"{lab} {clean(a)} -> {clean(b)}"
        if cosmetic(i,a,b): s+=' (format only)'
        parts.append(s)
    return wrapline('- ', f"`{r['id']}` {r['name']} ({tier(r['id'])}): " + '; '.join(parts))
groups={'regnan':[],'rework':[],'treasure':[],'expflags':[],'cosmetic':[],'other':[]}
for r in md:
    cols={i for i,*_ in r['diffs'] if not cosmetic(i,r['diffs'][[d[0] for d in r['diffs']].index(i)][2],r['diffs'][[d[0] for d in r['diffs']].index(i)][3])}
    if 10<=r['id']<=18: groups['regnan'].append(r)
    elif not cols: groups['cosmetic'].append(r)
    elif 3 in cols or 5 in cols or 4 in cols: groups['rework'].append(r)
    elif cols<= {7}: groups['treasure'].append(r)
    elif cols<= {6,15,16,17,18,22,24}: groups['expflags'].append(r)
    else: groups['other'].append(r)
print({k:len(v) for k,v in groups.items()})
print([r['id'] for r in groups['other']])
json.dump({k:[r['id'] for r in v] for k,v in groups.items()}, open('groups.json','w'))
out=[]
for k in ('regnan','treasure','rework','expflags','cosmetic','other'):
    out.append(f'### {k}')
    for r in groups[k]: out.append(rowline(r))
open('mon_rows.md','w').write('\n'.join(out)+'\n')
# map rows
MLBL={1:'Name',11:'Treasure lvl',16:'Mon1 pic',17:'Mon1 label',18:'Mon1 dif',19:'Mon1 count',20:'Mon2 pic',
      21:'Mon2 label',22:'Mon2 dif',23:'Mon2 count',24:'Mon3 pic',25:'Mon3 label',26:'Mon3 dif',27:'Mon3 count'}
tres=[];pool=[];label=[];other=[]
for r in mp:
    cols={i for i,*_ in r['diffs']}
    t=[d for d in r['diffs'] if d[0]==11]
    if t: tres.append((r['id'],r['extra'],r['name'],t[0][2],t[0][3]))
    rest=[d for d in r['diffs'] if d[0]!=11]
    if not rest: continue
    eff=[d for d in rest if d[0] not in (17,21,25)]
    s='; '.join(f"{MLBL[i]} {clean(a)} -> {clean(b)}" for i,c,a,b,o in rest)
    line=wrapline('- ', f"`{r['id']}` {r['extra']} {r['name'].strip()}: {s}")
    (pool if eff and any(d[0]!=1 for d in eff) else (other if eff else label)).append(line)
lines=['### tres']
# treasure: compact table rows
lines.append('| id | file | name | base | id | file | name | base |')
lines.append('|---|---|---|---|---|---|---|---|')
half=(len(tres)+1)//2
for a,b in zip(tres[:half], tres[half:]+[None]):
    def c(x): return f"{x[0]} | {x[1]} | {x[2].strip()} | {x[3]}" if x else ' | | | '
    lines.append(f"| {c(a)} | {c(b)} |")
lines.append('### pool'); lines+=pool
lines.append('### label'); lines+=label
lines.append('### other'); lines+=other
open('map_rows.md','w').write('\n'.join(lines)+'\n')
print(len(tres),len(pool),len(label),len(other))
