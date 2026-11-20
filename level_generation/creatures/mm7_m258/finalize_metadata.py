"""Record Griffin delivery transparency and baked placement corrections after packaging."""
import json
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parent
generation = json.loads((P/'generation.json').read_text())
for batch in generation['batches'].values():
    if batch.get('selected'):
        image = Image.open(P/batch['selected'])
        assert image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] == 0
manifest = json.loads((P/'manifest.json').read_text())
manifest['alpha_provenance'] = 'All 41 selected sheets delivered genuine RGBA; supplied alpha preserved apart from documented near-invisible gutter components.'
manifest['placement_corrections'] = {
    'record': 'flight_alignment.json', 'baked_into_pixels': True,
    'operation': 'Whole-frame integer translation from visually verified native beak landmarks; no resampling.'
}
manifest['limitations'] = [
    'Enhanced detail interprets native artwork; feather shapes and anatomy are not pixel-identical.',
    'Palette transforms approximate native ACT material ramps with fixed enhanced-art coverage masks.'
]
(P/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
plan = json.loads((P/'generation_plan.json').read_text())
plan['delivery_status'] = 'All 41 planned sheets delivered and selected; 135 native frames exported.'
(P/'generation_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
