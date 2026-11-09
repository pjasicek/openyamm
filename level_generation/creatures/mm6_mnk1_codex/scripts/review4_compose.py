import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parents[1];out=p/'review';frames=out/'final_frames';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for view in ['front','left','three_quarter']:
 rows=json.loads((frames/f'{view}.json').read_text());sheet=Image.new('RGB',(2000,len(rows)*424),(215,215,215));d=ImageDraw.Draw(sheet)
 for y,row in enumerate(rows):
  for x,(file,label) in enumerate(row):sheet.paste(Image.open(file).convert('RGB'),(x*400,y*424+24));d.text((x*400+8,y*424+2),label,fill='black',font=font)
 sheet.save(out/f'clips_{view}.png')
sheet=Image.new('RGB',(5*384,3*504),(215,215,215));d=ImageDraw.Draw(sheet)
for y,(k,pal,name) in enumerate(zip('abc',[774,775,776],['Novice','Initiate','Master'])):
 native=Image.open(p.parent/f'mm6_mnk1/native_variants/mnk1sta0_{pal}.png').convert('RGBA');native=native.resize((round(native.width*445/native.height),445),Image.Resampling.NEAREST);sheet.paste(native,(int((384-native.width)/2),y*504+48),native);d.text((8,y*504+5),name+' native',fill='black',font=font)
 for x,view in enumerate(['front','left','back','three_quarter'],1):
  im=Image.open(frames/f'tier_{k}_{view}.png').convert('RGB');im.thumbnail((384,480));sheet.paste(im,(x*384,y*504+24));d.text((x*384+8,y*504+2),name+' '+view,fill='black',font=font)
sheet.save(out/'tier_comparison.png')

# Current export evidence, preserving camera aspect and the captured playback times in the adjacent JSON.
def grid(items, columns, filename, width=400, height=320):
 sheet=Image.new('RGB',(columns*width,((len(items)+columns-1)//columns)*(height+28)),(215,215,215));draw=ImageDraw.Draw(sheet)
 for i,(file,label) in enumerate(items):
  im=Image.open(file).convert('RGB');im.thumbnail((width,height));x=(i%columns)*width;y=(i//columns)*(height+28)
  sheet.paste(im,(x+(width-im.width)//2,y+28+(height-im.height)//2));draw.text((x+6,y+4),label,fill='black',font=font)
 sheet.save(out/filename)
triangles=json.loads((p/'export/lods.json').read_text())['triangles']
grid([(frames/f'lod{level}_{clip}_three_quarter.png',f'{clip} LOD{level}: {triangles[level]} tris') for clip in ['Standing','Attack','Dead'] for level in range(4)],4,'lod_comparison.png',400,400)
playback=json.loads((out/'playback/playback.json').read_text());assert len(playback)==18 and all(len(r['frames'])==5 for r in playback)
for speed,name in [(1,'normal'),(.5,'slow')]:
 grid([(out/'playback'/f['file'],f"{row['clip']} {speed}x sample {i+1}") for row in playback if row['speed']==speed for i,f in enumerate(row['frames'])],5,f'playback_{name}.png')
