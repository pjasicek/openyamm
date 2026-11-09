"""Bind the review handoff to the exact exports and existing shared gate receipts."""
import json,hashlib,datetime,yaml
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(p):return json.loads((P/p).read_text())
def dump(p,d):(P/p).write_text(json.dumps(d,indent=2)+'\n')
s=read('review/round3/summary.json');a=read('review/round3/artifacts.json');curve=read('review/round3/reduction_curve.json');skin=read('review/round3/final_skin_luminance.json');g=read('review/gates/gates.json');selection=read('review/reduction/selection.json');cfg=read('gates.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();same=yaml.safe_load((P/'integration/actors.yml').read_text())==yaml.safe_load((P/'work/round3/actors.yml').read_text());assert same
stretch=[r for r in g['gates']if 'stretch' in r['gate']];cuffs=[r for r in g['gates']if r['gate']=='cloth_penetration_mm'and 'sleeve cuff'in r['region']];assert all(r['status']=='PASS'for r in stretch+cuffs)
arttable='\n'.join(f'| [{x["path"]}]({x["path"]}) | {x["bytes"]} | `{x["sha256"]}` |'for x in a)
visual='\n'.join(f'| {x["level"]} | {x["triangles"]} | {x["min_iou"]:.6f} | {x["pooled_iou"]:.6f} | {x["min_ssim"]:.6f} | {"PASS"if x["numeric_visual_pass"]else"FAIL"} |'for x in curve['body'])
skinlines='\n'.join(f'| {n} | '+ ' | '.join(f'{x["native"][k]:.6f} / {x["baked"][k]:.6f}'for k in ['mean','p90','p95'])+' |'for n,x in skin['regions'].items())
cloth=read('review/round3/cloth_findings.json')['findings'];caps=sum(x['nearest_is_synthetic_cap']for x in cloth)
text=f'''# MM6 Merchant mer1 — handoff

## Review round 3

**QA HOLD — revised exports and review evidence staged; technical completion remains false.**
The face/hands and apparent shoulder flaps are repaired. Every shared arm/hand stretch row and sleeve-cuff
containment row passes across the eight clips and all four colour/shadow LODs.
The full shared result is **{g['counts'].get('PASS',0)} PASS / {g['counts'].get('FAIL',0)} FAIL /
{g['counts'].get('UNVERIFIED',0)} UNVERIFIED**, plus {g['counts'].get('INFO',0)} INFO and {g['counts'].get('N/A',0)} N/A.
Rows include repeated colour/shadow evidence; they are not distinct defects. Remaining contact/motion and reduction
findings below prevent an all-gates-passing handoff. No artistic acceptance is recorded.

### What changed

- **Geometry:** LOD0 preserves **4,946 head** and **3,010 hand** triangles. Only the clothing/body was reduced
  and rebaked to **6,998 triangles**, for **14,954 total**. Fingers retain the source segments and volume.
  The higher near count follows the user's explicit round-3 body-only reduction instruction; far levels still
  stay below their previous counts. A small accidental five-edge hole above the right eye was filled with three
  triangles, using adjacent head UVs; eye rims sit behind the eyelids. No shoulder patches or detached sleeve roots.
- **Separate skin sets:** fresh Meshy head retexture from the retained HD head views, and a hand-only retexture
  with clean skin, crease/nail detail and no clothing colour. Head PBR maps are **1024²**, hand PBR maps **512²**,
  clothing maps **2048²**. They remain separate materials and share the same images across every LOD.
  No face or hand projection through the clothing rebake. UV carry-over errors are recorded in
  [uv_transfer.json](review/round3/uv_transfer.json).
- **Skin grading:** linear exposure and gentle chroma matching replaced the rank-based native-luminance remap
  that amplified pores into blotches. Head exposure is 1.30, hand exposure 1.92. Covered skin texels meet native
  mean/p90/p95 floors; face and hands use the same fair skin family. The hand comparison isolates the exported
  hand/cuff only, because the relaxed palm faces the thigh and is occluded from that camera in the complete model.
- **Shoulders/waist:** fresh bone-heat garment weights use anatomically fitted temporary bone tails, then smooth
  four-influence shoulder fitting against 81 samples of the retained library motions. The original source-frame
  rig and action choices remain. A lower-LOD shoulder fit clears the last reduced stretch failure.
  The apparently detached green ovals in the PBR previews were traced to exaggerated baked tangent normals:
  the same exported vertex poses rendered continuously without that map. The final shared clothing normal map
  keeps subtle detail with 0.15 XY strength and a positive unit Z component. No extra rebake or geometry wedge.
- **Cloth/boots:** tucked pelvis-weighted waist, matched cuff openings and preserved closed geometry. Covered
  trouser shafts were tapered within the robe, retaining all faces and the visible boots. Far sole patches
  were refitted to the unchanged planted Standing pose. These changes reduce some contact faults but do not
  certify the remaining robe/club/hand interaction.
- **Preserved:** the accepted club GLB is byte-identical, the **Club** node/belt loop and Attack draw remain,
  and Running remains **Jogging** (0.8 s, 1.302 m stride), never RelaxRunForward. All eight library-derived roles,
  Cast alias, scale, impact timing and source-frame rig are retained. No new animation purchase.

### Review and checks

- [Face before/after](review/round3/face_before_after.jpg): front, side, three-quarter.
- [Hand before/after](review/round3/hand_before_after.jpg): isolated exported palm/back, identical pose.
- [Shoulders in Standing, Attack and Death](review/round3/shoulder_closeups.jpg),
  [body turnaround](review/round3/body_turnaround.jpg), [all clip sheets](review/round3/).
- [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html):
  **24/24 tier/clip switches**, no console errors or failed switches; browser closed by the shared checker.
- [check_bindings.py output](review/bindings_check.txt): **no BAD line**. Final skin-weight sum error is
  **1.1920928955078125e-7**; material extension/opaque-shadow checks and the static geometry/weight identity pass.
- [Shared gates](review/gates/gates.md), [exact open findings](review/round3/open_findings.json).
  Stretch and cuff containment pass on every clip/LOD. The runner has no dedicated shoulder-volume or hem-vertex
  acceleration test; these are not claimed as independently certified. Existing Death cloth rotation-step checks
  pass, with worst **{s['death_cloth_rotation_step_max_deg']:.6f} degrees/sample**.

Skin values below are native / final linear luminance on covered UV skin texels, excluding padding:

| Region | Mean | P90 | P95 |
|---|---:|---:|---:|
{skinlines}

### Files, hashes and triangles

| File | Bytes | SHA-256 |
|---|---:|---|
{arttable}

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body including protected head/hands | 14954 | 2399 | 1727 | 682 |
| Unchanged club | 1122 | 290 | 252 | 200 |

All LODs share the three body material sets. The sole clothing rebake keeps >=16 px dilated margins
(34.816 px packing gap); the independent hand atlas has a 33+ px gap. Head UVs are retained from the dedicated
head set and background is dilated. [Texture resource receipt](review/round3/shared_textures.json).

### Reduction evidence and remaining findings

The explicit round-3 density requirement supersedes the old total-body ~7k count. The clothing-only reduction
is one rebake; head/hands bypass that bake. Far counts are below 2400 / 1730 / 685.
Actual tier materials were compared in eight views per tier at 700 / 550 / 220 / 88 px actor heights:

| LOD | Body triangles | Min IoU | Pooled IoU | Min SSIM | Numeric visual threshold |
|---|---:|---:|---:|---:|---|
{visual}

[Reduction sheets and curve](review/round3/reduction/README.md). No blanket perceptual exception is claimed.
A numeric or visual failure remains a failure, even when a separate binding/viewer check passes.

{(P/'review/round3/fault_table.md').read_text()}

**Cloth-check limitation:** {caps}/{len(cloth)} saved colour-LOD coat findings have their nearest point on the
checker's synthetic opening cap. The worst 87.412 mm Death sample is a boot exiting below the raised rear hem,
not a boot puncturing the cloth at that location; see [marked side](review/round3/cloth_fault_left.png),
[marked rear](review/round3/cloth_fault_back.png) and [per-finding localization](review/round3/cloth_findings.json).
A folded hem is not planar. This diagnosis does **not** waive the shared failures or claim that every remaining
cloth/contact sample is harmless. The shared runner was not modified and no replacement gate was introduced.
Club/body contact, coarse-LOD grip contact and any remaining gait/finger rows still need repair or an explicit
orchestrator review of the checker evidence. This candidate is not certified for final installation.

### Integration, budget and ownership

**integration/actors.yml changed only its review comment. Descriptor semantics are unchanged** from round 2:
scale 103.944653064, yaw -1.570796327, z offset -0.103944653, walk/run strides 0.84 / 1.302,
impact 0.8125, ids 577/578/579, Cast=Attack and Club attachment names retained.
[Staged descriptors](integration/actors.yml); the orchestrator owns installation/regression/game captures.

**20 credits spent this round; 80/100 total; 20 remain.** Head task
`01a133e8-f805-76c9-a51f-1376f2aee5e5` and hand task `01a133e8-9909-73d8-a291-1086543609c5`
cost 10 each. The first head request was rejected before task creation (mutually exclusive text/multiview
parameters), costing 0. No pending jobs. Requests/receipts are under work/round3 and meshy/.

Selected authoring state: work/round3/master.blend, work/round3/body_lod0..3.blend,
work/round3/shared_textures and review/reduction/selection.json. The final export pipeline is
round3_export_selected.py (Blender, --threads 4), round3_package.py and round3_viewer.py (system Python),
then portable copies, export_identity.py, round3_configure_gates.py, the shared run_gates.py, and review scripts.
Do not rerun round3_reduce.py: the single clothing rebake is already complete. Weight/cloth experiments and
old round-2 scripts are historical, not the selected pipeline.

README and creature_3d_progress.json identify the same revision. Lease is released at handoff.
No assets_dev/source installation, game launch, build or commit was performed. Native mm6_mer1 was read-only.

---

## Historical review round 2 (regenerated body)

The previous handoff, including its superseded hashes and findings, is preserved at
[work/round3/HANDOFF.md](work/round3/HANDOFF.md). Current exports are exclusively those listed above.
'''
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text(f'''# MM6 Merchant (mer1)

**Review round 3 staged — QA HOLD.** Face/hands restored with protected geometry and separate fresh skin sets.
Shoulder stretch and sleeve-cuff containment pass on every clip/LOD. Full shared checks still have
{g['counts'].get('FAIL',0)} FAIL rows; technical completion is false. [HANDOFF.md](HANDOFF.md) records exact
hashes, remaining faults and the cloth-cap diagnostic without waiving failures.

[Face before/after](review/round3/face_before_after.jpg), [hand before/after](review/round3/hand_before_after.jpg),
[shoulders](review/round3/shoulder_closeups.jpg), [clip sheets](review/round3/),
[reduction evidence](review/round3/reduction/README.md).

Unattended decisions: preserve 4,946 head and 3,010 hand triangles at LOD0; reduce only clothing to 6,998.
Use separate 1K head / 512px hand / 2K clothing maps, shared across LODs. Reuse adequate round-2 HD references;
spend 10 credits on each new skin retexture. Retain exact head/hand UVs outside the clothing bake, and replace
mottling-producing rank grading with gentle linear skin exposure. Correct false garment flaps caused by excessive
tangent normals, fit shoulder weights to retained library poses, preserve every closed trouser face, and keep
Jogging, the accepted club and its attachment scheme. No threshold was raised to clear these new failures.
The optional old total LOD0 count cap is superseded by the user's explicit protected head/hands instruction.

Body counts: 14954 / 2399 / 1727 / 682; club: 1122 / 290 / 252 / 200, unchanged binary.
Authoritative sources: work/round3/master.blend, work/round3/body_lod0..3.blend,
work/round3/shared_textures and review/reduction/selection.json. Editable/portable/runtime outputs are in export/.

Bindings: no BAD line. Viewer: 24/24 switches, no errors. actors.yml changed its comment only; scale/stride/socket
semantics are unchanged. These checks do not clear the contact and numerical visual findings.

Budget: 20 this round, 80/100 total, 20 remaining; no pending paid jobs. No installation, game/build or commit.
The orchestrator owns integration after reviewing or resolving the open findings.
''')
state=read('creature_3d_progress.json');state.update(stage='handoff',status='qa_hold',current_stage='review_round_3',current_substep='protected head/hands and separate skin sets staged; contact/visual findings remain',substep='round3_handoff',technical_completion=False,last_updated=now,selected_artifacts=a,next_action='Orchestrator: review round-3 face/hand/shoulder evidence; resolve listed contact, grip and numerical reduction findings before technical acceptance/install.',handoff='HANDOFF.md');state['review_round_3']={**s,'finished_at':now,'handoff':'HANDOFF.md','artifacts':a,'review_sheets':'review/round3/','integration_actors_changed':True,'integration_semantics_changed':False,'all_stretch_pass':True,'all_cuffs_pass':True,'credits_spent':20};state['rig_gate_checkpoint']={'blend':'work/round3/master.blend','shared_gate_report':'review/gates/gates.json','shared_gate_status':'FAIL','open_findings':'review/round3/open_findings.json','runtime_geometry_identity':'review/runtime_geometry_identity.json','note':'Stretch/cuffs pass all clips/LODs. Remaining contact/gait/grip failures retained; synthetic hem cap limitation localized. No dedicated shoulder-volume/hem-vertex acceleration checker.'};state['texture_checkpoint']={'skin_report':'review/round3/final_skin_luminance.json','all_skin_mean_p90_p95_not_darker':s['skin_numeric_pass'],'shared_atlases':'review/round3/shared_textures.json','meshy_credits':80,'numeric_visual_curve':'review/round3/reduction_curve.json','note':'Separate 1K head / 512px hands; protected from sole 2K clothing rebake.'};dump('creature_3d_progress.json',state)
(P/'integration/playbook_notes.md').write_text('''# Round 3 notes for the orchestrator

- Preserve dense head/hands outside the clothing reduction and rebake; dedicated sets avoid reprojection drift.
- Native luminance rank mapping amplified subtle skin noise. Linear exposure preserves generated skin detail.
- Apparent armpit/waist tears were partly exaggerated tangent normals, confirmed by equal source/export poses
  and a normal-disabled render. Positive-hemisphere, low-amplitude garment normals remove those visual flaps.
- Four-influence weight fitting over retained clips clears shoulder stretch without adding geometry patches.
- A folded robe hem violates the shared containment check's planar-opening assumption: see
  ../review/round3/cloth_findings.json. Do not silently waive this or count a virtual cap as real cloth.
- No shared checker/playbook change was made in this production project. Dedicated shoulder-volume and
  hem-vertex acceleration checks remain unavailable in the current shared runner.
''')
print(json.dumps({'status':state['status'],'counts':g['counts'],'credits':80,'integration_semantics_changed':not same},indent=2))
