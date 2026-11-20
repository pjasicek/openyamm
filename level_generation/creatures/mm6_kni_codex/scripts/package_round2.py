"""Replace only selected geometry; keep the accepted runtime skeleton, clips and materials."""
import sys,copy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2'
sys.path.insert(0,str(P.parents[2]/'tools'));sys.path.insert(0,str(P/'scripts'))
from merge_head_material import read_glb,write_glb,compact,append_accessor,accessor_array
import assemble_sword_round1 as A
import shrink_shadow_lods

def joints(d): return [d['nodes'][i]['name'] for i in d['skins'][0]['joints']]
def geometry(d,b,old,g,gb,new,skin=False):
    out=copy.deepcopy(old);attrs={}
    if skin:
        source,target=joints(g),joints(d);mapping=np.array([target.index(n)for n in source],np.uint16)
        ib=accessor_array(g,gb,g['skins'][0]['inverseBindMatrices']);ob=accessor_array(d,b,d['skins'][0]['inverseBindMatrices'])
        assert np.max(abs(ib-ob[mapping]))<1e-5
    for name,acc in new['attributes'].items():
        if name.startswith('_'):continue
        value=accessor_array(g,gb,acc);template=g['accessors'][acc]
        if name.startswith('JOINTS_'):
            value=mapping[value];template={'componentType':5123,'type':'VEC4'}
        attrs[name]=append_accessor(d,b,value,template,34962)
    out['attributes']=attrs;acc=new['indices'];out['indices']=append_accessor(d,b,accessor_array(g,gb,acc),g['accessors'][acc],34963)
    return out

for part,name,unchanged in [('body','mm6_kni',2),('sword','mm6_kni_sword',3)]:
    d,b=read_glb(W/f'baseline_{name}.glb')
    for lod in range(4):
        if lod==unchanged:continue
        g,gb=read_glb(W/f'geometry_{part}_l{lod}.glb');src=g['meshes'][0]['primitives'];dst=d['meshes'][lod]['primitives'];assert len(src)==len(dst)==1
        d['meshes'][lod]['primitives']=[geometry(d,b,dst[0],g,gb,src[0],part=='body')]
    if part=='body':
        for lod in range(4):
            q=copy.deepcopy(d['meshes'][lod]['primitives'][0]);acc=q['attributes']['POSITION']
            q['attributes']['POSITION']=append_accessor(d,b,accessor_array(d,b,acc),d['accessors'][acc],34962)
            d['meshes'][lod+4]['primitives']=[q]
    target=P/f'export/{name}.glb';write_glb(target,*compact(d,b))
    if part=='body':
        sys.argv=['shrink_shadow_lods.py',str(target),str(target)];shrink_shadow_lods.main()
A.attach(P/'export/mm6_kni.glb',P/'export/mm6_kni_sword.glb',W/'runtime_combined.glb')
# Each review tier retains its accepted baked texture and original animation arrays.
g,gb=read_glb(P/'export/mm6_kni.glb')
for tier in 'abc':
    d,b=read_glb(W/f'baseline_mm6_kni_{tier}.glb');q=d['meshes'][0]['primitives'][0]
    d['meshes'][0]['primitives']=[geometry(d,b,q,g,gb,g['meshes'][0]['primitives'][0],True)]
    tmp=W/f'viewer_body_{tier}.glb';write_glb(tmp,*compact(d,b));A.attach(tmp,P/'export/mm6_kni_sword.glb',P/f'review/viewer/mm6_kni_{tier}.glb')
m=json.loads((P/'review/viewer/manifest.json').read_text());m['revision']='mm6_kni_codex_triangle_round2'
for model in m['models']:
    name=f"mm6_{model['id']}.glb";model['sha256']=hashlib.sha256((P/'review/viewer'/name).read_bytes()).hexdigest();model['url']=name+'?v='+model['sha256'][:12];model['revision']=m['revision']
m['model_sha256']=m['models'][0]['sha256'];(P/'review/viewer/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
# Save combined exports at each LOD for contact checks; the static attachment is fitted independently.
for lod in range(1,4):
    bd,bb=read_glb(P/'export/mm6_kni.glb');wd,wb=read_glb(P/'export/mm6_kni_sword.glb');bd['meshes'][0]['primitives']=copy.deepcopy(bd['meshes'][lod]['primitives']);wd['meshes'][0]['primitives']=copy.deepcopy(wd['meshes'][lod]['primitives']);bp=W/f'contact_body_l{lod}.glb';wp=W/f'contact_sword_l{lod}.glb';write_glb(bp,bd,bb);write_glb(wp,wd,wb);A.attach(bp,wp,W/f'runtime_combined_l{lod}.glb')
print('Packaged geometry and three viewer tiers; original skeleton, clips, materials and tier maps retained.')
