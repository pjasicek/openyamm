"""Preserve source shading coordinates and prepare an isolated practical mesh/UV layout for material baking."""
import bpy
import math
import json
import sys
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import active,apply
SCENE='MM6 Goblin export studio'

def freeze_coordinates(obj):
    mesh=obj.data
    coords=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
    low=coords.min(axis=0);span=np.maximum(coords.max(axis=0)-low,.000001)
    if mesh.attributes.get('SourceGenerated') is None:
        attr=mesh.attributes.new(name='SourceGenerated',type='FLOAT_VECTOR',domain='POINT')
        attr.data.foreach_set('vector',((coords-low)/span).astype(np.float32).reshape(-1))
    default=mesh.uv_layers.active.name if mesh.uv_layers.active else None
    for uv in list(mesh.uv_layers):
        values=np.empty(len(mesh.loops)*2,dtype=np.float32);uv.data.foreach_get('uv',values)
        vectors=np.zeros((len(mesh.loops),3),dtype=np.float32);vectors[:,:2]=values.reshape(-1,2)
        names=['SourceUV '+uv.name]
        if uv.name==default:names.append('SourceDefaultUV')
        for name in names:
            attr=mesh.attributes.new(name=name,type='FLOAT_VECTOR',domain='CORNER')
            attr.data.foreach_set('vector',vectors.reshape(-1))
        mesh.uv_layers.remove(uv)

def freeze_material(mat):
    n=mat.node_tree.nodes;l=mat.node_tree.links
    generated=n.new('ShaderNodeAttribute');generated.attribute_name='SourceGenerated'
    uv=n.new('ShaderNodeAttribute');uv.attribute_name='SourceDefaultUV'
    for node in list(n):
        if node.type in {'TEX_NOISE','TEX_VORONOI','TEX_MUSGRAVE'} and not node.inputs['Vector'].is_linked:
            l.new(generated.outputs['Vector'],node.inputs['Vector'])
        if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:l.new(uv.outputs['Vector'],node.inputs['Vector'])
        if node.type=='UVMAP':
            source=n.new('ShaderNodeAttribute');source.attribute_name='SourceUV '+node.uv_map
            for link in list(node.outputs[0].links):l.new(source.outputs['Vector'],link.to_socket)
        if node.type=='TEX_COORD':
            for link in list(node.outputs['Generated'].links):l.new(generated.outputs['Vector'],link.to_socket)
            for link in list(node.outputs['UV'].links):l.new(uv.outputs['Vector'],link.to_socket)

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Archive the existing export preparation before rebuilding'
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.context.window.scene=bpy.data.scenes[manifest['scene']];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
    meshes=[o for o in scene.objects if o.type=='MESH'];materials={}
    source_triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    for obj in meshes:
        freeze_coordinates(obj)
        for slot in obj.material_slots:
            old=slot.material
            if old not in materials:materials[old]=old.copy();freeze_material(materials[old])
            slot.material=materials[old]
    skin=next(o for o in meshes if o.name.startswith('Goblin body | connected skin'))
    # Decimate preserves UV interpolation more faithfully than arbitrary corner-vector attributes.
    # Temporarily restore native UV layers during reduction, then freeze their corrected values for baking.
    projection_uvs=[]
    for attribute in list(skin.data.attributes):
        if not attribute.name.startswith('SourceUV '):continue
        values=np.empty(len(skin.data.loops)*3,dtype=np.float32);attribute.data.foreach_get('vector',values)
        name=attribute.name[len('SourceUV '):];uv=skin.data.uv_layers.new(name=name)
        assert uv is not None,'Too many source UVs for interpolation-preserving reduction'
        uv.data.foreach_set('uv',values.reshape(-1,3)[:,:2].copy().reshape(-1));projection_uvs.append((name,attribute.name))
    protected_before=sum((skin.matrix_world @ v.co).z>1.56 for v in skin.data.vertices)
    region=skin.vertex_groups.new(name='Export reduction region')
    for vertex in skin.data.vertices:
        z=(skin.matrix_world @ vertex.co).z
        weight=max(0,min(1,(1.55-z)/.06))
        if weight>0:region.add([vertex.index],weight,'REPLACE')
    # Reduce the dense voxel sculpt before skinning. Keep hands/feet and face for visual comparison after this stage.
    active(skin);decimate=skin.modifiers.new('Game skin surface reduction','DECIMATE');decimate.ratio=.60
    decimate.vertex_group=region.name;decimate.vertex_group_factor=1000
    while skin.modifiers.find(decimate.name)>0:bpy.ops.object.modifier_move_up(modifier=decimate.name)
    apply(skin,decimate)
    for name,attribute_name in projection_uvs:
        uv=skin.data.uv_layers[name];values=np.empty(len(skin.data.loops)*2,dtype=np.float32)
        uv.data.foreach_get('uv',values);vectors=np.zeros((len(skin.data.loops),3),dtype=np.float32)
        vectors[:,:2]=values.reshape(-1,2)
        skin.data.attributes[attribute_name].data.foreach_set('vector',vectors.reshape(-1))
        skin.data.uv_layers.remove(uv)
    skin.vertex_groups.remove(skin.vertex_groups['Export reduction region'])
    protected_after=sum((skin.matrix_world @ v.co).z>1.56 for v in skin.data.vertices)
    assert protected_after>=protected_before*.99,'Face protection failed during reduction'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:obj.select_set(True)
    bpy.context.view_layer.objects.active=skin;bpy.ops.object.join()
    mesh=bpy.context.object;mesh.name='MM6 Goblin render mesh'
    armatures=[m for m in mesh.modifiers if m.type=='ARMATURE']
    assert len(armatures)==1 and armatures[0].object==rig,'Joined mesh must use the copied character rig exactly once'
    uv=mesh.data.uv_layers.new(name='GameUV');mesh.data.uv_layers.active=uv;uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003,area_weight=.15,correct_aspect=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Freeze the same triangulation for the tangent bake and every glTF consumer.
    tri=mesh.modifiers.new('Portable triangulation','TRIANGULATE');tri.keep_custom_normals=True
    while mesh.modifiers.find(tri.name)>0:bpy.ops.object.modifier_move_up(modifier=tri.name)
    apply(mesh,tri)
    pruned=0;max_discarded=0.
    bone_groups={g.index for g in mesh.vertex_groups if g.name in rig.data.bones}
    for vertex in mesh.data.vertices:
        weights=sorted([(g.group,g.weight) for g in vertex.groups if g.group in bone_groups and g.weight>0],key=lambda x:-x[1])
        if len(weights)<=4:continue
        pruned+=1;max_discarded=max(max_discarded,sum(w for _,w in weights[4:]))
        keep=weights[:4];total=sum(w for _,w in keep)
        for group,_ in weights:mesh.vertex_groups[group].remove([vertex.index])
        for group,weight in keep:mesh.vertex_groups[group].add([vertex.index],weight/total,'REPLACE')
    rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    rig.data.pose_position='POSE';scene.frame_set(1)
    triangles=sum(len(p.vertices)-2 for p in mesh.data.polygons)
    report={'source_triangles':source_triangles,'game_triangles':triangles,'vertices':len(mesh.data.vertices),
        'head_vertices_before_reduction':protected_before,'head_vertices_after_reduction':protected_after,
        'vertices_pruned_to_four_influences':pruned,'maximum_discarded_weight':max_discarded,
        'materials':len(mesh.data.materials),'bones':len(rig.data.bones),'uv':'GameUV',
        'status':'Prepared mesh; reduction, material baking and exported appearance require visual review'}
    out=ROOT/'export_work';out.mkdir(exist_ok=True)
    (out/'mesh_report.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.data.libraries.write(str(out/'game_mesh_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    print(json.dumps(report))

if __name__=='__main__':build()
