"""Pack image-generated staff surface detail into one four-region runtime atlas."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
p=Path(__file__).resolve().parents[1]
src=p/'references_hd/staff_design.png';im=Image.open(src).convert('RGB')
# Interior samples avoid the gray backdrop; all artwork comes from the retained AI design.
crops=[(211,350,228,540),(823,530,961,683),(211,785,234,919),(789,303,907,387)]
atlas=Image.new('RGB',(1024,1024))
for i,box in enumerate(crops):
 tile=im.crop(box).resize((248,1008),Image.Resampling.LANCZOS)
 a=np.array(tile);pad=np.pad(a,((8,8),(4,4),(0,0)),mode='edge')
 atlas.paste(Image.fromarray(pad),(256*i,0))
atlas.save(p/'textures/sor1_staff_basecolor.png')
# Flat tangent normal: engraving and grain are colour detail, not guessed geometry.
Image.new('RGB',(1024,1024),(128,128,255)).save(p/'textures/sor1_staff_normal.png')
mr=np.empty((1024,1024,3),dtype=np.uint8)
for i,(spec,rough,metal) in enumerate([(26,210,0),(210,140,160),(20,225,0),(145,70,0)]):mr[:,i*256:(i+1)*256]=[spec,rough,metal]
Image.fromarray(mr).save(p/'textures/sor1_staff_metal_rough.png')
(p/'work/staff_design_record.json').write_text(json.dumps({'source':'references_hd/staff_design.png','sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'method':'Built-in imagegen native-sprite-derived standalone design; careful original hand model; cropped surface-detail atlas','atlas_size':[1024,1024],'regions':['wood','engraved antique brass','leather wrap','red jewel'],'crops_xyxy':crops,'material':'Muted brass; body remains matte; staff unchanged between native tiers'},indent=2))
