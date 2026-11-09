"""Preserve the selected geometry; label shells and export neutral joint-estimation input."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys,runpy
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert len(parts)==20
removed=[]
for name in ['P18','P19']:
    o=parts.pop(name);removed.append({'part':name,'triangles':len(o.data.polygons),'reason':'isolated two-face/one-face fragment behind collar/above forehead'})
    bpy.data.objects.remove(o,do_unlink=True)
for name,o in parts.items():
    o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(name[1:])]*len(o.data.vertices))
    o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
mat=bpy.data.materials.new('ClericRigNeutral');mat.use_nodes=True
tex=bpy.data.images.new('ClericRigNeutral',width=4,height=4);tex.pixels=[.55,.5,.45,1]*16;tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
assert len(body.data.vertices)>7000 and abs(co[:,2].max()-1.7)<1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
(p/'review/geometry/preparation.json').write_text(json.dumps({'removed':removed,'height_m':1.7,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'visual_review':'Native likeness, independent hands, five digits, covered feet, continuous robe and raised collar preserved; head/collar hair shell requires fitted weights.'},indent=2)+'\n')
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/geometry/prepared'),.85,1.9,views=('front','left','back','three_quarter'),resolution=(600,900))
s=p/'scripts/source_rest.py';sys.argv=[str(s),'--',str(p.parents[2]/'anim_library/humanoid_set/Armed.glb')];runpy.run_path(str(s),run_name='__main__')
