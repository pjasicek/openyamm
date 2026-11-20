"""Build a compact, native-timed review board from the audited MM6 captures."""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ACCEPTED = HERE.parent / 'ground_anchor_review' / 'accepted'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(queue_path, inventory_path, output_path):
    queue = json.loads(queue_path.read_text())
    inventory = json.loads(inventory_path.read_text())
    by_name = {family['family']: family for family in queue['families']}
    assert len(by_name) == inventory['family_count'] == len(inventory['families'])
    families = []
    for family in inventory['families']:
        name = family['family']
        record = by_name[name]
        package = REPO / record['package']
        index_path = REPO / family['index']
        assert digest(package) == record['manifest_sha256'] == family['manifest_sha256'], name
        assert digest(index_path) == family['index_sha256'], name
        index = json.loads(index_path.read_text())
        assert len(index['captures']) == family['distinct_captures'], name
        assert index['atlas_pages_sha256'] == family['atlas_pages_sha256'], name
        for relative, expected in index['atlas_pages_sha256'].items():
            assert digest(package.parent / relative) == expected, (name, relative)
        viewer = package.parent / 'placement_review.html'
        assert viewer.exists(), viewer
        captures = []
        for capture in index['captures']:
            webp = REPO / capture['webp']
            metadata = REPO / capture['metadata']
            assert digest(webp) == capture['webp_sha256'], webp
            assert digest(metadata) == capture['metadata_sha256'], metadata
            captures.append({
                'action': capture['action'],
                'view': capture['view'],
                'frames': capture['frames'],
                'duration_ms': capture['native_duration_ms'],
                'webp': os.path.relpath(webp, output_path.parent),
            })
        families.append({
            'name': name,
            'status': record['status'],
            'has_active_repair': bool(record.get('active_repair')),
            'manifest_sha256': record['manifest_sha256'],
            'index_sha256': family['index_sha256'],
            'viewer': os.path.relpath(viewer, output_path.parent),
            'captures': captures,
        })
    assert sum(len(family['captures']) for family in families) == inventory['distinct_capture_count']
    data = json.dumps(families, separators=(',', ':')).replace('</', '<\\/')
    title = html.escape('MM6 native-timed animation review')
    page = f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: dark; font: 15px system-ui, sans-serif; background: #1d2221; color: #eef1ec; }}
  body {{ margin: 0 auto; max-width: 1800px; padding: 16px; }}
  header {{ position: sticky; top: 0; z-index: 2; background: #1d2221; padding: 8px 0 12px; }}
  h1 {{ font-size: 1.3rem; margin: 0 0 8px; }}
  p {{ margin: 5px 0; }}
  .controls {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px; }}
  button, select, input {{ font: inherit; color: inherit; background: #303936; border: 1px solid #77817c;
    border-radius: 5px; padding: 5px 8px; }}
  button {{ cursor: pointer; }}
  a {{ color: #a9d9fd; }}
  #cards {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
  article {{ border: 1px solid #56615c; border-radius: 6px; padding: 6px; background: #272f2c; }}
  article img {{ width: 100%; display: block; background: #333b37; }}
  article div {{ display: flex; justify-content: space-between; gap: 10px; margin: 4px 2px 0; }}
  article small {{ color: #cad2cb; }}
  .count {{ color: #cad2cb; }}
  @media (max-width: 1100px) {{ #cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
  @media (max-width: 700px) {{ #cards {{ grid-template-columns: 1fr; }} }}
</style>
<header><h1>{title}</h1>
<p>Native and restored sprites play side by side from the current atlas captures at original frame timing.
Use the detailed viewer for overlays, frame stepping, transitions and speed control. Visual acceptance is still pending.</p>
<div class="controls"><button id="previous" type="button">← Family</button>
<select id="family" aria-label="Family"></select><button id="next" type="button">Family →</button>
<select id="action" aria-label="Action"><option value="">All actions</option></select>
<a id="viewer" target="_blank" rel="noopener">Detailed viewer ↗</a></div>
<p id="summary" class="count"></p></header><main id="cards"></main>
<script>
const families = {data};
const familySelect = document.getElementById('family');
const actionSelect = document.getElementById('action');
const cards = document.getElementById('cards');
const summary = document.getElementById('summary');
const viewer = document.getElementById('viewer');
for (const [index, family] of families.entries()) {{
  const option = new Option(family.name + (family.has_active_repair ? ' · follow-up' : ''), index);
  familySelect.add(option);
}}
function showFamily() {{
  const family = families[Number(familySelect.value)];
  const previousAction = actionSelect.value;
  actionSelect.length = 1;
  for (const action of [...new Set(family.captures.map(capture => capture.action))]) {{
    actionSelect.add(new Option(action, action));
  }}
  actionSelect.value = [...actionSelect.options].some(option => option.value === previousAction) ? previousAction : '';
  viewer.href = family.viewer;
  render();
  history.replaceState(null, '', '#'+encodeURIComponent(family.name));
}}
function render() {{
  const family = families[Number(familySelect.value)];
  const captures = family.captures.filter(capture => !actionSelect.value || capture.action === actionSelect.value);
  cards.replaceChildren();
  for (const capture of captures) {{
    const card = document.createElement('article');
    const image = document.createElement('img');
    image.src = capture.webp;
    image.alt = family.name+' '+capture.action+' direction '+capture.view+', native and restored';
    image.loading = 'lazy';
    const label = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = capture.action+' / direction '+capture.view;
    const timing = document.createElement('small');
    timing.textContent = capture.frames.length+' frames · '+capture.duration_ms.reduce((sum, ms) => sum+ms, 0)+' ms';
    label.append(name, timing);
    card.append(image, label);
    cards.append(card);
  }}
  summary.textContent = family.name+' · '+family.status.replaceAll('_', ' ')+' · '+captures.length+' of '+family.captures.length+
    ' distinct captures · manifest '+family.manifest_sha256.slice(0, 12)+' · index '+family.index_sha256.slice(0, 12);
}}
familySelect.addEventListener('change', showFamily);
actionSelect.addEventListener('change', render);
document.getElementById('previous').addEventListener('click', () => {{
  familySelect.value = (Number(familySelect.value)+families.length-1)%families.length;
  showFamily();
}});
document.getElementById('next').addEventListener('click', () => {{
  familySelect.value = (Number(familySelect.value)+1)%families.length;
  showFamily();
}});
const initial = families.findIndex(family => family.name === decodeURIComponent(location.hash.slice(1)));
familySelect.value = initial < 0 ? 0 : initial;
showFamily();
</script></html>
'''
    output_path.write_text(page)
    print(json.dumps({'families': len(families), 'captures': inventory['distinct_capture_count'],
                      'output': str(output_path)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--queue', type=Path, default=ACCEPTED / 'placement_queue.json')
    parser.add_argument('--inventory', type=Path, default=ACCEPTED / 'animation_capture_inventory.json')
    parser.add_argument('--output', type=Path, default=ACCEPTED / 'animation_review.html')
    arguments = parser.parse_args()
    build(arguments.queue, arguments.inventory, arguments.output)
