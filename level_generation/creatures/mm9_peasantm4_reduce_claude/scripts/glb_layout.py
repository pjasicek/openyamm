"""Print node / primitive / material / variant / clip layout of GLBs (argv)."""
import json, struct, sys
for f in sys.argv[1:]:
    b = open(f, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; d = json.loads(b[20:20 + n])
    print('==', f)
    for nd in d['nodes']:
        if 'mesh' in nd:
            m = d['meshes'][nd['mesh']]
            print(' ', nd['name'], [(d['materials'][p['material']]['name'], d['accessors'][p['indices']]['count'] // 3,
                   [d['materials'][x['material']]['name'] for x in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])]) for p in m['primitives']])
    print('  variants', d.get('extensions', {}).get('KHR_materials_variants'))
    print('  anims', [a['name'] for a in d['animations']])
    print('  scene extras', d['scenes'][0].get('extras'), 'images', len(d.get('images', [])))
