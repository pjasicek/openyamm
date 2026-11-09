
import json,hashlib,datetime,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
J=lambda n:json.loads((P/n).read_text())
H=lambda n:hashlib.sha256((P/n).read_bytes()).hexdigest()
G=J('review/round2/shared_gates/gates.json');B=J('review/round2/baseline_gates/gates.json')
V=J('review/export_validation.json');M=J('review/runtime_metrics.json');viewer=J('review/viewer_check.json')
assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD' not in (P/'review/bindings_check.txt').read_text()
assert G['status'] != 'RUNNING'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for name,entry in J('review/sheet_manifest.json').items():
 sheet=Image.new('RGB',(1600,1195),(235,235,235));draw=ImageDraw.Draw(sheet)
 draw.text((12,10),name+' — review round 2; actual export',font=font,fill='black')
 for row,view in enumerate(entry['views']):
  draw.text((12,50+row*380),view,font=font,fill='black')
  for i,t in enumerate(entry['times_seconds']):
   im=Image.open(P/f'review/frames/{name}_{i}_{view}.png').convert('RGB').resize((320,320),Image.Resampling.LANCZOS)
   sheet.paste(im,(i*320,76+row*380));draw.text((i*320+10,400+row*380),f'{t:.3f} s',font=font,fill='black')
 sheet.save(P/'review/sheets'/f'{name}.png')
sheet=Image.new('RGB',(1440,1000),'white')
for i,f in enumerate(range(34,40)):
 im=Image.open(P/f'review/viewer_horn_{f}.png').convert('RGB');im.thumbnail((480,500))
 sheet.paste(im,((i%3)*480,(i//3)*500))
sheet.save(P/'review/round2/horn_sequence.png')
paths=['export/mm6_min1.glb','export/mm6_min1_axe.glb','work/production_master.blend',
 'work/round1_lod1.blend','work/round1_lod2.blend','work/round1_lod3.blend','integration/actors.yml']
hashrows='\n'.join(f'| {n} | {H(n)} |' for n in paths)
body=[m['triangles'] for m in V['mm6_min1.glb']['meshes'][:4]]
axe=[m['triangles'] for m in V['mm6_min1_axe.glb']['meshes'][:4]]
assert body==[7876,1674,1591,735] and axe==[1854,389,343,127]
table='\n'.join(f'| {i} | {b} | {a} |' for i,(b,a) in enumerate(zip(body,axe)))
rows=[r for r in G['gates'] if r['lod']=='Minotaur/colour0']
openrows=[r for r in G['gates'] if r['status'] in ['FAIL','UNVERIFIED']]
(P/'review/round2/open_findings.json').write_text(json.dumps(openrows,indent=2))
selected=[r for r in rows if r['clip'] in ['Attack','Death','Dead'] and r['status']=='FAIL'
 and r['gate'] not in ['grip_gap_mm','grip_penetration_mm','palm_grip_deg']]
faulttable='\n'.join(f"| {r['clip']} | {r['gate']} {r['region']} | {r['worst']:.4f} | {r['threshold']} |" for r in selected)
sole='\n'.join(f"| {r['clip']} | {r['region']} | {r['gate']} | {r['worst']:.3f} |"
 for r in rows if r['gate'] in ['rest_sole_height_mm','rest_sole_tilt_deg'])
gap="""The current shared runner has no head/neck angular-acceleration check: its acceleration loop covers arms,
forearms and hands. Its floor test is inside the sole loop; it does not test all body vertices or the axe.
Those requested certificates remain unverified. No custom gate implementation or shared-file edit was added.

The frozen round-1 export also fails this shared configuration. Old project reports do not certify this revision.
The new per-digit grip test, wrist roll against the unrolled forearm, and capped-cloth containment differ from
the previous project checks. This is not a waiver: all failed rows remain open. Some reduced cloth surfaces have
branched boundaries and some reduced hands lack digit samples. See the shared runner's VALIDATION.md for its
documented coverage differences. Resolve the configuration/coverage and remaining asset findings before integration."""
(P/'review/round2/GATE_COVERAGE.md').write_text('# Shared-gate coverage\n\n'+gap+'\n')
if not (P/'review/round2/before/README.md').exists():shutil.copy2(P/'README.md',P/'review/round2/before/README.md')
(P/'HANDOFF.md').write_text(f"""# MM6 BMinotaur — staged handoff

**Review round 2 exported; technical done criteria NOT met.** Shared audit: **{G['status']}**.
Viewer and loader checks pass. Budget **30/100 credits total, 0 this round**. No commit or installation.

## Review round 1

[Archived round-1 handoff](review/round2/before/HANDOFF.md) preserves its exact files, hashes and historical checks.
The accepted attack is the starting point. [Reduction evidence](review/round1/reduction/README.md) is unchanged.

## Review round 2

Kept the accepted Great Sword Slash (2) spatial swing. Smoothed head/neck quaternion curves; horns were already
rigidly weighted to B_Head. Shortened the early wind-up by 20%, smoothly returning to the old release rate.
Attack duration **{M['clips']['Attack']['duration']:.6f} s**; impact **0.947917 s**.

Death now uses local **anim_library/mixamo/Two Handed Sword Death.fbx**, fitted into a single backward collapse.
The arms use a transported elbow guide and distributed twist; fingers relax before release. Death lasts
**{M['clips']['Death']['duration']:.6f} s**; Dead is baked from exactly its terminal pose.
The axe follows the right hand until **0.18 s**, then drops with initial vertical velocity **−0.35 m/s** and
gravity **−9.81 m/s²**, drifts away from the legs, and settles against the floor. The rigid axe GLB is byte-identical
to round 1: its changed animation is in the body GLB.

**integration/actors.yml changed: YES.** All three melee/ranged impacts now use **0.947917 s**.
Preserved attack_ranged: Attack, no axe_head alias, distinct Cast at **1.516667 s** and Socket_Axe_Head.
Descriptors 580/581/582, skins min1_a/b/c, scale/stride and attachment Axe are unchanged.

| Runtime LOD | Body triangles | Axe triangles |
|---|---:|---:|
{table}

No triangle reduction, geometry change, weight change or texture rebake this round. Shadow counts also remain unchanged.

| File | SHA-256 |
|---|---|
{hashrows}

Also refreshed: review/viewer/mm6_min1_a.glb, mm6_min1_b.glb, mm6_min1_c.glb and manifest.json;
review/frames/, review/sheets/, review/viewer_*.png; README.md, ANIMATION_STUDY.md,
creature_3d_progress.json, gates.json and integration notes. [Full hashes](artifact_manifest.json).

## Verification and open findings

[Current shared gates](review/round2/shared_gates/gates.md): **{G['status']}**; **{G['counts']}**.
[Round-1 baseline](review/round2/baseline_gates/gates.md): **{B['status']}**; **{B['counts']}**.
These counts repeat evidence across LODs and are not counts of unique defects.
[All failed/unverified rows](review/round2/open_findings.json).

[Bindings](review/bindings_check.txt): no BAD line. [Viewer](review/viewer_check.json): 27/27, zero browser errors.
[Export validation](review/export_validation.json): loader, materials, skin weights, LOD structure and preserved
animation data pass; this does not override the failed motion audit. Shared Attack blade/timing checks pass.

Selected LOD0 failures, in addition to the grip and lower-LOD findings in the full report:

| Clip | Check | Measured | Limit |
|---|---|---:|---:|
{faulttable}

Shared rest-sole measurements (height in mm; tilt in degrees):

| Clip | Foot | Check | Maximum |
|---|---|---|---:|
{sole}

{gap}

Existing export bounds sample the complete LOD0 body at 240 Hz: Death minimum Z
**{M['clips']['Death']['bounds_min'][2]*1000:.4f} mm**, Dead
**{M['clips']['Dead']['bounds_min'][2]*1000:.4f} mm**. This supports the authoring floor fit but does not replace
missing shared full-body/axe floor coverage. Horn continuity was visually reviewed, not shared-gate certified.

## Review and integration boundary

[Attack](review/sheets/Attack.png), [Death](review/sheets/Death.png), [corpse](review/viewer_corpse.png),
[Death frame 21](review/viewer_death_21.png), [frame 36](review/viewer_death_36.png),
[horn sequence](review/round2/horn_sequence.png). Original images 47/48 remain in review/round2/before/.

This is a review candidate with unresolved technical findings, not an all-gates-pass installation handoff.
The orchestrator owns the remaining shared-runner/configuration/asset corrections and integration.
No game launch, build, assets_dev write, gameplay regression, shared-file edit or commit occurred.
Runtime look, role blending, indoor/outdoor presentation and gameplay timing remain untested.
""")
(P/'README.md').write_text("""# MM6 BMinotaur — review round 2

**Re-exported candidate; shared gates FAIL. Technical done criteria are not met.**
[HANDOFF.md](HANDOFF.md) gives current hashes, unchanged triangle counts and unresolved checks.
Budget: **30/100 credits**, zero new spending.

The accepted attack keeps its spatial swing, with smoother head/neck curves and a faster wind-up.
Impact is **0.947917 s**. Death uses local Two Handed Sword Death, a single fall, downward axe release and an exact
held terminal Dead pose. These are unattended fitting decisions; no further artistic approval was requested.
Horn weights, geometry and textures are unchanged.

[Viewer](review/viewer/index.html) · [Attack](review/sheets/Attack.png) · [Death](review/sheets/Death.png) ·
[shared gates](review/round2/shared_gates/gates.md) · [coverage gaps](review/round2/GATE_COVERAGE.md).

Viewer: 27/27; bindings: no BAD. These do not override the failed shared audit.
Canonical master: work/production_master.blend; lower native files: work/round1_lod1.blend through round1_lod3.blend.
Rebuild: scripts/round2_motion.py from work/round2_sources.blend, round2_export.py, round1_pack_maps.py,
round1_assemble_lods.py, finish_export.py, then the shared gate runner, checks and review renders.
The sprite-restore project ../mm6_min1/ remains read-only. No install, build, game launch or commit.
""")
note="""
## Review round 2

Accepted Attack spatial motion retained; early wind-up shortened by 20%; impact 0.947917 s.
Head/neck curves smoothed; rigid horn weights retained. Death now uses local Two Handed Sword Death:
single backward fall, axe release at 0.18 s, gravity drop and held terminal Dead pose.
Inspect Death at 0.1875, 0.375, 0.75, 1.5 and 2.4 s. Inspect the old Attack 34–39 phase after the timing shift.
Current shared-gate failures and missing head/neck/full-body/axe floor coverage are explicit in HANDOFF.md.
Historical custom gate passes are not evidence for this export. No game checks were run.
"""
for name in ['ANIMATION_STUDY.md','integration/regression.md','integration/playbook_notes.md']:
 f=P/name;text=f.read_text().split('\n## Review round 2')[0]
 if name=='integration/regression.md':text=text.replace('1.075000','0.947917')
 f.write_text(text+note)
progress=J('creature_3d_progress.json')
progress.update(status='staged_with_open_gates',stage='review',substep='round 2 exported; shared verification unresolved',
 review_round=2,review_round2_spent_credits=0,meshy_spent_credits=30,remaining_credit_budget=70,
 artistic_acceptance='Attack spatial motion accepted; round-2 corrections agent-reviewed only',
 open_technical_faults=['Shared gates FAIL; review/round2/open_findings.json',
 'Shared runner lacks head/neck acceleration and complete body/axe floor coverage'],
 next_action={'owner':'batch orchestrator','action':'Resolve shared coverage/configuration and remaining failures before integration.'},
 next='Resolve shared gate findings; not an automatic-install candidate',
 shared_gate='review/round2/shared_gates/gates.json',handoff='HANDOFF.md',
 updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
for k in ['precision_gate','acceleration_gate','surface_gate','completed_at']:progress.pop(k,None)
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
(P/'review/visual_review.json').write_text(json.dumps({'revision':'mm6_min1_codex_review_round2',
 'agent_review':'Single fall and downward axe drop visually improved; technical acceptance blocked by shared gates.',
 'inspected':['sheets/Attack.png','sheets/Death.png','viewer_death_21.png','viewer_death_36.png','viewer_corpse.png','round2/horn_sequence.png'],
 'shared_gate_status':G['status'],'artistic_acceptance':'not requested; unattended last review round'},indent=2))
(P/'review/viewer/feedback/user_feedback.json').write_text(json.dumps({'findings':[
 {'id':'round2-horns','observed':'Rigid weights retained; head/neck curves smoothed; shared jitter coverage missing.'},
 {'id':'round2-windup','observed':'20% shorter early wind-up; impact 0.947917 s.'},
 {'id':'round2-death','observed':'Library fall and downward axe drop replace rejected motion; technical gate findings remain.',
 'evidence':['../round2/before/user_47.png','../round2/before/user_48.png','../viewer_death_21.png','../viewer_death_36.png']} ]},indent=2))
files=J('artifact_manifest.json')['files']
for n in list(files):
 f=P/n
 if f.exists():files[n]={'sha256':H(n),'bytes':f.stat().st_size}
for directory in ['review/round2','review/viewer','review/sheets','review/frames','integration']:
 for f in (P/directory).rglob('*'):
  if f.is_file():
   n=str(f.relative_to(P));files[n]={'sha256':H(n),'bytes':f.stat().st_size}
for f in list((P/'scripts').glob('round2_*.py'))+list((P/'review').glob('viewer_*.png'))+[P/'gates.json',P/'round2_baseline.gates.json',P/'scripts/finish_export.py',P/'scripts/validate_exports.py',P/'scripts/capture_viewer.mjs']:
 n=str(f.relative_to(P));files[n]={'sha256':H(n),'bytes':f.stat().st_size}
(P/'artifact_manifest.json').write_text(json.dumps({'identity':'mm6:min1','revision':'review_round2',
 'status':'staged_with_open_gates','mesh_credits':30,'files':files},indent=2)+'\n')
print('HANDOFF records the actual',G['status'],'verdict;',len(files),'hashed files')
