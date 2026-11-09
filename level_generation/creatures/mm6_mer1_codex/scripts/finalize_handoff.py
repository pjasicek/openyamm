from pathlib import Path
import json,hashlib,shutil,datetime
P=Path('level_generation/creatures/mm6_mer1_codex')
def read(name):return json.loads((P/name).read_text())
def write(name,data):(P/name).write_text(json.dumps(data,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
shutil.copyfile(P/'references_hd/club_design.png',P/'review/club_design.png')
write('review/death_leg_clearance.json',{'source':'Standing Death Forward 02','window_seconds':[.8,1.8],'foot_delta_peak_m':[-.20,.15,-.4],'minimum_target_ankle_m':.16,'actual_boot_floor_m':.003,'pelvis_changed':False,'pole':'source knee direction','bake_hz':120})
atlas=read('review/shared_texture_atlases.json');runtime=read('review/runtime_package.json')
runtime.update({'body_atlas_size':atlas['mm6_mer1']['atlas_size'],'club_atlas_size':atlas['mm6_mer1_club']['atlas_size'],'shared_texture_sets':True,'chart_margin_pixels':16})
write('review/runtime_package.json',runtime)
gate=read('review/gates/gates.json');worst={}
for g in gate['gates']:
 if g['status']not in ['FAIL','UNVERIFIED','ERROR']:continue
 key=(g['gate'],g.get('region'),g['clip'])
 if key not in worst or (g.get('worst')or 0)>(worst[key].get('worst')or 0):worst[key]=g
write('review/shared_gate_open_findings.json',{'status':gate['status'],'counts':gate['counts'],'findings':list(worst.values()),'note':'No failed verdict was waived. QA hold; not cleared for integration.'})
artifacts=[]
for role,name in [('runtime_body','export/mm6_mer1.glb'),('runtime_club','export/mm6_mer1_club.glb'),('editable_source','export/mm6_mer1.blend')]+[(f'portable_{t}',f'export/mm6_mer1_portable_{t}.glb')for t in 'abc']:
 path=P/name;artifacts.append({'role':role,'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
write('export/artifacts.json',{'created_at':now,'status':'QA HOLD','artifacts':artifacts})
p=read('creature_3d_progress.json')
p.update({'stage':'handoff','current_stage':'handoff','current_substep':'shared_gate_qa_hold','status':'handoff_with_open_qa','technical_completion':False,'user_acceptance':'not_recorded','last_updated':now,'selected_artifacts':artifacts,'next_action':'Resolve or conclusively reconcile review/shared_gate_open_findings.json; rerun shared gates before orchestrator installation. No user input is required to resume asset QA.'})
p['required_components']=[{'id':'body','required':True,'artifact_role':'runtime_body'},{'id':'wooden_club','required':True,'artifact_role':'runtime_club'},{'id':'belt_pouch','required':True,'artifact_role':'runtime_body'}]
p['g1']['note']='Library selection completed before modelling; final ROM evidence is work/g4_final.json.'
p['rig_gate_checkpoint']={'blend':'work/reduction_master.blend','surface_gates':'review/final_selected_gates.json','runtime_geometry_identity':'review/runtime_geometry_identity.json','source_motion_trace':'review/final_source_motion_trace.json','source_motion_trace_pass':read('review/final_source_motion_trace.json')['pass'],'shared_gate_report':'review/gates/gates.json','shared_gate_status':gate['status'],'open_findings':'review/shared_gate_open_findings.json'}
p['texture_checkpoint']={'skin_report':'review/final_skin_luminance.json','all_skin_mean_p90_p95_not_darker':all(v['not_darker']for v in read('review/final_skin_luminance.json').values()),'shared_atlases':'review/shared_texture_atlases.json','meshy_credits':30}
p['handoff']={'path':'HANDOFF.md','integration_applied':False,'runtime_checks_run':False,'committed':False,'budget_credits':100,'spent_credits':30}
write('creature_3d_progress.json',p)
readme="""# MM6 Merchant (mer1)

**Asset production staged; QA HOLD. Technical done criteria are not fully met.**
The final shared validator reports FAIL despite earlier project-specific surface checks passing.
[HANDOFF.md](HANDOFF.md) records the findings and deliverables. No artistic acceptance is claimed.

Owner: codex-batch-mer1. FULL batch scope, **30/100 Meshy credits spent**, no paid jobs pending.
Only this project was written; [mm6_mer1](../mm6_mer1/) remains read-only source material.
No shared integration edits, builds, game launches or commits.

## Decisions and provenance

Native Merchant A/B/C: ids 577/578/579, palettes 252/253/770. Preserve the stocky torso, short legs,
pale round face, plain grey cap, blue collar, green/blue/red long tunic, brown binding, belt and right
pouch. Shoulders remain wider than the upper hips. The wooden club is belt-carried during native
town idle/walking, drawn for Attack and dropped in Death; it is a separate animated attachment.

The [animation study](source/ANIMATION_STUDY.md) predates modelling. Eight clips use owned local
Mixamo/humanoid-set sources. No paid animation. Standing/Fidget are upright and relaxed; Walking
has visible 8–9 cm lifts; Running is a separate jog with 1.302 m stride (0.84 × engine 1.55).
Attack is a planted library slash with about 20% discrete leg steps. The library forward Death
uses a corrected heel path and small cloth-chain adjustments. Cast aliases Attack: no native spells.
The final 120 Hz polish smooths arm transitions and limits local head/neck excursions.
Blow time is 0.8125 s, measured from actual club-tip motion toward the target.

The source-frame rig has 121 bones, including four twist helpers, 64 cloth bones and Club.
The club is carefully modelled from its [standalone design](references_hd/club_design.png),
with shaped grip/pommel/head and worn wood texture.
Meshy: Smart Topology 5, rig 5, body retexture 10, head retexture 10 credits.
Requests, hashes and receipts remain in the progress file and meshy folders.

## Selected output

Body LODs: 9546 / 2420 / 2385 / 952; club: 1122 / 290 / 252 / 200 triangles.
Combined: 10668 / 2710 / 2637 / 1152, strictly decreasing. LOD3 is **10.80%** of LOD0:
the 200-triangle club preserves IoU >=0.97 where smaller trials failed. This is the recorded
interpretation of “about 10%” combined guidance. No prior Merchant 3D installation imposed caps.
[Reduction curves and comparisons](review/reduction/README.md) retain the last-pass evidence.
The search began before the later fixed-target cost rule.

Each selected level was freshly unwrapped/rebaked from the unreduced textured source with per-piece
projection, tangent-normal transport and complete coverage. Final charts share one atlas set per
body/club, with unchanged texel density and 16-pixel dilated margins. Body: four maps 2048×6528;
club: three maps 2048×2816. Runtime cooking, mip appearance and memory need hardware checks.
Skin mean/p90/p95 linear luminance meets native values at every LOD; the far face received a 2.5%
linear correction after resampling. Cloth uses native 16-stop ramps; skin/leather/cap/collar stay
protected. The clasp is dull grey. Shadows are OPAQUE; rejected material extensions are absent.

## Review and resume

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html)
passes all 24 tier/clip switches. Clip sheets and hand close-ups are in review/.
[Bindings](integration/actors.yml) pass the batch checker with no BAD line.

Resume from **work/reduction_master.blend** and **review/reduction/selection.json**.
The editable deliverable is export/mm6_mer1.blend. Earlier work files are historical.
Assembly: export_selected.py, package_runtime.py, share_lod_atlas.py, prepare_viewer.py.
Keep the QA hold until the [shared findings](review/shared_gate_open_findings.json) are resolved.
"""
(P/'README.md').write_text(readme)
hashes='\n'.join(f"| [{a['path']}]({a['path']}) | {a['role']} | {a['sha256']} |"for a in artifacts)
handoff="""# MM6 Merchant — staged handoff, QA HOLD

**Production files exist, but the technical done criteria are not fully met.**
Shared runtime validation is **FAIL: 5954 PASS, 302 FAIL, 12 UNVERIFIED** (bone findings repeat
across colour/shadow LODs). Do not install this as a validated actor yet. No user acceptance.
**30/100 Meshy credits used**, all four jobs succeeded, none pending.

## Files

| File | Role | SHA-256 |
|---|---|---|
"""+hashes+"""

The runtime body contains four colour/four shadow LODs, eight clips and mer1_a/b/c tiers.
The club has matching LODs and attaches at Club. Portable A/B/C files combine the near actor with
baked native colours for ordinary glTF viewers. The .blend is packed/editable.
[artifacts.json](export/artifacts.json) records exact sizes and hashes.

[Interactive viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html):
24 switches passed; [receipt](review/viewer_check.json).
[Bindings receipt](review/bindings_check.txt): exit 0, no BAD line.

## Reduction and visual evidence

| LOD / projected pixels | Body | Club | Total | Body IoU | Club IoU |
|---|---:|---:|---:|---:|---:|
| 0 / 700 | 9546 | 1122 | 10668 | 0.99659 | 0.99169 |
| 1 / 550 | 2420 | 290 | 2710 | 0.97938 | 0.97443 |
| 2 / 220 | 2385 | 252 | 2637 | 0.97632 | 0.97240 |
| 3 / 88 | 952 | 200 | 1152 | 0.97065 | 0.97101 |

Near SSIM: body 0.95834, club 0.98861; the next reductions failed.
[Curves/table](review/reduction/README.md), [plot](review/reduction/curves.png),
[near body](review/reduction/body_lod0_comparison.jpg),
[near club](review/reduction/club_lod0_comparison.jpg),
[far body](review/reduction/body_lod3_comparison.jpg).
LOD3 totals 10.80%; retain the 200-triangle club for the hard IoU >=0.97 gate.
This is the documented “about 10%” decision, not a claim of <=10.00%.

Sheets: [Standing](review/clip_Standing.jpg), [Walking](review/clip_Walking.jpg),
[Running](review/clip_Running.jpg), [Attack](review/clip_Attack.jpg),
[Hit](review/clip_Hit.jpg), [Death](review/clip_Death.jpg),
[Dead](review/clip_Dead.jpg), [Fidget](review/clip_Fidget.jpg).
[Club design](review/club_design.png), [club close-up](review/club_close_left.png),
[final right grip](review/hand_export_R_front.png), [left hand](review/hand_export_L_front.png).
Sheets were visually inspected; they do not override numerical failures.

## Measurements

[Project surface checks](review/final_selected_gates.json) pass all four levels:
arm p99 stretch <=1.81253, hand max <=3.63955; hand/body 0 mm, forearm/body 0.65437 mm,
physical cloth/boot 0.19541 mm, sleeve/hand 0 mm. These use per-piece closed volumes and actual
cloth triangle samples. Their cached palm/elbow/prop adjuncts are historical evidence, not a
substitute for the newer final-runtime runner.

[Runtime identity](review/runtime_geometry_identity.json): accepted geometry/weights preserved;
all colour/shadow weight sums have error <=1.1921e-7.
[Exported 48 Hz source-motion trace](review/final_source_motion_trace.json): every clip passes.
Attack arm/hand acceleration is 6659.82/11720.35 deg/s²; Death 44126.61/43678.29, below
measured library-source-relative limits.
[Head/strike/scale](review/final_intent.json): exposed head contact 0 mm all clips;
blow 0.8125 s, tip speed 14.15388 m/s, target dot 0.90541.
The cylindrical grip proxy gives 1.45085 mm palm gap; it is not equivalent to the shared actual-mesh test.

Walking sole peaks ~88.6/89.0 mm, knees 60.0/60.7 degrees.
Running peaks ~118.4/118.5 mm; near sampled contact 100%, far 84.6%, far maximum lowest sole
16.06 mm. Standing/Fidget heel/toe heights <8.15 mm before the -1 mm binding correction.
[Skin](review/final_skin_luminance.json): mean/p90/p95 meet native values at every LOD.
[Atlases](review/shared_texture_atlases.json): one set per object, 16-pixel margins,
unchanged texel density, UV round-trip error <0.0002 texel.

## Open faults: shared verdict FAIL

[Full report](review/gates/gates.md), [JSON](review/gates/gates.json),
[deduplicated findings](review/shared_gate_open_findings.json).
No failed verdict was waived by raising thresholds after this run.

- Wrist roll up to 131.740 degrees, upper-arm roll 115.470, Attack wrist flexion 73.271;
  Fidget left palm/thigh 54.648. Axial roll travels through helper bones: assess anatomical
  frames and actual deformation before editing, but do not assume these flags are false.
- Actual grip: near thumb gap 3.921 mm, penetration 4.574 mm; far palm gap 5.954 mm and
  index 47.155 mm. Some reduced pinky regions have no weighted samples. The cylinder proxy
  missed these; actual grip geometry and reduced digit coverage require resolution.
- Club/body 14.623 mm at Attack 0.145833 s, during draw before the declared held interval.
  Verify contact classification and the draw path.
- Branched right-sleeve boundary; left cuff reports ~13 mm even at rest. Capped-hem containment
  reaches 85.795 mm in Death. The physical fabric test disagrees, and the shared README
  explicitly limits deeply folded hem planes. Reconcile garment regions/openings or repair
  the geometry; keep the hold meanwhile.
- Far foot yaw reaches 32.539 degrees with asymmetric heel/toe sampling, versus near sole-PCA
  heading <0.009 degrees. Inspect reduced soles and the inferred axis.

The config records pre-existing choices: free-palm 45 degrees, walking knees 39–61,
source-relative acceleration limits, component LOD3 ceiling 18% for the 200-triangle club.
The combined far ratio is above. Club kind is “other” because the runner's melee path always
requires a cutting edge; blunt-club strike timing is measured separately.
No shared runner or playbook was modified.

## Integration and resume

Exact three blocks: [integration/actors.yml](integration/actors.yml).
After QA is cleared, the orchestrator installs mm6_mer1.glb and mm6_mer1_club.glb under
worlds/mm6/models and merges those blocks. Key binding snippet:

~~~yaml
descriptor: Merchant A
model: worlds/mm6/models/mm6_mer1.glb
scale: 103.841591817
yaw_offset: -1.570796327
z_offset: -0.103841592
skin: mer1_a
# B/C: mer1_b/mer1_c; scale_reference: Merchant A
# cast: Attack; run: Running; stride_length: 0.84
# attack_melee / attack_ranged / cast impact: 0.8125
# attachment mm6_mer1_club.glb at node Club
~~~

Native ids 577/578/579, no spells. Scale matches 253 px ×0.699997 =177.099241 game units,
using measured Walking height 1.705475 m.
[Regression proposal](integration/regression.md): mm6-mer1-codex, oute3.odm, all ids,
size bounds 140–220; include indoor/outdoor checks.
[Playbook notes](integration/playbook_notes.md) record production lessons.

No shared files, runtime assets, engine/game code or sprite-restore source were edited.
No builds, game launches, runtime regression, captures, installation or commits, per batch rules.
Runtime texture memory/cooking, mip appearance and GPU performance remain untested.
Resume from work/reduction_master.blend and review/reduction/selection.json.
"""
(P/'HANDOFF.md').write_text(handoff)
with (P/'integration/playbook_notes.md').open('a')as f:f.write("""
- Final shared validation is FAIL; see HANDOFF.md and review/shared_gate_open_findings.json.
  Source-frame axial roll uses helper bones; reconcile anatomical frames and actual deformation.
  Neither the older custom pass nor a generic bone-angle flag alone establishes correctness.
- The shared melee path demands a cutting edge for a blunt club. This config declares other and
  retains a separate actual-tip trajectory and impact measurement.
- A cylindrical grip proxy missed actual pommel/hand intersections and reduced digit gaps.
  Resolve the actual-mesh findings before integration.
- Final texture charts share one set per body/prop, unchanged texel density, 16-pixel dilated
  borders. Large dimensions require cooking/memory checks during orchestrator integration.
""")
print('Wrote handoff with explicit QA hold, selected hashes and 30/100 credits.')
