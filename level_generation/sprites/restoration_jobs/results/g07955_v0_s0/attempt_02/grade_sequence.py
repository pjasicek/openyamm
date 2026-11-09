from pathlib import Path
import json
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[3]
measurements=[]
for segment,gain in [(0,0.7709232425918799),(1,0.7151938779443993)]:
 d=root/f"results/g07955_v0_s{segment}/attempt_02"
 checks=json.loads((d/"checks.json").read_text())
 for key in checks["frames"]:
  f=d/f"{key}.png"; backup=d/f"{key}.before_tone.png"
  if not backup.exists(): backup.write_bytes(f.read_bytes())
  a=np.array(Image.open(backup).convert("RGBA"))
  a[:,:,:3]=np.rint(a[:,:,:3].astype(float)*gain).astype(np.uint8)
  Image.fromarray(a).save(f)
 measurements.append({"segment":segment,"gain":gain,"method":"Common segment RGB gain from pooled native/generated opaque Rec709 mean; alpha unchanged, preserves within-segment animation changes."})
(root/"results/g07955_v0_s0/attempt_02/tone.json").write_text(json.dumps(measurements,indent=2)+"\n")
