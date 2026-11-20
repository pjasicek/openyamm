import re, json
S='/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/itemsdata/'
def load(path, enc='cp1252'):
    rows={}
    with open(path, encoding=enc, errors='replace') as f:
        for line in f:
            c=line.rstrip('\r\n').split('\t')
            if c and c[0].strip().isdigit():
                rows[int(c[0])]=c
    return rows
maw=load(S+'maw/ITEMS.txt'); base=load(S+'base/ITEMS.txt')
ours=load('/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/items.txt','utf-8')
EQ={'weapon':0,'weapon2':1,'weapon1or2':0,'missile':2,'bow':2,'armor':3,'shield':4,'helm':5,'belt':6,'cloak':7,'gauntlets':8,'boots':9,'ring':10,'amulet':11}
slotMult={0:1,1:2,2:1.25,3:1.5,4:1,5:1.25,6:1,7:1,8:1.25,9:1.25,10:0.75,11:1}
artWeap1h=[500,501,502,503,504,506,507,508,509,510,512,523,524,526,527,528,529,538,539,542,1302,1303,1304,1305,1308,1310,1311,1312,1316,1319,1328,1329,1330,1333,1340,1342,1343,1344,1345,1353,1354,2020,2021,2023,2025,2035,2036,2037,2038,2040,2118,1666,866]
artWeap2h=[505,511,525,530,540,541,1309,1320,1351,2022,2024,2039,1667,867]
artArmors=[513,514,515,516,517,518,520,522,533,534,1306,1307,1313,1314,1318,1321,1322,1323,1324,1326,1327,1331,1332,1334,1335,1336,1337,1346,1349,1350,1352,2026,2027,2028,2030,2031,2041,2042,2043,2045,2046]
twoHandedAxes=None
def mod1(c):
    s=c.strip()
    m=re.match(r'(\d+)d(\d+)',s)
    if m: return int(m.group(1)),int(m.group(2))
    try: return int(s),0
    except: return 0,0
def num(s):
    try: return int(s.strip())
    except: return 0
def uid(i): r=maw.get(i); return r[10].strip() if r and len(r)>10 else ''
def skill(i): r=maw.get(i); return r[5].strip() if r else ''
SK={'Staff':0,'Sword':1,'Dagger':2,'Axe':3,'Spear':4,'Bow':5,'Mace':6,'Blaster':7,'Shield':8,'Leather':9,'Chain':10,'Plate':11,'Misc':40}
hi=max(maw)
def refAC(i):
    look=0
    while i+look+1<=hi and uid(i)==uid(i+look+1): look+=1
    r=maw[i+look]; dc,_=mod1(r[6]); return num(r[7])+dc, i+look
def ladder(k):
    # find run of equal NotIdentifiedName containing k (buildLadder scans from 0 in runs)
    i=0
    while i<=hi:
        name=uid(i); last=i
        while last<hi and uid(last+1)==name: last+=1
        if i<=k<=last:
            span=last-i
            return (1+(k-i)/span*5) if span>0 else 3.5, (i,last)
        i=last+1
lst=[500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,533,534,535,536,537,542]+list(range(1302,1339))+list(range(2021,2050))
extra=[516,532,538,539,540,541,543,1339,1340,1341,1342,1343,1344,1345,1346,1347,1348,1349,1350,1351,1352,1353,1354,2020,866,867,1666,1667,2118]
out={}
for i in lst+extra:
    r=maw[i]; eq=EQ.get(r[4].strip().lower(),-1); sk=SK.get(r[5].strip(),-1)
    d=dict(name=r[2].strip(), eq=eq, eqname=r[4].strip(), skill=r[5].strip(), mod1=r[6].strip(), mod2=r[7].strip(), mat=r[8].strip(), uid=uid(i))
    sm=slotMult.get(eq,1)
    if eq==5 and num(r[7])==0: sm*=1.5
    d['slotMult']=sm
    d['artWeap']='1h' if i in artWeap1h else ('2h' if i in artWeap2h else None)
    d['artArmor']= i in artArmors
    isArmor = (8<=sk<=11) or sk==40
    if isArmor and eq!=12:
        ra,src=refAC(i); d['refAC']=ra; d['refAC_from']=src
    if eq in (0,1,2):
        lt,run=ladder(i); d['ladder']=round(lt,3); d['ladder_run']=run
    b=base.get(i); o=ours.get(i)
    d['base_mod']=(b[6].strip(),b[7].strip()) if b else None
    d['ours']=(o[2].strip(),o[4].strip(),o[5].strip(),o[6].strip(),o[7].strip(),o[8].strip(),o[3].strip(), len(o)) if o else None
    out[i]=d
json.dump(out, open(S+'artifacts/calc.json','w'), indent=0)
for i,d in out.items(): print(i,d)
