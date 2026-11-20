import re,json
src=open('game/party/PartySpellSystem.cpp').read()
ids={}
for m in re.finditer(r'(\w+)\s*=\s*(\d+)',open('game/party/SpellIds.h').read()):
    ids[m.group(1)]=int(m.group(2))
start=src.index('std::optional<BackendSpellRule> resolveBackendSpellRule')
end=src.index('bool resolveSpellSkill',start)
body=src[start:end]
parts=re.split(r'case SpellId::(\w+):',body)
out={}
lineof=lambda name: src[:src.index('case SpellId::%s:'%name,start)].count('\n')+1
for i in range(1,len(parts),2):
    name=parts[i]; blk=parts[i+1]
    m=re.search(r'makeBackendSpellRule\((.*?)\);',blk,re.S)
    if not m: out[name]=None; continue
    a=' '.join(m.group(1).split())
    # split top-level commas
    args=[];depth=0;cur=''
    for ch in a:
        if ch in '({':depth+=1
        if ch in ')}':depth-=1
        if ch==',' and depth==0: args.append(cur.strip());cur=''
        else: cur+=ch
    args.append(cur.strip())
    out[name]=dict(id=ids.get(name),line=lineof(name),args=args[1:])
json.dump(out,open('%s/rules.json'%'/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/spells','w'),indent=0)
for k,v in out.items():
    if v: print(v['id'],k,v['line'],' | '.join(x.replace('PartySpellCastTargetKind::','T:').replace('PartySpellCastEffectKind::','E:').replace('SkillMastery::','').replace('PartyBuffId::','B:') for x in v['args']))
