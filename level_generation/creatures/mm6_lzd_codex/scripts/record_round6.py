from pathlib import Path
import json,hashlib,datetime,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));sys.dont_write_bytecode=True
from build_actor_lods import read_glb,accessor_bytes
def read(n):return json.loads((P/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n')
g=read('review/round6/gates_final/gates.json');layers=read('review/round6/gates_layers/gates.json');motion=read('review/round6/motion_diagnostics.json');view=read('review/viewer_check.json');files=read('review/round6/exports.json')
assert g['status']==layers['status']=='PASS'
assert view['switched']==27 and not view['failed'] and not view['consoleErrors']
for r in [g,layers]:
 for a in r['assets']:assert sha(Path(a['path']))==a['sha256']
assert motion['runtime_sha256']==sha(P/'export/mm6_lzd.glb')
assert motion['loop_endpoint_max_matrix_difference']<1e-5
for n,v in files.items():assert sha(P/n)==v['sha256']
baseline=P/'review/round6/baseline'
assert sha(P/'integration/actors.yml')==sha(baseline/'integration/actors.yml')
assert sha(P/'export/mm6_lzd_bow.glb')==sha(baseline/'export/mm6_lzd_bow.glb')
for n in files:
 old,b=read_glb(baseline/n);new,c=read_glb(P/n)
 for key in ['meshes','nodes','materials','images','textures','skins']:assert old.get(key)==new.get(key),(n,key)
 for i in range(len(old['accessors'])):assert accessor_bytes(old,b,i)==accessor_bytes(new,c,i)
for n in ['check_weights','check_bindings']:assert 'BAD'not in(P/f'review/round6/{n}.txt').read_text()
runtime={}
for name in ['mm6_lzd','mm6_lzd_bow']:
 path=P/f'export/{name}.glb';d,b=read_glb(path);levels=[0]+d['meshes'][0]['extras']['openyamm_lods']
 runtime[name]={'sha256':sha(path),'bytes':path.stat().st_size,'triangles':[sum(d['accessors'][x['indices']]['count']//3 for x in d['meshes'][i]['primitives'])for i in levels],'images':len(d['images'])}
walk=[r for r in g['gates']if r['clip']=='Walking' and '/colour'in r['lod']]
write('review/round6/walking_gates.json',walk)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt={'status':'technical_pass','completed_at':now,'runtime':runtime,'files':files,'actors_changed':False,'actors_sha256':sha(P/'integration/actors.yml'),'all_other_clips':'byte-identical animation channels; all prior accessor payloads, geometry, maps and node metadata preserved','shared_gates':g['counts'],'layer_gates':layers['counts'],'motion_diagnostics':motion,'viewer':view,'credits_total':60,'credits_added':0,'credit_limit':100,'native_checks':False}
write('review/review_round6.json',receipt)
before=motion['versions']['before']['B_Pelvis'];after=motion['versions']['after']['B_Pelvis'];head=motion['versions']['after']['B_Head']
metrics=f"""Pelvis peak vertical speed: {before['peak_abs_velocity_m_s']:.3f} -> {after['peak_abs_velocity_m_s']:.3f} m/s.
Pelvis peak vertical acceleration: {before['peak_abs_acceleration_m_s2']:.3f} -> {after['peak_abs_acceleration_m_s2']:.3f} m/s².
Head peaks: {head['peak_abs_velocity_m_s']:.3f} m/s and {head['peak_abs_acceleration_m_s2']:.3f} m/s²."""
counts='\n'.join(f"| export/{n}.glb | {' / '.join(map(str,d['triangles']))} | {d['sha256']} |"for n,d in runtime.items())
changed='\n'.join(f"| {n} | {v['sha256']} |"for n,v in files.items())
section=f"""## Review round 6 (walk)

Walking only. Other eight clips, bow geometry, all meshes/maps/LODs and event timings are preserved.
integration/actors.yml **unchanged**, SHA-256 {receipt['actors_sha256']}.

- Replaced per-frame pelvis grounding clamps with one smooth, symmetric periodic height curve:
  two equal highs/lows per 0.8-second cycle, fitted once to leg reach. Re-solved knees onto the existing foot paths.
  No root translation workaround. A second harmonic flattens the highs without adding extra extrema.
- Both shoulders counter-swing **±25°** opposite the legs; bow follows its accepted grip.
  Free wrist turns gently toward the thigh. Shared palm worst **30.536°**, wrist roll **41.777°**.
- Identical first/last Walking keys; decoded endpoint matrix difference
  **{motion['loop_endpoint_max_matrix_difference']:.3g}**. Binding stride **1.365689918 m** unchanged.
  Decoded foot-path differences are <= **{max(motion['foot_path_max_difference_m'].values())*1000:.3f} mm**
  (sampling/interpolation and closing the old ~1 mm endpoint mismatch).
- LOD0 swing peaks **97.579 / 97.740 mm**, knees **55.863 / 56.004°**, foot yaw **5.150 / 0.925°**.
  Lowest soles **0.5 / 0.1 mm above floor**. All LOD floor/contact gates pass.
- Standard shared runner **{g['counts']['PASS']:,} PASS**, layer runner **{layers['counts']['PASS']:,} PASS**,
  zero FAIL/UNVERIFIED; unchanged gate configs and thresholds.
- Bindings and weights: no BAD lines. Viewer **27/27**, no console errors.
- 48 Hz pelvis/spine/head traces: {metrics}
  The shared runner currently implements arm angular jitter, but has **no translation-jitter gate for
  pelvis/spine/head**. These height/velocity/acceleration traces use its GLB evaluator and are diagnostics,
  not a claimed shared-gate verdict or a replacement custom gate.
- Updated walk sheets and frames 13–15, plus side, front, hand and three-quarter viewer captures.
  Selected source: work/round6/master.blend, also work/master.blend and work/master_export.blend.
  round6_walk.py authors Walking; round6_pack.py replaces only its runtime channels from the saved round-5 baselines.
- **60 / 100 credits**, zero added. No native install, builds, game launches or commit.

| Runtime file | LOD0 / 1 / 2 / 3 triangles | SHA-256 |
|---|---|---|
{counts}

| Changed animated export / viewer file | SHA-256 |
|---|---|
{changed}

Static LOD intermediates and the bow are unchanged. Triangle reduction and texture rebaking were outside this
walking-only correction; existing reduction evidence remains historical.
[Review](review/round6/README.md), [receipt](review/review_round6.json).
Native integration and game checks remain with the orchestrator.
"""
old=(P/'HANDOFF.md').read_text();history=old[old.index('## Review round 1'):].split('## Review round 6')[0]
header=f"""# HANDOFF — MM6 LizardArch (mm6:lzd)

**Review round 6 (Walking) technical handoff ready.** Other clips remain accepted and unchanged.
Walking is 0.8 s with symmetric bob and wider counter-swing. Bindings/timings unchanged:
Attack/Cast 1.133333333 s, release 0.489583333333 s from Socket_Arrow; Death 2 s, Dead 1 s.

| File | LOD0 / 1 / 2 / 3 triangles | SHA-256 |
|---|---|---|
{counts}

[Current review](review/round6/README.md), [receipt](review/review_round6.json), [viewer](review/viewer/index.html).
Install through tools/install_model.py --world mm6 when accepted; orchestrator owns installation and native checks.
Lease released at handoff. No commit. Budget 60/100 credits.
Historical sections below are superseded by Review round 6 where applicable.

"""
(P/'HANDOFF.md').write_text(header+history+'\n'+section)
(P/'review/round6/README.md').write_text(f"""# Review round 6 — Walking

Smooth symmetric two-step bob; existing foot paths; ±25° shoulder counter-swing. Other clips unchanged.

- [Shared gates](gates_final/gates.md): {g['counts']}.
- [Layer gates](gates_layers/gates.md): {layers['counts']}.
- [48 Hz motion diagnostics](motion_diagnostics.json), [height plot](height_trace.png).
- [Walk sequence](walking_sequence.jpg), [full clip sheets](../clips_three_quarter.jpg).
- Frames [13](walk13.png), [14](walk14.png), [15](walk15.png); hands
  [back](hand_back.png) / [forward](hand_forward.png).
- [Bindings](check_bindings.txt), [weights](check_weights.txt), [viewer check](../viewer_check.json).
- [Complete receipt](../review_round6.json), [HANDOFF](../../HANDOFF.md#review-round-6-walk).

{metrics}

Shared runner gap: pelvis/spine/head translational jitter has no built-in gate. The recorded 48 Hz diagnostics
come from its runtime GLB sampler; arm angular jitter and all existing shared checks pass. No new gate code,
threshold changes or shared-tool modifications were made.

Decisions: keep accepted foot trajectories and stride. Fit a single analytic periodic bob against both leg-reach
envelopes instead of a per-frame clamp. Use the second harmonic to flatten the two equal highs, with no extra extrema.
Rotate shoulders for swing; gently orient the free palm toward the thigh without changing elbow roll.
Preserve every other animation channel and geometry/texture accessor. actors.yml remains byte-identical.

No new generation, reduction or rebake. Meshy 60/100 credits; zero added. No native install/build/game/commit.
""")
(P/'README.md').write_text("""# MM6 Lizard Archer — review round 6 (walk)

Walking correction ready for review: smooth symmetric bob, larger shoulder counter-swing, unchanged stride,
floor contact and seamless loop. All other clips, materials, geometry and bindings are preserved.

[HANDOFF](HANDOFF.md#review-round-6-walk) lists hashes, counts, checks and the shared runner's translation-jitter
coverage gap. [Review](review/round6/README.md), [viewer](review/viewer/index.html),
[receipt](review/review_round6.json). Standard/layer gates pass; bindings/weights clean; viewer 27/27.

Decisions: retain the accepted foot paths and re-solve the legs under one periodic height curve; rotate the shoulders
±25°, preserving the bow grip and gently turning the free palm toward the thigh. No root-facing or timing change.
Meshy 60/100 credits; zero added. Orchestrator owns native installation/checks. No commit.
""")
p=read('creature_3d_progress.json');p.update(status='complete',stage='batch_handoff_ready',substep='review_round_6_walk_complete',updated_at=now,completed_at=now,exports={n+'.glb':v for n,v in runtime.items()},gates={'status':'technical_pass','receipt':'review/review_round6.json'})
p['review_round_6']={'status':'technical_pass','receipt':'review/review_round6.json','actors_changed':False,'additional_credits':0,'completed_at':now}
p['integration']['status']='round6_walking_body_pending_orchestrator'
p['next_action']={'owner':'orchestrator','action':'Review Walking, install accepted body via tools/install_model.py, retain existing bow and bindings, run native checks.'}
p['correction_ledger'].append({'finding':'Walking vertical snap and insufficient arm swing','repair':'Reach-fitted symmetric bob with leg IK, ±25 degree shoulder counter-swing and thigh-facing palm; all shared gates pass.','status':'resolved'})
p['open_faults']=['Walking artistic acceptance/native checks pending orchestrator.','Shared runner lacks pelvis/spine/head translation-jitter gate; 48 Hz runtime-sampler diagnostics supplied.','Bow limbs remain rigid; string and arrow animate.']
write('creature_3d_progress.json',p)
print('ROUND6 RECORDED',runtime['mm6_lzd']['sha256'])
