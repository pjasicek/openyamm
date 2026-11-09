"""Prepare only the fresh compatible full-body pair; preserve frozen jobs and other siblings."""
import fcntl
import importlib.util
import json
import sys
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[1]
sys.path.insert(0, str(HUD))
spec = importlib.util.spec_from_file_location('hud_queue', HUD / 'queue.py')
qmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qmod)
with (HUD / 'checkpoint/state.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    q = qmod.Queue()
    job = 'fitted_equipment_variants-117062a8a557'
    cells = ['engine--icons--item086v2.bmp', 'engine--icons--item086v2a.bmp']
    fresh = {c for row in q.pending_work() for c in row['selected_cells']}
    assert set(cells) <= fresh, 'Only fresh cells may be submitted by this first-pass recipe'
    p = q.payload(job, cell_id=cells[0])
    members = [q.members[c][1] for c in cells]
    sizes = [m['export_region'][2:] for m in members]
    width, height = sum(w for w,h in sizes)+48, max(h for w,h in sizes)+32
    sheet = Image.new('RGBA', (width,height), '#ff00ff')
    x = 16
    rects = {}
    for c,m,(w,h) in zip(cells,members,sizes):
        with Image.open(qmod.ROOT/m['source_path']) as native:
            art = qmod.rendered(native,q.targets[m['target']]['compositing']['profiles'][0])
        sheet.alpha_composite(art.resize((w,h),Image.Resampling.NEAREST),(x,16))
        rects[c] = [x,16,w,h]
        x += w+16
    path = (OUT/'reference.png').resolve()
    sheet.convert('RGB').save(path)
    prompt = ('Restore these TWO native female fitted black leather armour variants faithfully in place. Preserve differing sleeve poses, '
        'small split collar, fitted chest with thin dark red vertical seams and short diagonal studded shoulder strips, '
        'fine dark leather grain, narrow studded waist and short irregular dark red outlined hip tabs. '
        'Keep dark short sleeves with sparse tiny pale studs, crossed smooth black trousers with red-laced outer panels '
        'and small muted gold eyelets, plain black boots with thin red edge lines. No mottled camouflage from the male body. '
        'Keep trim and laces narrow and dark, studs small and muted; no new studs, thick bright borders, buckles or emblems. '
        'Retain all native silhouettes, neck/sleeve gaps and foot placement. Restore continuous painted surfaces without '
        'reproducing enlarged pixel squares or inventing a heavy repeated texture. Pure magenta #FF00FF background and holes. '
        f'Canvas {width}x{height}; native x2 rectangles {json.dumps(rects)}. Keep empty gutters.\n\n'
        + qmod.registration.PROMPT)
    p.update(selected_cells=cells, execution_layout=dict(canvas_size=[width,height],cell_rects=rects),
             prompt=prompt,reference_roles={str(path):'Edit target: native x2 full-body pose pair; exact placement and materials.'},
             reference_hashes={str(path):qmod.digest(path)},
             tool_args=dict(prompt=prompt,referenced_image_paths=[str(path)]))
    qmod.save(q.payload_root/job/'payload.json',p)
    (q.payload_root/job/'submitted_prompt.txt').write_text(prompt)
    qmod.save(OUT/'payload.json',p)
    (OUT/'prompt.txt').write_text(prompt)
print(json.dumps(p['tool_args']))
