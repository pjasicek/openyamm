"""The isle's prop table: source model -> prop id (work/raw/<prop>), and the ABC placement binding origins."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]

# Source model file (lower case, forward slashes, as in the DAT Filename property) -> prop id.
MODELS = {
    'models/gibs/skeleton/bip01 head.abc': 'skull',
    'models/props/vikingship-wreck.abc': 'shipwreck',
    'models/props/vikingship.abc': 'vikingship',
    'models/props/book.abc': 'book',
    'models/props/podium03.abc': 'podium',
    'models/props/statstone.abc': 'statstone',
    'models/props/debris/stonedebris02.abc': 'stonedebris02',
    'models/props/debris/stonedebris03.abc': 'stonedebris03',
    'models/props/logsburning.abc': 'logsburning',
    'models/props/bed_cot.abc': 'cot',
    'models/props/stool03.abc': 'stool',
    'models/props/coatrack1.abc': 'coatrack',
    'models/props/dresser.abc': 'dresser',
    'models/props/tableround4.abc': 'roundtable',
    'models/props/well.abc': 'well',
    'models/props/cookpot.abc': 'cookpot',
    'models/props/plantsandtrees/tree05.abc': 'ref_tree05',
    'models/props/plantsandtrees/tree06.abc': 'ref_tree06',
}
ABC = {prop: model for model, prop in MODELS.items()}


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def model_key(filename):
    return filename.replace('\\', '/').lower()


def placements():
    """(object index, prop id) of every object whose model is in the table."""
    out = []
    for o in objects():
        filename = o['props'].get('Filename')
        if filename and model_key(filename) in MODELS:
            out.append((o['index'], MODELS[model_key(filename)]))
    return out


_origins = None


def binding_origin(prop):
    """The ABC's placement binding origin (LithTech units): the transcoder adds it to every model vertex."""
    global _origins
    if _origins is None:
        path = HERE / 'work/binding_origins.json'
        _origins = json.loads(path.read_text())
    return _origins[prop]
