"""Prepare native school-of-fish references and preserve exact job prompts."""
from pathlib import Path
import json,importlib.util,datetime
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('queue',ROOT.parent/'mm8_restore_queue.py');queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)
def run():
 batches=json.loads((ROOT/'batches.json').read_text())
 for d in ['raw','prompts','checkpoints','review']:(ROOT/d).mkdir(exist_ok=True)
 for key,b in batches.items():
  im=Image.open(ROOT/f'references/{key}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(0,255,0,255));bg.alpha_composite(im);bg.convert('RGB').save(ROOT/f'references/{key}_matte.png')
  detail='Five stored views of the same native school, each containing multiple fish at different apparent sizes and depths.' if key=='identity' else ('Preserve the native falling, turning and prone fish positions exactly. Each school changes its arrangement as the native fish roll and collapse. Do not replace it with a normal swimming school.' if key.startswith('native_d') else 'Preserve every native swimming frame: exact individual fish locations, sizes, overlaps, tail/fin angles and direction. The whole school is a single actor frame.')
  prompt=f'''Use case: identity-preserve. Restore Might and Magic VIII native School of Fish sprite artwork, base palette 637.
Input 1 is the exact pose, layout, appearance, relative size and tonal authority. Maintain {b['columns']} columns by {b['rows']} rows, {len(b['frames'])} occupied equal cells in row-major order: {', '.join(b['frames'])}. Keep the precise sheet aspect ratio, common scale, all empty margins and cell placements. Empty cells remain empty.
{detail}
Preserve EVERY fish and its exact location, orientation, size, spacing and overlap inside each school. Keep small distant fish small, and preserve all visible fish even if their heads or tails overlap. These are stylized spiny fantasy fish with long pointed mouths, narrow silver-gray fins, forked tails, dark violet-plum bodies, pale lavender/silver scale highlights and cream-gold irregular markings. Preserve native directional lighting and dark tonal weight. Add restrained coherent scale texture, crisp fin rays and clean readable anatomy without redesigning the species, changing markings, adding or removing fish, adding teeth, or enlarging eyes.
Render the refined sprite subjects on a perfectly flat saturated green RGB(0,255,0) background, used only outside the fish. No green light bounce or fringe. Keep violet, plum, cream and gray fish colors unchanged. No text, labels, borders, grid, bubbles, water, plants, cast shadow or environment. No recentering or fitting each school to equal silhouette bounds. Keep every thin fin and tail inside its cell. Match the supplied framing and aspect ratio with useful high-resolution detail.
'''
  if key!='identity':prompt+='Input 2 is the accepted enhanced identity reference for material and detail only; input 1 remains the sole pose, arrangement, size and placement authority.\n'
  (ROOT/f'prompts/{key}_v1.txt').write_text(prompt)
 names=['m636wa2','m636da0','m636xa2'];out=Image.new('RGB',(1536,1650),(35,35,35));draw=ImageDraw.Draw(out)
 for i,n in enumerate(names):
  for j,pal in enumerate([637,638,636]):
   im=queue.native(ROOT,n,pal).resize((512,512),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,(35,35,35,255));bg.alpha_composite(im);out.paste(bg.convert('RGB'),(j*512,i*550+25));draw.text((j*512+5,i*550+5),n+' native '+str(pal),fill='white')
 out.save(ROOT/'references/native_palette_materials.png')
 path=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(path.read_text());ledger['families']['m636'].update(status='partial',processed_frames=0,resume='Inspect native palettes, generate and accept five-view school identity; process 130 unique frames in 21 native-layout batches; derive variants and validate full coverage.');ledger['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};path.write_text(json.dumps(ledger,indent=2)+'\n');print('Prepared 21 native School of Fish references and exact prompts.')
if __name__=='__main__':run()
