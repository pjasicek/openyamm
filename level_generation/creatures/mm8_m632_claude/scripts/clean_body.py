"""Prepare the reviewed Dark Dwarf geometry and a temporary front/back texture for joint estimation."""
import bpy,sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import common
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert set(('P00','P01','P02','P03','P07','P08'))<=parts.keys()
for name,bottom,top in [('P01',.70,1.20),('P02',1.015,1.20),('P03',1.015,1.20)]:
    o=parts[name]
    old_bottom=min(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:
        if v.co.z<top:v.co.z=bottom+(v.co.z-old_bottom)*(top-bottom)/(top-old_bottom)
    if name=='P01':
        for v in o.data.vertices:
            v.co.y-=.085*max(0,min(1,(1.20-v.co.z)/.15))
    if name in ('P02','P03'):
        for v in o.data.vertices:
            t=max(0,min(1,(1.20-v.co.z)/.185))
            v.co.y-=.07*t
            v.co.x*=1-.4*t
    o.data.update()
    print('CLEAN hair',name,old_bottom,'->',bottom)
for o in bpy.data.objects:o.select_set(o in parts.values())
for name,o in parts.items():
    pid=int(name[1:])
    o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[pid]*len(o.data.vertices))
    o.data.materials.clear()
bpy.context.view_layer.objects.active=parts['P00']
bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body'
me=body.data
co=np.array([v.co[:] for v in me.vertices])
me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
# Upload texture is only a planar colour aid for pose estimation; final UVs are generated after deformation review.
image=bpy.data.images.load(str(P/'work/rig_reference_atlas.png'))
mat=bpy.data.materials.new('TemporaryPoseEstimation');mat.use_nodes=True
nodes=mat.node_tree.nodes
tex=nodes.new('ShaderNodeTexImage');tex.image=image
mat.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
me.materials.append(mat)
mat.diffuse_color=(.55,.55,.55,1)
uv=me.uv_layers.new(name='RigPreview')
for face in me.polygons:
    back=face.normal.y>0
    for li in face.loop_indices:
        v=me.vertices[me.loops[li].vertex_index].co
        u=(v.x/.594+1)*.5
        if back:u=1-u
        # Master alpha bounds preserve empty canvas margins.
        px=15+u*995
        py=1443-v.z/1.4*(1443-107)
        uv.data[li].uv=((px/1024+int(back))*.5,1-py/1536)
for face in me.polygons:face.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/m632_rig_input.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
common.workbench_clay(bpy.context.scene,False)
common.render_views(str(P/'review/clean_geometry'),.70,1.60,views=('front','three_quarter','left','back'),resolution=(800,800))
print('CLEAN complete',len(me.vertices),sum(len(f.vertices)-2 for f in me.polygons))
