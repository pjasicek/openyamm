import bpy,bmesh,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_gar.blend'));o=bpy.data.objects['Gargoyle'];bm=bmesh.new();bm.from_mesh(o.data);boundary=[e for e in bm.edges if e.is_boundary];nonman=[e for e in bm.edges if not e.is_manifold];print('SURFACE',len(boundary),len(nonman),o.data.has_custom_normals, [(m.name,m.type) for m in o.modifiers]);print('BOUNDARY_CENTRES',[list((e.verts[0].co+e.verts[1].co)/2) for e in boundary[:30]])
common.workbench_clay(bpy.context.scene,textured=False);common.render_views(str(P/'review/surface_clay'),1.5,3.3,views=('front','three_quarter'),resolution=(900,1200));common.render_views(str(P/'review/surface_head_clay'),1.68,.60,views=('front','three_quarter'),resolution=(900,900),target=(0,-.03))
