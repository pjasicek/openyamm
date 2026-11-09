"""Update only embedded texture maps; preserve every geometry/skin/animation accessor byte."""
import io, json, sys, runpy
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as rv
report = {}
for name in ['mm6_cdr1_selected.glb', 'mm6_cdr1_runtime_lod0.glb', 'mm6_cdr1_lods.glb', 'mm6_cdr1_shadow.glb']:
    doc, binary = rv.read_glb(P / 'work/before_scales_v4/export' / name)
    original = bytes(binary)
    accessor_bytes = [original[doc['bufferViews'][a['bufferView']].get('byteOffset', 0):][:doc['bufferViews'][a['bufferView']]['byteLength']] for a in doc['accessors']]
    for label in ['body', 'head']:
        material = next(m for m in doc['materials'] if m['name'] == 'Dragon' + label.title() + '_A')
        for key, suffix in [('baseColorTexture', 'basecolor_2k'), ('normalTexture', 'normal_2k')]:
            texture = material[key] if key == 'normalTexture' else material['pbrMetallicRoughness'][key]
            idx = doc['textures'][texture['index']]['source']
            view = doc['bufferViews'][doc['images'][idx]['bufferView']]
            old = Image.open(io.BytesIO(original[view.get('byteOffset', 0):][:view['byteLength']]))
            image = Image.open(P / 'textures' / f'cdr1_{label}_{suffix}.png').convert('RGB').resize(old.size, Image.Resampling.LANCZOS)
            stream = io.BytesIO(); image.save(stream, 'PNG'); data = stream.getvalue()
            binary += b'\0' * (-len(binary) % 4)
            doc['images'][idx] = {'bufferView': len(doc['bufferViews']), 'mimeType': 'image/png'}
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary += data
    doc, binary = rv._compact(doc, binary)
    after = [bytes(binary)[doc['bufferViews'][a['bufferView']].get('byteOffset', 0):][:doc['bufferViews'][a['bufferView']]['byteLength']] for a in doc['accessors']]
    assert accessor_bytes == after, name
    rv.write_glb(P / 'export' / name, doc, binary)
    report[name] = {'all_accessors_byte_identical': True, 'accessors': len(after)}
import burn_maps
burn_maps.add_burn_maps(P/'export/mm6_cdr1_shadow.glb',P/'export/mm6_cdr1_shadow.glb',{f'Dragon{label.title()}_A':P/f'textures/cdr1_{label}_burn.png' for label in ['body','head','wings']})
rv.apply_variants(P/'export/mm6_cdr1_shadow.glb', P/'export/mm6_cdr1.glb', P/'textures/cdr1_ramps.json', [(prefix,key,value) for prefix in ['DragonBody','DragonHead','DragonWings'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
runpy.run_path(str(P/'scripts/viewer_tiers.py'), run_name='__main__')
(P/'review/scales_v4/export.json').write_text(json.dumps(report, indent=2)+'\n')
