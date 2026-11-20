from pathlib import Path
from PIL import Image,ImageDraw
import sys
p=Path(__file__).resolve().parents[1]/'review'/sys.argv[1]
roles=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
for view in ['front','left','three_quarter']:
 out=Image.new('RGB',(1500,len(roles)*450),'white');d=ImageDraw.Draw(out)
 for j,role in enumerate(roles):
  for i in range(5):out.paste(Image.open(p/f'{role}_{i}_{view}.png'),(i*300,j*450+25))
  d.text((10,j*450+6),role,fill='black')
 out.save(p/f'{view}_sheet.jpg')
