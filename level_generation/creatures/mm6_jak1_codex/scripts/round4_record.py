"""Record the fixed staff reduction and unchanged accepted body at final handoff."""
import sys,json,hashlib,subprocess,shutil,datetime
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P/'review/round4';repo=P.parents[2]
sys.path.insert(0,str(repo/'tools'));from merge_head_material import read_glb
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
before=json.loads((R/'before_hashes.json').read_text());g=json.loads((R/'shared_gates/gates.json').read_text());assert g['status']=='PASS'and g['counts']=={'PASS':6602,'INFO':128,'N/A':56}
for row in g['assets']:assert sha(Path(row['path']))==row['sha256']
for script,args in [('check_bindings.py',[P/'integration/actors.yml']),('check_weights.py',[P/'export/mm6_jak1.glb',P/'export/mm6_jak1_staff.glb'])]:
 r=subprocess.run([sys.executable,'-B',str(repo/'output/codex_batch'/script),*map(str,args)],capture_output=True,text=True,check=True);assert 'BAD'not in r.stdout+r.stderr;(R/script.replace('.py','.txt')).write_text(r.stdout+r.stderr)
unchanged=['export/mm6_jak1.glb','export/mm6_jak1_body_unmerged.glb','source/mm6_jak1.blend','integration/actors.yml','textures/jak1_ramps_runtime.json']
for path in unchanged:assert sha(P/path)==before[path],path
combined=[]
for name in ['mm6_jak1_combined.glb','mm6_jak1_lods.glb','mm6_jak1_runtime_lod0.glb']:
 old,ob=read_glb(R/'before/export'/name);new,nb=read_glb(P/'export'/name)
 assert bytes(nb[:len(ob)])==bytes(ob)
 for field in ['nodes','skins','animations']:assert old[field]==new[field],(name,field)
 combined.append({'file':'export/'+name,'all_original_binary_bytes_preserved':True,'nodes_skins_animation_JSON_unchanged':True,'body_attributes_equal':True})
old,_=read_glb(R/'before/export/mm6_jak1_staff.glb');new,_=read_glb(P/'export/mm6_jak1_staff.glb');assert old['nodes']==new['nodes']
invariance={'byte_identical':{x:sha(P/x)for x in unchanged},'combined':combined,'staff_attachment_nodes_identical':True,'Staff_and_StaffTip': 'Body nodes and animation data are byte-identical; grip origin and socket transform unchanged.'};save(R/'invariance.json',invariance)
for path in ['export_validation.json','playback_check.json','clips_front.jpg','clips_left.jpg','clips_three_quarter.jpg','viewer_a.png','viewer_b.png','viewer_c.png','viewer_head.png']:
 shutil.copy2(P/'review'/path,R/path)
play=json.loads((R/'playback_check.json').read_text());assert len(play['playback'])==16 and all(x['ok']for x in play['playback'])and not play['errors']
viewer={'command':'node level_generation/creatures/claude_shared/check_viewer.mjs http://127.0.0.1:8926/level_generation/creatures/mm6_jak1_codex/review/viewer/ 90','exit_code':0,'ready':'true','errorHidden':True,'consoleErrors':[],'switched':24,'failed':[],'revision':'mm6_jak1_codex_review_round4_staff','models':json.loads((P/'review/viewer/manifest.json').read_text())['models']};save(R/'viewer_check.json',viewer)
paths=['export/mm6_jak1_staff.glb','export/mm6_jak1.glb','export/mm6_jak1_body_unmerged.glb','export/mm6_jak1_combined.glb','export/mm6_jak1_lods.glb','export/mm6_jak1_runtime_lod0.glb','source/mm6_jak1_staff.blend','source/mm6_jak1.blend','integration/actors.yml','gates.json']+[f'textures/round4_staff/{x}.png'for x in ['basecolor','metal_rough','normal']]+[f'review/viewer/mm6_jak1_{x}.glb'for x in 'abc']
files=[{'path':x,'sha256':sha(P/x),'bytes':(P/x).stat().st_size,'changed':sha(P/x)!=before.get(x),'before_sha256':before.get(x)}for x in paths];save(R/'files.json',files)
metrics=json.loads((R/'visual_metrics.json').read_text());tex=json.loads((R/'texture_audit.json').read_text())
assert metrics['rows'][0]['minimum_iou']>=.99 and metrics['rows'][0]['minimum_ssim_bbox']>=.95
assert all(x['pooled_iou']>=.97 for x in metrics['rows'][1:])
worst=lambda name:max(x['worst']for x in g['gates']if x['gate']==name and x['worst']is not None)
review={'round':4,'status':'PASS: fixed staff reduction complete','user_acceptance':'Entire Jackalman body accepted 2026-10-13; staff reduction submitted for review','files':files,'staff_before':[2018,1108,503,472],'staff_triangles':[866,472,214,86],'body_triangles':[7480,4113,1816,595],'integration_actors_changed':False,'shared_gate_counts':g['counts'],'shared_gates':'review/round4/shared_gates/gates.json','grip_gap_mm':worst('grip_gap_mm'),'grip_penetration_mm':worst('grip_penetration_mm'),'viewer_combinations':24,'playback_samples':16,'loader_BAD_lines':0,'visual_metrics':'review/round4/visual_metrics.json','credits_this_round':0,'credits_total':40,'credit_limit':100,'native_integration_owner':'orchestrator'};save(R/'validation.json',review)
for path in ['export/lods.json','export/export_info.json']:
 d=json.loads((P/path).read_text());d['triangles']=[8346,4585,2030,681]if'lods'in path else 8346;d['staff_review_round']=4;save(P/path,d)
s=json.loads((P/'review/gates_summary.json').read_text());s.update(review_round=4,status='staff_reduction_pass; accepted_body_byte_identical',shared_gate_counts=g['counts'],shared_gates=review['shared_gates'],canonical_glb_sha256=sha(P/'export/mm6_jak1_runtime_lod0.glb'),runtime_exports={x:sha(P/x)for x in ['export/mm6_jak1.glb','export/mm6_jak1_staff.glb']},staff_triangles=review['staff_triangles'],combined_triangles=[8346,4585,2030,681],grip_gap_mm=review['grip_gap_mm'],grip_penetration_mm=review['grip_penetration_mm'],g6_prop_body_mm=worst('prop_body_penetration_mm'),binary_parity='review/round4/invariance.json',staff_visual_metrics='review/round4/visual_metrics.json');s.pop('g6_dense_lod0_staff_mm',None);save(P/'review/gates_summary.json',s)
now=datetime.datetime.now(datetime.timezone.utc).isoformat();progress=json.loads((P/'creature_3d_progress.json').read_text());progress.update(stage='review_round4_handoff',substep='staff_reduction_validated',user_acceptance=review['user_acceptance'],next_action='Orchestrator: install only revised staff GLB through tools/install_model.py --world mm6; retain accepted body and actors.yml; native visual check.',review_handoff_utc=now,technical_completion_utc=now,artifacts=files,gates=s,open_review_items=['Staff reduction artistic review and native lighting check assigned to orchestrator/user; body explicitly accepted.'])
progress['stages']['runtime_integration']['status']='awaiting_orchestrator_round4_staff_only';progress['stages']['lod_fit']={'status':'staff_fixed_target_pass; body_accepted_unchanged','evidence':'review/round4/visual_metrics.json'};progress['reviews']=[x for x in progress['reviews']if x.get('round')!=4]+[review];save(P/'creature_3d_progress.json',progress)
rows='\n'.join(f"| {r['lod']} | {r['actor_height_px']} | {r['before_triangles']} → **{r['after_triangles']}** | {r['after_triangles']/866:.2%} | {r['pooled_iou']:.6f} | {r['minimum_ssim_bbox']:.6f} |"for r in metrics['rows'])
table='\n'.join(f"| `{r['path']}` | {'changed/new'if r['changed']else'byte-identical'} | `{r['sha256']}` |"for r in files if r['path']in ['export/mm6_jak1_staff.glb','export/mm6_jak1.glb','source/mm6_jak1_staff.blend','integration/actors.yml'])
section=f"""## Review round 4 (staff reduction)

The user accepted the entire Jackalman on 2026-10-13. **Only the staff changes.** Its LOD0 falls from
2,018 to **866 triangles (57.09% fewer)**; lower LODs are **472 / 214 / 86**, strictly decreasing.
Body geometry, all body LODs, skin/cloth colours, rig, animation clips, timings and actor bindings are preserved.
The delivered body GLB and packed body master are byte-identical to round 3.

[Staff close-ups](review/round4/staff_closeup.png) · [staff at melee size](review/round4/staff_ingame.png) ·
[700-pixel full actor](review/round4/lod0_comparison.png) · [current viewer](review/viewer/index.html).
Comparisons use identical cameras and lighting. They are offline renders, not native game captures.

### Fixed target and visual comparison

| LOD | Actor height px | Staff triangles | Fraction of new LOD0 | Pooled actor IoU, 8 views | Minimum bbox SSIM |
|---|---:|---:|---:|---:|---:|
{rows}

One fixed topology target, without a target search. The 250-triangle accepted hook topology is retained at LOD0;
a ten-sided shaft replaces nested cylinders and raised wraps. Bands, incisions and wraps are baked from the
accepted staff into base colour, material response and OpenGL tangent normals. Neck and grip surfaces were
fitted without adding triangles. Both hand animations, attachment node, grip origin and **StaffTip** stay fixed.

LOD0 minimum eight-view full-actor IoU is **{metrics['rows'][0]['minimum_iou']:.6f}**. Lower LODs pass the
0.97 pooled threshold at their switch sizes, compared with the previously accepted matching LOD.
These scores include the unchanged body. Staff-only silhouette IoU at 700-pixel actor scale is **0.9390 front /
0.9662 quarter**: baking the raised wraps removes small edge bumps. Close-ups expose those differences;
the agent's in-game-size comparison finds the hook, pole, bands and grip appearance retained.
[Full numeric receipt](review/round4/visual_metrics.json), [550px](review/round4/lod1_comparison.png),
[220px](review/round4/lod2_comparison.png), [88px](review/round4/lod3_comparison.png).
The accepted body's historical round-2 LOD3 limitation is outside this staff-only revision.

All staff LODs and tiers share **one 1024×1024 three-map set** in `textures/round4_staff/`.
There are 26 UV islands, **20.48px border padding**, and no overlap between their 16px dilations.
Average surface texel density is **{tex['after']['linear_texels_per_m']:.1f} texels/m**, versus
{tex['before']['linear_texels_per_m']:.1f} before. Source maps were 576×1024; the square atlas provides the
required gutters. [Texture audit](review/round4/texture_audit.json). Staff GLB size is 903,352 bytes,
versus 1,392,640 before. Skin, gold, cloth and all body maps remain unchanged.

### Files and hashes

| File | Status | SHA-256 |
|---|---|---|
{table}

Body colour/shadow triangles remain **7480 / 4113 / 1816 / 595**. Combined review counts become
**8346 / 4585 / 2030 / 681**. The updated `export/mm6_jak1_combined.glb`, `mm6_jak1_lods.glb`,
`mm6_jak1_runtime_lod0.glb`, and three viewer GLBs carry only the new staff; original body attributes,
nodes, skin and animation data are retained. [All file hashes](review/round4/files.json) ·
[body/socket invariance](review/round4/invariance.json).

**`integration/actors.yml` did not change.** The new editable staff is `source/mm6_jak1_staff.blend`.
The accepted `source/mm6_jak1.blend` is deliberately unchanged and still embeds its historical staff preview.
Use the separate staff source and current combined GLBs for this revision.

### Final checks

- Mandatory shared runner at **48 Hz**: **6,602 PASS, 0 FAIL, 0 UNVERIFIED** (128 INFO, 56 N/A),
  covering G4–G6, elbow/twist, palms, contact, posture, feet and smoothness across all clips/LODs.
  Worst grip gap **{review['grip_gap_mm']:.3f} mm**, penetration **{review['grip_penetration_mm']:.3f} mm**.
  [Final report](review/round4/shared_gates/gates.md).
- Grip surface selectors now cover the full pole, because the long reduced triangles cross the old narrow
  selector bounds. Contact tolerance remains **3 mm**. LOD3 ratio limit tightened from 24% to 10%.
  Intermediate fitting failures are superseded by the hash-bound final report.
- `check_bindings.py` and `check_weights.py`: **no BAD line**, worst weight error **0.000000**.
  [Bindings](review/round4/check_bindings.txt) · [weights](review/round4/check_weights.txt).
- Split/export equivalence passes. Browser viewer **24/24**, normal/quarter-speed playback **16/16**, no errors.
  [Export receipt](review/round4/export_validation.json) · [viewer](review/round4/viewer_check.json) ·
  [playback](review/round4/playback_check.json).
- Refreshed and inspected staff comparisons, tier viewer, and clip sheets:
  [front](review/round4/clips_front.jpg), [side](review/round4/clips_left.jpg),
  [three-quarter](review/round4/clips_three_quarter.jpg).

**Orchestrator next step:** install only `export/mm6_jak1_staff.glb` with
`python3 tools/install_model.py level_generation/creatures/mm6_jak1_codex/export/mm6_jak1_staff.glb --world mm6`.
Keep the accepted body and actor entries. Native lighting/integration review remains with the orchestrator.
No game launches, builds, installs or commits were performed. One background Blender process at a time,
four threads. Additional credits **0**, total **40/100**. Lease and own viewer processes released at handoff.

"""
h=P/'HANDOFF.md';old=h.read_text();start=old.find('## Review round 3 (skin tone)');h.write_text('# MM6 Jackalman / jak1 — review handoff\n\nRound 4 staff reduction is ready. Accepted body unchanged; checks pass. **40/100 credits spent.**\n\n'+section+old[start:])
f=P/'README.md';s=f.read_text();start=s.index('## Current deliverables');s='# MM6 Jackalman — review round 4 (staff reduction)\n\nThe user accepted the entire body. Only the staff was reduced: **2018 → 866 triangles**, with LODs\n**472 / 214 / 86**. Body export, animations, skin, sockets and actor bindings are byte-identical.\n[Close-ups](review/round4/staff_closeup.png) · [in-game-size comparison](review/round4/staff_ingame.png) ·\n[round-4 handoff](HANDOFF.md#review-round-4-staff-reduction). All 6,602 shared gates and 24 viewer switches pass.\n40/100 credits spent; round 4 costs zero. The orchestrator installs only the new staff.\n\n'+s[start:];s=s.replace('Staff: **2018 / 1108 / 503 / 472**.','Staff: **866 / 472 / 214 / 86**.').replace('[gates](review/round2/shared_gates/gates.md)','[gates](review/round4/shared_gates/gates.md)');s=s.replace('## Unattended decisions','## Unattended decisions\n\nRound 4 uses one fixed staff target, retaining the hook and baking wraps onto a ten-sided shaft.\nFixed-count grip fitting preserves both accepted hands. Shared 1K maps have 16px dilated gutters.\nThe separate editable source is `source/mm6_jak1_staff.blend`; the accepted body master is unchanged.\nNo animation, body LOD or palette corrections were authorized or made. See round-4 HANDOFF for metrics.\n');f.write_text(s)
(R/'README.md').write_text('# Staff reduction — round 4\n\nCurrent evidence: `shared_gates/`, `validation.json`, `files.json`, `invariance.json`, `texture_audit.json`,\n`visual_metrics.json`, `viewer_check.json`, and the labelled comparison PNGs.\n\n`before/` is the accepted input snapshot. `first_gate_findings/`, `grip_probe.json` and `grip_check.json`\nare intermediate diagnostics, superseded by the final shared report. `grip_fit.json` and\n`grip_neck_fit.json` record the fixed-topology contact fitting. No body or animation edits.\n')
print('ROUND4 HANDOFF RECORDED',review['grip_gap_mm'],sha(P/'export/mm6_jak1_staff.glb'))
