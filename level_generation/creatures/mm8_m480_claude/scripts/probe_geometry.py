from pathlib import Path
import bpy,bmesh,json,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_v1_parts.blend'))
ob=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(ob.data);edge=[e for e in bm.edges if e.is_boundary];print('SKIN_BOUNDARIES',[(list(e.verts[0].co),list(e.verts[1].co)) for e in edge]);bm.free()
for o in bpy.data.objects:
 if o.type=='MESH':o.show_wire=False
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/body_v1_hand'),.59,.43,views=('front','left'),resolution=(700,700),target=(.52,-.04))
common.render_views(str(P/'review/body_v1_face'),1.43,.47,views=('front','three_quarter'),resolution=(700,700))
