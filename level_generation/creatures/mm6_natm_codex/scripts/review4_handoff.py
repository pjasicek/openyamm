"""Bind round-four handoff records to the tested exports and shared reports."""
import json,hashlib,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,image_of
read=lambda f:json.loads((P/f).read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
manifest=read('export/manifest.json');main=read('review/runtime_gates/gates.json');neck=read('review/round4_neck_floor_gates/gates.json');diag=read('review/round4_final_diagnostics.json');costume=read('review/round4_costume_diagnostic.json');clearance=read('review/round4_clearance_diagnostic.json');lod=read('review/reduction/round4_metrics.json')
reports=['review/runtime_gates/gates.json','review/round4_neck_floor_gates/gates.json']+[f'review/round4_shaft_gates/lod{i}/gates.json'for i in range(4)]
for file in reports:
 report=read(file);assert report['status']=='PASS'
 for asset in report['assets']:assert sha(Path(asset['path']))==asset['sha256'],asset['path']
for row in read('review/round4_pairs/provenance.json')['pairs']:assert row['body_source_sha256']==manifest['files']['mm6_natm.glb']['sha256']
for d in [diag,costume,clearance]:assert d['source_sha256']==manifest['files']['mm6_natm.glb']['sha256']
assert (P/'integration/actors.yml').read_bytes()==(P/'work/review_round4_before/integration/actors.yml').read_bytes()
memory={}
for name in ['mm6_natm.glb','mm6_natm_spear.glb','mm6_natm_buckler.glb']:
 memory[name]={}
 for key,path in [('round3',P/'work/review_round4_before/export'/name),('round4',P/'export'/name)]:
  d,b=read_glb(path);sizes=[image_of(d,b,i)[0].size for i in range(len(d['images']))]
  memory[name][key]={'images':len(sizes),'sizes':sizes,'rgba8_bytes_without_mips':sum(w*h*4 for w,h in sizes),'encoded_image_bytes':sum(d['bufferViews'][im['bufferView']]['byteLength']for im in d['images']),'glb_bytes':path.stat().st_size}
manifest['texture_memory']=memory;manifest['bindings_changed']=False
manifest['review_artifacts']={f:sha(P/f)for f in ['review/round4_skin_comparison.jpg','review/round4_attack_path.jpg','review/round4_costume_comparison.jpg','review/viewer/manifest.json','review/round4_costume_diagnostic.json','review/round4_final_diagnostics.json','review/round4_clearance_diagnostic.json','review/viewer_check.json','review/bindings_check.txt']}
manifest['gate_reports']={f:sha(P/f)for f in reports};(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def maximum(report,gate,clip=None):return max(r['worst']for r in report['gates']if r['gate']==gate and (clip is None or r['clip']==clip))
feathers=[v for level in costume['lods'].values()for role,groups in level.items()if role not in ['Death','Dead']for name,v in groups.items()if name.startswith('Feather_B_')]
first=max(r['first_mm']for r in feathers);through=max(r['max_mm']for r in feathers)
table='\n'.join(f'| {name} | {v["bytes"]:,} | `{v["sha256"]}` |'for name,v in manifest['files'].items())
counts=manifest['triangles'];triangles='\n'.join(f'| {i} | {counts["body"][i]} | {counts["spear"][i]} | {counts["buckler"][i]} |'for i in range(4))
contact='\n'.join(f'| {i} | {maximum(read(f"review/round4_shaft_gates/lod{i}/gates.json"),"prop_body_penetration_mm"):.6f} | {clearance["rows"][i]["minimum_surface_distance_mm"]:.6f} |'for i in range(4))
body_memory=memory['mm6_natm.glb'];before=body_memory['round3']['rgba8_bytes_without_mips']/1048576;after=body_memory['round4']['rgba8_bytes_without_mips']/1048576
text=f"""# MM6 PeasantM4 / natm — staged review handoff

Latest: **Review round 4**. The requested costume, right-side spear path and skin repairs are re-exported and checked.
Shared rig/collision/floor gates, binding validation and viewer pass on the files below. Artistic acceptance and native
integration belong to the orchestrator. **50/100 Meshy credits spent; zero this round.**
No installation, shared registry edit, build, game launch or commit. Original `../mm6_natm` remains read-only.

## Review round 4

### Changes and review images

- **Costume:** repaired the mismatched feather-helper rest transforms in Attack. Upright clips now key the helpers
  to identity relative to their body parents. Collar, waist feathers and calf feathers follow the same parent-relative
  rest as Standing. Cast, Hit, Fidget, Walking and Running were also sampled. Death/Dead retain the accepted floor-fold
  animation. Free front/back cloth panels retain their intentional secondary motion.
  [Standing versus Attack frame 0](review/round4_costume_comparison.jpg).
- **Spear:** rebuilt the draw-back and recovery hand/forearm paths on the creature's RIGHT (negative Blender X).
  The shaft stays beside the flank and hip through frames 28–40, then drives forward. The off hand keeps a fixed shaft
  grip through the blow, opens, and releases before recovery. Small bind-space palm/finger corrections keep coarse LOD
  hands from spanning the shaft; maximum corrections are 4.60/4.55/7.06/11.96 mm at LOD0–3. Weights and triangle counts
  are unchanged by this fitting. [48 Hz attack path selections](review/round4_attack_path.jpg).
- **Skin:** removed the floating collar fragment (22 near triangles, six LOD1 triangles), repaired skin UV pixels
  that overlapped feather texels, cleaned the painted necklace/armband remnants and narrow chest streaks, and kept
  round-3 anatomical luminance and normal detail outside the selected repair regions. Armbands remain visible dark
  leather geometry. No body skin faces were deleted. [Before/after front and angled close-ups](review/round4_skin_comparison.jpg).
- **Unchanged timing:** Attack 2.25 s, impact **0.90625 s**; Cast release **0.479166667 s**. Death remains
  **1.666666627 s**, Dead **0.041666664 s**; both endpoint bone-matrix differences versus round 3 are exactly zero.
  `integration/actors.yml` is **byte-for-byte unchanged** from round 3. SHA256 `{manifest['bindings_sha256']}`.
- **Texture packing:** one shared four-map set per model, reused by every LOD. True UV charts receive independent
  16-pixel dilation at unchanged texel density. Separating skin from overlapping feather charts prevents the pale
  triangle returning during filtering. All dedicated shadow materials remain OPAQUE.

### Files, hashes and triangle counts

Integrate only the three `export/*.glb` files below. `mm6_natm.blend` is the editable near source;
`work/runtime_lod0.blend` through `runtime_lod3.blend` are editable final LODs.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
{table}

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
{triangles}

Body was 12192/6378/2818/1240 in round 3; props are unchanged in triangle count. Switch-size pooled silhouette IoU:
{', '.join(f'LOD{k} {v["pooled_iou"]:.6f}'for k,v in lod.items())}, all above 0.97.
[Manifest](export/manifest.json) records textures, animations, comparisons, checks and hashes.

**Memory tradeoff:** body maps grew from 2048×2368 to **4096×2144** to separate actual islands and preserve density
with full margins. Four maps estimated as RGBA8 without mipmaps are **{before:.1f} → {after:.1f} MiB**; this is an
estimate, not a measured GPU allocation. Encoded body images grew from 8,410,458 to 10,529,648 bytes. Spear maps are
1536×1152 and buckler maps 1536×1280. There are four images per model, with no duplicate per-LOD sets. This revision
improves padding correctness at a real memory cost; it does not claim a memory reduction.

### Validation on these exports

- [Main shared runner](review/runtime_gates/gates.md): **PASS**, {main['counts']}, all nine clips and colour/shadow LODs.
- [Neck and whole-solid-body floor probe](review/round4_neck_floor_gates/gates.md): **PASS**, {neck['counts']}.
  Neck p99 **{maximum(neck,'arm_stretch_p99'):.6f}×**, maximum **{maximum(neck,'arm_stretch_max'):.6f}×**, limits 1.5×/2×.
  Worst floor penetration **{maximum(neck,'floor_penetration_mm'):.6f} mm**.
- [Dense shaft collision probes](review/round4_shaft_gates/): **PASS** at every one of 109 Attack samples, 48 Hz,
  for matching LOD0–3 body/spear/buckler. Probe-only coplanar shaft subdivision measures long shaft faces between the
  sparse original vertices; runtime geometry is unchanged. [Probe provenance](review/round4_pairs/provenance.json).
  Tiny residual contacts in the table are at the grasping/releasing off hand. Torso/hips/legs have zero measured
  penetration and strictly positive separation in the separate authoring distance diagnostic.
- [Bindings](review/bindings_check.txt): exit 0, **no BAD line**, including all weight sums and shadow opacity.
- [Viewer](review/viewer_check.json): **27 switches**, zero failures/console errors. Owned Chrome processes stopped.
- [Clip sheets](review/sheets/): front, side and three-quarter for all nine clips. [LOD metrics](review/reduction/round4_metrics.json).

| LOD | Shared maximum shaft contact, mm | Body distance excluding hands, mm |
|---|---:|---:|
{contact}

[Costume diagnostic](review/round4_costume_diagnostic.json): upright rigid feather groups' maximum first-frame parent
relative deviation is **{first:.6f} mm**, maximum through the clips **{through:.6f} mm**. This uses the shared pose
reader but is **not an implemented shared gate**. Corpse feather folding is intentionally retained (about 185–247 mm
relative change); free cloth hems also move relative to the pelvis and are not rigid attachments. Their phase-dependent
first-frame offsets in locomotion are reported, not hidden or classified as zero.

[Head diagnostic](review/round4_final_diagnostics.json): maximum forward deviation Attack
**{diag['head']['Attack']['max_forward_angle_deg']:.3f}°**, Cast **{diag['head']['Cast']['max_forward_angle_deg']:.3f}°**,
Fidget **{diag['head']['Fidget']['max_forward_angle_deg']:.3f}°**. Neck/head translation and scale animation channels
are absent. [Body-clearance diagnostic](review/round4_clearance_diagnostic.json) uses the unmodified shared evaluator;
its strict separation measurement is additional authoring evidence, separate from the production shared gate status.

Existing Death smoothness allowances reflect round 3's explicit 2× retiming; Attack low-lunge posture and LOD3 ratio
allowances are retained. No collision, grip or arm-smoothness threshold was loosened for this review. Shared runner
source was not edited. The paired probe config uses zero head-penetration tolerance to force all 48 Hz samples.

### Remaining qualifications and integration ownership

1. Shared runner does not implement head-forward, Cast palm-to-target or parent-relative costume checks and rejects
   unknown config fields. [Extension request](integration/shared_gate_request.json) records them; diagnostics above
   are not presented as shared-gate PASS. Orchestrator owns shared extensions and runtime head-look verification.
2. Strict native per-region luminance percentiles remain unmatched from round 3. The consistent warm-brown hue and
   anatomical detail are retained; before/after images need artistic review. Some existing geometric faceting at the
   necklace and leather band edges remains visible at close range.
3. Historical Running still uses `RelaxRunForward`, so it does **not** satisfy the later Standard Run batch rule.
   This review preserves round-3 motion outside the requested repairs. Existing near-body reduction remains around
   12k triangles; no new 5–8k reduction search was performed.
4. The larger padded body atlas has the memory cost stated above. Native installation, regression and indoor/outdoor
   captures are orchestrator-owned. Nothing was copied into assets_dev.

### Selected reproduction sources

Start with the read-only round-3 checkpoint `work/review_round4_before/`. `review4_skin.py` repairs pre-atlas maps;
`review4_build.py` applies `review4_motion.py`, `review4_costume.py`, `review4_fragment.py`, selected corrections through
`review4_apply_hand_fit.py`, then reloads maps/exports via `review2_reload.py`. Selected hand corrections are in
`work/round4_hand_corrections.json`. `runtime_pack.py` calls `review4_atlas.py` and `review4_skin_layers.py` for separate
skin sampling and shared padded maps. `review4_finalize.py` removes constant head channels and writes probe configs.
`review4_dense_spear.py`, `review4_probe.py`, `review4_pairs.py` prepare collision probes; run the shared gate runner
with each selected config. `review1_preview_source.py`, `make_viewer.py`, `review4_comparison_models.py`,
`review4_final_render.py`, `review4_standing_render.py`, `review4_records.py`, `review4_handoff.py` produce the review
package and records. Earlier numbered trials are provenance, not selected final validation.

## Review round 3

[Preserved full handoff, hashes and findings](work/review_round4_before/HANDOFF.md).
Native-pose wind-up/lunge, muscle detail and 2× Death speed remain, with round-4 repairs above.

## Review round 2

[Preserved handoff](work/review_round3_before/HANDOFF.md). Head/neck and forward Cast/socket repairs remain.

## Review round 1

[Preserved handoff](work/review_round2_before/HANDOFF.md). Opaque shadows and floor-folded corpse feathers remain.
"""
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text("""# MM6 PeasantM4 / natm — review round 4

Cannibal / Head Hunter / Witch Doctor, male. Three tiers, nine clips, four LODs.
**50/100 Meshy credits spent; zero this round.**

[HANDOFF.md](HANDOFF.md) records selected files, hashes, checks and remaining qualifications.
[Viewer](review/viewer/index.html), [skin before/after](review/round4_skin_comparison.jpg),
[attack path](review/round4_attack_path.jpg), [costume frame 0](review/round4_costume_comparison.jpg),
[all clip sheets](review/sheets/).

Costume helpers now inherit the Standing parent-relative rest in upright clips. The spear follows the right flank,
with a fixed offhand grip through the blow and an explicit release. Collar/armband texture remnants and overlapping
skin/feather UV pixels are repaired while retaining muscle shading. Corpse feather folding and round-3 timings remain.
Integration actors.yml is unchanged. Implemented shared gates, bindings and viewer pass on the staged exports.

## Recorded decisions

- Work only here; original ../mm6_natm remains read-only. No commits, installs, builds or game launches.
- Preserve round-3 body/leg motion and event times; repair hand paths and helper transforms locally.
- Keep intentional Death/Dead feather folding and free cloth motion; report them separately from rigid attachment rest.
- Probe long shaft faces with coplanar subdivision; the runtime prop triangles remain unchanged.
- Preserve texture density and independent 16-pixel chart padding. This grows the body atlas to 4096×2144;
  estimated four-map RGBA8 memory without mips rises from 74 to 134 MiB. One shared set serves every LOD.
- Separate overlapping skin and feather sampling layers so filtering cannot restore pale skin triangles.
- Shared head/palm/costume extensions remain orchestrator-owned; authoring diagnostics are labeled separately.
- Existing Running source, near-body triangle target and strict native pixel percentiles remain qualified in HANDOFF.
- Orchestrator owns installation, native captures, regression and artistic acceptance.
""")
progress=read('creature_3d_progress.json');entry={'credits_spent':0,'files':manifest['files'],'bindings_changed':False,'shared_gates':main['counts'],'neck_floor_gates':neck['counts'],'dense_shaft_gates':'PASS, all four LODs, 109 samples each at 48 Hz','viewer_switches':27,'attack_impact_s':.90625,'death_duration_s':80/48,'texture_memory':memory,'open_qualifications':['Shared head/palm/costume checks unsupported; authoring diagnostics separate','Strict native luminance percentiles remain unmatched','Historical Running source does not meet later Standard Run rule','Existing near-body reduction retained','Larger padded atlas increases decoded texture memory'],'next_action':'Orchestrator: review round-4 comparisons and memory tradeoff, integrate selected exports, run native captures/regression.'}
progress.update(stage='Review round 4: re-exported and checked; qualifications documented',status='handoff_with_review_gaps',review_round_4=entry,next_action=entry['next_action'],handoff={'file':'HANDOFF.md','review_round':4,**entry});(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('ROUND4_HANDOFF_WRITTEN',{'first_costume_mm':first,'through_costume_mm':through,'memory':memory},flush=True)
