"""Immutable accepted data and reduction-only gates for the staged runtime file."""
import sys,json,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction';sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
from merge_head_material import accessor_array
before,bb=read_glb(R/'baseline/export/mm6_lch.glb');after,ab=read_glb(P/'export/mm6_lch.glb')
assert before['nodes']==after['nodes']
assert before['materials']==after['materials']
assert before.get('extensions')==after.get('extensions')
assert len(before['skins'])==len(after['skins'])
for old,new in zip(before['skins'],after['skins']):
    assert {k:v for k,v in old.items()if k!='inverseBindMatrices'}=={k:v for k,v in new.items()if k!='inverseBindMatrices'}
    assert accessor_bytes(before,bb,old['inverseBindMatrices'])==accessor_bytes(after,ab,new['inverseBindMatrices'])
assert len(before['animations'])==len(after['animations'])
for old,new in zip(before['animations'],after['animations']):
    assert old['name']==new['name'] and old['channels']==new['channels']
    for a,b in zip(old['samplers'],new['samplers']):
        assert a.get('interpolation','LINEAR')==b.get('interpolation','LINEAR')
        for k in ['input','output']:assert accessor_bytes(before,bb,a[k])==accessor_bytes(after,ab,b[k]),(old['name'],k)
def pixels(doc,data):
    out=[]
    for im in doc['images']:
        v=doc['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
        out.append(hashlib.sha256(Image.open(io.BytesIO(data[off:off+v['byteLength']])).convert('RGBA').tobytes()).hexdigest())
    return out
assert pixels(before,bb)==pixels(after,ab)
assert (P/'integration/actors.yml').read_bytes()==(R/'baseline/integration/actors.yml').read_bytes()
rigs={};contacts={};baseline=json.loads((R/'lod_baseline_contacts.json').read_text())
for level in range(4):
    g=json.loads((R/f'lod_{level}_rig.json').read_text());c=json.loads((R/f'lod_{level}_contacts.json').read_text())
    assert len(g)==8 and len(c)==8
    for clip,values in g.items():
        assert max(values['g4_arm_edge_max'],values['g5_hand_edge_max'],values['whole_mesh_edge_max'])<1.001
    for clip,values in c.items():
        for part,value in values.items():
            if part.endswith('_cloth'):
                assert value==baseline[clip].get(part),(level,clip,part,value,baseline[clip].get(part))
            else:assert value[0]<=(1 if part=='head' else .2),(level,clip,part,value)
    rigs[level]={'g4_max':max(v['g4_arm_edge_max']for v in g.values()),'g5_max':max(v['g5_hand_edge_max']for v in g.values()),'whole_mesh_max':max(v['whole_mesh_edge_max']for v in g.values()),'floor_min_mm':min(v['lowest_vertex_m']for v in g.values())*1000}
    contacts[level]={'head_max_mm':max(v.get('head',[0])[0]for v in c.values())*10,'arms_hands_max_mm':max([value[0]*10 for v in c.values()for part,value in v.items()if part not in ['head','legs_cloth','hands_cloth']]+[0]),'cloth_equal_baseline':True}
# Nontrivial metric helper self-check: identity is exactly 1, an altered image is lower.
sys.path.insert(0,str(P/'scripts'));from round1_metrics import ssim
a=np.arange(40*40*3,dtype=np.uint8).reshape(40,40,3);assert abs(ssim(a,a)-1)<1e-12;assert ssim(a,np.zeros_like(a))<.98
report={'runtime_sha256':hashlib.sha256((P/'export/mm6_lch.glb').read_bytes()).hexdigest(),
    'nodes_rig_inverse_binds_animations_materials_tiers_image_pixels_actors_unchanged':True,
    'animation_sampler_bytes_equal':True,'image_pixel_hashes':pixels(after,ab),'rig_gates':rigs,'contacts':contacts,
    'reduction_regressions':False,
    'absolute_gate_status':'FAIL inherited Attack elbow hyperextension and cloth intersections; frozen accepted clips retained',
    'new_credits':0}
(R/'preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
