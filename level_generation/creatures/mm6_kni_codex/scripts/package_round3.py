"""Replace only selected geometry; keep the accepted runtime skeleton, clips and materials."""
import sys,copy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3'
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


from PIL import Image
T=P/'textures/round3'
im=Image.open(T/'knight_region_mask.png').convert('RGBA');a=np.array(im);a[:,:,2:]=0;Image.fromarray(a).save(T/'knight_region_mask.png')
for path in sorted(T.glob('knight_*.png')):
 im=Image.open(path);pixels=np.array(im);im.save(path,optimize=True,compress_level=9);assert np.array_equal(pixels,np.array(Image.open(path)))
def replace_image(d,b,index,path):
 raw=path.read_bytes();b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b.extend(raw);d['images'][index]['bufferView']=len(d['bufferViews'])-1;d['images'][index]['mimeType']='image/png'
d,b=read_glb(W/'baseline_mm6_kni.glb')
for lod in range(4):
 g,gb=read_glb(W/f'geometry_body_l{lod}.glb');d['meshes'][lod]['primitives']=[geometry(d,b,d['meshes'][lod]['primitives'][0],g,gb,g['meshes'][0]['primitives'][0],True)]
 q=copy.deepcopy(d['meshes'][lod]['primitives'][0]);acc=q['attributes']['POSITION'];q['attributes']['POSITION']=append_accessor(d,b,accessor_array(d,b,acc),d['accessors'][acc],34962);d['meshes'][lod+4]['primitives']=[q]
for i,key in enumerate(['normal','basecolor','metal_rough','region_mask']):replace_image(d,b,i,T/f'knight_{key}.png')

# Each tangent frame needs its own normal bake; every tier shares the same images for that LOD.
base_materials=copy.deepcopy(d['materials'])
for lod in range(1,4):
 raw=(T/f'knight_normal_l{lod}.png').read_bytes();b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b.extend(raw);d['images'].append({'name':f'KnightPlate_LOD{lod}_normal','bufferView':len(d['bufferViews'])-1,'mimeType':'image/png'});tex=copy.deepcopy(d['textures'][0]);tex['source']=len(d['images'])-1;d['textures'].append(tex);tex_index=len(d['textures'])-1
 offset=len(d['materials'])
 for mat in base_materials:
  m=copy.deepcopy(mat);m['name']+=f'_LOD{lod}';m['normalTexture']['index']=tex_index;d['materials'].append(m)
 for mesh_index in [lod,lod+4]:
  for q in d['meshes'][mesh_index]['primitives']:
   q['material']+=offset
   for mapping in q.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']+=offset

write_glb(P/'export/mm6_kni.glb',*compact(d,b));sys.argv=['shrink_shadow_lods.py',str(P/'export/mm6_kni.glb'),str(P/'export/mm6_kni.glb')];shrink_shadow_lods.main()
assert (P/'export/mm6_kni_sword.glb').read_bytes()==(W/'baseline_mm6_kni_sword.glb').read_bytes()
A.attach(P/'export/mm6_kni.glb',P/'export/mm6_kni_sword.glb',W/'runtime_combined.glb')
g,gb=read_glb(P/'export/mm6_kni.glb')
for tier in 'abc':
 d,b=read_glb(W/f'baseline_mm6_kni_{tier}.glb');q=d['meshes'][0]['primitives'][0];d['meshes'][0]['primitives']=[geometry(d,b,q,g,gb,g['meshes'][0]['primitives'][0],True)]
 for i,key in enumerate(['normal','basecolor','metal_rough','region_mask']):replace_image(d,b,i,T/f'knight_{key}.png')
 tex=d['materials'][q['material']]['pbrMetallicRoughness']['baseColorTexture']['index'];replace_image(d,b,d['textures'][tex]['source'],W/f'low_tier_{tier}.png')
 tmp=W/f'viewer_body_{tier}.glb';write_glb(tmp,*compact(d,b));A.attach(tmp,P/'export/mm6_kni_sword.glb',P/f'review/viewer/mm6_kni_{tier}.glb')
m=json.loads((P/'review/viewer/manifest.json').read_text());m['revision']='mm6_kni_codex_rebake_round3'
for model in m['models']:
 name=f"mm6_{model['id']}.glb";model['sha256']=hashlib.sha256((P/'review/viewer'/name).read_bytes()).hexdigest();model['url']=name+'?v='+model['sha256'][:12];model['revision']=m['revision']
m['model_sha256']=m['models'][0]['sha256'];(P/'review/viewer/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
for lod in range(1,4):
 bd,bb=read_glb(P/'export/mm6_kni.glb');wd,wb=read_glb(P/'export/mm6_kni_sword.glb');bd['meshes'][0]['primitives']=copy.deepcopy(bd['meshes'][lod]['primitives']);wd['meshes'][0]['primitives']=copy.deepcopy(wd['meshes'][lod]['primitives']);bp=W/f'contact_body_l{lod}.glb';wp=W/f'contact_sword_l{lod}.glb';write_glb(bp,bd,bb);write_glb(wp,wd,wb);A.attach(bp,wp,W/f'runtime_combined_l{lod}.glb')
print('Packaged rebaked body; sword, skeleton, clips, ramps and bindings preserved.')
