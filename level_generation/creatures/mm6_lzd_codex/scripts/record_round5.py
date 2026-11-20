from pathlib import Path
import json,hashlib,struct,subprocess,datetime
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def read(n):return json.loads((P/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n')
for name,args in [('check_weights',[P/'export/mm6_lzd.glb',P/'export/mm6_lzd_bow.glb']),('check_bindings',[P/'integration/actors.yml'])]:
 r=subprocess.run(['python3',str(R/'output/codex_batch'/f'{name}.py'),*map(str,args)],capture_output=True,text=True,check=True)
 out=r.stdout+r.stderr;assert 'BAD'not in out;(P/f'review/round5/{name}.txt').write_text(out);print(out)
g=read('review/round5/gates_final/gates.json');layers=read('review/round5/gates_layers/gates.json')
assert g['status']==layers['status']=='PASS'
for result in [g,layers]:
 for a in result['assets']:assert sha(Path(a['path']))==a['sha256']
viewer=read('review/viewer_check.json');assert viewer['switched']==27 and not viewer['failed']and not viewer['consoleErrors']
ex=read('review/round5/exports.json');info=read('export/export_info.json');dist=read('review/round5/layer_distances.json')
assert dist['body_sha256']==ex['mm6_lzd']['sha256']
clearance={n:min(r['distance_m']for r in dist['rows']if r['layers']==n)*1000 for n in ['shoulders','belt']}
assert min(clearance.values())>=1
orientation=read('review/round5/forward_orientation.json');preservation=read('review/round5/end_pose_preservation.json')
assert max(preservation.values())<1e-5
files={}
for p in sorted((P/'export').glob('*.glb'))+sorted((P/'review/viewer').glob('*.glb')):
 if p.name=='mm6_lzd_lods.geometry.glb':continue
 b=p.read_bytes();d=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]])
 files[str(p.relative_to(P))]={'sha256':sha(p),'bytes':len(b),'triangles_per_mesh':[sum(d['accessors'][q['indices']]['count']//3 for q in m['primitives'])for m in d['meshes']]}
for n,v in ex.items():assert v['sha256']==files[f'export/{n}.glb']['sha256']
actors=sha(P/'integration/actors.yml');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt={'status':'passed','completed_at':now,'files':files,'runtime':ex,'actors_changed':True,'actors_sha256':actors,'shared_gates':{'standard':g['counts'],'layers':layers['counts'],'runner_sha256':g['runner_sha256']},'minimum_sampled_layer_clearance_mm':clearance,'orientation':[{k:v for k,v in r.items()if k!='samples'}for r in orientation],'clips':info['clips'],'release_s':info['impact_seconds'],'cast':'Exact Attack copy, verified by round5_retime.py','end_pose_preservation':preservation,'viewer':viewer,'credits_spent_total':60,'additional_credits':0,'credit_limit':100,'installation_executed':False,'native_checks_executed':False}
write('review/review_round5.json',receipt)
gait=[r for r in g['gates']if '/colour'in r['lod']and r['gate']in ['foot_yaw_deg','lowest_sole_m','walking_lift_min_mm','walking_lift_max_mm','running_contact_pct','running_airborne_mm']]
write('review/round5/gait.json',gait)
write('review/round5/curve.json',{'round4_reduction_curve':'../round4/curve.json','current_triangles':{n:v['triangles']for n,v in ex.items()},'further_reduction':False,'note':'Topology, counts and shared maps unchanged. Round 4 image metrics remain historical; round 5 layer/motion repairs have current shared gates and review images.'})
(P/'review/round5/README.md').write_text(f"""# Review round 5

- [Standard shared gates](gates_final/gates.md): {g['counts']}.
- [Worn-layer shared gates](gates_layers/gates.md): {layers['counts']}.
- [Surface clearance](layer_distances.json): shoulders >= {clearance['shoulders']:.3f} mm,
  belt/tabard >= {clearance['belt']:.3f} mm; every clip and applicable colour LOD at 48 Hz.
  Nearest-surface diagnostics use the shared Glb/Mesh/Surface evaluator with vertex, edge and triangle-centre samples.
  These are sampled checks, not a continuous intersection proof.
- [Facing trace](forward_orientation.json), [gait](gait.json), [endpoint preservation](end_pose_preservation.json).
- [Hit](hit.png), [front Hit](hit_front.png), [standing](native_stand.png), Walking
  [36](walk36.png), [37](walk37.png), [38](walk38.png).
- [Clip sheets](../clips_three_quarter.jpg), [release](../release_sheet.jpg), [hands](../exported_hands.jpg).
- [Weights](check_weights.txt), [bindings](check_bindings.txt), [viewer](../viewer_check.json),
  [complete receipt](../review_round5.json).

The initial combined garment volume incorrectly sealed the open tunic hem. The uncapped query put its flagged
buckle point 52.689 mm outside the fabric. The final config separates garments and declares the actual hem centroid
with a pelvis-following exit plane: [intent](hem_opening.json). Thresholds were not loosened; earlier failures remain
as history.

Matched shoulder/pad deformation, transferred belt/buckle weights and tucked cloth separate the layers.
The tabard fold is limited during the middle of Death; a one-millimetre LOD1 knee-plate adjustment clears it.
Bow geometry, maps, UVs and triangle counts are unchanged. [Counts and historical reduction curve](curve.json);
no additional decimation or rebake was done.

Attack/Cast last 1.133333333 s; release is exactly 0.734375 / 1.5 = 0.489583333333 s.
Death lasts 2 s and drops the bow at 0.5 s; Dead remains 1 s. Short monotonic timing eases after release and around
the falling hand/body motion keep acceleration and finger steps within the shared limits while preserving
the requested total durations and endpoints.
""")
counts='\n'.join(f"| export/{n}.glb | {' / '.join(map(str,v['triangles']))} | {v['sha256']} |"for n,v in ex.items())
hashes='\n'.join(f"| {n} | {v['sha256']} | {' / '.join(map(str,v['triangles_per_mesh']))} |"for n,v in files.items())
yaw='\n'.join(f"| {r['clip']} | {r['pelvis_max_abs_deg']:.3f} | {r['shoulder_max_abs_deg']:.3f} | {r['counterrotation_max_abs_deg']:.3f} |"for r in orientation)
header=f"""# HANDOFF — MM6 LizardArch (mm6:lzd)

**Review round 5 technical handoff ready.** Artistic acceptance and native integration remain with the orchestrator.
No commit, build, game launch or installation. Meshy **60 / 100 credits**, zero added this round.

Install the staged body/bow through tools/install_model.py with --world mm6; merge
[integration/actors.yml](integration/actors.yml). The bow export is byte-identical to round 4.

Attack/Cast: **1.133333333 s**, release **0.489583333333 s**, **Socket_Arrow**; Cast is an exact named Attack copy.
Death: **2.0 s**, endpoint preserved. Dead: **1.0 s**, unchanged.
Square native-style rest and horizontal string-up bow carry remain. Scale and stride are unchanged.

| File | LOD0 / 1 / 2 / 3 triangles | SHA-256 |
|---|---|---|
{counts}

[Review and checks](review/round5/README.md), [viewer](review/viewer/index.html),
[receipt](review/review_round5.json). Historical sections below are superseded by Review round 5.

"""
old=(P/'HANDOFF.md').read_text();history=old[old.index('## Review round 1'):].split('## Review round 5')[0]
section=f"""## Review round 5

- Separated shoulder plates/pads and belt/tabard. Matched shoulder/pad weights, transferred belt/buckle weights
  from supporting surfaces, tucked the cloth and fitted the distant shoulder surfaces.
  Minimum sampled clearance: shoulders **{clearance['shoulders']:.3f} mm**, belt **{clearance['belt']:.3f} mm**.
  Hit and all other clips were checked at every runtime LOD.
- Kept the correct root facing. Replaced inherited walking trunk rotations with smooth absolute frames;
  the late-cycle twist is removed and the native front stance retained.
- Death **4.0 -> 2.0 s**. Limited the middle-fall tabard fold to keep it out of the belt.
  Final Death pose and Dead are preserved against round 4 (matrix errors <1e-5); floor gates pass.
- Attack/Cast **1.7 -> 1.133333333 s**. Socket_Arrow release **0.734375 -> 0.489583333333 s**.
  Cast remains an exact copy. Local timing eases retain total duration/release and remove acceleration/finger-step
  failures exposed by uniform retiming.
- integration/actors.yml **changed**: all tiers' melee/ranged/cast event times and review marker.
  Scale 105.473370075 and stride 1.365689918 remain unchanged. SHA-256: **{actors}**.
- Standard shared runner: **{g['counts']['PASS']:,} PASS**, zero FAIL/UNVERIFIED.
  Worn-layer shared runner: **{layers['counts']['PASS']:,} PASS**, zero FAIL/UNVERIFIED.
  The real tunic hem opening is explicit; thresholds are unchanged.
- check_weights.py and check_bindings.py: **no BAD lines**. Viewer **27/27**, no console errors.
  Full clip sheets, hand close-ups and browser captures regenerated.
- Counts, UVs and shared texture maps are unchanged. The round 4 reduction curve is historical evidence;
  this scoped correction did no further reduction, texture work or paid generation.

Measured facing over each complete cycle, absolute yaw in degrees:

| Clip | Pelvis | Shoulders | Shoulder/pelvis difference |
|---|---:|---:|---:|
{yaw}

Selected editable source: work/round5/retimed_master.blend (also work/master.blend and work/master_export.blend).
work/round5/lod0.blend through lod3.blend retain original-time authoring/static-LOD inputs.
The round5_motion, round5_repair, round5_contact_fit, round5_flap and round5_leg_contact scripts record fitting;
round5_pack packages LODs and round5_retime retimes fresh exports. Do not apply the retimer twice.

Changed/exported file receipt; triangle lists include colour and shadow meshes where present:

| File | SHA-256 | Triangles per mesh |
|---|---|---|
{hashes}

Limits: bow limbs remain rigid while string/arrow animate. Sampled surface checks are not an exhaustive
continuous collision proof. Native installation, lighting, indoor/outdoor captures and game regression
were not run under the batch rules; those remain orchestration work.
"""
(P/'HANDOFF.md').write_text(header+history+'\n'+section)
(P/'README.md').write_text("""# MM6 Lizard Archer — review round 5

Technical handoff ready; artistic acceptance and native integration remain pending.
[HANDOFF](HANDOFF.md#review-round-5) lists files, hashes, counts, timings and limitations.

- Shoulder plates and belt clear their cloth layers across all clips.
- Walking remains square through frames 36–38; native standing and horizontal bow carry retained.
- Attack/Cast 1.133333333 s; Socket_Arrow release 0.489583333333 s. Cast copies Attack exactly.
- Death 2 s; endpoint and the unchanged Dead animation preserved.
- Body triangles 9,854 / 5,141 / 2,172 / 691; bow 1,788 / 964 / 388 / 110. Shared maps unchanged.
- Standard/worn-layer shared gates pass; bindings/weights clean; viewer 27/27.
- [Review](review/round5/README.md), [viewer](review/viewer/index.html), [receipt](review/review_round5.json).
- Meshy 60 / 100 credits; zero added. No installation, build, game launch or commit.

Reclaim the lease before further edits. The orchestrator installs through tools/install_model.py.
""")
r=P/'integration/regression.md';s=r.read_text().replace('0.734375','0.489583333333').replace('Attack/Cast now last 1.7 s','Attack/Cast now last 1.133333333 s').replace('appears at 0.56 s','appears at 0.373333333 s')
s+='\nRound 5: Death is 2 s and Dead is unchanged. Inspect Hit layer clearance, late Walking frames 36–38, the faster bow release and preserved corpse floor pose. Install through tools/install_model.py --world mm6; never copy directly into assets_dev.\n';r.write_text(s)
r=P/'integration/playbook_notes.md';s=r.read_text().replace('# Lizard batch lessons (shared playbooks left unchanged)','# Lizard batch lessons (shared playbooks left unchanged)\n\n## Round 5 — current\n\n- Match supporting weights as well as separating worn layers; offsets alone cannot prevent contact through a fold.\n- Keep the tabard below its belt during the fall; check exact reduced meshes too.\n- Declare real hem openings. A non-planar artificial cap can misclassify a buckle below the garment.\n- Retiming exposes acceleration/finger steps; ease affected intervals while retaining duration, endpoint and release.\n- Attack/Cast release is 0.489583333333 s, duration 1.133333333 s; Death 2 s; Dead unchanged.\n').replace('## Round 4 — current','## Round 4 — historical, superseded above');r.write_text(s)
progress=read('creature_3d_progress.json')
progress.update(status='complete',stage='batch_handoff_ready',substep='review_round_5_complete',updated_at=now,completed_at=now,exports={k+'.glb':v for k,v in ex.items()},clips=info['clips'],gates={'status':'technical_pass','receipt':'review/review_round5.json'},next_action={'owner':'orchestrator','action':'Install accepted GLBs with tools/install_model.py, merge event times, run native registry and indoor/outdoor checks.'})
progress['review_round_5']={'status':'passed','completed_at':now,'receipt':'review/review_round5.json','actors_changed':True,'additional_credits':0}
progress['integration']['status']='round5_body_and_event_times_pending_orchestrator'
progress['open_faults']=['Artistic acceptance and native integration/captures pending orchestrator.','Bow limbs remain rigid; string and arrow animate.']
progress['correction_ledger'].append({'finding':'Round 5 worn-layer z-fighting, late-walk trunk turn and requested speed changes','repair':'Separated/matched layers, smooth walking trunk, faster Attack/Cast and Death total durations with preserved endpoints and shared gates.','status':'resolved'})
write('creature_3d_progress.json',progress)
print('ROUND 5 RECORDED',ex['mm6_lzd']['sha256'])
