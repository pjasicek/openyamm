import json,shutil,sys
from PIL import Image,ImageDraw
from process import ROOT,save,queue,spill
b=json.loads((ROOT/'batches.json').read_text())['identity'];sheet=Image.new('RGB',(256*5,820),(35,35,35));d=ImageDraw.Draw(sheet)
for i,n in enumerate(b['frames']):
 im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');edge=spill(im);x,y=edge['position'];crop=im.crop((max(0,x-20),max(0,y-20),min(im.width,x+21),min(im.height,y+21)))
 for row,color in enumerate([(20,20,20),(235,235,235)]):
  bg=Image.new('RGBA',crop.size,(*color,255));bg.alpha_composite(crop);sheet.paste(bg.resize((246,246),Image.Resampling.NEAREST).convert('RGB'),(i*256+5,300+row*260))
 bg=Image.new('RGBA',im.size,(235,235,235,255));bg.alpha_composite(im);bg.thumbnail((256,256));sheet.paste(bg.convert('RGB'),(i*256,30));d.text((i*256+4,4),n,fill='white')
sheet.save(ROOT/'review/identity_edges.png')
if '--accept' in sys.argv:
 target=ROOT/'checkpoints/accepted_identity_generation_reference.png';assert not target.exists();shutil.copyfile(ROOT/'raw/identity_v1.png',target)
 save(ROOT/'checkpoints/identity_acceptance.json',{'status':'accepted_identity','raw':'raw/identity_v1.png','raw_sha256':queue.sha(ROOT/'raw/identity_v1.png'),'reference':str(target.relative_to(ROOT)),'reference_sha256':queue.sha(target),'tone':json.loads((ROOT/'tone_settings.json').read_text()),'decision':'Five native standing angles retain the lumpy gray-violet rock shapes, front fissures and rear surfaces. Native/restored contacts and dark/light edge crops inspected. Common native logical placement retained; one fixed tone multiplier restores native tonal weight. Generation reference retains raw exposure so that the same offline tone is applied exactly once to each generated batch.','review':['review/identity_native_restored.png','review/identity_edges.png'],'palette':588,'variants':'Native A/B/C use the same palette; native scale differs.'})
 bs=json.loads((ROOT/'batches.json').read_text());bs['identity']['state']='accepted_identity';save(ROOT/'batches.json',bs);g=json.loads((ROOT/'generation.json').read_text());g['batches']['identity']['status']='accepted_identity';save(ROOT/'generation.json',g)
 print('Boulder identity accepted; 15 native action/view batches ready.')
else:print('Boulder identity edge contact saved for review.')
