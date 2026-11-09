"""Rebuild the authoring chain and update only Running in the retained textured master."""
from pathlib import Path
import bpy,hashlib,json,runpy,sys
P=Path(__file__).resolve().parents[1];S=P/'scripts'
def run(name,*args):
 sys.argv=[name,'--',*[str(x) for x in args]];runpy.run_path(str(S/name),run_name='__main__')
run('refine_motion.py');run('finish_motion.py');run('check_motion.py')
# UVs, mesh, weights and all other actions belong to the selected textured master.
def curves(a):
 return [f for layer in a.layers for strip in layer.strips for bag in strip.channelbags for f in bag.fcurves]
def fingerprint():
 body=bpy.data.objects['Body'];m=body.data
 data={'vertices':[list(v.co) for v in m.vertices], 'faces':[list(f.vertices) for f in m.polygons],
  'weights':[[[g.group,g.weight] for g in v.groups] for v in m.vertices],
  'uv':{u.name:[list(d.uv) for d in u.data] for u in m.uv_layers}}
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def channels():
 result={}
 for a in bpy.data.actions:
  result[a.name]={f'{f.data_path}/{f.array_index}':[[*k.co,k.interpolation] for k in f.keyframe_points] for f in curves(a)}
 return result
master=P/'work/rig_textured_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(master));before_mesh=fingerprint();before_actions=channels()
sys.argv=['sync_actions.py','--',str(P/'work/rig_gated_candidate.blend'),str(master),'Running']
runpy.run_path(str(P.parent/'mm6_natm_claude/scripts/sync_actions.py'),run_name='__main__')
assert fingerprint()==before_mesh
changed=[]
after_actions=channels()
assert after_actions.keys()==before_actions.keys()
for name,ch in after_actions.items():
 assert ch.keys()==before_actions[name].keys()
 for key,values in ch.items():
  if values!=before_actions[name][key]:
   changed.append((name,key))
   assert name=='Running' and any(f'"B_R_{n}"' in key for n in ('Clavicle','UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist')), (name,key)
(P/'review/arm_20261016/preservation.json').write_text(json.dumps({'mesh_uv_weights_sha256':before_mesh,'changed_channels':changed,'unchanged_other_clips':True},indent=2)+'\n')
run('export_runtime.py')
