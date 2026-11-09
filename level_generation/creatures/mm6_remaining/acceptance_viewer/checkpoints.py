"""Versioned placement and scale proposals; never modify sprite packages."""

from datetime import datetime, timezone
import json
import math
import os

from landmarks import CONTRACT as LANDMARK_CONTRACT, validate_landmarks


COLOR_CHANNELS = {'mask_r': 'R', 'mask_g': 'G', 'mask_b': 'B', 'mask_a': 'A'}


def color_regions(manifest):
    return {key: label for key, label in manifest.get('regions', {}).items() if key in COLOR_CHANNELS}


def validate_colors(colors, manifest):
    if not isinstance(colors, dict):
        raise ValueError('colors must be a palette-keyed object')
    for palette, settings in colors.items():
        if palette not in manifest.get('variants', {}) or not isinstance(settings, dict):
            raise ValueError('Unknown color palette or invalid settings')
        if set(settings) != {'region', 'saturation', 'brightness', 'enabled'}:
            raise ValueError('Color settings require region, saturation, brightness and enabled')
        if not isinstance(settings['region'], str) or settings['region'] not in {'all', *color_regions(manifest)}:
            raise ValueError('Unknown color region')
        if type(settings['enabled']) is not bool:
            raise ValueError('Color preview enabled must be boolean')
        for field in ('saturation', 'brightness'):
            value = settings[field]
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 2:
                raise ValueError(f'{field} must be finite and between 0 and 2')
    return colors


class Checkpoints:
    def __init__(self, path):
        self.path = path

    def load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            if data.get('schema_version') != 1 or not isinstance(data.get('families'), dict):
                raise ValueError('Unsupported frame_fixups.json schema')
            data['coordinates']['center_guide_offset_px'] = (
                'reference guide offset right of native opaque center, in atlas pixels before mirroring; review only')
            data['coordinates']['guides'] = (
                'family-wide x/y from canvas top-left at 1x; zoom records shared display magnification; review only')
            data['coordinates']['scale'] = self.scale_contract()
            data['coordinates']['colors'] = self.color_contract()
            data['coordinates']['landmarks'] = LANDMARK_CONTRACT
            return data
        return {
            'schema_version': 1,
            'coordinates': {
                'units': 'atlas pixels at pixels_per_logical_pixel',
                'operation': 'add offset_px to manifest.frames[name].crop_origin_px',
                'axes': '+x right, +y down, before view mirroring and native frame scaling',
                'scope': 'one frame name across all palettes, actions and views',
                'guides': ('family-wide x/y from canvas top-left at 1x; '
                           'zoom records shared display magnification; review only'),
                'guide_offset_px': 'reference guide offset below native opaque top, in atlas pixel units; review only',
                'center_guide_offset_px': (
                    'reference guide offset right of native opaque center, in atlas pixels before mirroring; review only'),
                'status': 'proposals only; no sprite metadata or images have been modified',
                'scale': self.scale_contract(),
                'colors': self.color_contract(),
                'landmarks': LANDMARK_CONTRACT,
            },
            'families': {},
        }

    @staticmethod
    def color_contract():
        return ('colors is keyed by palette; each setting applies to all frames/actions/views. '
                'region is all or a manifest material mask key; enabled toggles preview. '
                'saturation and brightness are 0..2 with 1 neutral. On decoded RGB: '
                'Y=.2126R+.7152G+.0722B; adjusted=clamp((Y+saturation*(RGB-Y))*brightness). '
                'Blend with original RGB by material coverage, preserving sprite alpha. '
                'Saved preview proposal only; no PNG or runtime asset changes.')

    @staticmethod
    def scale_contract():
        return ('Optional scale_factor defaults to 1; scale_anchor defaults to bottom. '
                'For a physical canvas point p: anchor + scale_factor * (p - anchor) + offset_px. '
                'top/bottom use unmodified alpha>=128 bounds center X and top/bottom Y; '
                'pivot uses logical_pivot * tier. Apply before native frame scale and mirroring. '
                'Bounds missing: top/bottom use atlas crop edges. Preview only; no source image resampling.')

    def get(self, family):
        return self.load()['families'].get(family.id, {}).get(
            family.artifact_sha256, {'revision': 0, 'frames': {}})

    def save(self, family, request):
        data = self.load()
        versions = data['families'].setdefault(family.id, {})
        current = versions.get(family.artifact_sha256, {'revision': 0})
        if type(request.get('revision')) is not int or request['revision'] != current['revision']:
            raise RuntimeError('Fixups changed in another tab. Export unsaved edits, then reload before editing.')
        supplied = request.get('frames')
        if not isinstance(supplied, dict):
            raise ValueError('frames must be an object')
        guides = request.get('guides', current.get('guides'))
        if guides is not None and (not isinstance(guides, dict) or set(guides) != {'x', 'y', 'zoom'} or
                any(type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1000000
                    for value in guides.values()) or guides['zoom'] not in (0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 6, 8)):
            raise ValueError('guides must contain finite canvas x/y within ±1000000 and a supported display zoom')
        frames = {}
        colors = validate_colors(request.get('colors', current.get('colors', {})), family.manifest)
        landmarks = validate_landmarks(request.get('landmarks', current.get('landmarks', {})), family.manifest)
        for name, record in supplied.items():
            if name not in family.manifest['frames'] or not isinstance(record, dict):
                raise ValueError(f'Unknown or invalid frame: {name}')
            offset = record.get('offset_px')
            if (not isinstance(offset, list) or len(offset) != 2 or
                    any(type(value) is not int or abs(value) > 16384 for value in offset)):
                raise ValueError('offset_px must contain two integer atlas pixel offsets within ±16384')
            scale = record.get('scale_factor', 1)
            anchor = record.get('scale_anchor', 'bottom')
            if type(scale) not in (int, float) or not math.isfinite(scale) or not 0.5 <= scale <= 1.5:
                raise ValueError('scale_factor must be finite and between 0.5 and 1.5')
            if anchor not in ('top', 'bottom', 'pivot'):
                raise ValueError('scale_anchor must be top, bottom or pivot')
            regenerate = record.get('regenerate')
            guide_offset = record.get('guide_offset_px', 0)
            if type(guide_offset) is not int or abs(guide_offset) > 16384:
                raise ValueError('guide_offset_px must be an integer within ±16384')
            center_offset = record.get('center_guide_offset_px', 0)
            if type(center_offset) is not int or abs(center_offset) > 16384:
                raise ValueError('center_guide_offset_px must be an integer within ±16384')
            note = record.get('note', '')
            if type(regenerate) is not bool or not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Invalid regeneration flag or note (maximum 2000 characters)')
            if (offset == [0, 0] and not regenerate and not note.strip() and guide_offset == 0 and
                    center_offset == 0 and scale == 1 and anchor == 'bottom'):
                continue
            frames[name] = {
                'offset_px': offset, 'regenerate': regenerate, 'note': note.strip(),
                'guide_offset_px': guide_offset,
                'center_guide_offset_px': center_offset,
                'original_crop_origin_px': family.manifest['frames'][name]['crop_origin_px'],
                'scale_factor': scale, 'scale_anchor': anchor,
            }
        result = {
            'revision': current['revision'] + 1,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'label': family.label,
            'manifest_path': str(family.root / 'manifest.json'),
            'manifest_sha256': family.manifest_sha256,
            'artifact_sha256': family.artifact_sha256,
            'pixels_per_logical_pixel': family.manifest['pixels_per_logical_pixel'],
            'frames': frames,
            'guides': guides,
            'colors': colors,
            'landmarks': landmarks,
        }
        versions[family.artifact_sha256] = result
        temporary = self.path.with_suffix('.json.tmp')
        with temporary.open('w') as output:
            json.dump(data, output, indent=2, ensure_ascii=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, self.path)
        return result
