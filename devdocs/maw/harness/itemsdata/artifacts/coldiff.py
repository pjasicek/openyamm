import sys
sys.path.insert(0,'.')
S='/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/itemsdata/'
def load(path, enc='cp1252'):
    rows={}
    with open(path, encoding=enc, errors='replace') as f:
        for line in f:
            c=line.rstrip('\r\n').split('\t')
            if c and c[0].strip().isdigit():
                rows[int(c[0])]=c
    return rows
ours=load('/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/items.txt','utf-8')
maw=load(S+'maw/ITEMS.txt'); base=load(S+'base/ITEMS.txt')
H=['id','pic','name','value','equip','skill','mod1','mod2','material','idrep','uid','sprite','varA','varB','eqX','eqY','notes']
ids=[500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,533,534,535,536,537,542]+list(range(1302,1339))+list(range(2021,2050))+[516,532,538,539,540,541,543,1347,1348,1406,2020,2055]
for i in ids:
    o,m,b=ours[i],maw[i],base[i]
    for k in range(1,17):
        ov=o[k].strip() if k<len(o) else ''; mv=m[k].strip() if k<len(m) else ''; bv=b[k].strip() if k<len(b) else ''
        if ov.lower()!=mv.lower():
            if k==16: print(i,H[k],'ours==base' if ov==bv else 'ours!=base', '| ours:',ov[:90],'| maw:',mv[:200])
            else: print(i,H[k],'ours=',ov,'maw=',mv,'base=',bv)
