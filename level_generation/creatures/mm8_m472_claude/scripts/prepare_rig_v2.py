"""Keep the inspected Smart Topology parts and add only provisional rig-service UV/material data."""
from pathlib import Path
import bpy, numpy as np, runpy, sys
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/clean_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
for o in bpy.data.objects: o.select_set(False)
for n,o in parts.items():
    o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(n[1:])]*len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00']
bpy.ops.object.join()
body=bpy.context.object
body.name=body.data.name='Body'
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('NecromancerProvisional');mat.use_nodes=True
tex=bpy.data.images.new('NecromancerProvisional',width=16,height=16)
tex.generated_color=(0.35,0.29,0.24,1);tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
assert len(parts)==13 and len(body.data.uv_layers)==1
assert np.isfinite(co).all() and abs(co[:,2].min())<.002
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig_v2.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
for name,args in [('source_rest.py',['anim_library/humanoid_set/Armed.glb']),('proportions.py',['source','anim_library/humanoid_set/Armed.glb'])]:
    script=p/'scripts'/name;sys.argv=[str(script),'--',*args];runpy.run_path(str(script),run_name='__main__')
