import json,ast,hashlib
import numpy as np
from PIL import Image,ImageDraw
from process import ROOT,queue,save,spill

def composite(im,color):
 out=Image.new('RGBA',im.size,(*color,255));out.alpha_composite(im);return out.convert('RGB')
def run():
 m=json.loads((ROOT/'draft_manifest.json').read_text());batches=json.loads((ROOT/'batches.json').read_text());pages=[Image.open(ROOT/p['base']).convert('RGBA') for p in m['pages']]
 for key,b in batches.items():
  sheet=Image.new('RGB',(256*len(b['frames']),830),(35,35,35));draw=ImageDraw.Draw(sheet)
  for i,n in enumerate(b['frames']):
   f=m['frames'][n];x,y,w,h=f['atlas_xywh'];im=pages[f['page']].crop((x,y,x+w,y+h));aligned=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');ex,ey=spill(im)['position'];box=(max(0,ex-20),max(0,ey-20),min(im.width,ex+21),min(im.height,ey+21));edge=im.crop(box)
   sheet.paste(composite(aligned,(235,235,235)),(i*256,28));draw.text((i*256+4,5),n+' final atlas / R8 mask=0',fill='white')
   for row,color in enumerate([(18,18,18),(235,235,235)]):sheet.paste(composite(edge,color).resize((246,246),Image.Resampling.NEAREST),(i*256+5,300+row*265))
  sheet.save(ROOT/f'review/{key}_final_edges.png')
 # One source-backed transition contact per action, including every native bound step.
 for action in ['standing','attack','death']:
  steps=m['animations']['97']['actions'][action]['views']['0'];sheet=Image.new('RGB',(256*len(steps),580),(35,35,35));draw=ImageDraw.Draw(sheet)
  for i,step in enumerate(steps):
   n=step['frame'];draw.text((i*256+4,4),n+' '+str(step['duration_ms'])+'ms',fill='white')
   for row,im in enumerate([queue.native(ROOT,n).resize((256,256),Image.Resampling.NEAREST),Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA')]):sheet.paste(composite(im,(35,35,35)),(i*256,row*290+28))
  sheet.save(ROOT/f'review/transition_{action}.png')
 # Preserve the exact processing settings from the accepted identity checkpoint.
 record=json.loads((ROOT/'checkpoints/identity_acceptance.json').read_text())
 for node in ast.walk(ast.parse((ROOT/'process.py').read_text())):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='save' and len(node.args)==2 and isinstance(node.args[0],ast.BinOp) and isinstance(node.args[0].right,ast.Constant) and node.args[0].right.value=='processing.json':
   data={k.arg:ast.literal_eval(k.value) for k in node.args[1].keywords};raw=(json.dumps(data,indent=2)+'\n').encode();assert hashlib.sha256(raw).hexdigest()==record['processing_sha256'];(ROOT/'checkpoints/identity_processing.json').write_bytes(raw);record['processing_path']='checkpoints/identity_processing.json';save(ROOT/'checkpoints/identity_acceptance.json',record)
 print('Final atlas edges for all 56 frames and native action transitions saved.')
if __name__=='__main__':run()
