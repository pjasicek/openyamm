"""Compare every final atlas frame and inspect its most suspicious alpha edge."""
import json
from PIL import Image,ImageDraw
from process import ROOT,queue,save,spill
def composite(im,color):
 out=Image.new('RGBA',im.size,(*color,255));out.alpha_composite(im);return out.convert('RGB')
def run():
 m=json.loads((ROOT/'draft_manifest.json').read_text());batches=json.loads((ROOT/'batches.json').read_text());pages=[Image.open(ROOT/p['base']).convert('RGBA') for p in m['pages']]
 for key,b in batches.items():
  sheet=Image.new('RGB',(256*len(b['frames']),1120),(35,35,35));draw=ImageDraw.Draw(sheet)
  for i,n in enumerate(b['frames']):
   f=m['frames'][n];x,y,w,h=f['atlas_xywh'];im=pages[f['page']].crop((x,y,x+w,y+h));aligned=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');ex,ey=spill(im)['position'];box=(max(0,ex-20),max(0,ey-20),min(im.width,ex+21),min(im.height,ey+21));edge=im.crop(box)
   native=queue.native(ROOT,n);sheet.paste(composite(native,(35,35,35)),(i*256,25));thumb=aligned.resize((round(aligned.width/2),round(aligned.height/2)),Image.Resampling.LANCZOS);sheet.paste(composite(thumb,(235,235,235)),(i*256,310));draw.text((i*256+4,4),n+' native / final atlas',fill='white')
   for row,color in enumerate([(18,18,18),(235,235,235)]):sheet.paste(composite(edge,color).resize((246,246),Image.Resampling.NEAREST),(i*256+5,590+row*265))
  sheet.save(ROOT/f'review/{key}_final_edges.png')
 for action in ['standing','attack','hit','death','corpse']:
  steps=m['animations']['142']['actions'][action]['views']['0'];sheet=Image.new('RGB',(512*len(steps),1120),(35,35,35));draw=ImageDraw.Draw(sheet)
  for i,step in enumerate(steps):
   n=step['frame'];draw.text((i*512+4,4),n+' '+str(step['duration_ms'])+'ms',fill='white')
   for row,im in enumerate([queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA')]):sheet.paste(composite(im,(35,35,35)),(i*512,row*560+28))
  sheet.save(ROOT/f'review/transition_{action}.png')
 print('All 95 final atlas frames, dark/light edge crops and native transitions saved.')
if __name__=='__main__':run()
