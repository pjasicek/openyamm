"""Static body, hooded skull and bow uploads from the reduced animated master."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
piece=np.array([x.value for x in me.attributes['piece'].data]);head=[]
for f in me.polygons:
    ids=list(f.vertices);head.append(int(2000<=piece[ids[0]]<=2003 or
        (piece[ids[0]]<4000 and min(me.vertices[i].co.z for i in ids)>1.535)))
at=me.attributes.get('head')or me.attributes.new('head','INT','FACE');at.data.foreach_set('value',head)
for name in ['UVMap','HeadUV','BowUV']:
    if name not in me.uv_layers:me.uv_layers.new(name=name)
me.uv_layers.active=me.uv_layers['HeadUV']
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:f.select=bool(head[f.index])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012)
bpy.ops.uv.pack_islands(margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active=me.uv_layers['UVMap']
out=P/'texturing';out.mkdir(exist_ok=True);report={}
invbow=rig.data.bones['Bow'].matrix_local.inverted()
for kind,layer in [('body','UVMap'),('head','HeadUV'),('bow','BowUV')]:
    ob=body.copy();ob.data=me.copy();scene.collection.objects.link(ob);ob.parent=None
    ob.modifiers.clear();ob.vertex_groups.clear();bm=bmesh.new();bm.from_mesh(ob.data)
    pl=bm.verts.layers.int['piece'];hl=bm.faces.layers.int['head']
    def keep(f):
        pid=f.verts[0][pl]
        return (pid<4000)if kind=='body'else bool(f[hl])if kind=='head'else pid in [4000,4003,4004]
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep(f)],context='FACES')
    if kind=='bow':
        for v in bm.verts:
            v.co=(v.co+Vector((.25,0,-.30)))if v[pl]==4003 else invbow@v.co
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(ob.data);bm.free()
    for uv in list(ob.data.uv_layers):
        if uv.name!=layer:ob.data.uv_layers.remove(uv)
    ob.data.uv_layers.active=ob.data.uv_layers[layer]
    for attr in list(ob.data.attributes):
        if attr.name in ['head','piece','material_class']:ob.data.attributes.remove(attr)
    mat=bpy.data.materials.new('Neutral_'+kind);mat.use_nodes=True;ob.data.materials.clear();ob.data.materials.append(mat)
    for f in ob.data.polygons:f.material_index=0
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    path=out/f'm628_{kind}_upload.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_yup=True,
        export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
    report[kind]={'triangles':len(ob.data.polygons),'layer':layer,'path':str(path.relative_to(P))}
    bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_upload.blend'))
(P/'work/texture_uploads.json').write_text(json.dumps(report,indent=2));print('UPLOADS',report)
