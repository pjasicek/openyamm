"""Record the selected review revision and distinguish measured passes from remaining review gaps."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,image_of,slot,TEXTURE_SLOTS
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads((P/f).read_text())
main=read('review/runtime_gates/gates.json');neck=read('review/round2_neck_floor_gates/gates.json')
assert main['status']==neck['status']=='PASS'
for report in [main,neck]:
    for asset in report['assets']:assert sha(Path(asset['path']))==asset['sha256']
viewer=read('review/viewer_check.json');assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD' not in (P/'review/bindings_check.txt').read_text()
info=read('export/export_info.json');counts=read('export/lods.json');skin=read('review/round2_skin.json')
inventory={};textures={}
for name in ['mm6_natm.glb','mm6_natm_spear.glb','mm6_natm_buckler.glb','mm6_natm.blend']:
    f=P/'export'/name;inventory[name]={'bytes':f.stat().st_size,'sha256':sha(f)}
for kind,file,node in [('body','mm6_natm.glb','Natm'),('spear','mm6_natm_spear.glb','Spear'),('buckler','mm6_natm_buckler.glb','Buckler')]:
    d,b=read_glb(P/'export'/file);assert len(d['images'])==4
    index=next(n['mesh']for n in d['nodes']if n.get('name')==node);chain=[index]+d['meshes'][index]['extras']['openyamm_lods'];sets=[]
    for mi in chain:
        pr=d['meshes'][mi]['primitives'][0];sets.append([slot(d['materials'][pr['material']],key)['index']for key in TEXTURE_SLOTS])
    assert all(v==sets[0]for v in sets)
    for mesh in d['meshes']:
        if mesh.get('name','').endswith('_Shadow'):
            for pr in mesh['primitives']:assert d['materials'][pr['material']].get('alphaMode','OPAQUE')=='OPAQUE'
    textures[kind]={'images':4,'texture_indices_by_lod':sets,'sizes':[image_of(d,b,i)[0].size for i in sets[0]]}
images={str(f.relative_to(P)):{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted((P/'export/textures_shared').rglob('*.png'))}
manifest={'review_round':2,'files':inventory,'triangles':counts,'animations':info['clips'],'bones':78,
          'textures':textures,'image_files':images,'bindings_sha256':sha(P/'integration/actors.yml')}
(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'review/round2_texture_audit.json').write_text(json.dumps(textures,indent=2)+'\n')
for role,row in info['clips'].items():
    page=Image.new('RGB',(2100,1228),(32,32,32));draw=ImageDraw.Draw(page)
    draw.text((12,10),f'Review round 2 | {role} | {row["duration"]:.6f}s | final runtime GLBs',fill='white')
    for j,view in enumerate(['front','left','three_quarter']):
        for i,t in enumerate(np.linspace(0,row['duration'],7)):
            image=Image.open(P/f'review/final/{role}_{i:02}_{view}.png').convert('RGB');image.thumbnail((300,370))
            x=i*300+(300-image.width)//2;y=42+j*390;page.paste(image,(x,y));draw.text((i*300+8,y+370),f'{view}: {t:.3f}s',fill='white')
    page.save(P/f'review/sheets/{role}.jpg',quality=93)
focus=Image.new('RGB',(1440,1500),(32,32,32));draw=ImageDraw.Draw(focus)
for i,(role,frame,view)in enumerate([('Attack',15,'three_quarter'),('Cast',23,'front'),('Fidget',77,'left'),('Standing',0,'front')]):
    picture=Image.open(P/f'review/final/round2_{role}_{frame:02}_head_{view}.png').convert('RGB');picture.thumbnail((720,720))
    x=(i%2)*720;y=(i//2)*750;draw.text((x+12,y+10),f'{role} | frame {frame} @ 48 Hz | {view}',fill='white');focus.paste(picture,(x,y+30))
focus.save(P/'review/round2_focus.jpg',quality=94)
lod_metrics={}
for level,size in [(1,550),(2,220),(3,88)]:
    intersections=unions=0;rows=[]
    for i in range(8):
        a=np.array(Image.open(P/f'review/reduction/round2_lod0_{size}/natm_b_{i}.png'))[:,:,3]>127
        b=np.array(Image.open(P/f'review/reduction/round2_lod{level}_{size}/natm_b_{i}.png'))[:,:,3]>127
        ii=int((a&b).sum());uu=int((a|b).sum());intersections+=ii;unions+=uu;rows.append(ii/uu)
    lod_metrics[str(level)]={'actor_pixels':size,'views_iou':rows,'pooled_iou':intersections/unions}
    assert intersections/unions>=.97,(level,intersections/unions)
(P/'review/reduction/round2_metrics.json').write_text(json.dumps(lod_metrics,indent=2)+'\n')
def maximum(report,name,clip=None):
    return max(r['worst']for r in report['gates']if r['gate']==name and (clip is None or r['clip']==clip))
table='\n'.join(f'| {name} | {v["bytes"]:,} | `{v["sha256"]}` |'for name,v in inventory.items())
triangles='\n'.join(f'| {i} | {counts["body"][i]} | {counts["spear"][i]} | {counts["buckler"][i]} |'for i in range(4))
gate_rows='\n'.join(f'| {name} | {maximum(main,name):.6g} |'for name in ['arm_stretch_p99','hand_stretch_max','elbow_plane_deg','wrist_flexion_deg','angular_acceleration_deg_s2','prop_body_penetration_mm','cloth_penetration_mm','grip_gap_mm'])
release=read('review/round2_release_diagnostic.json')
skin_means=[r['mean_srgb_255']for r in skin['regions'].values()]
skin_p95=[r['p05_p50_p95_p98_srgb_255'][2]for r in skin['regions'].values()]
text=f'''# MM6 PeasantM4 / natm — staged review handoff

Latest: **Review round 2**. Re-exported for orchestrator review; the implemented shared gates and viewer pass.
Two requested qualifications remain open: shared head/palm gate support, and a strict raw-native luminance-percentile match.
Do not describe this package as having passed those checks. **50/100 Meshy credits spent; zero this round.**
No installation, shared registry edit, build, game launch or commit. The original ../mm6_natm remains read-only.

## Review round 2

- Attack/Cast and upright clips counter-rotate the head while preserving the library torso/leg motion. Authored maximum
  forward deviation: Attack **2.443°**, Cast **1.407°**, Fidget **0.334°**. The neck/upper-chest weights transition smoothly
  from spine to neck to head; jaw skin no longer follows the clavicles. Fidget retains its body/arm motion with a restrained head.
- Removed every exported B_Neck/B_Head translation and scale channel; the bones retain their bind offsets/scales.
  The actual skin edge deformation is measured below on every clip/LOD. Death/Dead retain the natural falling/lying head orientation.
- Cast lifts the arm, presents the palm and angles the fingers clear of the buckler. Final release diagnostic:
  **{release['palm_forward_deg']:.3f}°** from forward at **23/48 = 0.479166667 s**. Socket_LeftPalm remains the launch socket.
  Its inherited offset was corrected onto the measured palm surface; final surface distance is
  **{release['socket_to_hand_surface_mm']:.3f} mm**. [Socket calibration](review/round2_socket.json).
  The fitted wrist roll is -46° over the gesture envelope; the complete shared wrist/hand/contact checks pass.
- Restored nine coarse buckler back-rim vertices to the near mesh rear plane (maximum correction **9.235 mm**).
  Added at most **1.5 mm** of clearance to the upper strap arch on all LODs. No triangles added or removed.
  These changes remove the coarse rim/upper-arm and strap/forearm contacts during the revised Cast.
- Recoloured/repacked the existing body and **1K head** maps using one native warm-brown chroma, mild detail and matched
  neck-seam albedo. Head/neck/chest region means differ by **{skin['maximum_region_mean_difference_srgb_255']:.3f}/255**;
  mean hue **20.688°**, within **1.17°** of all three native ROIs. Broad painted face/neck/pectoral lighting patches are removed.
  Skin-only body normal strength is reduced to 15% to suppress baked triangular shading; head and equipment normals,
  region masks, equipment tiers and 16 px dilation remain. All LODs reference four shared images per GLB.
  Old high-pass colour residuals at UV-island boundaries were removed after the close-up review exposed triangular patches;
  the mild replacement grain is continuous in object space.
  Every shadow mesh remains opaque. Decoded atlas area is unchanged from round 1; no GPU-memory saving is claimed.
- **integration/actors.yml changed:** all three tiers' Cast impact moves from 0.447916667 to **0.479166667**.
  Attack remains 0.489583333; launch socket, scale, attachments and runtime look limits remain unchanged.
  Bindings SHA256: `{sha(P/'integration/actors.yml')}`.

### Files, hashes and triangle counts

Install only these three runtime GLBs; the .blend is the editable near source. Final editable LODs are
work/runtime_lod0.blend through runtime_lod3.blend. Earlier masters and review GLBs are not installation inputs.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
{table}

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
{triangles}

Counts are unchanged. [Manifest](export/manifest.json) records the twelve shared PNG hashes and animation inventory.
Far switch-size silhouette IoU: {', '.join(f'LOD{k} {v["pooled_iou"]:.6f}'for k,v in lod_metrics.items())}.
The original reduction curve is retained; no new reduction search was performed. Texture appearance intentionally changed,
so SSIM against the rejected patchy skin is not used as an acceptance criterion.

### Validation on these files

- [Main shared runner](review/runtime_gates/gates.md): **PASS**, {main['counts']}.
- [Neck and whole-body floor probe](review/round2_neck_floor_gates/gates.md): **PASS**, {neck['counts']}.
  The existing edge-stretch implementation selects neck skin through the configurable arm regions; maximum p99
  **{maximum(neck,'arm_stretch_p99'):.6f}×**, maximum edge **{maximum(neck,'arm_stretch_max'):.6f}×**, limits 1.5×/2×.
  The same probe selects the whole solid body as the floor region, including feathers: worst penetration
  **{maximum(neck,'floor_penetration_mm'):.6f} mm**, Dead **{maximum(neck,'floor_penetration_mm','Dead'):.6f} mm**.
- [Bindings check](review/bindings_check.txt): exit 0, **no BAD line**; staged model weights/materials/shadow opacity checked.
- [Viewer check](review/viewer_check.json): **27 switches**, zero failed switches or console errors; nine clips, three tiers.
- [Clip sheets](review/sheets/), [head/attack/cast close-ups and corpse floor](review/final/),
  [review focus sheet](review/round2_focus.jpg), [skin measurements](review/round2_skin.json), [LOD metrics](review/reduction/round2_metrics.json).

| Main measurement | Worst value |
|---|---:|
{gate_rows}

### Open qualifications / decisions for the orchestrator

1. The shared runner has **no head-facing or cast-palm target gate** and rejects unknown config fields.
   Shared files are read-only and per-creature replacement gates are prohibited by the batch rules.
   [Requested config](integration/shared_gate_request.json) and [tooling gap](integration/round2_gate_runner_gap.md)
   record the missing checks. The authoring measurements and release diagnostic are evidence, **not a shared-gate PASS**.
2. **Strict raw-native per-region luminance matching is not met.** Native head/neck/chest means are
   55.54/33.38/43.76, with p95 105.02/60.06/97.31; these include painted directional shadows.
   Revised skin albedo means are {min(skin_means):.2f}–{max(skin_means):.2f}, p95 {min(skin_p95):.2f}–{max(skin_p95):.2f}. I prioritized the explicit request for one consistent
   skin colour without a dark neck or pale facial patches, preserving native hue and leaving lighting to the renderer.
   This decision needs user review; do not report the raw-native percentile requirement as passed.
3. Native installation, runtime head-look layering, indoor/outdoor captures and regression belong to the orchestrator.
   The staged files have not been copied into assets_dev. Running retains the pre-batch historical source clip;
   no new running clip was selected in this review.

## Review round 1

Resolved the MASK shadow-material registry rejection, consolidated the LOD texture sets, and folded the corpse's
back feathers above the floor. Those repairs are retained and rechecked in round 2. The complete prior handoff and
hashes are preserved in [the round-1 checkpoint](work/review_round2_before/HANDOFF.md).
'''
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text('''# MM6 PeasantM4 / natm — review round 2

Cannibal / Head Hunter / Witch Doctor, male. Three tiers, nine library-derived clips, 78 bones and four LODs.
**50/100 Meshy credits spent; zero for this round.**

[HANDOFF.md](HANDOFF.md) records the current files, hashes, checks, changed Cast timing and remaining qualifications.
[Viewer](review/viewer/index.html), [clip sheets](review/sheets/), [manifest](export/manifest.json).

The head now counter-rotates through upright actions, neck skin blends smoothly, and the presenting Cast palm clears
the shield. Skin uses one native warm-brown hue across the 1K head, neck and chest. The shared implemented gates,
neck/full-body floor probe, bindings and 27-switch viewer check pass. Triangle counts and atlas sizes are unchanged.

## Recorded decisions

- Work only in this project; ../mm6_natm is read-only. No commit, installation, build or game launch.
- Preserve the library torso/leg motion and round-1 opaque shadows, shared padded textures and feather-floor repair.
- Cast release is now frame 23 at 48 Hz, bound to Socket_LeftPalm in all three staged descriptors.
- The head/palm checks requested by review are absent from the shared runner. Its source remains unchanged;
  integration/shared_gate_request.json records the missing intent, and HANDOFF distinguishes diagnostic evidence from gates.
- Uniform skin albedo and native hue take precedence over copying the sprite's dark-neck and bright-face lighting into
  paint. Strict raw-native luminance percentiles are therefore an open review qualification, with exact measurements recorded.
- Final editable files are work/runtime_lod*.blend. They retain packed pre-atlas images; runtime_pack.py produces the
  shared atlas layout. Earlier authoring scripts/checkpoints can overwrite later repairs and are historical provenance.
- Review round 2 still needs user artistic review and orchestrator native integration/captures.
''')
progress=read('creature_3d_progress.json');progress.update(stage='Review round 2: re-exported, shared checks passed; qualifications documented',status='handoff_with_review_gaps')
progress['review_round_2']={'credits_spent':0,'files':inventory,'bindings_changed':True,
    'shared_gates':main['counts'],'neck_floor_gates':neck['counts'],'viewer_switches':27,
    'open_qualifications':['Shared runner lacks head-facing/cast-palm checks','Strict raw-native per-region luminance percentiles not matched'],
    'next_action':'Orchestrator: review qualifications with user, extend shared gates, then install and capture if accepted.'}
progress['next_action']=progress['review_round_2']['next_action']
progress['handoff']={'file':'HANDOFF.md','review_round':2,**progress['review_round_2']}
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('ROUND2_RECORDS_WRITTEN',inventory,flush=True)
