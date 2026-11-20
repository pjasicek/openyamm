"""Review the final authoring export: posed bounds, native prop detail, x-rays and dense motion evidence."""
import bpy,sys,json,math,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import common,reduction_common as C
info=json.loads((P/'export/export_info.json').read_text());folder=P/'review/final';folder.mkdir(exist_ok=True)
def invoke(name,args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/f'scripts/{name}.py'),run_name='__main__')
invoke('proportions',['source',ROOT/'anim_library/humanoid_set/Armed.glb'])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];C.reset()
mapping={b.name:b.name for b in r.data.bones};(P/'work/bone_map.json').write_text(json.dumps(mapping))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/proportion_rest.blend'))
invoke('proportions',['target',P/'work/proportion_rest.blend','Rig','Body',P/'work/bone_map.json'])
invoke('joint_xray',[P/'work/runtime_lod0.blend','Body',P/'work/joints_final.json',folder/'joints'])
for side in ['R','L']:invoke('hand_xray',[P/'work/runtime_lod0.blend',side,folder/f'hand_{side}'])
invoke('stretch_heatmap',[P/'work/runtime_lod0.blend','Attack',30,folder/'stretch_attack30'])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.cleanup();r=bpy.data.objects['Rig'];sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE';sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
 data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=5;ob=bpy.data.objects.new('Softbox',data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.85))-ob.location).to_track_quat('-Z','Y').to_euler()
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.18,.18,1)
for name,tags in [('Body',['body','head']),('SpearMesh',['spear']),('BucklerMesh',['buckler'])]:
 for m,tag in zip(bpy.data.objects[name].data.materials,tags):
  bs=m.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(P/f'export/textures_lod0/{"body"if tag=="head"else tag}/natm_b_{tag}_preview.png'))
for role,row in info['clips'].items():
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];lo=np.array(row['bounds'][:3]);hi=np.array(row['bounds'][3:]);center=(lo+hi)/2;height=max((hi-lo)[2],np.linalg.norm((hi-lo)[:2])*520/420)*1.10
 for i,t in enumerate(np.linspace(0,row['duration'],7)):
  f=t*48;sc.frame_set(int(f),subframe=f%1);common.render_views(str(folder/f'{role}_{i:02}'),center[2],max(height,1.9),views=('front','left','three_quarter'),resolution=(420,520),target=tuple(center[:2]))
# The two attachment close-ups use their real held pose and final detailed maps.
C.activate('Standing',0)
for tag in ['Spear','Buckler']:
 for name in ['Body','SpearMesh','BucklerMesh']:bpy.data.objects[name].hide_render=name!=tag+'Mesh'
 lo,hi=common.world_bounds([bpy.data.objects[tag+'Mesh']]);center=(lo+hi)/2;height=max(hi-lo)*1.15;common.render_views(str(folder/f'prop_{tag.lower()}'),center.z,height,views=('front','left','three_quarter'),resolution=(720,720),target=(center.x,center.y))
for name in ['Body','SpearMesh','BucklerMesh']:bpy.data.objects[name].hide_render=False
common.render_views(str(folder/'grip_and_straps'),.95,.70,views=('front','left','three_quarter'),resolution=(720,720),target=(-.2,-.04))
common.render_views(str(folder/'head'),1.53,.45,views=('front','left','three_quarter'),resolution=(720,720))
print('REVIEW_RENDERS_COMPLETE',flush=True)
