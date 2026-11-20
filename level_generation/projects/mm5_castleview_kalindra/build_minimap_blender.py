"""Blender MCP: bake cropped and full-terrain overviews from the completed native ODM.

The runtime crop uses the existing world map-presentation catalogue. This command
only produces review artifacts; stage the inspected crop alongside its provenance.
"""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
output = Path(globals().get('MINIMAP_OUTPUT', PROJECT/'review/native_minimap_v1'))
script = PROJECT/'render_terrain_materials.py'
exec(compile(script.read_text(), str(script), 'exec'), {
    '__file__': str(script), '__name__': '__main__', 'REVIEW_NATIVE': True,
    'REVIEW_OUTPUT': output, 'REVIEW_SCENE': 'MM5 native overview',
    'REVIEW_RESOLUTION': (1024, 1024), 'REVIEW_MAP_LIGHTING': True,
    'REVIEW_VIEWS': [
        ('travel_crop', (0, 0, 80000), (0, 0, 0), 49152),
        ('full_terrain', (-256, 256, 80000), (-256, 256, 0), 65024),
        ('town', (-2600, -200, 80000), (-2600, -200, 0), 15000),
    ],
})
catalog = {
    'format_version': 1, 'kind': 'world_map_presentation_catalog',
    'maps': [{
        'map': 'mm5_sw',
        'world_bounds': {'min_x': -24576, 'max_x': 24576, 'min_y': -24576, 'max_y': 24576},
        'flip_u': False, 'flip_v': True, 'reveal_entire_map': False,
        'variants': [{'texture': 'ui/maps/mm5_sw.png', 'width': 1024, 'height': 1024}],
    }],
}
(output/'catalog.yml').write_text(json.dumps(catalog, indent=2)+'\n')
print('Native overview and candidate map-presentation catalogue written for visual review:', output)
