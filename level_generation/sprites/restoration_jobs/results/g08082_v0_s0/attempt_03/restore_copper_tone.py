from pathlib import Path
import json
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[3]
for job in ["g08082_v0_s0"]:
 d=root/"results"/job/"attempt_03"
 records=[]
 for key in json.loads((d/"checks.json").read_text())["frames"]:
  f=d/f"{key}.png";backup=d/f"{key}.before_tone.png"
  if not backup.exists(): backup.write_bytes(f.read_bytes())
  a=np.array(Image.open(backup).convert("RGBA"));n=np.array(Image.open(root/"native"/f"{key}.png").convert("RGBA"))
  target=n[:,:,:3][n[:,:,3]>=192].mean(axis=0)/255
  rgb=a[:,:,:3].astype(float)/255;opaque=a[:,:,3]>=192;gammas=[]
  for channel in range(3):
   lo,hi=.1,5.
   for _ in range(40):
    mid=(lo+hi)/2
    if np.mean(rgb[:,:,channel][opaque]**mid)>target[channel]:lo=mid
    else:hi=mid
   gamma=(lo+hi)/2;gammas.append(gamma);rgb[:,:,channel]**=gamma
  a[:,:,:3]=np.rint(rgb*255).astype(np.uint8);Image.fromarray(a).save(f)
  records.append({"asset":key,"native_opaque_mean_rgb":(target*255).tolist(),"channel_gamma":gammas,"alpha":"unchanged"})
 (d/"tone.json").write_text(json.dumps(records,indent=2)+"\n")
 (d/"POSTPROCESS.md").write_text("Unadjusted native rectangle extraction, then results/g08082_v0_s0/attempt_03/restore_copper_tone.py, then queue.py check for the mile marker. Script uses immutable before_tone exports; per-channel bounded gamma matches native opaque mean RGB, preserving alpha and shading detail.\n")
