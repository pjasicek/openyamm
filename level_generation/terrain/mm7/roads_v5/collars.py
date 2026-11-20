"""Continue finished border artwork through road joins using paired donor half-strips."""
import numpy as np
from scipy.ndimage import distance_transform_edt,gaussian_filter


def graft(images, fields, dirt):
    result = {}
    length = 64
    # Donor strips are taken around the middle of the completed straight tile.
    # Opposing halves meet at adjacent donor pixels, retaining actual 2D detail.
    donors = {'h': images['7drsrns'], 'v': images['7drsrew']}
    for name, image in images.items():
        out = image.copy()
        for side, kind in fields[name]['topology'].items():
            if kind == '000':
                continue
            donor = donors['h' if side in 'NS' else 'v']
            source_mask = fields['7drsrns' if side in 'NS' else '7drsrew']['alpha']
            profile = source_mask[256] if side in 'NS' else source_mask[:,256]
            solid = profile > .5
            distance = distance_transform_edt(solid) + distance_transform_edt(~solid) - 1
            across = np.clip((64-distance)/20,0,1)
            across = across*across*(3-2*across)
            for depth in range(length):
                along = np.clip((length-depth)/32,0,1)
                along = along*along*(3-2*along)
                index = 256+depth if side in 'NW' else 255-depth
                if side in 'NS':
                    sample = donor[index].copy()
                    sample_dirt = dirt[index]
                    dest = depth if side == 'N' else 511-depth
                    base_dirt = dirt[dest]
                    current = out[dest]
                else:
                    sample = donor[:,index].copy()
                    sample_dirt = dirt[:,index]
                    dest = depth if side == 'W' else 511-depth
                    base_dirt = dirt[:,dest]
                    current = out[:,dest]
                # Transplant stones/contact detail, preserving destination dirt phase.
                chroma = (sample[:,0]-sample[:,2])/np.maximum(sample.mean(1),1)
                earth = chroma > .42
                shade = np.clip(gaussian_filter(sample.mean(1)/np.maximum(sample_dirt.mean(1),1),1),.5,1)
                sample[earth] = (base_dirt*shade[:,None])[earth]
                weight = (across*along)[:,None]
                current[:] = current*(1-weight) + sample*weight
        result[name] = out
    return result
