"""Confirm UV preparation left geometry, weights, bone frames and animation keys unchanged."""
import bpy,sys,os,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY']
def fingerprint(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
 data={'vertices':[list(v.co)for v in b.data.vertices],'faces':[list(p.vertices)for p in b.data.polygons],
 'weights':[[[b.vertex_groups[g.group].name,g.weight]for g in v.groups]for v in b.data.vertices],
 'bones':{x.name:{'matrix':[list(row)for row in x.matrix_local],'parent':x.parent.name if x.parent else None}for x in r.data.bones},'actions':{}}
 for a in bpy.data.actions:
  if not a.name.startswith('Kept_'):continue
  curves=[f for l in a.layers for s in l.strips for c in s.channelbags for f in c.fcurves]
  data['actions'][a.name]=sorted([(f.data_path,f.array_index,[(list(p.co),list(p.handle_left),list(p.handle_right),p.interpolation)for p in f.keyframe_points])for f in curves])
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
source=P/'work'/kind/'rig_final_done.blend';master=P/'work'/kind/'rig_texturing.blend';before=fingerprint(source);after=fingerprint(master);assert before==after,(before,after)
(P/'review'/kind/'master_invariance.json').write_text(json.dumps({'pass':True,'checked_rig':str(source.relative_to(P)),'checked_rig_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'texturing_master':str(master.relative_to(P)),'texturing_master_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'geometry_weights_bones_actions_sha256':before},indent=2)+'\n');print('MASTER_UNCHANGED',kind,before,flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
