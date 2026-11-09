import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;r.animation_data.action=bpy.data.actions['Death'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(41,subframe=.5)
pv=np.array([v.value for v in b.data.attributes['piece'].data]);skin=[p for p in b.data.polygons if all(pv[i] in [0,1] for i in p.vertices)];f=skin[2486];print('CONTACT FACE',f.index,'rest',[(i,list(b.data.vertices[i].co),int(pv[i])) for i in f.vertices]);print('AXE LOCAL',list(ax.data.vertices[879].co));common.workbench_clay(sc);common.render_views(str(P/'review/death_contact'),.65,3.6,views=('front','left','three_quarter'),resolution=(800,800))
