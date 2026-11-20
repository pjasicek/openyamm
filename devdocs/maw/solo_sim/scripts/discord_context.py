import re, sys
lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
kw = re.compile(sys.argv[3], re.I); n = int(sys.argv[4])
keep=set()
for i,l in enumerate(lines):
    if kw.search(l[17:]):
        keep.update(range(max(0,i-n), min(len(lines), i+n+1)))
out=[lines[i] for i in sorted(keep)]
open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(out)); print(len(out), sum(map(len,out)))
