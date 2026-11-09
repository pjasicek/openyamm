"""Package reviewed assets and publish reproducible review evidence."""
import csv,json,zipfile
from pathlib import Path
from PIL import Image,ImageDraw
from build import P,R,T,ROOT,OUT,OLD,MASTER,sha

def main():
    validation=json.loads((P/'reports/validation.json').read_text())
    assert not validation['failures']
    assert validation['files']=={p.name:sha(p) for p in OUT.glob('*.png')}
    assert not json.loads((MASTER/'report.json').read_text())['failures']
    manifest=json.loads((P/'runtime_x2/manifest.json').read_text())
    for name,digest in manifest['files'].items():assert sha(P/'runtime_x2'/name)==digest
    assert all(sha(p)==sha(OUT/p.name) for p in OLD.glob('*.png'))
    original_validation=T/'mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/validation.json'
    previous=json.loads(original_validation.read_text());assert not previous['failures']
    for name,digest in previous['files'].items():assert sha(OUT/name)==digest
    incompatible=validation['native_incompatible_placements']
    with (P/'reports/native_layout_mismatches.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['first','side','second','placements','example_map','row','column'])
        for r in incompatible:writer.writerow([r['a'],r['side'],r['b'],r['placements'],r['example']['map'],r['example']['row'],r['example']['column']])
    selected=sorted(incompatible,key=lambda r:-r['placements'])[:12]
    sheet=Image.new('RGB',(1024,12*280),'#202933');draw=ImageDraw.Draw(sheet)
    for row,r in enumerate(selected):
        draw.text((4,row*280+4),r['a']+' '+r['side']+' '+r['b']+' : original left / restored right',fill='white')
        for z in (0,1):
            for col,name in enumerate((r['a'],r['b'])):
                im=Image.open(ROOT/'assets_dev/worlds/mm6/textures'/(name+'.bmp')).convert('RGB') if z==0 else Image.open(OUT/(name+'.png')).convert('RGB')
                if r['side']=='S':im=im.transpose(Image.Transpose.TRANSPOSE)
                sheet.paste(im.resize((256,256)),(z*512+col*256,row*280+24))
    sheet.save(P/'reports/native_layout_mismatches.png')
    roads=[r['tile'] for r in json.loads((P/'reports/build.json').read_text())['tiles'] if r['family']=='roads']
    sheet=Image.new('RGB',(1024,840),'#202933');draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(roads):
        for j,path in enumerate((R/'references'/(name+'.png'),OUT/(name+'.png'))):
            x=i%2*512+j*256;y=i//2*280
            draw.text((x+3,y+3),name+(' original' if j==0 else ' x2'),fill='white')
            sheet.paste(Image.open(path).resize((256,256)),(x,y+24))
    sheet.save(P/'reports/roads_review.png')
    stage=json.loads((P/'reports/review_stage.json').read_text())
    assert stage['files']=={p.name:sha(p) for p in OUT.glob('*.png')}
    for mode in stage['map_hashes']:
        for name,digest in stage['files'].items():
            assert sha(Path(stage['stage'])/mode/'assets_dev/worlds/mm6/terrain_x2'/name)==digest
    captures={}
    for name,pose in stage['poses'].items():
        path=P/'captures'/('mm6_'+name+'.json');image=path.with_suffix('.png')
        if not path.exists():continue
        c=json.loads(path.read_text())
        assert c['binary_sha256']==stage['binary_sha256']
        assert c['native_sha256']==stage['map_hashes'][pose['mode']]
        assert image.stat().st_mtime >= (P/'reports/review_stage.json').stat().st_mtime
        captures[name]=dict(image_sha256=sha(image),metadata_sha256=sha(path))
    assert len(captures)==5,'Complete all five native family captures before packaging.'
    result=dict(runtime_files=134,new_masters=5,new_transitions=66,unchanged_existing_files=63,compatible_join_checks=validation['compatible_joins'],compatible_join_failures=0,unchanged_pack_previous_join_checks=previous['unique_joins'],unchanged_water_frames=14,previous_validation_sha256=sha(original_validation),native_layout_mismatch_pairs=len(incompatible),native_layout_mismatch_placements=sum(r['placements'] for r in incompatible),captures=captures,scope='Asset generation and isolated fixture review. Existing peasants enhanced and source maps are not modified.')
    (P/'reports/review.json').write_text(json.dumps(result,indent=2)+'\n')
    text='''# Complete MM6 terrain x2

134 runtime PNGs: all 120 static terrain names used by the 15 MM6 outdoor maps, plus 14 water animation frames.

- Five 256px masters, with the corrected tropical v3 artwork; other four masters unchanged from v2.
- Sixty material-to-dirt transitions: sand, snow, cracked, tropical and swamp, twelve directional variants each.
- Six additional cobble roads, joined to the existing roads' accepted coverage and shading profiles.
- All 63 accepted New Sorpigal terrain/water files preserved byte-for-byte.

Coverage and contact shading are recovered from the original tile artwork and transferred onto the accepted restored materials. Snow keeps its broad soft mixing; vegetation keeps irregular edges; sand and cracked ground retain their original boundary treatment. Original low-resolution colour grain is not overlaid onto the masters. Authoring masks and scalar shading fields are retained under `masks/`, `shading/` and `fields/`. Shading PNG neutral value is 200; NPZ stores the actual floating-point multiplier.

[Review gallery](index.html) · [Validation](reports/validation.json) · [Combined runtime ZIP](mm6_complete_terrain_x2.zip) · [Master review](../masters/v3/index.html)

## Validation and limits

All five master wrap checks pass. All 1,526 compatible tile joins pass the local 16px boundary-window tests against neighbouring/interior gradients, including new-to-existing road joins. Closed islands and inward corners show all 60 material transitions. The unchanged older pack retains its 332-join, full 14-frame water-cycle validation; its files are hash-checked here.

The shipped map layouts also contain 184 distinct incompatible neighbour pairs. These are recorded with map/cell locations in `reports/native_layout_mismatches.csv`, with original-versus-restored examples. The pack does not repair those map placements. Passing compatible asset joins is not a claim that every shipped map layout is seamless.

## Iteration policy

1. Edit the authoritative master or native coverage/shading extraction; preserve material phase and accepted file hashes.
2. Rebuild with `python3 level_generation/terrain/mm6_remaining/transitions/build.py`.
3. Run `check.py`. Any compatible-join failure blocks acceptance. Never weaken thresholds to hide a bad join.
4. Visually inspect master repeat/offset previews, every family island and dirt-hole fixture, road originals/composites, native contexts, and worst boundary windows. Numerical checks alone do not detect all internal artistic artifacts.
5. Rebuild the isolated fixtures with `prepare_review.py` and capture with the existing gameplay capture tool. Review engine filtering and oblique views; bind capture metadata to the current map, executable and texture hashes.
6. Run `review.py` to verify and package. Preserve source evidence and previous accepted versions. Native layout mismatches remain explicit map work, not texture exceptions.

## Runtime use

The ZIP contains `worlds/mm6/terrain_x2/*.png` and `manifest.json`. Overlay the `worlds` directory into the desired staged `assets_dev` and set `[video_quality] terrain = x2`. Existing filenames replace terrain only. No engine code, sprites, decorations, bmodel textures, or map placements are included. The current peasants-enhanced playtest was preserved; native captures use a separate `/tmp/openyamm-mm6-complete-terrain-review` copy.

`prepare_review.py` currently uses the existing local editor build, peasants playtest and `/tmp/sorpigal-transition-capture-save` helper. Flat map sources and built ODM fixtures are preserved in `fixture/`; those external local prerequisites are needed only to recreate engine captures, not to use the ZIP.
'''
    (P/'README.md').write_text(text)
    page='''<!doctype html><meta charset="utf-8"><title>Complete MM6 terrain x2</title><style>body{background:#202933;color:#eee;font:16px/1.5 system-ui;max-width:1320px;margin:24px auto}img{max-width:100%}a{color:#9cf}details{margin:20px 0}</style><h1>Complete MM6 terrain x2</h1><p>134 runtime files. Five masters, 60 material transitions, six additional roads; 63 accepted files unchanged.</p><p><a href="mm6_complete_terrain_x2.zip">Download runtime ZIP</a> · <a href="README.md">Method and iteration policy</a> · <a href="reports/review.json">Review evidence</a> · <a href="reports/validation.json">1,526 compatible join checks</a></p><p>Original map placement mismatches remain separate: <a href="reports/native_layout_mismatches.csv">184 distinct neighbour pairs</a>. This is a texture pack, not a map-layout repair.</p><h2>Masters</h2><img src="../masters/v3/comparison.png">'''
    for name in ('sand','snow','cracked','tropical','swamp','roads'):
        page+='<h2>'+name+'</h2>'
        if name!='roads':page+='<img src="contexts/'+name+'_flat.png">'
        else:page+='<img src="reports/roads_review.png">'
        if name in captures:page+='<img src="captures/mm6_'+name+'.png">'
        page+='<details><summary>All original / restored / mask / shading comparisons</summary><img src="sheets/'+name+'.png"></details><details><summary>All native 3x3 contexts, original / restored</summary><img src="contexts/'+name+'_native.png"></details>'
    page+='<details><summary>Worst compatible boundary windows</summary><img src="reports/worst_joins.png"></details><details><summary>Original map-layout mismatches, before / after</summary><img src="reports/native_layout_mismatches.png"></details>'
    (P/'index.html').write_text(page)
    with zipfile.ZipFile(P/'mm6_complete_terrain_x2.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted((P/'runtime_x2').rglob('*')):
            if path.is_file():z.write(path,path.relative_to(P/'runtime_x2'))
        z.writestr('README.txt','Complete MM6 terrain x2: 134 PNGs. Overlay worlds/ into staged assets_dev; set video_quality terrain=x2. All original map placements retained. See repository level_generation/terrain/mm6_remaining/transitions/README.md for evidence and limitations.\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
