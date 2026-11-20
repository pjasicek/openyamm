import math, json
def step(L): return 1000*L*max(1+(L-100)*0.01,1)
req=[0,0]
for L in range(2,2001): req.append(req[L-1]+step(L-1))
def calcExp(L):
    if L<=1: return 0
    if L>=2000: return req[2000]+(L-2000)*step(2000)
    b=math.floor(L); return req[b]+(L-b)*step(b)
def calcLevel(x):
    if x<=0: return 1
    if x>=req[2000]: return 2000+(x-req[2000])/step(2000)
    lo,hi=1,2000
    while hi-lo>1:
        mid=(lo+hi)//2
        if req[mid]<=x: lo=mid
        else: hi=mid
    return lo+(x-req[lo])/step(lo)
def bolstered(f,n):
    f=max(f,0)
    if n<=0: return f+n
    t=f+n
    return calcLevel(calcExp(f)+500*(t*(t-1)-f*(f-1)))
assert abs(bolstered(100,30)-126.817)<1e-3 and abs(bolstered(500,100)-521.118)<1e-3
def rnd(x): return math.floor(x)+1 if x%1>=0.5 else math.floor(x)
mon={}
for ln in open('zmawT/MONSTERS.txt',encoding='latin1').read().replace('\r','').split('\n'):
    c=ln.split('\t')
    if c and c[0].strip().isdigit(): mon[int(c[0])]=(c[1],c[2].strip(),int(c[3]))
maps={}
for ln in open('zmawT/mapstats.txt',encoding='latin1').read().replace('\r','').split('\n'):
    c=ln.split('\t')
    if c and c[0].strip().isdigit(): maps[c[2].strip()]=(c[1],[c[16].strip(),c[20].strip(),c[24].strip()])
import yaml
ML=yaml.safe_load(open('/home/pjasicek/github/OpenYAMM/devdocs/maw/data/map_levels.yml'))
def resolve(fname, party_bolster, mode, starter=False, reset=0, madness=None):
    name,pics=maps[fname]; mp=ML['map_levels'][fname]
    lo,mi,hi=mp['low'],mp['mid'],mp['high']; mean=(lo+mi+hi)/3
    natives=[]
    for i in range(1,652):          # MAW gathers in monster-id order (zzMaw-Monsters.lua:450-458)
        for p in pics:
            if mon[i][1]==p+' B': natives.append(i)
    natives.sort(key=lambda i: mon[i][2])   # stable, like MAW's 3-element bubble sort
    out={}
    for b in natives:
        for i in (b-1,b,b+1):
            base=mon[i][2]; LB=mon[b][2]
            j=natives.index(b)+1
            if j==1: X=lo
            elif j==2 and len(natives)==3: X=mi
            else: X=hi
            extra=X-LB; adjust=(mean-X)*(1 if madness else 1.5)
            bl=max(party_bolster,0)+reset
            if mode=='free': L=bolstered(bl, base+extra)
            elif mode=='horizontal' and starter: L=max(min((base+extra)*2.5, bolstered(bl+reset, base+extra)),1)
            elif mode=='horizontal': L=max(base*2.5+extra*2.5-5-(base-LB)*1.5+adjust-4+reset,5)
            elif mode=='madness':
                off=(X-mean)*2+(base-LB)*2
                L=bolstered(madness,off) if off>=0 else 2*madness-bolstered(madness,-off)
                L=max(L,5)
            out[i]=(mon[i][0],base,X,rnd(max(L,1)))
    return name,natives,out
for args in (('out02.odm',0,'free'),('out02.odm',96,'free'),('out02.odm',0,'horizontal'),('out02.odm',0,'horizontal',False,20),
             ('7d29.blv',96,'horizontal',True),('6d03.blv',0,'madness',False,0,43)):
    name,nat,out=resolve(*args)
    print(args, name)
    for i,v in out.items(): print('  ',i,v)
