"""Publish the measured round-4 handoff after every final-hash check succeeds."""
from pathlib import Path
import json,hashlib,csv,io,datetime,re
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
read=lambda path:json.loads(path.read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
v=read(P/'review/final_validation.json');visual=read(R/'final_visual.json');lod=read(R/'lod_gates.json');selection=read(R/'selection.json')
h=sha(P/'export/mm6_dwa1.glb');assert v['status']=='PASS'and visual['pass']and lod['pass']
assert h==v['body']['sha256']==visual['runtime_sha256']==lod['runtime_sha256']
before=read(P/'work/round4_before/review/final_validation.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
rows=[];curve_rows=[]
for kind in ['body','axe']:
 for level in range(4):
  d=read(R/f'{kind}_lod{level}_curve.json');m=visual['levels'][f'{kind}_lod{level}']['metrics'];n=v[kind]['triangles'][level];old=before[kind]['triangles'][level]
  assert n==selection[kind][level]['triangles']
  rows.append({'mesh':kind,'lod':level,'before':old,'after':n,'reduction_percent':100*(1-n/old),'min_iou':m['min_iou'],'min_ssim':m['min_ssim'],'gates':'PASS'})
  for step in d['steps']:
   chosen=step['blend']==selection[kind][level]['blend'];status='selected; final visual and rig gates PASS'if chosen else 'visual pass; superseded'
   if not step['visual']['pass']:status='rejected: visual threshold'
   elif step.get('uv_gate_pass')is False:status='rejected: UV foldover'
   elif step.get('rig_gate_pass')is False:status='rejected: cloth contact'
   curve_rows.append({'mesh':kind,'lod':level,'step':step['step'],'triangles':step['triangles'],'min_iou':step['visual']['min_iou'],'min_ssim':step['visual']['min_ssim'],'status':status})
with (R/'reduction_curve.csv').open('w')as f:
 writer=csv.DictWriter(f,fieldnames=list(curve_rows[0]));writer.writeheader();writer.writerows(curve_rows)
table='| Mesh | LOD | Before | After | Reduction | Minimum IoU | Minimum SSIM | Gates |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
for r in rows:table+=f"| {r['mesh'].title()} | {r['lod']} | {r['before']} | {r['after']} | {r['reduction_percent']:.2f}% | {r['min_iou']:.6f} | {r['min_ssim']:.6f} | PASS |\n"
curve_md='# Triangle minimisation — round 4\n\n'+table+"""
Reference: the accepted round-3 mesh at each corresponding LOD. LOD0 uses the viewer's 4.3 m orbit,
35-degree field of view and 820-pixel viewport. LOD1–3 use the engine's 500 / 200 / 80-pixel projected-bound
switch calibration. Four body poses (Standing, Running, Attack, Death) are compared from eight azimuths;
the axe has eight additional close-up/switch-distance views. SSIM uses Gaussian RGB windows over the
foreground union plus a five-pixel border, excluding the otherwise score-inflating empty background.
Every individual view must reach IoU 0.995 and SSIM 0.98.

Decimation uses planar dissolve followed by approximately 10% collapse steps, with face, hands/fingers,
joint regions, soles, eight-view visible contours and grip contact protected. Exported UV seams stay split;
additional UV foldover patches are protected. Rejected 10% steps are bracketed with smaller final cuts.
The LOD0 10% UV-safe trial reached SSIM 0.977570 and was rejected; the selected 7.51% cut passes.
Body LOD2's first visual pass failed cloth contact and was rejected. Its contact-protected 10% cut then
missed the visual limits, while 5% passes. LOD3 retains a small fitted tunic patch described below.
The last axe LOD0 trials at 2,013 / 1,907 triangles fail the texture/silhouette criteria.
The far axe levels reach the protected-geometry limit: further collapse produces no reduction.

Because the user accepted the existing LOD set and asked for no visible changes, lower levels are compared
to their accepted counterparts, rather than replacing them with denser close-range geometry. The preliminary
full-detail-reference trials remain in lod0_distance_trials/ for inspection. No fixed 50% chain was used.

All four colour LODs pass G4, G5, G6, actual cloth surface crossing and cloth stretch on all eight clips at
48 Hz. Elbow and palm frames use the identical shared rig/actions; LOD0 additionally passes strict soles,
gait, floor, blade event, posture and UV gates. Skin weights are checked on every final colour/shadow primitive.

See reduction_curve.csv and the eight *_curve.json files for every retained trial. Failed visual candidates
were rejected before rig testing; only the selected candidates are claimed to pass the complete final gates.
"""
(R/'reduction_curve.md').write_text(curve_md)
# Review sheets are derived from the final reimported models, not from an earlier candidate.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for role in ['Walking','Running']:
 sheet=Image.new('RGB',(1800,720),(30,33,37));draw=ImageDraw.Draw(sheet)
 for row,view in enumerate(['front','left','three_quarter']):
  for col in range(9):
   im=Image.open(R/f'{role}_{col}_{view}.png').convert('RGB').resize((200,200));sheet.paste(im,(col*200,row*240+30));draw.text((col*200+4,row*240+5),f'{role} {col*.1:.1f}s',font=font,fill='white')
 sheet.save(R/f'{role}_contact_sheet.jpg',quality=94)
sheet=Image.new('RGB',(1640,1720),(30,33,37));draw=ImageDraw.Draw(sheet)
for row,(tag,view)in enumerate([('body_lod0','Standing_0.png'),('axe_lod0','Standing_2.png')]):
 for col,folder in enumerate(['reference','final_export']):
  im=Image.open(R/tag/folder/view).convert('RGBA');bg=Image.new('RGBA',im.size,(70,73,77,255));bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(col*820,row*860+40));draw.text((col*820+12,row*860+10),tag+' / '+('accepted before'if col==0 else'reduced final'),font=font,fill='white')
sheet.save(R/'before_after.jpg',quality=95)
patch=read(R/'cloth_support.json')
section="""
## Triangle reduction

"""+table+f"""
The measured reduction preserves the accepted appearance, clips, tiers, prop design and bindings.
The strict eight-view limits determine the stopping point; the 15k ceiling is not the chosen target.
[Full curve and method](review/round4/reduction_curve.md), [trial CSV](review/round4/reduction_curve.csv),
[final hash-bound visual scores](review/round4/final_visual.json), [before/after sheet](review/round4/before_after.jpg).

The accepted LOD3 already had a covered trouser/tunic intersection. Six tunic vertices were fitted back to
the accepted full-detail surface (maximum {patch['max_position_delta_m']*1000:.3f} mm), with skin weights interpolated
from that same surface. This removes the intersection while preserving the required silhouette and texture scores.
The other candidate cloth corrections that changed the silhouette were rejected. LOD0 anatomy, rest feet,
Walking/Running, alternate Hit, axe grip and all timing remain accepted and unchanged.
[Patch receipt](review/round4/cloth_support.json), [all-LOD gates](review/round4/lod_gates.json).
The head-contact mask excludes the intentionally inserted neck below the measured collar top; the old fixed
height misclassified one far-LOD neck vertex. The existing local contact algorithm remains unchanged.
[Diagnostic correction](review/round4/contact_gate_correction.json).

## Review round 4

**Triangle minimisation complete; ready for orchestrator reinstall.**
Replace both runtime GLBs. Integration/actors.yml is byte-identical; no registry merge or timing change is needed.
All eight animation sample streams, channel targets, rest rig, inverse binds, material definitions, embedded
texture payloads and tier ramps are exact matches to round 3. [Parity](review/round4/artifact_parity.json).

Final files and SHA-256:

| File | SHA-256 | Triangles |
|---|---|---|
| export/mm6_dwa1.glb | {v['body']['sha256']} | {' / '.join(map(str,v['body']['triangles'][:4]))}; shadows same |
| export/mm6_dwa1_axe.glb | {v['axe']['sha256']} | {' / '.join(map(str,v['axe']['triangles']))} |
| export/mm6_dwa1.blend | {sha(P/'export/mm6_dwa1.blend')} | Packed reduced LOD0 master |
| integration/actors.yml | {sha(P/'integration/actors.yml')} | Unchanged |

Previous body hash: {before['body']['sha256']}. Previous axe hash: {before['axe']['sha256']}.
All four body/axe colour LODs, shadows, viewer tier GLBs, editable master, clip/LOD/tier/hand/foot sheets and
manifests were refreshed. The production scripts are scripts/round4_*.py; contact_final.py uses the measured collar plane for exposed-head sampling, and validate_export.py now requires
round-4 evidence. [Evidence hashes](review/round4/manifest.json).

At 48 Hz, every clip on every colour LOD passes G4/G5/G6 and cloth contact/stretch.
LOD0 maximum arm p99 is {max(x['G4_arm_p99']for x in v['clips'].values()):.2f}×; maximum hand stretch
{max(x['G5_hand_max']for x in v['clips'].values()):.3f}×. Arm/exposed-head/axe/blade penetration and tunic/trouser
surface crossings are zero. Elbows, accepted palm/grip frames, sole planes, visible walking swing,
grounded running, floor, source-relative motion and the 0.71875 s cutting event pass.
LOD0 UV overlaps/collapsed faces remain zero. Final weight-sum error over every colour/shadow skin primitive is
{v['body']['weight_sum_max_error']:.12g}, below 1e-4. check_bindings.py (including check_weights.py) prints no BAD line.
[Final validation](review/final_validation.json), [bindings](review/round4/bindings_check.json).

The viewer passes 24/24 tier/clip switches and 16/16 complete normal/half-speed playbacks, zero errors.
Agent inspection of the refreshed sheets confirms unchanged accepted rest feet, gait, tunic appearance,
alternate Hit and axe design. Native installation, loading, LOD transitions, lighting/shadows and indoor/outdoor
regression remain the orchestrator's checks.

**Additional credits: 0; total 40/100, 60 remain. No assets_dev writes, game launches, builds, shared-file edits
or commits. Workspace lease released at handoff.**
"""
f=P/'HANDOFF.md';s=f.read_text();s=s.split('\n## Triangle reduction')[0];prefix,history=s.split('\n## Review round 1',1)
prefix=prefix.replace('**Review round 3 technical criteria passed. Accepted Standing/Hit/axe retained; revised locomotion awaits review.**','**Review round 4 technical criteria passed. The user-accepted appearance and clips are retained.**')
prefix=re.sub(r'For round 3, replace the body GLB;[^\n]+','For round 4, replace both runtime GLBs. Integration/actors.yml is unchanged.',prefix)
prefix=prefix.replace('G4/G5/G6 measure LOD0; every reduced LOD additionally\npasses finite-data, index, joint-count, up-to-eight-influence, combined-weight normalization and variant validation,\nplus Standing/Attack visual review.','G4/G5/G6 and cloth gates cover all four colour LODs. Every colour/shadow primitive passes finite-data, index,\njoint-count, combined-weight normalization and variant validation; all LODs pass the measured visual limits.')
prefix=prefix.replace('**<1.3e-7**','**<1.4e-7**')
prefix=prefix.replace('12502 / 6251 / 2202 / 698',' / '.join(map(str,v['body']['triangles'][:4]))).replace('2630 / 1314 / 472 / 150',' / '.join(map(str,v['axe']['triangles'])))
for role,r in v['clips'].items():
 prefix=re.sub(r'^\| '+role+r' \|[^\n]+',f"| {role} | {r['G4_arm_p99']:.2f} | {r['G5_hand_max']:.3f} | {r['G6_max_contact_m']*1000:.3f} | 0 |",prefix,count=1,flags=re.M)
f.write_text(prefix+'\n## Review round 1'+history+section)
f=P/'README.md';s=f.read_text().replace('**Review round 3 complete; ready for orchestrator reinstall. Standing, new Hit and axe accepted; locomotion revised.**','**Review round 4 complete; reduced body and axe ready for orchestrator reinstall. Accepted appearance and clips retained.**').replace('grip; 2,630 triangles at LOD0','grip; 2,119 triangles at LOD0')
s=s.replace('| Body | 12502 | 6251 | 2202 | 698 |','| Body | 11563 | 5938 | 2091 | 629 |').replace('| Axe | 2630 | 1314 | 472 | 150 |','| Axe | 2119 | 1248 | 470 | 149 |')
s=s.split('\n## Review round 4')[0]+"""
## Review round 4

Reduced body LODs to 11563 / 5938 / 2091 / 629 and axe LODs to 2119 / 1248 / 470 / 149.
Protected collapse, UV carry, contact checks and eight-view IoU/SSIM determine the stopping point.
Lower levels use their already-accepted meshes as the appearance reference at the 500/200/80-pixel switches.
Rejected trials and this unattended reference decision are recorded in [the reduction curve](review/round4/reduction_curve.md).
A six-vertex covered LOD3 tunic patch restores the original detailed surface and clears its inherited intersection;
all eight animation streams, texture payloads, tier materials, rig and actor entries stay exact.

Every colour LOD passes all-clip deformation/contact/cloth checks; all final skin primitives pass normalization.
The viewer passes 24 switches and 16 playbacks. [Triangle reduction and round-4 handoff](HANDOFF.md#triangle-reduction).
Reproduction: search/refine scripts retain the measured trials; selection.json identifies the chosen local sources.
Run round4_finish_build.py with the leased four-thread Blender wrapper, then finish_review.py, viewer checks,
validate_export.py and round4_record.py. Preserved authoring masters and earlier-round backups remain under work/.
No new Meshy work; total 40/100 credits. No installation, game/build check or commit; the orchestrator integrates.
"""
f.write_text(s)
files=['export/mm6_dwa1.glb','export/mm6_dwa1_axe.glb','export/mm6_dwa1.blend','integration/actors.yml','integration/regression.md','integration/playbook_notes.md']
hashes={name:sha(P/name)for name in files}
manifest=read(P/'export/manifest.json');manifest.update(updated_utc=now,review_round=4,status='technical_handoff_ready',body=v['body'],axe=v['axe'],files_sha256=hashes);(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'export/lods.json').write_text(json.dumps({'body_triangles':v['body']['triangles'][:4],'axe_triangles':v['axe']['triangles'],'method':'Measured protected reductions at viewer/switch distances; review/round4/reduction_curve.md','runtime_sha256':h},indent=2)+'\n')
(P/'export/SHA256SUMS').write_text(''.join(f'{sha(f)}  {f.name}\n'for f in sorted((P/'export').iterdir())if f.is_file()and f.name!='SHA256SUMS'))
state=read(P/'creature_3d_progress.json');state.update(status='technical_handoff_ready',stage='review_round4_complete',technical_done=True,completed_utc=now,artistic_acceptance='round3 creature accepted; round4 appearance preserved by measured thresholds',integration_status='orchestrator_reinstall_required',next_action={'owner':'orchestrator','action':'Replace body and axe GLBs; keep actors.yml; run native integration and LOD checks.'},open_faults=[],deliverables={**hashes,'export/manifest.json':sha(P/'export/manifest.json')})
state['review_round4']={'completed_utc':now,'runtime_sha256':h,'axe_sha256':v['axe']['sha256'],'previous_runtime_sha256':before['body']['sha256'],'actors_yml_changed':False,'additional_credits':0,'reduction':rows,'evidence':'review/round4/manifest.json','native_checks':'Not run per Batch rules'}
state['decisions'].append({'round':4,'decision':'Minimise each accepted LOD against its own appearance at its switch distance; protect UV/contact patches and reject every visual or rig failure.'})if isinstance(state['decisions'],list)else None
(P/'creature_3d_progress.json').write_text(json.dumps(state,indent=2)+'\n')
evidence=[*R.glob('*.json'),*R.glob('*.md'),*R.glob('*.csv'),*R.glob('*.jpg'),*R.glob('lod*/*.json'),*P.glob('review/*.json'),P/'README.md',P/'HANDOFF.md',P/'creature_3d_progress.json',P/'export/manifest.json']
(R/'manifest.json').write_text(json.dumps({'round':4,'runtime_sha256':h,'axe_sha256':v['axe']['sha256'],'previous_runtime_sha256':before['body']['sha256'],'actors_yml_changed':False,'additional_credits':0,'files_sha256':{str(f.relative_to(P)):sha(f)for f in evidence if f.name!='manifest.json'},'reduction':rows},indent=2)+'\n')
print('ROUND4 HANDOFF RECORDED',h)

