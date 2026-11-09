"""Prepare only the fresh compatible torso pair; preserve frozen jobs and other siblings."""
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
    job = 'fitted_equipment_variants-943629ec1073'
    cells = ['engine--icons--7item076v1.bmp', 'engine--icons--7item076v1a.bmp']
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
    prompt = ('Faithful restoration of the TWO matching Might and Magic equipped torso variants in the reference, '
        'in their existing left-to-right order. Preserve fitted dark silver plate torso and hanging thigh guards, '
        'native sleeve-pose differences, fine mail shoulders/groin and dark brown reflected regions. Keep the exact '
        'soft irregular native plate reflections and plain unornamented construction. Restore continuous painted '
        'surfaces without adding rivets, border piping, engravings, extra seams or sculpted anatomy. Preserve '
        'all panel contours, attachment points, margins and material boundaries. Retain subdued native values; '
        'no high-gloss chrome redesign, enlarged pixel blocks or coarse mail rings. No wearer or extra objects. '
        'Uniform pure opaque magenta #FF00FF background and holes, no checkerboard or magenta spill. '
        f'Canvas {width}x{height}; native x2 rectangles {json.dumps(rects)}. Preserve empty gutters.\n\n'
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
