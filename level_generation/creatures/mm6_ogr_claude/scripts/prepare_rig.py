"""Preserve the native three fingers and tusks; remove only internal mouth and eye shells."""
from pathlib import Path
import bpy, numpy as np, runpy, sys
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
for n in ['P15','P16','P17','P22','P23']:
 bpy.data.objects.remove(parts.pop(n),do_unlink=True)
for o in bpy.data.objects: o.select_set(False)
for n,o in parts.items():
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(n[1:])]*len(o.data.vertices))
 o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00']
bpy.ops.object.join()
body=bpy.context.object
body.name=body.data.name='Body'
body.data.materials.clear()
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
# A packed neutral texture meets the rig service input contract; final art follows deformation review.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('OgreProvisional'); mat.use_nodes=True
tex=bpy.data.images.new('OgreProvisional',width=16,height=16)
tex.generated_color=(0.35,0.29,0.24,1); tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image=tex
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
assert len(parts)==32
assert len(body.data.uv_layers)==1
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
s=p/'scripts/source_rest.py'
sys.argv=[str(s),'--',str(p.parents[2]/'anim_library/humanoid_set/Armed.glb')]
runpy.run_path(str(s),run_name='__main__')
# The Ogre has thumb plus three fingers. Retarget the outer digit from the source pinky.
import json
f=p/'work/source_rest.json'
a=json.loads(f.read_text())
a={k:v for k,v in a.items() if not k.startswith(('B_L_Finger3','B_R_Finger3'))}
f.write_text(json.dumps(a,indent=1))
assert len([k for k in a if 'Finger' in k])==24
