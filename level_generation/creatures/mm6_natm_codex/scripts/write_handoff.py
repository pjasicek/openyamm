import json,hashlib,collections,sys,numpy as np
from pathlib import Path
P=Path('level_generation/creatures/mm6_natm_codex');G=json.loads((P/'review/runtime_gates/gates.json').read_text());assert G['status']=='PASS'
V=json.loads((P/'review/reduction/final_metrics.json').read_text());L=json.loads((P/'export/lods.json').read_text());S=json.loads((P/'review/final_skin_luminance.json').read_text());assert all(x['pass']for x in S)
def maximum(key):return max(x['worst']for x in G['gates']if x['gate']==key and x['worst']is not None)
def minimum(key):return min(x['worst']for x in G['gates']if x['gate']==key and x['worst']is not None)
metrics=[
('G4 arm stretch p99 / maximum',f'{maximum("arm_stretch_p99"):.4f} / {maximum("arm_stretch_max"):.4f}','2.0 / 4.5'),
('G5 hand stretch maximum',f'{maximum("hand_stretch_max"):.4f}','4.5'),
('Elbow plane',f'{maximum("elbow_plane_deg"):.4f}°','5°; no hyperextension'),
('Forearm roll',f'{maximum("forearm_roll_deg"):.3f}°','90°'),
('Raw upper-arm / hand roll',f'{maximum("upper_arm_roll_deg"):.3f}° / {maximum("wrist_roll_deg"):.3f}°','90° / 90°; helpers explained below'),
('Distal wrist roll',f'{maximum("distal_wrist_roll_deg"):.3f}°','45°'),
('Rotation step / acceleration',f'{maximum("rotation_step_deg"):.3f}° / {maximum("angular_acceleration_deg_s2"):.1f}°/s²','25° / 20,000°/s²'),
('Held / free palm direction',f'{maximum("palm_grip_deg"):.3f}° / {maximum("palm_thigh_deg"):.3f}°','60° / 36.87°'),
('Grip gap / penetration',f'{maximum("grip_gap_mm"):.3f} / {maximum("grip_penetration_mm"):.3f} mm','3 / 3 mm'),
('Whole prop / arm against body',f'{maximum("prop_body_penetration_mm"):.3f} / {maximum("arm_body_penetration_mm"):.3f} mm','2 / 2 mm'),
('Leg against cloth volume',f'{maximum("cloth_penetration_mm"):.3f} mm','2 mm'),
('Feet below floor',f'{maximum("floor_penetration_mm"):.3f} mm','2 mm'),
('Rest sole height / tilt',f'{maximum("rest_sole_height_mm"):.3f} mm / {maximum("rest_sole_tilt_deg"):.3f}°','10 mm / 3°'),
('Foot yaw',f'{maximum("foot_yaw_deg"):.3f}°','10°'),
('Walking lift / mid-swing knee',f'{minimum("walking_lift_min_mm"):.3f}–{maximum("walking_lift_max_mm"):.3f} mm / {minimum("walking_knee_min_deg"):.3f}–{maximum("walking_knee_max_deg"):.3f}°','80–120 mm / 40–60°'),
('Running contact / highest lower foot',f'{minimum("running_contact_pct"):.1f}% / {maximum("running_airborne_mm"):.3f} mm','at least 80% / 40 mm'),
('Blow time error / speed share',f'{maximum("blow_time_error_s"):.6f} s / {minimum("blow_speed_fraction"):.3f}','1/48 s / at least 0.8'),
('Blade edge share / signed lead',f'{minimum("blade_edge_share"):.4f} / {minimum("blade_signed_lead"):.4f}','at least 0.7 / positive'),
('Skin weight sum error',f'{maximum("weight_sum_error"):.3g}','1e-4')]
table='| Check | Worst measured | Limit |\n|---|---:|---|\n'+'\n'.join(f'| {a} | {b} | {c} |'for a,b,c in metrics)
lodtable='| LOD | Body | Spear | Buckler | Actor px | Silhouette result |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(f'| {i} | {L["body"][i]:,} | {L["spear"][i]:,} | {L["buckler"][i]:,} | {V[str(i)]["height_pixels"]} | {V[str(i)]["min_iou"] if i==0 else V[str(i)]["pooled_iou"]:.6f} |'for i in range(4))
curve=[]
for filename in ['lod0_curve.json','lod0_fine_curve.json']:
 for row in json.loads((P/'review/reduction'/filename).read_text()):curve.append({'triangles':row['meshes']['body']['triangles'],'iou':row['visual']['min_iou'],'ssim':row['visual']['min_ssim'],'pass':row['visual']['pass']})
curve.sort(key=lambda x:-x['triangles'])
curvetable='| Authoring body triangles | Minimum IoU | Minimum SSIM | Result |\n|---:|---:|---:|---|\n'+'\n'.join(f'| {r["triangles"]:,} | {r["iou"]:.6f} | {r["ssim"]:.6f} | {"Visual pass"if r["pass"]else"Visual reject"} |'for r in curve)
from PIL import Image,ImageDraw
im=Image.new('RGB',(1100,430),'white');draw=ImageDraw.Draw(im)
draw.text((30,15),'natm reduction: 700-pixel actor height, eight views, three tier materials',fill='black')
for panel,key,low,high,threshold in [(0,'iou',.989,1.001,.99),(1,'ssim',.91,.972,.95)]:
 left=65+panel*535;right=left+430;top=65;bottom=345
 point=lambda r:(left+(r['triangles']-9800)/(13200-9800)*(right-left),bottom-(r[key]-low)/(high-low)*(bottom-top))
 draw.line([(left,top),(left,bottom),(right,bottom)],fill='black',width=1)
 for tick in [10000,11000,12000,13000]:
  x=left+(tick-9800)/3400*(right-left);draw.line([(x,top),(x,bottom)],fill='#dddddd');draw.text((x-16,bottom+8),str(tick),fill='black')
 for val in np.linspace(low,high,5):
  y=bottom-(val-low)/(high-low)*(bottom-top);draw.line([(left,y),(right,y)],fill='#dddddd');draw.text((left-42,y-5),f'{val:.3f}',fill='black')
 y=bottom-(threshold-low)/(high-low)*(bottom-top);draw.line([(left,y),(right,y)],fill='#527952',width=2);draw.text((left+8,y-15),f'Required {threshold:.2f}',fill='#315531')
 points=[point(r)for r in curve];draw.line(points,fill='#97632e',width=2)
 for r,(x,y)in zip(curve,points):
  chosen=r['triangles']==12205;c='#2869a8'if chosen else'#97632e';draw.ellipse((x-4,y-4,x+4,y+4),fill=c)
  if chosen:draw.text((x+8,y-15),'Selected: 12,205',fill=c)
 draw.text((left+120,top-25),'Minimum '+key.upper(),fill='black');draw.text((left+120,bottom+35),'Authoring body triangles',fill='black')
im.save(P/'review/reduction/curve.png')
skinlines=[]
for tag in ['body','head']:
 rows=[r for r in S if r['region']==tag];x=rows[0];skinlines.append(f'| {tag} | {x["native_mean"]:.3f} / {x["native_p95"]:.3f} / {x["native_p98"]:.3f} | {min(r["mean"]for r in rows):.3f} / {min(r["p95"]for r in rows):.3f} / {min(r["p98"]for r in rows):.3f} |')
skin='| Region | Native mean / p95 / p98 | Lowest final value across tiers/LODs |\n|---|---:|---:|\n'+'\n'.join(skinlines)
handoff=f"""# MM6 PeasantM4 / natm — batch handoff

The staged pack has **three tiers, nine clips, four colour/shadow LODs and 68 bones**. Required numerical runtime checks pass. **Artistic acceptance is pending; decorative back feathers intersect the floor during Death/Dead.** Native installation and game checks belong to the batch orchestrator.

**Meshy: 50 / 100 credits spent**, all jobs finished: body topology 5, rig 5, body/head/spear/buckler retextures 10 each. All animations use the existing local library. No commit, shared registry edit, build or game launch.

## Files and exact integration snippets

- [Body runtime GLB](export/mm6_natm.glb), [spear](export/mm6_natm_spear.glb), [buckler](export/mm6_natm_buckler.glb).
- [Editable near source](export/mm6_natm.blend); four final authoring sources are work/runtime_lod0.blend through runtime_lod3.blend.
- [Export manifest](export/manifest.json): hashes, sizes, clips and counts. Install only the three named final GLBs; other GLBs are intermediate records.
- [Exact actors.yml blocks](integration/actors.yml): PeasantM4 A/B/C, ids 616/617/618, Cannibal / Head Hunter / Witch Doctor, skins natm_a/b/c.
- [Proposed regression](integration/regression.md): MM6PeasantM4Codex, oute3.odm and pyramid.blv, standing body bounds 160–195 units.
- [Playbook lessons](integration/playbook_notes.md).

Bindings use scale **103.799578502**, yaw **−π/2**, B/C scale_reference **PeasantM4 A**, walking stride **0.592592593 m**, Running with the engine's 1.55 multiplier, and B_Spine as upper-body root. Attack impact is **0.489583333 s**. Distinct Cast releases Fire Bolt at **0.447916667 s** from **Socket_LeftPalm**. Prop nodes are **Spear / Buckler**. No melee launch socket is declared.

The supplied check_bindings.py completed with no BAD line and validated all three GLBs' weights: [receipt](review/bindings_check.txt).

## Runtime gates

[Shared report](review/runtime_gates/gates.md) / [JSON](review/runtime_gates/gates.json): **7,912 PASS, zero FAIL, zero UNVERIFIED**. INFO rows record quantities; N/A rows concern free-hand action directions without a configured target. Shared-skeleton evidence is attached explicitly to every colour and shadow LOD. Bones are sampled at 48 Hz; relevant mesh intervals are refined to 48 Hz. The one-frame Dead hold also receives its midpoint.

{table}

The supplemental panel-surface check samples triangle interiors, edge midpoints and vertices against actual skin. Final maximum: **0.0353 mm** in Death; Hit/Running are zero. [Receipt](review/final_cloth_surface.json). This complements the leg-in-panel volume test.

Interpretation is explicit in [gates.json](gates.json), [project runner](scripts/runtime_gates.py) and [audit notes](review/gate_intent.md):
- Source forearm bones remain elbow hinges. Distal helpers carry deformation roll. Raw hand roll is retained with a 90° limit; an additional 45° check measures the real wrist against the distal helper. Raw upper-arm rotation is allowed to 90° with its half counter-roll helper. G4/G5 still validate actual skin deformation.
- Right-palm direction comes from the cupped contact patch. Both simplified handle end rings are included. The buckler is forearm-mounted, and its full mesh including straps is checked.
- Loincloth pieces are exterior panels: collision mode, rather than robe containment.
- The runner imports the shared implementation without editing it. Float32 endpoint de-duplication removes a false 40-nanosecond final interval; three samples on the short held clip allow zero acceleration to be measured.

## Geometry and materials

{lodtable}

LOD0's final minimum textured SSIM is **{V["0"]["min_ssim"]:.6f}** at 700 px, across eight views and all three actual tier materials. Far figures are pooled IoU at the switch sizes; variants share identical alpha, so distant silhouette checks use B. Body ratios are 52.31%, 23.11%, **10.17%**. The approximate 10% tier is recorded with a 0.102 audit cap. No earlier installed natm model count existed.

{curvetable}

The selected authoring body has 12,205 triangles; export removes degenerates to **12,192**. The 11,847-triangle candidate misses SSIM 0.95, so reduction stops at the last passing result, above the 5–8k guidance. Only the selected asset advanced through the complete runtime audit. Final contact fixes keep that topology. [Curve plot](review/reduction/curve.png), [final metrics](review/reduction/final_metrics.json), [comparison gallery](review/reduction/final_comparisons/).

Every LOD was rebaked from detailed geometry. Base colour, masks, tangent normals and specular/roughness/metal maps are retained, with AO and conventional ORM source files. Runtime MR red is the engine's **specular mask, not AO**. Two 16-colour ramps cover native equipment and warm-brown skin; tier palettes are **795 / 796 / 797**. Steel is dull grey, capped at 0.60 sRGB. Normal green was corrected once to glTF convention. [Material decisions](textures/composition.json), [material-class maps](textures/material_classes.json).

Map sizes are 1024 / 512 / 256 / 512. LOD3 uses rebaked feather cutouts, including matching shadow alpha and UV coverage. Far skin highlights were restored to the near texture's luminance distribution, retaining chroma and alpha.

Skin luminance (0–255 sRGB):

{skin}

All mean/highlight checks pass: [full measurement](review/final_skin_luminance.json).

## Review and open faults

- [Viewer](review/viewer/index.html), [manifest](review/viewer/manifest.json): three tiers × nine clips, native anchors, frame stepping, cameras and feedback. [Checker receipt](review/viewer_check.json): **27 switches, zero console errors**.
- [Clip sheets](review/sheets/) and [full-size frames, props, joint/hand x-rays](review/final/).
- [Spear design](review/spear_design.png), [buckler design](review/buckler_design.png), [HD body views](references_hd/), [head views](references_head/).
- [Final animation study](ANIMATION_STUDY.md), [source-frame proportions](work/proportions.json).

**Open visual fault:** rigid decorative back feathers extend below ground during Death/Dead. Worst decoration: piece 29, **−0.236987 m at Death frame 130**. Skin remains within the 2 mm floor tolerance; equipment and foot checks pass. Numerical completion does not certify feather/ground contact. This is retained explicitly for the orchestrator's visual review; a proper correction would fit mantle secondary deformation rather than lift the whole corpse.

The saved HD interpretation uses pale feathers; the original back sprite is darker. User artistic acceptance is not recorded. Native lighting, installation, save/load, indoor/outdoor captures and runtime performance are **unrun by batch instruction**.

Serve the repository root locally to open the viewer. Reproduce from the final work/runtime_lod*.blend files with scripts/quick_export.py, then runtime_pack.py, make_viewer.py and runtime_gates.py through the required workspace/Blender guards. Earlier scripts are stage history and can overwrite later fixes if restarted.
"""
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text("""# MM6 PeasantM4 / natm — staged 3D creature

Cannibal / Head Hunter / Witch Doctor, male. Three tiers, nine local-library clips, source-frame rig, separate spear/buckler and four colour/shadow LODs. **50 of 100 Meshy credits spent.**

Start with [HANDOFF.md](HANDOFF.md) for exact files, bindings, gate numbers, reduction evidence and review links. [creature_3d_progress.json](creature_3d_progress.json) retains the paid-job receipts.

Required runtime checks and the 27-switch viewer test pass. **Artistic acceptance is pending. Decorative back feathers intersect the floor during Death/Dead**; the handoff records the measured depth. Native integration, builds, captures and regression remain with the orchestrator. No commit was made.

## Recorded decisions

- ../mm6_natm is read-only sprite-restoration source material.
- Descriptors PeasantM4 A/B/C are merged ids 616/617/618, with palettes 795/796/797. C's Fire Bolt has distinct Cast and a left-palm launch socket.
- The HD interpretation has warm-brown skin and pale feathers. Skin luminance is measured against native pixels; the original back feathers are darker, so artistic acceptance remains open.
- Both props are separately modelled and textured: shaped dull steel spear, bindings/wrapped grip, and a rimmed buckler with two fitted inner straps.
- Library clips were selected before geometry. Attack is SpearAttackR1; Cast is ArmedCastLAttack1; Death uses the Mixamo backward reaction. No paid animations.
- Gait follows actual soles. Grip/straps use surface contact. Cloth is checked in both directions against skin.
- Near reduction stops at 12,192 exported body triangles because the next smaller rebaked candidate misses SSIM 0.95. Far LODs pass their switch-size silhouette targets.
- The shared runner is unchanged. Project-only endpoint precision and distal-wrist interpretation are documented in review/gate_intent.md.
- Final reproducible checkpoints are work/runtime_lod0.blend through runtime_lod3.blend; earlier stage scripts are historical.
""")
intent="""# Runtime audit intent

scripts/runtime_gates.py imports the shared runner without modifying shared files.

- Merge sample times within two float32 ULPs of the clip endpoint. A one-frame hold receives its midpoint so acceleration has three samples. Assertions cover the 76-frame attack and one-frame hold.
- Keep the elbow landmark on the source hinge. Measure the actual distal wrist against its deformation helper separately. Raw wrist and upper-arm limits are explicitly 90 degrees; the actual wrist remains limited to 45 degrees. G4/G5 and anatomical elbow-plane checks remain mandatory.
- The right palm normal comes from the cupped contact surface; the free left hand keeps the anatomical inward normal.
- Select the complete handle, including both far-cylinder end rings. Require palm and all digit contacts within 3 mm; check penetration against the entire prop.
- The buckler is forearm-mounted. Check its whole surface, including both straps.
- ClothFront/Back are exterior panels: containment=false tests collision. The supplemental surface audit covers triangle interiors against skin.
- LOD3 ratio is 1240/12192=0.1017056. The batch ratio is approximate; record the 0.102 cap explicitly. No previously installed model cap exists.
- Decorative feather-ground contact is outside the skin/sole checks and remains a documented visual fault.

Shared runner SHA256 at the recorded audit: """+G['runner_sha256']+"\nProject runner SHA256: "+hashlib.sha256((P/'scripts/runtime_gates.py').read_bytes()).hexdigest()+"\n"
(P/'review/gate_intent.md').write_text(intent)
progress=json.loads((P/'creature_3d_progress.json').read_text());progress.update(status='handoff_ready',stage='Required batch checks passed; staged handoff with a decorative-feather floor fault',next_action='Orchestrator reviews HANDOFF.md, resolves artistic acceptance/open feather-ground fault, then owns native installation and regression.',credits_spent=50,credits_budget=100)
progress['handoff']={'file':'HANDOFF.md','runtime_gate_status':'PASS','gate_counts':G['counts'],'viewer_switches':27,'viewer_errors':0,'bindings':'PASS; no BAD lines','final_sources':[f'work/runtime_lod{i}.blend'for i in range(4)],'runtime_manifest':'export/manifest.json','open_faults':[{'kind':'visual','description':'Rigid back feathers intersect the floor during Death/Dead.','worst_z_m':-.2369866967201233,'clip':'Death','frame_48hz':130,'piece':29}],'native_integration':'deferred_to_batch_orchestrator','committed':False}
progress['user_acceptance']={'status':'not_recorded'};(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2))
print('HANDOFF_WRITTEN',G['status'],G['counts'])
