"""Focused culling/material fixtures and the explicitly selected owned production bakes."""
import json,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import codex_texture as texture
if '--self-check' in sys.argv:
    import bmesh
    from repair_geometry import split_pinched_fans
    bm=bmesh.new()
    vertices=[bm.verts.new(v) for v in [(0,0,0),(1,0,0),(0,1,0),(0,0,1),(0,-1,0),(0,0,-1)]]
    for face in [(0,2,1),(0,1,3),(1,2,3),(2,0,3),(0,4,1),(0,1,5),(1,4,5),(4,0,5)]:
        bm.faces.new([vertices[i] for i in face])
    assert any(len(e.link_faces)==4 for e in bm.edges)
    bm=split_pinched_fans(bm)
    assert len(bm.faces)==8 and all(e.is_manifold for e in bm.edges)
    bm.free()
    print('PINCHED_FAN_SELF_CHECK_PASSED: both touching solids retained with all eight faces.')
    runpy.run_path(str(P/'scripts/check_review_culling.py'))
    runpy.run_path(str(P/'scripts/check_mask_bake.py'))
    texture.WORK=str(P/'work/codex_tex');texture.PAINT=str(P/'codex_tex');texture.TEXTURE=512
    texture.DESIGNS=json.loads((P/'designs.json').read_text())
for icon in sys.argv[sys.argv.index('--')+1:]:
    if icon=='--self-check':continue
    assert 'equipment_'+icon in texture.DESIGNS
    texture.bake('equipment_'+icon)
