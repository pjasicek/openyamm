import re, sys
def split_top(s):
    out=[];depth=0;cur='';inq=False
    for ch in s:
        if ch=='"' : inq=not inq
        if not inq and ch=='{': depth+=1
        if not inq and ch=='}': depth-=1
        if ch==',' and depth==0 and not inq:
            out.append(cur.strip()); cur=''
        else: cur+=ch
    if cur.strip(): out.append(cur.strip())
    return out
def wrap(path):
    res=[]
    for line in open(path).read().split('\n'):
        if len(line)<=120: res.append(line); continue
        m=re.match(r'^(\s*)([^:#]+):\s*\{(.*)\}(\s*#.*)?$', line)
        if not m: res.append(line); continue
        ind,key,body,com=m.groups()
        res.append(f'{ind}{key}:' + (f'  {com.strip()}' if com else ''))
        for part in split_top(body):
            res.append(f'{ind}  {part}')
    open(path,'w').write('\n'.join(res))
for p in sys.argv[1:]: wrap(p)
