"""Process Dragonfly's retained keyed sheets and newer native-alpha deliveries."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('dragonfly_shared_process', HERE.parent / 'mm7_m514/process.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
keyed_extract = pipeline.extract


def extract(image, *args):
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        rgba = np.array(image)
        alpha = rgba[:, :, 3]
        labels, count = ndimage.label(alpha > 0)
        maxima = ndimage.maximum(alpha, labels, np.arange(count + 1))
        # These deliveries contain detached 1/255-opacity specks in empty gutters.
        # Keep every component with stronger coverage and its complete soft edge.
        rgba[(alpha > 0) & (maxima[labels] <= 1)] = 0
        return Image.fromarray(rgba)
    return keyed_extract(image, *args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-only', action='store_true')
    args = parser.parse_args()
    pipeline.extract = extract
    pipeline.run(HERE, tone=.80, selected_only=args.selected_only)
    path = HERE / 'processing_settings.json'
    settings = json.loads(path.read_text())
    settings['native_alpha_delivery'] = {
        'extraction': 'Preserve supplied RGBA alpha; opaque RGB sheets retain chroma extraction.',
        'detached_gutter_specks': 'Remove only disconnected alpha components whose maximum is 1/255. Preserve complete alpha of every stronger component, including translucent wings and connected 1/255 edges.',
        'shared_processing': 'Native registration, tone 0.80, contour audit and premultiplied resizing.'
    }
    path.write_text(json.dumps(settings, indent=2) + '\n')
