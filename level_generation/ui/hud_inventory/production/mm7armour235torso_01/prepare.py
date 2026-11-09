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
    job = 'fitted_equipment_variants-4914aed66c3c'
    cells = ['engine--icons--7item235v1.bmp', 'engine--icons--7item235v1a.bmp']
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
    prompt = ('Faithful x2 restoration of TWO native gold chainmail torso-and-upper-leg armour variants, left to right. '
        'Keep each distinct arm pose, open V neck, dense fine horizontal mail links, dull gray shield-shaped belly plate '
        'with its original faint engraved motif, dark studded shoulder straps, short sleeves with studded cuffs, '
        'dark studded waist/hem band and separate hanging upper-leg mail sections. Preserve exact native shapes and openings. '
        'Mail must remain fine textured flexible metal, not large scales. Preserve muted old gold, dark bronze recesses '
        'and gray plate, not polished yellow gold. No wearer, new emblems, extra gems or invented ornaments. '
        'Reconstruct continuous painted surfaces and fine curves, not enlarged pixel blocks or repeated square highlights. '
        'Pure opaque magenta #FF00FF background and holes, no checkerboard, no spill. '
        f'Canvas {width}x{height}; native x2 rectangles {json.dumps(rects)}. Keep empty gutters.\n\n'
        + qmod.registration.PROMPT)
    p.update(selected_cells=cells, execution_layout=dict(canvas_size=[width,height],cell_rects=rects),
             prompt=prompt,reference_roles={str(path):'Edit target: native x2 torso pose pair; exact placement and materials.'},
             reference_hashes={str(path):qmod.digest(path)},
             tool_args=dict(prompt=prompt,referenced_image_paths=[str(path)]))
    qmod.save(q.payload_root/job/'payload.json',p)
    (q.payload_root/job/'submitted_prompt.txt').write_text(prompt)
    qmod.save(OUT/'payload.json',p)
    (OUT/'prompt.txt').write_text(prompt)
print(json.dumps(p['tool_args']))
