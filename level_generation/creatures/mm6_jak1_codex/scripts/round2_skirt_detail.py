import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_gate_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];row=json.loads((P/'work/g6_fauld.json').read_text())['Death'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(int(row['frame']));me=body.data;pv=[a.value for a in me.attributes['piece'].data];sp=[p for p in me.polygons if pv[p.vertices[0]]==1 and p.normal.dot(Vector((p.center.x,p.center.y,0)).normalized())>.25];p=sp[row['outer_face']];print('SKIRT FACE',list(p.vertices),[tuple(me.vertices[i].co)for i in p.vertices],[[ (body.vertex_groups[g.group].name,g.weight)for g in me.vertices[i].groups]for i in p.vertices],flush=True)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[tuple(p.vertices)for p in sp]);skin=Vector(row['skin_point']);normal=(skin-Vector(row['cloth_point'])).normalized();print('OUTWARD',tuple(normal),'RAY',tree.ray_cast(skin+normal*.0001,normal,2),flush=True)
for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:print('RAY',d,tree.ray_cast(skin,Vector(d),2),flush=True)
ev.to_mesh_clear();sc=bpy.context.scene;common.workbench_clay(sc,True)
for mat in body.data.materials:
 bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
common.render_views(str(P/'review/round2/skirt_worst'),.40,1.05,views=('front','back','left','right'),resolution=(650,650),target=(0,-.10))
# A small marker identifies the measured skin point in a separate diagnostic image.
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.009,location=skin);marker=bpy.context.object;marker.color=(1,0,0,1);mat=bpy.data.materials.new('Contact marker');mat.diffuse_color=(1,0,0,1);marker.data.materials.append(mat)
common.render_views(str(P/'review/round2/skirt_marker'),.40,1.05,views=('front','back','left','right'),resolution=(650,650),target=(0,-.10))
