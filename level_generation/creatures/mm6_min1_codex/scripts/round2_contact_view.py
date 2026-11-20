import bpy,sys,json,importlib.util
sys.dont_write_bytecode=True
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
file=P.parent/'claude_shared/gates/run_gates.py';spec=importlib.util.spec_from_file_location('shared_gates',file);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
c=json.loads((P/'gates.json').read_text());glb=g.Glb(P/'export/mm6_min1.glb');mesh=g.load_meshes(glb)[0];report=g.Report(c);g.configure_mesh(mesh,c,report);clip=next(a for n,a,s,e in glb.clips() if n=='Death');t=20/48;pose=glb.pose(clip,np.array([t]))[0];points=mesh.posed(pose)
D=json.loads((P/'review/round2/shared_gates/gates.json').read_text());row=next(r for r in D['gates'] if r['clip']=='Death' and r['lod']=='Minotaur/colour0' and r['gate']=='arm_body_penetration_mm' and r['region']=='L');ix=np.flatnonzero(mesh.contact_samples['L'])[row['detail']['sample_vertex']];pt=points[ix];print('DIAGNOSTIC',row,'point',pt,'bind',mesh.rest[ix],flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_min1_a.glb'));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');sc=bpy.context.scene;r.animation_data.action=bpy.data.actions['Death'];r.animation_data.action_slot=r.animation_data.action.slots[0];f=t*sc.render.fps;sc.frame_set(int(f),subframe=f%1)
for m in bpy.data.materials:
 bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bs and bs.inputs['Base Color'].links:m.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard'
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.012,location=pt);marker=bpy.context.object;marker.color=(1,0,0,1);mat=bpy.data.materials.new('diagnostic');mat.diffuse_color=(1,0,0,1);marker.data.materials.append(mat)
common.render_views(str(P/'review/round2/contact'),1.1,1.9,views=['front','left','three_quarter'],resolution=(700,700))
