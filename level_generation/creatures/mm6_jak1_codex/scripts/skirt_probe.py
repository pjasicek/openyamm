import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.argv=['x','--',str(P/'work/animated_master.blend')]
s=(P/'scripts/g6_skirt_poke.py').read_text();exec(s[:s.index('for an in a[1:]:')]);import common
rig.animation_data.action=bpy.data.actions['Walking'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(8)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([tuple(v.co)for v in em.vertices]);ev.to_mesh_clear();c=inside(co,r0);worst=sorted([(d,i)for i,(out,d,_)in c.items()if out and i in r0 and not r0[i][0]],reverse=True);print('WORST',[(d,i,rest[i].tolist(),co[i].tolist(),[(body.vertex_groups[g.group].name,g.weight)for g in me.vertices[i].groups])for d,i in worst[:10]],flush=True)
for d,i in worst[:5]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.008,location=co[i]);mat=bpy.data.materials.new('red');mat.diffuse_color=(1,0,0,1);bpy.context.object.data.materials.append(mat)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/skirt_probe'),.85,1.0,views=('front','left','three_quarter'),resolution=(700,700))
