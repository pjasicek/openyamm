"""Verify owned results and write the coordinator handoff; shared manifests stay read-only."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
from link_static_model_lods import read_glb
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
owned={x['icon']:x for x in json.loads((P/'ownership.json').read_text())}
ledger=json.loads((P/'ledger.json').read_text())
accepted=[icon for icon,row in ledger.items() if row['installed']]
for icon,row in ledger.items():
    source=R/'assets_source'/owned[icon]['model'];runtime=R/'assets_dev'/owned[icon]['model']
    if not row['installed']:
        assert sha(source)==owned[icon]['baseline_source_sha256'],icon
        assert sha(runtime)==owned[icon]['baseline_runtime_sha256'],icon
        row.update(source_sha256=sha(source),runtime_sha256=sha(runtime))
        continue
    canonical='6boots5' if icon in ['6boots6','6boots7'] else icon
    report=json.loads((P/f'review/equipment_{canonical}_export_check.json').read_text())
    low,high=report['bounds_gltf'];scale=owned[icon]['length']/max(high[0]-low[0],high[2]-low[2])
    bounds=[low[0]*scale,-high[2]*scale,low[1]*scale,high[0]*scale,-low[2]*scale,high[1]*scale]
    assert sha(source)==row['source_sha256'] and sha(runtime)==row['runtime_sha256'],icon
    assert sha(P/f'work/codex_tex/geometryfinish_{icon}_export.glb')==row['export_sha256'],icon
    row.update(status='complete',native_outdoor=True,
               recommended_bounds=[round(x,4) for x in bounds],runtime_fit_scale=scale,
               triangle_count=report['triangles'],pbr_maps=3,normal_map=True,canonical_geometry=canonical,
               pbr_scene=f'work/codex_tex/geometryfinish_{canonical}_pbr.blend',
               exact_guides=f'codex_tex/equipment_{canonical}')
for key in ['export_sha256','source_sha256']:
    assert len({ledger[icon][key] for icon in ['6boots5','6boots6','6boots7']})==1,key
shared=[]
for icon in ['6boots5','6boots6','6boots7']:
    document,binary=read_glb(R/'assets_dev'/owned[icon]['model'])
    assert document['asset']['extras']['openyamm_cooked'].pop('source')==owned[icon]['model']
    shared.append((document,binary))
assert shared[0]==shared[1]==shared[2]
for mode,count in [('outdoor',12),('indoor',8),('outdoor_finish',14)]:
    assert len(list((P/f'review/native_{mode}').glob('*.png')))==count
    run=json.loads((P/f'receipts/native_{mode}/run.json').read_text())
    assert run.get('exit_code',0)==0
(P/'ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
handoff={
    'worker':'equipment_geometry_finish','date':'2026-10-18',
    'owned_icons':13,'owned_geometry_sources':11,'completed_icons':len(accepted),
    'completed_geometry_sources':len({ledger[icon]['canonical_geometry'] for icon in accepted}),
    'deferred_icons':13-len(accepted),'meshy_additional_credit_limit':200,'meshy_additional_credits_used':20,
    'shared_boots':{'icons':['6boots5','6boots6','6boots7'],'same_export_and_source_bytes':True,
                    'same_runtime_geometry_and_textures':True,
                    'runtime_container_difference':'Only each cooked source-path receipt differs.'},
    'budget_exceptions':{'6boots1':'3400: real pair interiors and physical brass buckle solids',
                         '7item348':'3388: preserve 3200-triangle cloth body plus 188-triangle physical brooch',
                         '6hat1':'3498: exact union of the cap with a real solid feather adds cut triangles'},
    'validation':{'desktop_cook_verify':f'{len(accepted)} individual scoped installs passed',
                  'pbr_review':'Five explicit-culling PBR views beside each original icon for every accepted shape',
                  'native_outdoor':'12 actual-item captures of the first six entries, 14 of the seven finished later',
                  'native_indoor':'8 shared-model captures covering four unique shapes at binding scale on flat floor',
                  'focused_fixtures':'Pinched fans, explicit culling, mixed PBR/GLB, physical lining, UV domain and per-face classes passed',
                  'android':'Not cooked or tested','builds':False},
    'coordinator_actions':{
        'bounds':'Apply recommended_bounds from completed rows only. Current length / largest glTF horizontal extent; axes [x,-z,y]. Shared items.yml was not edited.',
        'shared_boots':'One underlying model and texture set; unique owned filenames have identical source GLBs. Cooked containers differ only in their source-path receipt.',
        'baker':'Own copy carries UV barycentric >= -1e-8 and reviewed per-face classes. Also resets polygon material indices after assigning one bake material, and preserves individual-view paint layout when preparing guide atlases.',
        'moon':'Final recipe moon_clasp.py; scene geometryfinish_7item348_pbr.blend. Original cloth body geometry/UVs preserved without repainting or resampling. Separate closed constant-gold PBR brooch. Earlier voxel-cloth trials are rejected.',
        'registration':'register_views.py registers generated paint/mask views onto the exact guides (component extraction, bounding-box affine, bounded demons warp; gates IoU >= 0.95 and p95 displacement <= 4% of the object diagonal) instead of requiring imagegen to hit the guide size. Designs may list material_classes (and gems_in_metal) to reclassify crease strokes drawn black in masks.',
        'self_intersections':'resolve_self_intersections.py (7item095) and rebuild_6hat1_feather.py remove decimation/feather crossings by exact self-union, separating touching folds; zero exposed back faces from 60 sampled directions.',
        'moon_normals':'Fixed by moon_normals.py: seam welding, outward winding and re-smoothed normals on the preserved cloth body; UVs/textures unchanged.',
        'read_only_inputs':'216 of 218 originals still match. Two shared helper scripts changed during concurrent coordinator work; preserved and their corrections copied locally.'},
    'items':ledger}
(P/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
print(f"{len(accepted)}/13 entries complete; {handoff['completed_geometry_sources']}/11 unique geometries; Meshy 20/200.")
