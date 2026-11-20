"""Assemble the review evidence and honest geometry-only handoff."""
import json,hashlib,datetime,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];D=P/'review/round3'
J=lambda n:json.loads((P/n).read_text())
H=lambda n:hashlib.sha256((P/n).read_bytes()).hexdigest()
G=J('review/round3/shared_gates/gates.json');B=J('review/round2/shared_gates/gates.json');R=J('review/round3/geometry_receipt.json');V=J('review/export_validation.json');viewer=J('review/viewer_check.json')
assert G['assets'][0]['sha256']==R['body_sha256']==H('export/mm6_min1.glb')
assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD' not in (P/'review/bindings_check.txt').read_text()
assert all(v['unintended_skin_below_belt']==0 for v in R['boundaries']['after'].values())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for role,entry in J('review/sheet_manifest.json').items():
 sheet=Image.new('RGB',(1600,1195),(235,235,235));draw=ImageDraw.Draw(sheet);draw.text((12,10),role+' — review round 3; exported geometry, accepted animation unchanged',font=font,fill='black')
 for row,view in enumerate(entry['views']):
  draw.text((12,50+row*380),view,font=font,fill='black')
  for i,t in enumerate(entry['times_seconds']):
   im=Image.open(P/f'review/frames/{role}_{i}_{view}.png').convert('RGB').resize((320,320),Image.Resampling.LANCZOS);sheet.paste(im,(i*320,76+row*380));draw.text((i*320+10,400+row*380),f'{t:.3f} s',font=font,fill='black')
 sheet.save(P/'review/sheets'/f'{role}.png')
for role,t in J('review/round3/lod_frames.json')['poses']:
 sheet=Image.new('RGB',(1440,790),'white');draw=ImageDraw.Draw(sheet);draw.text((12,8),f'{role} {t:.3f} s — LOD0 / LOD1 / LOD2 / LOD3; front then back',font=font,fill='black')
 for level in range(4):
  for row,view in enumerate(['front','back']):
   im=Image.open(D/f'lod_frames/LOD{level}_{role}_{view}.png').convert('RGB').resize((360,360));sheet.paste(im,(360*level,40+370*row))
 sheet.save(D/f'hips_lods_{role}.png')
sheet=Image.new('RGB',(1440,1050),'white');draw=ImageDraw.Draw(sheet)
for i,(role,view) in enumerate([('standing','back'),('walking','front'),('attack','rear'),('fidget','back')]):
 im=Image.open(D/f'viewer_hips_{role}_{view}.png').convert('RGB').crop((0,110,1060,850));im.thumbnail((720,490));x=(i%2)*720;y=(i//2)*525;sheet.paste(im,(x,y+30));draw.text((x+10,y+6),f'{role} / {view} — final red tier',font=font,fill='black')
sheet.save(D/'closed_hips_viewer.png')
source=Path('/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/5707d78c-82f0-4aec-b463-6fc01c03b6f9/images')
for number in [74,75]:
 if (source/f'{number}.png').exists():shutil.copy2(source/f'{number}.png',D/f'before/user_{number}.png')
key=lambda r:tuple(r[k] for k in ['asset','clip','lod','gate','region'])
previous={key(r):r for r in B['gates']};newfails=[r for r in G['gates'] if r['status']=='FAIL' and key(r) in previous and previous[key(r)]['status']=='PASS']
cloth=[r for r in G['gates'] if r['gate']=='cloth_penetration_mm' and r['lod'].endswith('colour0')]
(D/'open_findings.json').write_text(json.dumps([r for r in G['gates'] if r['status'] in ['FAIL','UNVERIFIED','ERROR']],indent=2))
(D/'gate_delta.json').write_text(json.dumps({'before_counts':B['counts'],'after_counts':G['counts'],'new_failed_rows':newfails,'cloth_lod0':[{**r,'round2_worst':previous[key(r)]['worst']} for r in cloth]},indent=2))
clothrows='\n'.join(f"| {r['clip']} | {previous[key(r)]['worst']:.3f} | {r['worst']:.3f} |" for r in cloth)
(D/'GATE_COMPARISON.md').write_text(f"""# Shared gate comparison — round 3

Final body SHA-256: `{R['body_sha256']}`. Same shared runner and unchanged creature config/thresholds.
Round 2: **{B['counts']}**. Round 3: **{G['counts']}**. Verdict **{G['status']}**.
Rows repeat evidence across LODs; these are not counts of unique defects.

The 14 newly failing rows are eight previous-triangle-cap checks and six Death head-penetration rows.
LOD0 Death head penetration measures **23.377 mm at 1.479167 s** (previously 9.157 mm; limit 10 mm).
Head geometry, weights and animation are unchanged. Closing the body can alter the runner's open-surface
ray-parity sign estimate; that is a possible explanation, not a demonstrated false positive. The finding remains open.
The previous round's grip, arm-roll, gait, contact and coverage findings remain open; this geometry-only repair
preserves the user's accepted motion. No threshold was raised and no failing row was hidden.

## Cloth / legs against kilt

| Clip | Round 2 worst mm | Round 3 worst mm |
|---|---:|---:|
{clothrows}

These measurements are unchanged. All nine LOD0 cloth checks fail the 2 mm containment limit;
cloth setup for colour/shadow LOD1–3 remains UNVERIFIED because the existing hem boundary branches.
The shared tool uses one average exit plane for the ragged hem; it does not prove every reported outside
sample crosses fabric. These results still require review and must not be presented as passes.

The lower-mesh hem geometry and accepted cloth motion were preserved. Runtime topology inspection independently
confirms **zero unintended skin boundary edges below the belt on all eight body meshes**.
See [geometry receipt](geometry_receipt.json), [all findings](open_findings.json) and [shared report](shared_gates/gates.md).
The shared runner's existing head/neck jitter and full-body/axe floor coverage limits are documented in
[the round-2 coverage record](../round2/GATE_COVERAGE.md). No new motion gate code was authored.
""")
rows=[]
for level in range(4):
 old=R['boundaries']['before'][f'colour{level}'];new=R['boundaries']['after'][f'colour{level}'];rows.append(f"| {level} | {old['unintended_skin_below_belt']} → 0 | {old['below_belt_open_edges']} → {new['below_belt_open_edges']} | {old['triangles']} → {new['triangles']} |")
paths=['export/mm6_min1.glb','export/mm6_min1_axe.glb','work/production_master.blend',*[f'work/round1_lod{i}.blend' for i in range(1,4)],'integration/actors.yml']
hashrows='\n'.join(f'| {n} | {H(n)} |' for n in paths)
(P/'HANDOFF.md').write_text(f"""# MM6 BMinotaur — staged handoff

## Review round 3 (closed hips)

**Scoped hip repair exported and visually checked; full shared technical gates still FAIL.**
Budget **30/100 credits total; 0 this round**. No install, build, game launch or commit.

The old `trim_hidden_body.py` deleted skin that later showed through the ragged hem. Closed the waist and both
upper-thigh cut loops with one connected, pelvis/thigh-weighted fur surface at every colour LOD; regenerated all
shadow LODs. The legacy deletion script now fails explicitly instead of recreating the defect.
Also remapped **20/14/15/8** existing cut-rim triangles whose UVs sampled empty bake texels to opaque brown fur
already present in the atlas. The added surfaces use that same fur. No texture image or palette changed.
Kilt materials retain `doubleSided: true`; rear/front and moving-hip inspections no longer show the reported voids.

| LOD (colour and shadow) | Unintended skin edges below belt | All below-belt edges, including intended openings | Body triangles |
|---|---:|---:|---:|
{chr(10).join(rows)}

Remaining below-belt edges are the **kilt hem/waistband and belt-jewel back**, itemized by native piece in
[geometry_receipt.json](review/round3/geometry_receipt.json). The full mesh's open-edge counts are
504→441, 254→217, 243→206, 147→125; upper mane/ornament boundaries remain outside this hip repair.
There are zero non-manifold edges after position welding. Colour and corresponding shadow counts agree.

The necessary closure adds **119/69/69/46** triangles. This exceeds the previous installed triangle caps;
the unchanged shared runner reports those eight colour/shadow cap failures. No unrelated reduction was performed.
The resulting LOD ratios are 21.80%, 20.76%, 9.77%; the chain still decreases strictly.
Axe triangles remain **1854/389/343/127**, with the entire axe GLB byte-identical.

**integration/actors.yml changed: NO.** All **2,214 animation channels** (including Attack, Death, Dead, axe motion
and cloth), embedded texture payloads and the standalone axe are byte-identical to the accepted round-2 export.
Original body vertex positions and weights are retained; only the added pelvis vertices receive new weights.
Attack impact remains **0.947917 s**, Cast **1.516667 s**; melee/ranged Attack, distinct Cast and sockets unchanged.

| File | SHA-256 |
|---|---|
{hashrows}

Also updated: `work/runtime_master.blend`, the export intermediates, all three `review/viewer/mm6_min1_*.glb`
and its manifest, nine clip sheets, 72 all-LOD hip renders, browser close-ups, export/weight/binding reports,
README, progress and [artifact manifest](artifact_manifest.json). Repair/export/review scripts live in `scripts/round3_*`;
`finish_export.py`, `round1_pack_maps.py` and `validate_exports.py` now target round-3 evidence.
Accepted round-2 native files and exports are preserved in `review/round3/before/`.

### Verification and remaining findings

- [Geometry and preservation receipt](review/round3/geometry_receipt.json): zero unintended skin openings on
  all four colour and four shadow meshes; unchanged accepted animations, axe, image payloads and bindings.
- [Bindings](review/bindings_check.txt): **no BAD line**. [Loader/weights](review/export_validation.json): pass,
  maximum weight-sum error **1.382e-7**. These checks do not override the motion report.
- [Shared viewer check](review/viewer_check.json): **27/27**, zero console errors; Chrome closed after checking.
- [Shared gates](review/round3/shared_gates/gates.md): **{G['status']}**, **{G['counts']}**. All nine clips and all LODs sampled.
  [Comparison and cloth values](review/round3/GATE_COMPARISON.md) explicitly retain the old cloth/arm/grip/gait findings,
  six newly failing Death head-penetration rows, triangle-cap failures and the existing coverage limitations.
  **This is not an all-gates-passing or automatic-install handoff.** Accepted animation was not changed to chase them.

Review: [closed hips in the viewer](review/round3/closed_hips_viewer.png),
[all LODs standing](review/round3/hips_lods_Standing.png), [all LODs attacking](review/round3/hips_lods_Attack.png),
[Attack sheet](review/sheets/Attack.png), [Death sheet](review/sheets/Death.png), [viewer](review/viewer/index.html).
Original feedback images are in `review/round3/before/user_74.png` and `user_75.png`.

Next owner: **batch orchestrator** for review of the listed findings/count increase and integration of this staged export.
Do not copy these files to assets_dev directly; the orchestrator owns installation through the model installer.
Lease released at handoff. The sprite-restore source `../mm6_min1/` was read-only throughout.

## Review round 2

[Exact archived round-2 handoff](review/round3/before/HANDOFF.md) records the accepted attack/death changes and old hashes.

## Review round 1

[Exact archived round-1 handoff](review/round2/before/HANDOFF.md) and
[original reduction curve](review/round1/reduction/README.md) remain available. That curve predates this required closure.
""")
(P/'README.md').write_text("""# MM6 BMinotaur — review round 3, closed hips

The hip/crotch/upper-thigh skin is now continuous at every colour and shadow LOD. Empty-bake UVs along the cut rims
now sample opaque fur from the existing atlas. All accepted animation channels, texture images, the axe and
integration/actors.yml are unchanged. **Shared gates still FAIL; this is a staged geometry repair, not full technical completion.**

[Handoff, hashes and counts](HANDOFF.md) · [hip review](review/round3/closed_hips_viewer.png) ·
[geometry receipt](review/round3/geometry_receipt.json) · [shared comparison](review/round3/GATE_COMPARISON.md) ·
[viewer](review/viewer/index.html). Viewer 27/27; bindings no BAD. Budget **30/100 credits**, zero this round.

Unattended decisions: preserve every accepted curve and original body vertex; add the smallest connected hip patch
at each LOD using the pre-trim anatomical cross section; weight new vertices to pelvis/thighs; reuse opaque fur UVs
instead of changing texture files. Retain the kilt's intentional hem/waist openings and existing two-sided material.
Required closure increases body triangles to **7995/1743/1660/781** (including identical shadow counts).
The previous-count caps remain unchanged in gates.json and correctly flag this increase; no further reduction was requested.

Canonical master: work/production_master.blend. Lower masters: work/round1_lod1.blend through round1_lod3.blend.
With a reclaimed lease, export using the four-thread Blender wrapper on scripts/round3_export.py, then run
scripts/round1_pack_maps.py, scripts/round1_assemble_lods.py and scripts/finish_export.py through the workspace wrapper.
Use the shared gate runner with gates.json, scripts/validate_exports.py, check_bindings.py and shared check_viewer.mjs.
The round3 repair script starts from immutable round-2 backups and is separate from ordinary re-export.
Do not rerun the old round2 motion/export producers: they replace the repaired masters. The old hidden-skin deletion
script is retired and rejects use because it violates the closed-body rule.

No install, game launch, build or commit. The orchestrator owns integration; ../mm6_min1/ is read-only source material.
""")
progress=J('creature_3d_progress.json');progress.update(review_round=3,substep='round 3 closed hips exported; shared technical findings remain',status='staged_with_open_gates',artistic_acceptance='Attack, Death, axe, textures and bindings accepted and preserved; closed-hip revision agent-reviewed',next='Orchestrator reviews staged closed hips and outstanding shared findings/count increase',next_action={'owner':'batch orchestrator','action':'Review closed-hip export, shared findings and required triangle increase, then integrate within batch workflow.'},shared_gate='review/round3/shared_gates/gates.json',geometry_receipt='review/round3/geometry_receipt.json',review_round3_spent_credits=0,open_technical_faults=['Shared gates FAIL: review/round3/GATE_COMPARISON.md and open_findings.json','Previous-count caps exceeded by necessary closed-body surfaces','Death head-penetration measurement newly fails on six LOD rows; accepted head/motion preserved','Existing shared jitter/full-floor coverage limits unchanged'],updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
(P/'review/visual_review.json').write_text(json.dumps({'revision':'mm6_min1_codex_review_round3','agent_review':'Closed fur surface replaces the reported voids; original texture holes on cut rims remapped. Technical shared findings remain.','inspected':['round3/closed_hips_viewer.png','round3/hips_lods_Standing.png','round3/hips_lods_Attack.png','round3/lod_frames/LOD3_Walking_back.png','round3/lod_frames/LOD2_Standing_front.png','sheets/Attack.png','sheets/Death.png'],'shared_gate_status':G['status'],'artistic_acceptance':'Accepted animations preserved; this geometry revision is not user-approved.'},indent=2))
f=P/'review/viewer/feedback/user_feedback.json';feedback=json.loads(f.read_text());feedback['findings']=[r for r in feedback['findings'] if r['id']!='round3-closed-hips'];feedback['findings'].append({'id':'round3-closed-hips','observed':'Closed waist/thigh skin on all colour/shadow LODs; empty cut-rim bake UVs remapped to existing fur. Animations, axe, texture images and bindings unchanged; shared technical findings remain.','region':'hips','evidence':['../round3/before/user_74.png','../round3/before/user_75.png','../round3/closed_hips_viewer.png']});f.write_text(json.dumps(feedback,indent=2)+'\n')
files=J('artifact_manifest.json')['files'];paths=set(files)
for folder in ['review/round3','review/viewer','review/sheets','review/frames','scripts','export']:
 paths.update(str(f.relative_to(P)) for f in (P/folder).rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix!='.blend1')
paths.update(['HANDOFF.md','README.md','creature_3d_progress.json','review/visual_review.json','review/viewer_check.json','review/bindings_check.txt','review/export_validation.json','review/weights_check.txt','review/runtime_metrics.json','work/production_master.blend','work/runtime_master.blend',*[f'work/round1_lod{i}.blend' for i in range(1,4)]])
files={n:{'sha256':H(n),'bytes':(P/n).stat().st_size} for n in sorted(paths) if (P/n).is_file()}
(P/'artifact_manifest.json').write_text(json.dumps({'identity':'mm6:min1','revision':'review_round3','status':'staged_with_open_gates','mesh_credits':30,'files':files},indent=2)+'\n')
print('Round 3 handoff written;',len(files),'hashes;',G['status'])
