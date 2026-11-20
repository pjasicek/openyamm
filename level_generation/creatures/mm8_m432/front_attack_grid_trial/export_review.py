"""Export the eight-pose trial and an offline native/previous/grid comparison. No family acceptance."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

T = Path(__file__).resolve().parent
sys.path.insert(0, str(T.parent))
import process, materials
from process_trial import contact, grade
from foot_alignment import translate, sha


def run():
    reg = json.loads((T/'registration.json').read_text())
    src = json.loads((T/'source_layout.json').read_text())
    alignment = json.loads((T/'foot_alignment.json').read_text()) if (T/'foot_alignment.json').exists() else None
    config = materials.settings()
    config['enhanced_support'] = {'seed': 'knn>165, G-R>10, G>=B-10, opaque distance>2, component>=12',
                                  'falloff': 'full within4 physical pixels, zero at6',
                                  'source': 'enhanced RGB/alpha only; no native mask transfer'}
    for folder in ['runtime_aligned_2x', 'masks_2x', 'native_2x', 'previous_2x', 'previews', 'atlas']:
        (T/folder).mkdir(exist_ok=True)
    base_page = Image.new('RGBA', (1728, 1728))
    mask_page = Image.new('L', base_page.size)
    frames, variants, labels, comparisons, comp_labels = {}, [], [], [], []
    for i, name in enumerate(src['frames']):
        selected = reg['selected'][name]
        im = Image.open(T/selected['image']).convert('RGBA')
        native = Image.new('RGBA', im.size)
        native.paste(process.queue.native(process.ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
        old = grade(Image.open(T.parent/'registered_2x'/(name+'.png')).convert('RGBA'), native, name)
        native.save(T/'native_2x'/(name+'.png'))
        old.save(T/'previous_2x'/(name+'.png'))
        mask = materials.masks(im, config)
        a = np.asarray(im)
        r, g, b = np.moveaxis(a[:, :, :3].astype(float), -1, 0)
        seed = (mask>165)&(g-r>10)&(g>=b-10)&(ndi.distance_transform_edt(a[:, :, 3]>=250)>2)
        connected, _ = ndi.label(seed)
        sizes = np.bincount(connected.ravel()); sizes[0] = 0
        seed = sizes[connected]>=12
        support = np.clip((6-ndi.distance_transform_edt(~seed))/2, 0, 1) if seed.any() else np.zeros(seed.shape)
        mask = Image.fromarray(np.round(mask*support).astype(np.uint8))
        if alignment:
            placement = alignment['frames'][name]
            assert sha(T/selected['image']) == placement['selected_master_sha256'], 'Re-audit feet after artwork changes'
            im = translate(im, placement['translation_2x_px'])
            mask = translate(mask, placement['translation_2x_px'])
        im.save(T/'runtime_aligned_2x'/(name+'.png'))
        mask.save(T/'masks_2x'/(name+'.png'))
        palette_checks = {}
        for pal in materials.PALETTES:
            v = materials.recolor(im, mask, pal, config)
            assert np.array_equal(np.asarray(im)[:, :, 3], np.asarray(v)[:, :, 3])
            assert pal != 433 or np.array_equal(np.asarray(v), np.asarray(im))
            v.save(T/'previews'/(name+'_'+str(pal)+'.png'))
            palette_checks[str(pal)] = process.spill(v, name)
            variants.append(v); labels.append(name+' '+str(pal))
        overlay = np.array(im); m = np.asarray(mask)/255
        overlay[:, :, :3] = np.round(overlay[:, :, :3]*(1-.65*m[:, :, None])+
                                    np.array([255, 70, 30])*.65*m[:, :, None]).astype(np.uint8)
        variants.append(Image.fromarray(overlay)); labels.append(name+' mask')
        before = Image.open(T/'before_alignment/runtime_aligned_2x'/(name+'.png')) if alignment else old
        comparisons.extend([native, before, im]); comp_labels.extend([name+' native', 'before foot alignment', 'after foot alignment'])
        x, y = i%3*576, i//3*576
        base_page.paste(im, (x, y)); mask_page.paste(mask, (x, y))
        frames[name] = {'atlas_xywh': [x, y, 576, 576], 'canvas_origin_2x': [-32, -32],
                        'logical_size': [256, 256], 'pivot_logical': [128, 256],
                        'mirror': False, 'selected_job': selected['job'],
                        'sampling_generated_per_native': selected['generated_pixels_per_native_pixel'],
                        'variant_edges': palette_checks}
        if alignment:
            frames[name]['art_translation_2x_px'] = alignment['frames'][name]['translation_2x_px']
    base_page.save(T/'atlas/base_2x.png'); mask_page.save(T/'atlas/mask_2x.png')
    for name, f in frames.items():
        x, y, w, h = f['atlas_xywh']
        reconstructed = base_page.crop((x, y, x+w, y+h))
        assert np.array_equal(reconstructed, Image.open(T/'runtime_aligned_2x'/(name+'.png')))
        assert np.array_equal(mask_page.crop((x, y, x+w, y+h)), Image.open(T/'masks_2x'/(name+'.png')))
        assert process.spill(reconstructed, name)['max_score'] == 0
    contact(comparisons[:12], comp_labels[:12], T/'review/comparison_first_four.png', columns=3, size=384)
    contact(comparisons[12:], comp_labels[12:], T/'review/comparison_last_four.png', columns=3, size=384)
    contact(variants[:16], labels[:16], T/'review/variants_first_four.png', columns=4)
    contact(variants[16:], labels[16:], T/'review/variants_last_four.png', columns=4)
    overlaps, overlap_labels = [], []
    for name in ['m432ac0', 'm432ad0', 'm432ae0', 'm432af0']:
        for key in ['front_attack_3x2_start', 'front_attack_3x2_end']:
            overlaps.append(Image.open(T/'toned_2x'/key/(name+'.png')))
            overlap_labels.append(name+' '+key.split('_')[-1])
    contact(overlaps, overlap_labels, T/'review/overlap.png', columns=2, size=384)
    manifest = {'schema': 'openyamm.creature-front-attack-trial.v1', 'state': 'partial_visual_defects',
                'installed': False, 'frames': frames, 'animation': {'steps': src['native_steps'],
                'playback': src['native_playback']}, 'physical_scale': 2,
                'base': 'atlas/base_2x.png', 'mask': 'atlas/mask_2x.png',
                'variants': config, 'decoded_atlas_bytes': base_page.width*base_page.height*5,
                'packing': 'Review atlas with aligned 576 cells. Tight production packing deferred until pose acceptance.',
                'checks': {'unique_frames': len(frames), 'atlas_reconstruction': True, 'mask_reconstruction': True,
                           'alpha_preserved': True, 'base_palette_exact_bypass': True,
                           'base_edge_spill': 0, 'minimum_sampling_passed': True, 'visual_acceptance': False},
                'visual_defects': ['Some generated head angles face the camera instead of following native turn.',
                                   'Generated stance widths/anatomy still differ; whole-frame foot translation preserves these shapes.',
                                   'Blade foreshortening differs between overlap versions; ae0 is too long.'],
                'resume': 'Use compact native sequence sheets and accepted identity; repair demonstrated head/weapon/placement drift as a coherent sequence. Reprocess, inspect overlaps/playback/variants, then freeze acceptance. Do not count this trial as a completed family.'}
    if alignment:
        manifest['foot_alignment'] = alignment
        manifest['checks']['native_foot_baseline_aligned'] = True
        manifest['checks']['stance_center_error_max_2x_px'] = max(abs(v['after']['stance_center_x']-v['native']['stance_center_x']) for v in alignment['frames'].values())
        manifest['resume'] = 'Review deterministic foot alignment in viewer.html; retain foot_alignment.json and before_alignment checkpoint. Remaining head/weapon/anatomy differences require separate review. Re-audit foot landmarks if selected artwork changes.'
    process.save(T/'manifest.json', manifest)
    process.save(T/'material_settings.json', config)
    html = '''<!doctype html><html><head><meta charset="utf-8"><title>Dark Elf front attack grid trial</title>
<style>body{background:#202124;color:#eee;font:16px system-ui;margin:20px}button,select,input{margin:6px;padding:7px}main{display:flex;gap:8px;flex-wrap:wrap}figure{margin:0}canvas{width:432px;height:432px;background:#333}figcaption{text-align:center}p{max-width:1200px}#status{color:#edc988}</style></head><body>
<h1>Dark Elf Warrior — compact front attack trial</h1>
<p id="status">Foot alignment review · 8 native poses, 125 ms each. Same artwork and scale; only whole-frame position changed.</p>
<button id="play">Replay attack</button><label>Review repeat <input id="repeat" type="checkbox"></label>
<label>Speed <select id="speed"><option value="1">Native</option><option value="0.25">Quarter speed</option></select></label>
<label>Palette <select id="palette"><option>433</option><option>434</option><option>435</option></select></label>
<label>Background <select id="background"><option value="#333">Dark</option><option value="#ddd">Light</option></select></label>
<label>Anchor guides <input id="guides" type="checkbox" checked></label>
<input id="scrub" type="range" min="0" max="7" value="0"><span id="caption"></span>
<main><figure><canvas id="native" width="576" height="576"></canvas><figcaption>Native · base palette 433</figcaption></figure>
<figure><canvas id="old" width="576" height="576"></canvas><figcaption>Restored · before alignment</figcaption></figure>
<figure><canvas id="new" width="576" height="576"></canvas><figcaption>Restored · corrected placement</figcaption></figure></main>
<p>Cyan guides show the fixed native anchor and ground line. The display is reduced to 75%; exports are 2×. Original and restored anatomy still differ. No resizing or redrawing was applied for this alignment correction.</p>
<p><a href="review/comparison_first_four.png">First four at larger size</a> · <a href="review/comparison_last_four.png">Last four</a> · <a href="review/overlap.png">Overlapping poses</a> · <a href="review/variants_first_four.png">Variants and masks 1–4</a> · <a href="review/variants_last_four.png">Variants and masks 5–8</a></p>
<script>const M=MANIFEST;const names=Object.keys(M.frames),$=id=>document.getElementById(id),images={};let playing=false,start=0,selected=0;
function frameAt(t){let sum=0;for(let i=0;i<M.animation.steps.length;i++){sum+=M.animation.steps[i].duration_ms;if(t<sum)return i}return names.length-1}
function pathFor(id,n){return id==='native'?'native_2x/'+n+'.png':(id==='old'?'before_alignment/':'')+'previews/'+n+'_'+$('palette').value+'.png'}
function draw(){const n=names[selected];$('scrub').value=selected;$('caption').textContent=n+' · '+(selected+1)+'/8';for(const id of ['native','old','new']){const c=$(id),ctx=c.getContext('2d'),p=pathFor(id,n);ctx.fillStyle=$('background').value;ctx.fillRect(0,0,576,576);if(images[p]?.complete&&images[p].naturalWidth)ctx.drawImage(images[p],0,0);else if(!images[p]){const im=new Image;images[p]=im;im.onload=draw;im.src=p}if($('guides').checked){ctx.strokeStyle='#66d7df';ctx.lineWidth=1;ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(0,544.5);ctx.lineTo(576,544.5);ctx.moveTo(288.5,32);ctx.lineTo(288.5,568);ctx.stroke();ctx.setLineDash([]);ctx.strokeRect(284,540,8,8)}}}
$('play').onclick=()=>{playing=true;start=performance.now();selected=0;draw()};$('scrub').oninput=()=>{playing=false;selected=+$('scrub').value;draw()};$('palette').onchange=draw;$('background').onchange=draw;$('guides').onchange=draw;
function tick(now){if(playing){let t=(now-start)*+$('speed').value;if($('repeat').checked)t%=1000;selected=frameAt(t);if(t>=1000)playing=false;draw()}requestAnimationFrame(tick)}
const q=new URLSearchParams(location.search);if(q.has('frame'))selected=Math.min(7,Math.max(0,+q.get('frame')));draw();requestAnimationFrame(tick);
window.reviewCheck=async()=>{let decoded=0;const paths=new Set;for(const n of names){paths.add('native_2x/'+n+'.png');for(const pal of ['433','434','435'])for(const prefix of ['','before_alignment/'])paths.add(prefix+'previews/'+n+'_'+pal+'.png')}for(const p of paths){const im=new Image;await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=()=>reject(Error(p));im.src=p});if(im.width!==576||im.height!==576)throw Error('size '+p);images[p]=im;decoded++}for(let i=0;i<8;i++)if(frameAt(i*125)!==i||frameAt(i*125+124)!==i)throw Error('timing '+i);if(frameAt(1000)!==7)throw Error('hold');draw();return {decoded,timing_boundaries:16,hold_last:true}};
reviewCheck().then(r=>{document.body.dataset.checks=JSON.stringify(r)}).catch(e=>{document.body.dataset.error=String(e)});
</script></body></html>'''.replace('MANIFEST', json.dumps(manifest))
    (T/'viewer.html').write_text(html)
    print('Exported 8 unique frames, 3 palettes, matching atlas/mask, exact native timing; visual gate remains false.')


if __name__ == '__main__':
    run()
