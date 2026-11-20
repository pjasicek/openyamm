"""Assemble the nine required native captures after the integrator has run both tours."""
from pathlib import Path
import yaml
from PIL import Image, ImageDraw, ImageOps

project=Path(__file__).resolve().parent
folder=project/'review/build02'
shots=[]
for name in ('review_tour_01.yml','review_tour_01_powered.yml'):
    tour=yaml.safe_load((project/name).read_text())
    shots.extend(Path(tour['output_dir'])/f'{i:02d}-{shot["name"]}.png' for i,shot in enumerate(tour['shots'],1))
assert len(shots)==9 and len({p.name for p in shots})==9
assert all(p.is_file() for p in shots),'Run both revised tours before assembling build02.'
sheet=Image.new('RGB',(1920,1188),(18,18,22));draw=ImageDraw.Draw(sheet)
for i,path in enumerate(shots):
    with Image.open(path) as original:shot=ImageOps.contain(original.convert('RGB'),(640,360))
    x,y=i%3*640,i//3*396
    sheet.paste(shot,(x+(640-shot.width)//2,y+(360-shot.height)//2))
    draw.text((x+10,y+368),path.stem,fill='white')
sheet.save(folder/'sheet.jpg',quality=92)
