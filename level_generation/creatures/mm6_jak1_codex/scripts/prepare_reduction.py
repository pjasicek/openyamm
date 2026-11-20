"""Freeze the gate-passing mesh and canonical textures for the rebake study."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction';R=P/'review/round2/reduction'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,image_of
source=P/'export/mm6_jak1_runtime_lod0.glb';digest=hashlib.sha256(source.read_bytes()).hexdigest()
receipt=json.loads((P/'review/round2/rig_gate_receipt.json').read_text())
assert receipt['status']=='pass' and receipt['glb_sha256']==digest,'Run the complete rig gates on this export first.'
if (W/'source.json').exists():
 assert json.loads((W/'source.json').read_text())['model_sha256']==digest,'The source changed; archive the previous study explicitly.'
W.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);maps=W/'high_maps';maps.mkdir(exist_ok=True)
shutil.copy2(P/'work/runtime_master.blend',W/'unreduced.blend')
shutil.copy2(source,W/'unreduced.glb')
shutil.copy2(P/'review/round2/rig_gate_receipt.json',R/'unreduced_rig_gate_receipt.json')
doc,binary=read_glb(source);ramps=json.loads((P/'textures/jak1_ramps.json').read_text());images={}
for tag,name in [('body','Jackalman_A'),('head','JackalmanHead_A'),('staff','HookedStaff_A')]:
 material=next(m for m in doc['materials']if m['name']==name);pbr=material['pbrMetallicRoughness']
 for key,info in [('basecolor',pbr['baseColorTexture']),('metal_rough',pbr['metallicRoughnessTexture']),('normal',material['normalTexture'])]:
  image,_=image_of(doc,binary,info['index']);path=maps/f'{tag}_{key}.png';image.save(path);images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
 if tag!='staff':
  entry=next(m for m in ramps['materials']if m['base']==name);path=maps/f'{tag}_region_mask.png';shutil.copy2(P/'textures'/entry['mask'],path);images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
shutil.copy2(P/'textures/jak1_ramps.json',maps/'source_ramps.json')
subprocess.run([sys.executable,str(P/'scripts/reduction_images.py'),'tiers',str(maps)],check=True)
(W/'source.json').write_text(json.dumps({'model_sha256':digest,'blend_sha256':hashlib.sha256((W/'unreduced.blend').read_bytes()).hexdigest(),'images':images,'rig_gate_receipt':'review/round2/rig_gate_receipt.json'},indent=2))
(R/'README.md').write_text("""# Jackalman round 2 reduction study

The corrected, gate-passing model is frozen in work/round2/reduction/unreduced.blend.
The curve uses approximately ten-percent geometry steps, planar dissolve and protected collapse.
Hands, face, joint loops, soles, silhouette edges and staff contact areas receive protection.

Every retained candidate is rebaked from the frozen high mesh: base colour, region mask, packed
engine specular/roughness/metal channels and an OpenGL tangent normal map. Projection separates
connected components. The existing chart layout is reprojected; its interpolated old pixels are
not reused as the finished texture. Every map remains 1024 square.

The colour comparison uses all three engine region-ramp tiers, eight directions, a 700-pixel actor
height, identical Workbench studio lighting and transparent silhouettes. SSIM is measured over a
dilated foreground crop, so the background cannot conceal a difference. Required LOD0 limits:
minimum silhouette IoU 0.99 and minimum textured SSIM 0.95. The final selected mesh must also pass
the rig/contact gates. Native PBR presentation remains the batch orchestrator's game check.
""")
print('Froze current rig-gate source and canonical maps:',digest)
