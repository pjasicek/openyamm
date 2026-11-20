import re, json
M='/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/'
items=open(M+'General/zzMaw-Items.lua',encoding='utf-8',errors='replace').read().split('\n')
arts=open(M+'General/zzzMaw_Artifacts.lua',encoding='utf-8',errors='replace').read().split('\n')
def blocks(lines, prefix, start=0, end=None):
    out={}
    end=end or len(lines)
    i=start
    while i<end:
        m=re.match(r'^\s*'+re.escape(prefix)+r'\[(\d+)\]\s*=\s*\{',lines[i])
        if m:
            depth=0; j=i; text=''
            while True:
                l=re.sub(r'--.*$','',lines[j]); text+=l+'\n'
                depth+=l.count('{')-l.count('}')
                if depth<=0: break
                j+=1
            out[int(m.group(1))]=(i+1,j+1,text)
            i=j+1
        else: i+=1
    return out
ap=blocks(items,'artifactPower',3505,3835)
res={}
for k,(a,b,t) in ap.items():
    sk=re.search(r'Skills\s*=\s*\{([^}]*)\}',t); fl=re.search(r'Flat\s*=\s*\{([^}]*)\}',t)
    t2=t
    for g in (sk,fl):
        if g: t2=t2.replace(g.group(0),'')
    stats=[(n,v) for n,v in re.findall(r'\[const\.Stats\.(\w+)\]\s*=\s*(-?[\d.]+)',t2)]
    skills=[(n,v) for n,v in re.findall(r'\[const\.Skills\.(\w+)\]\s*=\s*(-?[\d.]+)',sk.group(1))] if sk else []
    flat=[(n,v) for n,v in re.findall(r'\[const\.Stats\.(\w+)\]\s*=\s*(-?[\d.]+)',fl.group(1))] if fl else []
    bsm=re.search(r'baseStatMultiplier\s*=\s*([\d.]+)',t2)
    res[k]=dict(lines=[a,b],stats=stats,skills=skills,flat=flat,bsm=bsm.group(1) if bsm else None)
oh=blocks(arts,'artifactOnHit')
onhit={}
for k,(a,b,t) in oh.items():
    d=dict(lines=[a,b])
    m=re.search(r'DamageKind\s*=\s*const\.Damage\.(\w+)',t); d['kind']=m.group(1) if m else None
    m=re.search(r'Damage\s*=\s*([\d.]+)',t); d['damage']=m.group(1) if m else None
    d['multvs']=re.findall(r'\[const\.MonsterKind\.(\w+)\]\s*=\s*([\d.]+)',t)
    d['vamp']='Vampiric = true' in t
    m=re.search(r'Text\s*=\s*"([^"]*)"',t); d['text']=m.group(1) if m else None
    d['onhit']='OnHit' in t
    onhit[k]=d
print('artifactPower entries',len(res),sorted(res))
print('onhit entries',len(onhit),sorted(onhit))
json.dump(dict(power=res,onhit=onhit),open('parsed.json','w'),indent=1)
lst=[int(x) for x in re.search(r'^mawArtifacts=\{([^}]*)\}',items[4480]).group(1).split(',')]
print('list',len(lst),len(set(lst)))
L=set(lst)
print('list without power', sorted(L-set(res)))
print('power not in list', sorted(set(res)-L))
print('onhit not in list', sorted(set(onhit)-L))
