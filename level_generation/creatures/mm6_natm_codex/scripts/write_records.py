import json,hashlib,collections,shutil,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path('level_generation/creatures/mm6_natm_codex');sys.path.insert(0,str(P/'scripts'));from reduction_metrics import compare
root=P/'review/reduction';result={}
for level,size in [(0,700),(1,550),(2,220),(3,88)]:
 ref=root/f'final_reference{size}';cur=root/f'final_lod{level}_{size}';rows={};I=U=0
 for f in sorted(cur.glob('*.png')):
  row=compare(ref/f.name,f);a=np.array(Image.open(ref/f.name))[:,:,3]>127;b=np.array(Image.open(f))[:,:,3]>127;inter=int((a&b).sum());union=int((a|b).sum());I+=inter;U+=union;row.update(intersection_pixels=inter,union_pixels=union);rows[f.name]=row
 assert len(rows)==(24 if level==0 else 8)
 summary={'height_pixels':size,'min_iou':min(x['iou']for x in rows.values()),'min_ssim':min(x['ssim']for x in rows.values()),'pooled_iou':I/U,'views':rows};summary['pass']=summary['min_iou']>=.99 and summary['min_ssim']>=.95 if level==0 else summary['pooled_iou']>=.97;assert summary['pass'],summary
 result[str(level)]=summary
 for i in range(8):
  a=Image.open(ref/f'natm_b_{i}.png').convert('RGBA');b=Image.open(cur/f'natm_b_{i}.png').convert('RGBA');page=Image.new('RGB',(1640,852),(48,48,48));page.paste(a,(0,32),a);page.paste(b,(820,32),b);draw=ImageDraw.Draw(page);draw.text((12,10),f'Reference | actor height {size}px',fill='white');draw.text((832,10),f'LOD{level} | IoU {rows[f"natm_b_{i}.png"]["iou"]:.6f}',fill='white');out=root/'final_comparisons';out.mkdir(exist_ok=True);page.save(out/f'lod{level}_view{i}.jpg',quality=94)
(root/'final_metrics.json').write_text(json.dumps(result,indent=2))
# Three-view clip sheets with exact timing; raw frames remain available beside them.
info=json.loads((P/'export/export_info.json').read_text());sheetdir=P/'review/sheets';sheetdir.mkdir(exist_ok=True)
for role,row in info['clips'].items():
 page=Image.new('RGB',(7*300,3*390+58),(32,32,32));d=ImageDraw.Draw(page);d.text((12,10),f'{role} | {row["duration"]:.6f}s | front / left / three-quarter',fill='white')
 for j,view in enumerate(['front','left','three_quarter']):
  for i,t in enumerate(np.linspace(0,row['duration'],7)):
   im=Image.open(P/f'review/final/{role}_{i:02}_{view}.png').convert('RGB');im.thumbnail((300,370));x=i*300+(300-im.width)//2;y=42+j*390;page.paste(im,(x,y));d.text((i*300+8,y+370),f'{view}: {t:.3f}s',fill='white')
 page.save(sheetdir/f'{role}.jpg',quality=93)
# Preserve final runtime hashes; signed Meshy receipt URLs stay in the progress file.
inventory={}
for name in ['mm6_natm.glb','mm6_natm_spear.glb','mm6_natm_buckler.glb','mm6_natm.blend']:
 path=P/'export'/name;inventory[name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(P/'export/manifest.json').write_text(json.dumps({'files':inventory,'descriptors':['PeasantM4 A','PeasantM4 B','PeasantM4 C'],'triangles':json.loads((P/'export/lods.json').read_text()),'animations':info['clips'],'scale':103.7995785021,'bones':68},indent=2))
(P/'ANIMATION_STUDY.md').write_text("""# Final natm animation study

Native source is the read-only ../mm6_natm project: 59 frames at 125 ms per frame. Standing and walking have five stored directions. The native attack is a raised one-handed spear thrust. The native death falls backward; the early forward-collapse candidate was rejected.

| Runtime role | Local library source | Duration |
|---|---|---:|
| Standing | Mixamo Standard Idle.fbx | 3.000000 s |
| Fidget | Mixamo Standing Idle 02 Looking.fbx | 3.208333 s |
| Walking | humanoid_set/Armed.glb, ArmedWalk | 0.958333 s |
| Running | humanoid_set/Relax.glb, RelaxRunForward | 0.729167 s |
| Attack | humanoid_set/1Hand.glb, SpearAttackR1 | 1.583333 s |
| Cast | humanoid_set/Armed.glb, ArmedCastLAttack1 | 1.583333 s |
| Hit | humanoid_set/Unarmed.glb, UnarmedGetHitF1 | 0.625000 s |
| Death | Mixamo Standing React Death Backward.fbx | 3.333333 s |
| Dead | Exact held Death endpoint | 0.020833 s |

G1 library mannequin sheets are in review/g1. G2 measurements are in work/proportions.json. The fitted rig keeps the source bone frames, measured segment lengths and anatomical elbow planes; helpers distribute deformation roll. Rest-delta Mixamo retargeting moves source forearm roll into the hand before the deformation helpers distribute it.

Standing/Fidget use planted soles and relaxed native carry. Walk/run foot placement follows measured sole geometry. Walking stride is 0.592592593 m; the engine's running multiplier 1.55 gives 0.918518519 m. Attack/Cast/Hit retain the library torso/arm motion, with planted leg adaptation, continuous elbow poles and fixed spear grip. Death uses the library backward reaction, with signed-contact panel adjustments. No paid library jobs or procedural replacement of the main action clips.

The fastest target-facing spear-tip interval is centered at 0.489583333 s. The left-palm spell release is 0.447916667 s. Cast is deliberately distinct for the Witch Doctor's Fire Bolt.

Final front/side/three-quarter sheets are in review/sheets; the three-tier review viewer is review/viewer/index.html. Decorative back feathers still extend below the ground plane during the fall/corpse pose; this is an explicit open visual fault in HANDOFF.md.
""")
(P/'integration/playbook_notes.md').write_text("""# natm production lessons

- Check the native death direction from the whole sequence. The first forward-collapse choice was wrong; the selected source is Mixamo's backward death.
- Keep the humanoid source frames and fit measured anatomy. Elbow pole continuity and actual angular acceleration matter more than a clip's name.
- Align gait to the visible sole, not just Foot-to-Toe0 joint direction. natm needed a 16-degree correction on each side.
- A forearm buckler's upper strap must stay below the elbow; the initial strap crossed the bending joint. Validate straps along with the shell.
- Select the entire simplified grip cylinder, including both end rings. Cutting one ring out of the audit region falsely produced 90 mm hand gaps.
- Measure the cupped palm's actual contact-surface normal. The open-hand plane differed from the closed palm's local contact patch.
- Test leg-in-panel volume and panel-in-skin triangle interiors. Either direction alone missed the falling rear panel's overlap.
- Per-row unconstrained contact pushes caused cloth jitter and were rejected. Fit a coherent panel-normal clearance, then a small targeted bidirectional fall correction.
- Preserve clear gaps between distant feathers with a rebaked alpha cutout. The matching shadow LOD needs the same UV/alpha coverage.
- Recheck skin after far-LOD rebaking/downsampling. Restoring the near skin luminance distribution preserved native mean and highlights on every tier/LOD.
- Shared audit sampling needs float32 endpoint de-duplication; a 40 ns final interval falsely became the fastest weapon motion. A one-frame held clip also needs a third, midpoint sample to measure zero acceleration.
- The shared runner measures raw hand roll against the source hinge frame. Keep that measurement and separately measure the wrist against its actual distal forearm twist frame; do not move the elbow landmark to the helper's head.
- Decorative feather floor contact needs a separate visual gate: skin/feet/props can clear the floor while rigid cape strands pass below it. This remains the explicit visual fault in this handoff.
""")
print('RECORDS', {k:{x:v[x]for x in ['min_iou','min_ssim','pooled_iou','pass']}for k,v in result.items()})
