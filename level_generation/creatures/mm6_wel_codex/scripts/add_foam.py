"""Independent waterline foam, reusing the selected Sea Serpent foam artwork."""
import bpy,bmesh,json,math,shutil
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
src=P.parent/'mm6_seas_claude/references_hd/05_foam_ring.png';dst=P/'textures/foam.png';shutil.copy2(src,dst)
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap');grid=[];segments=48;rings=3
for i in range(rings+1):
 f=i/rings;rad=.45+.55*f;grid.append([bm.verts.new((.30*rad*math.cos(2*math.pi*k/segments),.35+.65*rad*math.sin(2*math.pi*k/segments),.025-.018*f)) for k in range(segments)])
for i in range(rings):
 for k in range(segments):
  face=bm.faces.new((grid[i][k],grid[i+1][k],grid[i+1][(k+1)%segments],grid[i][(k+1)%segments]))
  for loop in face.loops:loop[uv].uv=(.5+loop.vert.co.x/.30*.49,.5+(loop.vert.co.y-.35)/.65*.49)
me=bpy.data.meshes.new('Foam');bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('Foam',me);sc.collection.objects.link(ob);mat=bpy.data.materials.new('Foam');mat.use_nodes=True;mat.diffuse_color=(.8,.87,.8,1);nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(dst));nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);bs.inputs['Roughness'].default_value=1;mat.use_backface_culling=False;me.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('FoamRoot');b.head=(0,0,0);b.tail=(0,.1,0);bpy.ops.object.mode_set(mode='OBJECT');g=ob.vertex_groups.new(name='FoamRoot');g.add(list(range(len(me.vertices))),1,'REPLACE');ob.parent=rig;mod=ob.modifiers.new('Waterline','ARMATURE');mod.object=rig;pb=rig.pose.bones['FoamRoot'];pb.rotation_mode='QUATERNION'
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
for a in bpy.data.actions:
 rig.animation_data.action=a;lo,hi=a.frame_range
 for f in range(int(lo),int(hi)+1):
  u=(f-lo)/(hi-lo);wave=math.sin(2*math.pi*u);scale=(1-smooth((u-.62)/.38)) if a.name=='Death' else 0 if a.name=='Dead' else 1
  pb.scale=(max(.0001,scale*(1+.025*wave)),max(.0001,scale*(1+.04*wave)),1);pb.keyframe_insert('scale',frame=f,group='FoamRoot')
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_foam.blend'))
D=json.loads((P/'work/rig.json').read_text());D['bones']['FoamRoot']={'head':[0,0,0],'tail':[0,.1,0],'parent':None,'rot':list(map(list,rig.data.bones['FoamRoot'].matrix_local.to_3x3()))};D['bone_count']=len(rig.data.bones);D['foam']={'source':str(src),'selected':'textures/foam.png','alpha_mode':'MASK','independent_waterline':True};(P/'work/rig_final.json').write_text(json.dumps(D,indent=2));print('FOAM',len(me.polygons)*2,'triangles')
