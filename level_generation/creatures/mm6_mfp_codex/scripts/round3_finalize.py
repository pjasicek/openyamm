"""Publish review-3 timing receipts and the integration handoff."""
import datetime
import hashlib
import json
import shutil
from pathlib import Path

P=Path(__file__).resolve().parents[1]
ROOT=P.parents[2]
R=P/'review/round3'
B=P/'work/round3/before'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=lambda p:{'sha256':sha(p),'bytes':p.stat().st_size}
def write(p,data):p.write_text(json.dumps(data,indent=2)+'\n')
g=json.loads((R/'shared_gates/gates.json').read_text())
assert g['status']=='PASS' and not g['error']
for asset in g['assets']:assert sha(Path(asset['path']))==asset['sha256']
v=json.loads((R/'viewer_check.json').read_text())
assert v['switched']==24 and not v['failed'] and not v['consoleErrors']
assert 'BAD' not in (R/'bindings.txt').read_text()
motion=json.loads((R/'motion_preservation.json').read_text())
assert motion['after_sha256']==sha(P/'export/mm6_mfp.glb')
retime=json.loads((R/'retime_receipt.json').read_text())
for path,receipt in retime['changed_files'].items():assert sha(P/path)==receipt['after_sha256']
for path,digest in retime['unchanged_files'].items():assert sha(P/path)==digest
assert sha(P/'integration/actors.yml')==sha(B/'integration/actors.yml')
old_manifest=json.loads((B/'export/manifest.json').read_text())
texture_files={p:r for p,r in old_manifest['files'].items() if p.startswith('work/round2/textures/')}
for p,r in texture_files.items():assert sha(P/p)==r['sha256']
sources=json.loads((P/'source/native_inputs.json').read_text())
for source in sources:assert sha(ROOT/source['path'])==source['sha256']
write(R/'unchanged_sources.json',{'texture_files_verified':len(texture_files),'native_library_receipts_verified':len(sources),
                                'all_match':True,'actors_yml_sha256':sha(P/'integration/actors.yml')})
summary={}
death={}
for gate in sorted({r['gate'] for r in g['gates']}):
    rows=[r for r in g['gates'] if r['gate']==gate and isinstance(r.get('worst'),(int,float))]
    if rows:summary[gate]={'min':min(r['worst'] for r in rows),'max':max(r['worst'] for r in rows)}
    rows=[r for r in rows if r['clip']=='Death']
    if rows:death[gate]={'min':min(r['worst'] for r in rows),'max':max(r['worst'] for r in rows)}
tri={asset:[int(next(r['worst'] for r in g['gates'] if r['gate']=='triangles' and r['asset']==asset and r['lod']==f'colour{i}')) for i in range(4)] for asset in ['body','knife']}
assert tri=={'body':[10183,5513,2278,1235],'knife':[2344,1289,543,303]}
delivery={f:record(P/f) for f in ['export/mm6_mfp.glb','export/mm6_mfp_knife.glb','export/mm6_mfp.blend','integration/actors.yml']}
write(P/'review/final_metrics.json',{'revision':'review_round_3','generated_utc':now,'status':g['status'],
      'authority':'Unchanged claude_shared/gates/run_gates.py','counts':g['counts'],'assets':g['assets'],
      'triangles':tri,'summary':summary,'death':death,'sampling':g['sampling'],
      'motion':'round3/motion_preservation.json','viewer':'round3/viewer_check.json','bindings':'round3/bindings.txt'})
write(P/'review/runtime_audit.json',{'revision':'review_round_3','assets':g['assets'],
      'authority':'round3/shared_gates/gates.json','bindings':'round3/bindings.txt','viewer':'round3/viewer_check.json',
      'runtime_game':'Not run; orchestrator owns installation and game checks.'})
shutil.copy2(R/'viewer_check.json',P/'review/viewer_check.json')
shutil.copy2(R/'bindings.txt',P/'review/check_bindings.txt')
(P/'review/GATES.md').write_text('''# Current verification

Review round 3: **PASS** — 6,288 PASS, 136 INFO, 72 N/A; no failures or unverified rows.

[Shared report](round3/shared_gates/gates.md), [bound hashes and sampling](round3/shared_gates/gates.json),
[motion preservation](round3/motion_preservation.json), [bindings](round3/bindings.txt), [viewer](round3/viewer_check.json).

Death: worst floor penetration 0.902 mm; arm stretch max 2.29094, P99 1.77008; hand stretch max 1.000346.
All pass the unchanged project limits. Angular acceleration max 12198.9 degrees/s²; rotation step max 14.0217 degrees.
The changed time grid samples different points on the identical floor trajectory; differences from old extrema are
sampling differences, not geometry repairs. Bones 48 Hz; meshes 24 Hz with adaptive refinement to 48 Hz.
No new gate code or threshold changes. Shared pose sampler confirms identical corpse endpoint and unchanged other clips.
''')
hash_table='\n'.join(f'| [{f}]({f}) | `{r["sha256"]}` |' for f,r in delivery.items())
count_table='\n'.join(f'| {i} | {tri["body"][i]:,} | {tri["knife"][i]:,} | {tri["body"][i]+tri["knife"][i]:,} |' for i in range(4))
changed='\n'.join(f'| `{f}` | `{r["after_sha256"]}` |' for f,r in retime['changed_files'].items())
(P/'HANDOFF.md').write_text(f'''# MM6 PeasantF3 / mfp — batch handoff

## Review round 3 (death timing)

The user accepted Cutpurse otherwise. The requested **Death-only timing change is complete and verified**.
Updated {now}. [Accepted round-2 handoff](work/round3/before/HANDOFF.md) preserves earlier production details.

Death: **2.979166667 s → 2.144444444 s**. Source frames 100–143 at 48 fps run at 1.5×;
the complete result then runs at 1.25×. The old frame-100 pose now occurs at **1.666666667 s**.
The last segment lasts **0.477777778 s**. Effective speed is 1.25× before the boundary and 1.875× after it.
The exact endpoint is 102.933333 audit frames at 48 fps; it is intentionally not rounded to an integer frame.

### Scope and preservation

- All 716 dense Death pose samples are retained; only timestamps change. Sparse exporter-compressed tracks gain
  an interpolated boundary key to preserve their original path. No pose smoothing or spatial edits.
- Shared-sampler comparison at {motion['sample_count']} corresponding times: maximum node position discrepancy
  **{motion['all_node_position_max_delta_m']*1000:.9f} mm**, from float32 timing/interpolation. Final corpse matrix difference **0**.
- **Dead and every other clip are unchanged**, including key data and durations. All seven shared-sampler comparisons are exactly zero.
- Original binary payload is retained byte-for-byte: mesh topology, vertices, normals, UVs, weights and embedded textures.
  Knife export is unchanged. No triangle reduction, no texture work and no additional paid generation.
- Packed authoring and new editable checkpoints **work/round3/lod0.blend … lod3.blend** carry the retimed Death action.
  Canonical textures remain **work/round2/textures/**. Prior checkpoints stay preserved.

[Timing and file-change receipt](review/round3/retime_receipt.json), [shared-sampler preservation](review/round3/motion_preservation.json),
[authoring receipt](review/round3/authoring.json), [Death sheet](review/round3/Death.png).

### Delivery and integration

| File | SHA-256 |
|---|---|
{hash_table}

**integration/actors.yml changed: no, byte-identical.** Death has no impact event or descriptor duration to update.
Attack remains 1.125 s; melee/ranged/cast impacts remain 0.656250 s. IDs 601–603, scale 107.495710585,
yaw −π/2, skins mfp_a/b/c and strides remain unchanged.

The orchestrator installs the revised body with **tools/install_model.py --world mm6** and runs runtime checks.
The already-installed knife and actor descriptors need no replacement. This session did not install, launch a game,
build or commit. Meshy spending remains **55/100 credits** (0 this round).

| LOD | Body triangles | Knife triangles | Total |
|---|---:|---:|---:|
{count_table}

Colour and shadow counts are unchanged. 121 joints and eight clips. No geometry or material changes.

### Verification

- Shared runner: **PASS — 6,288 PASS, 136 INFO, 72 N/A**. Same gates.json and thresholds.
- Death floor penetration maximum **0.901704 mm**, arm stretch max **2.290938**, arm stretch P99 **1.770072**,
  hand stretch max **1.000345**; all pass existing limits across all LODs/shadows.
- Death angular acceleration max **12198.866 degrees/s²**, largest 48 Hz rotation step **14.021697 degrees**; no new pops.
- Bindings/weights: **no BAD line**. Shared viewer: **24/24** switches, no console errors or failed switches.
- Refreshed front/side/three-quarter Death sheet inspected. Final corpse and floor contact match the accepted poses.
  Other review sheets remain unchanged. Browser captures use software WebGL, not game GPU evidence.

[Full gates](review/round3/shared_gates/gates.md), [JSON/hashes](review/round3/shared_gates/gates.json),
[bindings](review/round3/bindings.txt), [viewer](review/round3/viewer_check.json), [review index](review/round3/README.md).
All {len(texture_files)} canonical texture files and {len(sources)} native/library receipts still match their prior hashes.
No known new fault. The batch rules leave installation/game verification to the orchestrator.

### Re-exported GLBs

| File | New SHA-256 |
|---|---|
{changed}

[Complete current manifest](export/manifest.json) includes editable checkpoints, review evidence and scripts.
Production scripts: scripts/round3_retime.py, round3_authoring.py, round3_review.py, round3_finalize.py.
Reproduce the timing patch from the accepted round-2 snapshot; do not rerun the historical round-2 full exporter over this delivery.
Historical round-2 LOD viewer assets are retained as historical evidence, not current animated delivery.
''')
(R/'README.md').write_text('''# Review round 3 — Death timing

Death shortened from **2.979166667 to 2.144444444 seconds** using the requested segment and overall speed factors.
The rest of the creature was accepted and remains unchanged.

- [Death sheet](Death.png): front, side and three-quarter; same source poses/cameras as the previous review.
- [Interactive viewer](../viewer/index.html): current three tiers, eight clips.
- [Timing receipt](retime_receipt.json), [motion preservation](motion_preservation.json), [editable actions](authoring.json).
- [Shared gates](shared_gates/gates.md), [bindings](bindings.txt), [viewer check](viewer_check.json).
- [Capture hashes](capture_receipt.json), [unchanged source/texture receipts](unchanged_sources.json).

The complete corpse pose is identical. Dead and all other clips are byte-identical. No mesh or texture edits.
The two speed changes meet at old frame 100 (new time 1.666667 s), with no discontinuity in pose.
The clip retains its exact fractional endpoint; no extra held frame was added.
''')
(P/'README.md').write_text('''# MM6 PeasantF3 — Cutpurse / Bounty Hunter / Assassin

User accepted the creature otherwise; **review round 3 Death timing is complete**.
Death is now **2.144444444 s**, previously 2.979166667 s. Frames 100–143 at 48 fps run 1.5× faster,
then the whole result runs 1.25× faster. All poses, other clips, mesh and textures are preserved.
[HANDOFF.md](HANDOFF.md) contains current hashes, triangle counts and integration notes. Meshy: **55/100 credits**.

## Current delivery

- [Body](export/mm6_mfp.glb), unchanged [knife](export/mm6_mfp_knife.glb), [packed authoring](export/mm6_mfp.blend).
- [Descriptors](integration/actors.yml) are byte-identical; [orchestrator regression notes](integration/regression.md).
- [Round-3 review](review/round3/README.md), [shared gates](review/round3/shared_gates/gates.md), [manifest](export/manifest.json).
- Editable checkpoints: work/round3/lod0.blend through lod3.blend. Canonical maps: work/round2/textures/.

## Unattended decisions and reproduction

Retime existing dense GLB samples directly, retaining their pose values and all existing binary payload.
Add an interpolated speed-change key to sparse tracks so their original path is also retained. Keep the exact
fractional endpoint (102.933333 frames at 48 fps), instead of rounding and altering the requested duration.
The corpse endpoint and all seven other clips match exactly. Float32 interpolation position difference is below 0.000361 mm.
No events belong to Death, so actors.yml needs no change. No geometry, UV, texture or reduction work this round.

Claim a fresh workspace lease before writes. One background Blender process with four threads.
Round-3 scripts: round3_retime.py (from accepted round-2 snapshots), round3_authoring.py (Death action only),
round3_review.py (shared sampler/checkers and viewer capture), round3_finalize.py (records).
Do not rerun the historical round-2 full exporter over the timing-only delivery.

The accepted round-2 production and its decisions are preserved in [the prior README](work/round3/before/README.md)
and [review evidence](review/round2/README.md). Historical round-2 LOD viewer assets keep the old timing for provenance.
Body counts: 10183 / 5513 / 2278 / 1235; knife: 2344 / 1289 / 543 / 303. Shared 5152×4096 atlas is unchanged.

Sibling mm6_mfp/, shared tools, runtime assets and engine remain read-only. No game/build/install/commit.
Orchestrator installs the revised body with tools/install_model.py and runs game checks. Knife/descriptors need no update.
''')
(P/'review/README.md').write_text('''# PeasantF3 review

Current: [Round 3 — Death timing](round3/README.md), [viewer](viewer/index.html),
[shared gates](round3/shared_gates/gates.md), [metrics](final_metrics.json).

Accepted appearance and other motion: [round 2](round2/README.md). Earlier history: [round 1](round1/),
[reduction study](REDUCTION.md). Only the Death sheet changed this round.
''')
reg=P/'integration/regression.md'
text=reg.read_text().replace('review round 2','review round 3').replace('codex_review2','codex_review3')
text += '\nReview round 3: install only the revised body; knife and actors.yml are unchanged. Verify Death lasts 2.144444444 s, with old frame 100 at 1.666666667 s, and transitions to the unchanged Dead pose without a pop. Appearance and all other clips were accepted; this delivery only changes Death timing.\n'
reg.write_text(text)
feedback_path=P/'review/viewer/feedback/user_feedback.json'
feedback=json.loads(feedback_path.read_text());feedback['revision']='mm6_mfp_codex_review3'
feedback['findings'].insert(0,{'id':'R3-death','region':'Death timing',
    'observed':'Complete: 2.979167 → 2.144444 s; frames 100–143 at 1.5x, then whole clip at 1.25x. Final pose and Dead unchanged. Other appearance/motion accepted by user.',
    'evidence':['../round3/Death.png','../round3/motion_preservation.json','../round3/shared_gates/gates.md']})
write(feedback_path,feedback)
selection_path=P/'review/reduction_soft/selection.json'
shutil.copy2(selection_path,B/'selection.json')
selection=json.loads(selection_path.read_text())
for level,entry in selection.items():entry['blend']=f'work/round3/lod{level}.blend'
write(selection_path,selection)
progress_path=P/'creature_3d_progress.json'
progress=json.loads(progress_path.read_text())
progress.update(stage='review_round_3',status='complete',completed_utc=now,handoff='HANDOFF.md',deliverables=delivery,
    user_acceptance='Creature otherwise accepted by user; requested Death timing correction completed.',
    next_action={'owner':'orchestrator','action':'Install revised body via tools/install_model.py and verify Death timing in game; knife and actor descriptors unchanged.'})
progress['checks']={'shared_gates':g['counts'],'bindings':'no BAD','viewer':'24/24, no errors',
                    'death_endpoint':'identical','other_clips':'identical','runtime_game':'Delegated to orchestrator'}
progress['known_tradeoffs']=[x for x in progress.get('known_tradeoffs',[]) if 'artistic acceptance' not in x]
progress['known_tradeoffs'].append('Game installation and runtime verification delegated to orchestrator under batch rules.')
progress['review_round_3']={'status':'complete','completed_utc':now,'death_old_duration_s':143/48,
    'death_new_duration_s':193/90,'source_segment_frames_48fps':[100,143],'segment_speed':1.5,'overall_speed':1.25,
    'actors_changed':False,'other_clips_mesh_textures_changed':False,'meshy_spend':0,'meshy_total':55,
    'credit_limit':100,'gate_report':'review/round3/shared_gates/gates.json','review':'review/round3/README.md'}
write(progress_path,progress)
selected={P/f for f in old_manifest['files']}
for pattern in ['scripts/round3*.py','review/round3/**/*','work/round3/lod?.blend']:
    selected.update(f for f in P.glob(pattern) if f.is_file())
write(P/'export/manifest.json',{'identity':'mm6:mfp','revision':'review_round_3','generated_utc':now,
    'runtime_files':delivery,'files':{str(f.relative_to(P)):record(f) for f in sorted(selected)}})
print('Published round-3 handoff and manifest;',len(selected),'files; mesh/textures/other clips unchanged.')
