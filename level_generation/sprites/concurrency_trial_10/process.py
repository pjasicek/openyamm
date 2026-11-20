"""Preserve benchmark results, clean ten drafts, and report observed timing without counting queue wait twice."""
from pathlib import Path
import importlib.util,json,hashlib,statistics
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('decoration_processing',HERE.parents[1]/'decorations/mm6_new_sorpigal/process.py')
processing=importlib.util.module_from_spec(spec);spec.loader.exec_module(processing)
jobs=json.loads((HERE/'jobs.json').read_text());records=[json.loads((HERE/'raw'/f"{j['id']}.result.json").read_text()) for j in jobs]
start=min(r['submitted_ms'] for r in records);end=max(r['completed_ms'] for r in records);wall=(end-start)/1000
control=json.loads((HERE/'raw/32haxe_serial_control.result.json').read_text())
completed=sorted(records,key=lambda r:r['completed_ms']);intervals=np.diff([start]+[r['completed_ms'] for r in completed])/1000
report=dict(submitted_jobs=10,successful_image_outputs=10,submission_spread_seconds=(max(r['submitted_ms'] for r in records)-start)/1000,
            batch_wall_seconds=wall,throughput_seconds_per_image=wall/10,serial_control_seconds=control['duration_seconds'],
            extrapolated_10_serial_seconds=control['duration_seconds']*10,
            estimated_speedup_from_one_control=control['duration_seconds']*10/wall,
            completion_gaps_seconds=intervals.tolist(),completion_gap_median_seconds=statistics.median(intervals),
            caveat='One serial control, not a matched ten-image sequential run. Client latency includes queue wait; its sum is not a serial baseline. No end-to-end speedup claim.',
            observation='Results arrived approximately every 24-32 seconds. Consistent with effective serialization somewhere in the tool/service path.',
            records=records,control=control)
(HERE/'timing.json').write_text(json.dumps(report,indent=2)+'\n')
frames={};images={}
for j in jobs:
 name=j['id'];raw=Image.open(HERE/'raw'/f'{name}.png');clean,stats=processing.clean(raw,(255,0,255));source=dict(size=j['native_size'],visible_bounds=j['native_bounds']);out,registration=processing.register(clean,source,(255,0,255));out.save(HERE/'enhanced'/f'{name}.png');images[name]=out
 a=np.array(out);visible=a[:,:,3]>0;excess=np.minimum(a[:,:,0].astype(int),a[:,:,2].astype(int))-a[:,:,1].astype(int);assert not np.any(visible & (excess>16)),name
 frames[name]=dict(file=f'enhanced/{name}.png',physical_size=list(out.size),native_size=j['native_size'],logical_pivot=[j['native_size'][0]/2,j['native_size'][1]],palette_baked=j['palette_id'],raw_sha256=hashlib.sha256((HERE/'raw'/f'{name}.png').read_bytes()).hexdigest(),sha256=hashlib.sha256((HERE/'enhanced'/f'{name}.png').read_bytes()).hexdigest(),cleanup=stats,registration=registration,contour_spill_candidates_over_16=0)
(HERE/'manifest.json').write_text(json.dumps(dict(status='Benchmark drafts; not installed or production-accepted',pixels_per_logical_pixel=2,frames=frames,
 review_notes={'3amber':'AI introduced holes into the amber; repair against native before production acceptance.','3apple':'Coarse pixel steps retained at master resolution; refine before production acceptance.','all':'One-pass timing experiment. Transparent 2x drafts preserve native canvas; full artistic approval is separate.'}),indent=2)+'\n')
for label,bg in [('dark',(35,39,37)),('light',(225,227,222))]:
 sheet=Image.new('RGB',(1200,1500),bg);draw=ImageDraw.Draw(sheet)
 for i,j in enumerate(jobs):
  x=i%2*600;y=i//2*300;name=j['id'];draw.text((x+8,y+8),name+' - native / enhanced draft',fill=(150,150,150))
  native=Image.open(HERE/'native'/f'{name}.png');scale=min(280/native.width,255/native.height);size=(round(native.width*scale),round(native.height*scale))
  for col,im in enumerate([native,images[name]]):
   pic=im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');tile=Image.new('RGBA',size,(*bg,255));tile.alpha_composite(pic);sheet.paste(tile.convert('RGB'),(x+col*300+(300-size[0])//2,y+285-size[1]))
 sheet.save(HERE/'review'/f'comparison_{label}.png')
lines=['# Ten-request image-generation timing trial','', '2026-09-09; built-in imagegen only. First ten confirmed entries in the non-creature CSV.', '',
'## Result','',f'- All ten requests submitted within {report["submission_spread_seconds"]:.3f} seconds; all ten returned images.',
f'- Batch: **{wall:.3f} seconds** ({wall/60:.2f} minutes); **{wall/10:.2f} seconds per delivered image**.',
f'- One matching standalone request (32haxe, identical prompt/reference): **{control["duration_seconds"]:.3f} seconds**.',
f'- Ten times that single sample: **{control["duration_seconds"]*10:.2f} seconds**, implying an **estimated {report["estimated_speedup_from_one_control"]:.2f}x** throughput ratio.',
'- That ratio is not a measured ten-versus-ten speedup. Different assets, service variance and one control limit the comparison.',
'- Results arrived in approximately 24–32-second increments, consistent with a queued/effectively serial tool/service path.',
'  The client cannot distinguish tool scheduling from service-side scheduling. Ten simultaneous submissions did not yield ten simultaneous completions.',
'- Excludes preparation, review, cleanup, model/tool message handling after the result callback and export. Historical serial runs',
'  did not retain equivalent timings. Do not sum queued request latencies and call that the old serial runtime.', '',
'| Completion order | Asset | Seconds since submission |','| ---: | --- | ---: |']
for i,r in enumerate(completed,1):lines.append(f"| {i} | `{r['id']}` | {r['duration_seconds']:.3f} |")
lines+=['','## Assets and checks','','[Dark comparison](review/comparison_dark.png) · [Light comparison](review/comparison_light.png)',
'','All 11 raw outputs (ten jobs and one control) were copied into `raw/`; exact prompts, inspected paletted references,',
'source hashes and per-job timing metadata are saved. Ten transparent 2x drafts are in `enhanced/`, with native',
'canvas/pivot metadata in `manifest.json`. Matte extraction, contour decontamination and premultiplied resizing ran.',
'','These are **benchmark drafts**, not installed artwork. The amber gained holes and the apple retained coarse',
'pixel stepping; those need targeted correction before a full restoration goal accepts them. No extra repair calls',
'were mixed into the timing sample. Visual quality is a separate gate from a successful tool response.', '',
'## Reproduce offline processing','','```sh','python3 level_generation/sprites/concurrency_trial_10/process.py','```','',
'This reuses outputs and makes no image-generation calls. `prepare.py` regenerates the ten native references.',
'Live generation requires the agent built-in tool; use [the scheduling guidance](../PARALLEL_IMAGEGEN.md).', '',
'[Machine-readable timings](timing.json) · [Export manifest](manifest.json)','']
(HERE/'README.md').write_text('\n'.join(lines));print(json.dumps({k:v for k,v in report.items() if k not in ['records','control']},indent=2))
