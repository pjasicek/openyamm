import bpy,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport_lod0.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(12,subframe=.5);gn={g.index:g.name for g in b.vertex_groups};labels=[]
for v in b.data.vertices:
 best=max(v.groups,key=lambda x:x.weight);name=gn[best.group];labels.append(int(name[len('B_R_Finger')])+1 if name.startswith('B_R_Finger')else 0)
b.data.materials.clear()
for colour in [(0.6,.6,.6,1),(1,.08,.08,1),(1,.4,.01,1),(.95,.8,.03,1),(.03,.8,.2,1),(.03,.3,1,1)]:
 m=bpy.data.materials.new('label');m.diffuse_color=colour;b.data.materials.append(m)
for f in b.data.polygons:f.material_index=max(set(labels[i]for i in f.vertices),key=lambda v:sum(labels[i]==v for i in f.vertices))
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='MATERIAL';H=r.pose.bones['B_R_Hand'].head;common.render_views(str(P/'review/hand_labels'),H.z-.025,.28,views=('front','left','three_quarter'),resolution=(600,600),target=(H.x,H.y))
