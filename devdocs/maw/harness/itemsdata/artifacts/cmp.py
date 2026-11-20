import sys, json
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
lst=[500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,533,533,534,535,536,537,542]+list(range(1302,1339))+list(range(2021,2050))
extra=[516,532,538,539,540,541,543,1309,1310,1311,1315,1339,1340,1341,1342,1343,1344,1345,1346,1347,1348,1349,1350,1351,1352,1353,1354,2020,2055,1406,866,867,1666,1667]
ids=sorted(set(lst+extra))
g=lambda r,i: r[i].strip() if r and len(r)>i else None
for i in ids:
    o=ours.get(i); m=maw.get(i); b=base.get(i)
    print(i, 'IN' if i in lst else 'EX', '|', g(o,2),'|',g(m,2),'|',g(b,2),'| eq',g(o,4),g(m,4),'| sk',g(o,5),g(m,5),'| mod',g(o,6),g(o,7),'/',g(m,6),g(m,7),'| mat',g(o,8),g(m,8),'| val',g(o,3),g(m,3),'| uid',g(o,10),'|',g(o,17),g(o,18),g(o,19),g(o,20))
