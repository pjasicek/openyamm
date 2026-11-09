import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round6';v=json.loads((R/'validation.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for rel in ['export/mm6_arc1.glb','export/mm6_arc1_bow.glb','export/mm6_arc1_arrow.glb']:
 f=v['files'][rel];counts=list(f['triangles'].values())[:4];rows.append(f"| [{Path(rel).name}]({rel}) | {' / '.join(map(str,counts))} | {f['bytes']} | {f['sha256']} |")
table='\n'.join(rows);counts=v['shared_runner']['counts'];integration=v['files']['integration/actors.yml']['sha256']
section=f"""## Review round 6

**Scoped review complete. Attack and Cast play at 1.5x speed: 1.733333 s -> 1.155556 s; release 1.200 s -> 0.800 s.** Cast remains the exact 189-channel Attack copy under its distinct name. Every keyed pose is unchanged; only input clocks changed. The arrow becomes hidden at 0.822222 s. No thresholds were relaxed.

Walking, Standing and Fidget already had identical first/last keys, so their animation data was retained. Running binds Walking on all tiers. The exported GLB evaluator compared all 63 joints, local TRS and world matrices at exact endpoints: maximum position difference **0 mm**, maximum rotation difference **0 degrees**, matrix/component difference **0**. Zero-scale hidden-arrow matrices and local quaternion keys also match exactly.

| Clip | First / last time (s) | Max bone position / rotation difference | Left heel / toe at both ends (mm) | Right heel / toe at both ends (mm) |
|---|---|---|---|---|
| Walking | 0 / 0.800000012 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Running (Walking alias) | 0 / 0.800000012 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Standing | 0 / 2 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Fidget | 0 / 2 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |

These are near-LOD deformed surface samples using the shared runner's heel/toe selection. Lowest sole points at both endpoints: left 1.698 mm, right 1.894 mm. Every colour/shadow LOD is recorded in [loop_endpoints.json](review/round6/loop_endpoints.json). At the final 48 Hz sample before Walking wraps (0.791667 s), left heel/toe are 3.267 / 4.379 mm and right 5.037 / 6.219 mm. This final recovery movement stays within the 10 mm contact gate; the exact final frame matches frame zero. Retaining the duplicate boundary key preserves interpolation to the floor pose.

[Loop comparison](review/round6/loop_comparison.jpg) · [Attack timing](review/round6/attack_timing_comparison.jpg) · [Attack soles at release](review/round6/browser_attack_feet.png) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).

### Files and integration

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{table}

Only the body runtime GLB changed; bow/arrow files and all triangle counts are unchanged. Body size: 6353884 -> {v['files']['export/mm6_arc1.glb']['bytes']} bytes. All meshes, normals, UVs, skin weights, materials, skeleton nodes and embedded PNG bytes equal R5. Texture memory remains **53.125 MiB**, ten shared images, 16 px dilated margins. Both bracers, carry pose, grip, all LODs, flat feet and other clips remain accepted-as-is.

**integration/actors.yml changed**, SHA-256 **{integration}**. Its only edit is nine impact values changing from 1.2 to 0.8 across melee/ranged/cast on all three tiers. IDs 475/476/477, scale/yaw/stride, run alias and Socket_Arrow_Release remain. Updated timing prose in integration/regression.md and integration/playbook_notes.md.

Editable masters retimed: work/rig_equipped.blend, work/rig_textured.blend, work/round2/lod0.blend through lod3.blend; runtime_authoring.blend rebuilt from the final viewer export. Rebuilt three viewer GLBs and manifest, Attack/Cast sheets, release hand-sheet timestamps and loop comparison sheets. [Full hashes/sizes](review/round6/artifact_manifest.json). R5 exports, integration, scripts and editable masters retained under review/round6/baseline/.

### Validation and open findings

Shared runner rerun on all clips, colour/shadow LODs and props: **FAIL**, {counts}. [Report](review/round6/shared_final/gates.md), [comparison](review/round6/shared_comparison.json). This is not an all-gates acceptance claim.

Attack/Cast feet pass on all visible LODs: heel/toe <= 5.180381 mm, sole tilt <= 0.933210 degrees, floor penetration 0. Pre-existing far shadow sole tilt and other accepted-as-is findings remain recorded.

Relative to R5, six head-contact rows now fail (10.289 mm versus 10 mm at 0.270833 s; colour0/1 and shadow0 in Attack/Cast), and four arrow-contact rows now pass. Retiming shifts the fixed 48 Hz sample phases; keyed poses are identical. No geometry or pose changes were made to chase these inherited contacts.

[check_bindings.py / skin weights](review/round6/check_bindings.log): exit 0, no BAD line. [Viewer](review/round6/check_viewer.log): all 24 tier/clip switches pass, no console errors; eight browser captures. Comparison sheets and release soles visually checked. All 71 native source files unchanged.

Decisions: kept already exact loop boundaries; interpreted Running using its Walking alias; directly retimed animation accessors to preserve accepted mesh/maps, and retimed editable masters. Budget: **0 additional credits, 40 / 100 total**. Lease released at handoff. No game launches, builds, installs, assets_dev writes or commits. Runtime regression and game captures remain the orchestrator's responsibility.

Reproduction with a reclaimed lease: scripts/round6_retime.py (reads R5 baseline), scripts/round5_viewer.py, scripts/round6_audit.py via the four-thread Blender wrapper, scripts/round6_check_viewer.py, scripts/round6_validate.py, scripts/round6_sheets.py, scripts/round6_record.py. Historical generators predate this timing pass; final exports and R6 scripts are authoritative.

"""
text=(R/'baseline/HANDOFF.md').read_text();title,rest=text.split('\n',1);(P/'HANDOFF.md').write_text(title+'\n\n'+section+rest.lstrip())
(P/'README.md').write_text("""# MM6 BArcher arc1 — review round 6

Attack and its exact Cast copy now play 1.5x faster: 1.155556 s duration, 0.800 s release. Staged actor events updated. Accepted poses, meshes, bracers, LODs and textures are preserved; memory remains 53.125 MiB.

All 63 bone transforms match exactly at Walking, Standing and Fidget loop endpoints: 0 mm / 0 degrees. Running aliases Walking. Endpoint heel/toe heights are 3.14–4.48 mm; the last Walking sample before wrap stays below 6.22 mm. No loop pose correction was necessary.

[HANDOFF.md](HANDOFF.md) records files, hashes, counts, decisions and validation. Bindings and all 24 viewer switches pass. Shared gates still report 363 failures (361 in R5); existing contacts are accepted-as-is for this narrow pass, not certified as passing. No game/build/install/commit. Budget 40/100 credits; lease released at handoff.

![Loop endpoints](review/round6/loop_comparison.jpg)

[Attack timing](review/round6/attack_timing_comparison.jpg) · [Shared audit](review/round6/SHARED_AUDIT.md) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).
""")
(R/'SHARED_AUDIT.md').write_text(f"""# Review round 6 shared audit

Verdict: FAIL, {counts}. Configuration and thresholds unchanged from R5. Scoped timing, loop endpoints, shooting soles, binding and viewer checks pass.

Six new failing head-penetration rows: 10.289315 mm > 10 mm in Attack/Cast colour0, colour1 and shadow0 at 0.270833 s. Four former arrow/body rows pass at shifted sample phases. All pose outputs and mesh/weight data equal R5; only shooting clocks changed. Existing contacts remain outside the accepted-as-is R6 scope.

Far shadow sole tilt remains above 3 degrees, as in R5. All visible shooting LODs: heel/toe <= 5.180381 mm, tilt <= 0.933210 degrees, no floor penetration. No waiver or threshold relaxation added.

[Runner](shared_final/gates.md) · [Row comparison](shared_comparison.json) · [Validation](validation.json) · [R5 audit](../round5/SHARED_AUDIT.md).
""")
progress=json.loads((P/'creature_3d_progress.json').read_text());progress['runtime']['installation']='round6_staged_with_open_shared_gate_findings';progress['validation']={'report':'review/delivery_validation.json','status':v['status'],'shared_runner':v['shared_runner'],'viewer':'review/round6/check_viewer.log','viewer_switches':24,'skin_weights':'review/round6/check_bindings.log'}
progress['review_round_6']={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'scoped_timing_and_loop_review_complete','credits_spent':0,'total_credits':40,'integration_actors_yml_changed':True,'changed_runtime_files':['export/mm6_arc1.glb'],'shared_runner':v['shared_runner'],'retiming':v['retiming'],'loop_report':'review/round6/loop_endpoints.json','decoded_texture_mib':53.125,'handoff':'HANDOFF.md'}
progress.pop('artifacts',None)
progress.update(stage='review_round_6_handoff',status='needs_review',user_acceptance='review_round_6_pending; other artwork accepted_as_is',next_action='Orchestrator integrates faster Attack/Cast and 0.8 s release events; loop endpoints verified exact. Shared findings documented without widening this pass.',updated_at=progress['review_round_6']['recorded_at'])
for rel,f in v['files'].items():progress.setdefault('selected_artifacts',{}).setdefault(rel,{'path':rel}).update(f)
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
paths=set(json.loads((P/'review/round5/artifact_manifest.json').read_text()))
paths.update(str(x.relative_to(P))for x in R.rglob('*')if x.is_file()and 'baseline'not in x.relative_to(R).parts and x.name!='artifact_manifest.json')
paths.update(str(x.relative_to(P))for x in (P/'scripts').glob('round6*'))
paths.update(['HANDOFF.md','README.md','creature_3d_progress.json','integration/actors.yml','integration/regression.md','integration/playbook_notes.md','scripts/viewer_manifest.py','review/delivery_validation.json'])
manifest={rel:{'sha256':sha(P/rel),'bytes':(P/rel).stat().st_size}for rel in sorted(paths)if(P/rel).is_file()};(R/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Round6 handoff; artifacts',len(manifest))
