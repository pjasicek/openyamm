"""Serve completed MM6 masters and store human decisions and frame placement checkpoints."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

from PIL import Image

from checkpoints import Checkpoints, COLOR_CHANNELS, color_regions
from landmarks import CONTRACT as LANDMARK_CONTRACT, registration_seeds, source_signature


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PROGRESS = REPO / 'level_generation/creatures/mm6_remaining/redo_2x/progress.json'
LEGACY_AUDIT = REPO / 'level_generation/creatures/mm6_remaining/quality_review/audit.json'
DECISIONS = HERE / 'decisions.json'
VIEWER_REVISION = 4

sys.path.insert(0, str(HERE.parent / 'quality_review'))
from classify_scale import saved_measurements


@dataclass
class Family:
    id: str
    label: str
    source: str
    pipeline_status: str
    minimum_sampling: float
    root: Path
    manifest: dict
    manifest_sha256: str
    artifact_sha256: str
    native_bounds: dict
    restored_bounds: dict
    scale_hints: dict

    def summary(self):
        return {
            'id': self.id,
            'label': self.label,
            'source': self.source,
            'pipeline_status': self.pipeline_status,
            'minimum_sampling': self.minimum_sampling,
            'frame_count': len(self.manifest['frames']),
            'manifest_sha256': self.manifest_sha256,
            'artifact_sha256': self.artifact_sha256,
        }


def artifact_digest(root, raw_manifest, manifest):
    paths = {Path('aligned_2x') / f'{frame}.png' for frame in manifest['frames']}
    paths.update(Path('native_variants') / f'{frame}_{palette}.png'
                 for frame in manifest['frames'] for palette in manifest['variants'])
    for page in manifest['pages']:
        paths.add(Path(page['base']))
        paths.add(Path(page['mask']))
        paths.update(Path(image) for image in page['variant_previews'].values())
    digest = hashlib.sha256(raw_manifest)
    for relative in sorted(paths):
        path = root / relative
        if not path.is_file():
            raise ValueError(f'Missing review artifact: {path}')
        digest.update(relative.as_posix().encode())
        with path.open('rb') as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest()


def load_family(label, path, source, status, sampling=None):
    raw = path.read_bytes()
    manifest = json.loads(raw)
    root = path.parent
    minimum = sampling if sampling is not None else manifest['generated_detail']['measured_minimum']
    frame_names = set(manifest['frames'])
    masters = {file.stem for file in (root / 'aligned_2x').glob('*.png')}
    if frame_names != masters:
        raise ValueError(f'{label}: master set differs from manifest frames')
    for frame in frame_names:
        for palette in manifest['variants']:
            if not (root / 'native_variants' / f'{frame}_{palette}.png').is_file():
                raise ValueError(f'{label}: missing native frame {frame}/{palette}')
    for page in manifest['pages']:
        for image in page['variant_previews'].values():
            if not (root / image).is_file():
                raise ValueError(f'{label}: missing atlas preview {image}')
    for actions in manifest['animations_by_palette'].values():
        for action in actions.values():
            for steps in action['views'].values():
                for step in steps:
                    if step['frame'] not in frame_names:
                        raise ValueError(f"{label}: unknown animation frame {step['frame']}")
    base_palette = next(palette for palette, variant in manifest['variants'].items()
                        if variant.get('exact_base_bypass'))
    native_bounds = {}
    for frame in frame_names:
        with Image.open(root / 'native_variants' / f'{frame}_{base_palette}.png') as image:
            native_bounds[frame] = image.getchannel('A').getbbox()
    restored_bounds = {}
    for page_index, page in enumerate(manifest['pages']):
        with Image.open(root / page['variant_previews'][base_palette]) as image:
            alpha = image.getchannel('A').point(lambda value: 255 if value >= 128 else 0)
            for name, frame in manifest['frames'].items():
                if frame['page'] != page_index:
                    continue
                x, y, width, height = frame['atlas_xywh']
                restored_bounds[name] = alpha.crop((x, y, x + width, y + height)).getbbox()
    family_id = manifest['creature'].replace(':', '_')
    registration_path = root / 'registration.json'
    registration = json.loads(registration_path.read_text()) if registration_path.exists() else {}
    scale_hints = {}
    for name in manifest['frames']:
        measurements = saved_measurements(registration.get(name, {}), None, None,
                                          manifest['pixels_per_logical_pixel'])
        # Longest vertical span first; never average it with silhouette width.
        scale_hints[name] = sorted(measurements, key=lambda value: (value['axis'] != 'y', -value['native_length']))
    return Family(family_id, label, source, status, minimum, root, manifest,
                  hashlib.sha256(raw).hexdigest(), artifact_digest(root, raw, manifest),
                  native_bounds, restored_bounds, scale_hints)


def build_queue():
    progress = json.loads(PROGRESS.read_text())
    audit = json.loads(LEGACY_AUDIT.read_text())
    selections = json.loads((HERE / 'selected_packages.json').read_text())
    families = []
    excluded = []
    queued = []
    progress_names = {record['family'] for record in progress['families']}
    for record in progress['families']:
        path = REPO / record['project'] / 'redo_2x/manifest.json'
        if not path.is_file():
            excluded.append({'label': record['family'], 'reason': 'no completed redo master set'})
            continue
        queued.append((record['family'], path, 'redo master', record['status'], None))
    for record in audit['families']:
        if record['family'] in progress_names:
            continue
        queued.append((record['family'], REPO / record['package'], 'earlier master',
                       'sampling sufficient; motion review pending', record['minimum_sampling']))
    unknown = set(selections) - {row[0] for row in queued}
    if unknown:
        raise ValueError(f'Selected packages name unknown queue families: {sorted(unknown)}')
    for label, path, source, status, sampling in queued:
        if label in selections:
            selection = selections[label]
            original_id = json.loads(path.read_text())['creature']
            path = REPO / selection['manifest']
            metadata = json.loads(path.read_text())
            if metadata['creature'] != original_id:
                raise ValueError(f'{label}: selected package has a different creature ID')
            label = metadata.get('review_label', label)
            source = 'selected staging master'
            status = metadata['quality_status']
            sampling = None
        family = load_family(label, path, source, status, sampling)
        families.append(family)
    if len({family.id for family in families}) != len(families):
        raise ValueError('Duplicate family IDs in review queue')
    return families, excluded


def load_collection(path):
    """Load exactly the pinned packages; never consult the historical discovery queue."""
    path = path.resolve()
    collection = json.loads(path.read_text())
    records = collection.get('families')
    if collection.get('schema_version') != 1 or not isinstance(records, list) or not records:
        raise ValueError('Unsupported or empty review collection')
    creatures = [record['creature'] for record in records]
    if len(set(creatures)) != len(creatures):
        raise ValueError('Duplicate creature IDs in review collection')
    families = []
    for record in records:
        manifest_path = (path.parent / record['manifest']).resolve()
        raw = manifest_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record['manifest_sha256']:
            raise ValueError(f"{record['label']}: selected manifest changed; review collection needs updating")
        metadata = json.loads(raw)
        if metadata['creature'] != record['creature']:
            raise ValueError(f"{record['label']}: selected package has a different creature ID")
        if (metadata['pixels_per_logical_pixel'] != collection['pixels_per_logical_pixel'] or
                len(metadata['frames']) != record['frame_count']):
            raise ValueError(f"{record['label']}: selected package has different resolution or coverage")
        family = load_family(record['label'], manifest_path, record['source'], record['pipeline_status'])
        if family.artifact_sha256 != record['artifact_sha256']:
            raise ValueError(f"{record['label']}: selected review pixels changed; review collection needs updating")
        families.append(family)
    if collection['family_count'] != len(families):
        raise ValueError('Review collection family count differs from selected packages')
    if collection['frame_count'] != sum(len(family.manifest['frames']) for family in families):
        raise ValueError('Review collection frame count differs from selected packages')
    return families, collection


def load_decisions(path=DECISIONS):
    if not path.exists():
        return {'schema_version': 1, 'decisions': {}}
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('decisions'), dict):
        raise ValueError('Unsupported decisions.json schema')
    return data


def save_decisions(data, path=DECISIONS):
    temporary = path.with_suffix('.json.tmp')
    with temporary.open('w') as output:
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


class ReviewServer(ThreadingHTTPServer):
    def __init__(self, address, families, excluded, state_dir=HERE, collection=None, landmarks_dir=None):
        super().__init__(address, ReviewHandler)
        self.families = families
        self.by_id = {family.id: family for family in families}
        self.excluded = excluded
        self.collection = collection
        state_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_path = state_dir / 'decisions.json'
        self.checkpoints = Checkpoints(state_dir / 'frame_fixups.json')
        self.landmarks_dir = landmarks_dir
        from threading import Lock
        self.decision_lock = Lock()

    def landmark_suggestions(self, family):
        if self.landmarks_dir:
            path = self.landmarks_dir / f'{family.id}.json'
            if path.is_file():
                result = json.loads(path.read_text())
                seeds_path = self.landmarks_dir / 'seeds.json'
                seeds = json.loads(seeds_path.read_text()) if seeds_path.exists() else {}
                if (result.get('artifact_sha256') == family.artifact_sha256 and
                        result.get('manifest_sha256') == family.manifest_sha256 and
                        result.get('source_signature') == source_signature(
                            family.root, seeds.get(family.manifest['creature'], {}))):
                    return result
                # A stale suggestion must never attach itself to different pixels.
                return {'frames': {}, 'coordinate_contract': LANDMARK_CONTRACT,
                        'warning': 'Landmark suggestions changed or refer to different art; rebuild them.'}
        return {'frames': registration_seeds(family.root, family.manifest),
                'coordinate_contract': LANDMARK_CONTRACT}

    def landmark_export(self, family):
        suggestions = self.landmark_suggestions(family)
        manual = self.checkpoints.get(family).get('landmarks', {})
        registration_path = family.root / 'registration.json'
        registration = json.loads(registration_path.read_text()) if registration_path.exists() else {}
        frames = {}
        tier = family.manifest['pixels_per_logical_pixel']
        for name, frame in family.manifest['frames'].items():
            sides = {}
            for side in ('original', 'restored'):
                values = {**suggestions.get('frames', {}).get(name, {}).get(side, {}),
                          **manual.get(name, {}).get(side, {})}
                points = {}
                for kind, value in values.items():
                    confirmed = kind in manual.get(name, {}).get(side, {})
                    point = value if confirmed else value['xy']
                    info = {'logical_xy': point, 'status': 'recorded' if confirmed else 'suggested'}
                    if not confirmed:
                        info.update(confidence=value['confidence'], source=value['source'])
                    if point is not None:
                        if side == 'original':
                            offset = frame['native_offset']
                            info['source_bitmap_xy'] = [p-offset[i] if p is not None else None
                                                        for i, p in enumerate(point)]
                        else:
                            info['atlas_local_xy'] = [p*tier-frame['crop_origin_px'][i] if p is not None else None
                                                      for i, p in enumerate(point)]
                            record = registration.get(name, {})
                            if all(k in record for k in ('raw_rect', 'scale', 'translate', 'raw_path')) and not (
                                    record.get('geometry_correction') or record.get('warp')):
                                correction = frame.get('anchor_correction_px', [0, 0])
                                info['generated_sheet'] = record['raw_path']
                                info['generated_sheet_xy'] = [
                                    record['raw_rect'][i] + (p*tier-record['translate'][i]-correction[i])/record['scale']
                                    if p is not None else None for i, p in enumerate(point)]
                    points[kind] = info
                if points:
                    sides[side] = points
            if sides:
                frames[name] = {'source_bitmap': frame['source'], 'points': sides}
        return {**family.summary(), 'coordinate_contract': LANDMARK_CONTRACT, 'frames': frames}


class ReviewHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if len(args) > 1 and str(args[1]).startswith(('4', '5')):
            super().log_message(format, *args)

    def send_bytes(self, data, content_type, disposition=None):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if disposition:
            self.send_header('Content-Disposition', disposition)
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data):
        self.send_bytes(json.dumps(data, ensure_ascii=False).encode(), 'application/json; charset=utf-8')

    def send_error_json(self, status, message):
        data = json.dumps({'error': message}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ('/', '/index.html', '/app.js', '/landmarks.js', '/style.css'):
            asset = HERE / ('index.html' if path == '/' else path[1:])
            content_type = mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
            self.send_bytes(asset.read_bytes(), content_type + '; charset=utf-8')
            return
        if path == '/api/families':
            decisions = load_decisions(self.server.decisions_path)['decisions']
            fixups = self.server.checkpoints.load()['families']
            self.send_json({
                'viewer_revision': VIEWER_REVISION,
                'collection': ({'id': self.server.collection['collection_id'],
                                'title': self.server.collection['title']}
                               if self.server.collection else None),
                'families': [{**family.summary(), 'fixups_revision': fixups.get(family.id, {}).get(
                    family.artifact_sha256, {}).get('revision', 0), 'decision': decisions.get(family.id, {}).get(
                    family.artifact_sha256)} for family in self.server.families],
                'excluded': self.server.excluded,
            })
            return
        if path == '/api/export':
            decisions = load_decisions(self.server.decisions_path)['decisions']
            fixups = self.server.checkpoints.load()['families']
            export = {'schema_version': 1, 'families': [{**family.summary(), 'decision':
                decisions.get(family.id, {}).get(family.artifact_sha256), 'fixups_revision':
                fixups.get(family.id, {}).get(family.artifact_sha256, {}).get('revision', 0)}
                for family in self.server.families]}
            self.send_bytes(json.dumps(export, indent=2, ensure_ascii=False).encode(), 'application/json',
                            'attachment; filename="mm6-master-decisions.json"')
            return
        if path == '/api/fixups/export':
            self.send_bytes(json.dumps(self.server.checkpoints.load(), indent=2).encode(), 'application/json',
                            'attachment; filename="mm6-frame-fixups.json"')
            return
        if path == '/api/landmarks/export':
            export = {'schema_version': 1, 'families': [self.server.landmark_export(family)
                                                       for family in self.server.families]}
            self.send_bytes(json.dumps(export, indent=2).encode(), 'application/json',
                            'attachment; filename="creature-landmarks.json"')
            return
        if path.startswith('/api/family/'):
            family = self.server.by_id.get(path.removeprefix('/api/family/'))
            if family is None:
                self.send_error_json(404, 'Unknown family')
            else:
                self.send_json({**family.manifest, 'review_native_bounds': family.native_bounds,
                                'review_restored_bounds': family.restored_bounds,
                                'review_scale_hints': family.scale_hints,
                                'review_color_regions': color_regions(family.manifest),
                                'review_landmark_suggestions': self.server.landmark_suggestions(family),
                                'review_fixups': self.server.checkpoints.get(family)})
            return
        if path.startswith('/mask/'):
            parts = path.removeprefix('/mask/').split('/')
            family = self.server.by_id.get(parts[0])
            if (len(parts) != 3 or family is None or not parts[1].isdigit() or
                    parts[2] not in color_regions(family.manifest) or
                    int(parts[1]) >= len(family.manifest['pages'])):
                self.send_error_json(404, 'Unknown material mask')
                return
            page = family.manifest['pages'][int(parts[1])]
            mask_path = (family.root / page['mask']).resolve()
            if not mask_path.is_relative_to(family.root.resolve()):
                self.send_error_json(404, 'Unknown material mask')
                return
            with Image.open(mask_path) as mask:
                channel = COLOR_CHANNELS[parts[2]]
                if channel not in mask.getbands():
                    self.send_error_json(404, 'Missing material mask channel')
                    return
                # RGBA mask alpha is coverage data, not transparency. Send one opaque channel
                # so browser canvas decoding cannot destroy R/G/B where mask A is zero.
                output = io.BytesIO()
                mask.getchannel(channel).convert('RGB').save(output, format='PNG')
            self.send_bytes(output.getvalue(), 'image/png')
            return
        if path.startswith('/media/'):
            parts = path.removeprefix('/media/').split('/')
            family = self.server.by_id.get(parts[0])
            relative = Path(*parts[1:])
            if (family is None or len(parts) < 3 or relative.parts[0] not in
                    ('native_variants', 'atlas', 'previews') or relative.suffix.lower() != '.png'):
                self.send_error_json(404, 'Unknown image')
                return
            image = (family.root / relative).resolve()
            if not image.is_relative_to(family.root.resolve()) or not image.is_file():
                self.send_error_json(404, 'Unknown image')
                return
            self.send_bytes(image.read_bytes(), 'image/png')
            return
        self.send_error_json(404, 'Unknown route')

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ('/api/decision', '/api/fixups'):
            self.send_error_json(404, 'Unknown route')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1048576:
                raise ValueError('Invalid request length')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError('Expected a JSON object')
            family = self.server.by_id.get(request.get('family'))
            if family is None:
                raise ValueError('Unknown family')
            if request.get('manifest_sha256') != family.manifest_sha256:
                self.send_error_json(409, 'Package changed; reload the viewer before deciding')
                return
            if request.get('artifact_sha256') != family.artifact_sha256:
                self.send_error_json(409, 'Review images changed; reload the viewer before deciding')
                return
            raw_manifest = (family.root / 'manifest.json').read_bytes()
            if artifact_digest(family.root, raw_manifest, family.manifest) != family.artifact_sha256:
                self.send_error_json(409, 'Package changed on disk; restart the viewer before deciding')
                return
            if route == '/api/fixups':
                with self.server.decision_lock:
                    try:
                        result = self.server.checkpoints.save(family, request)
                    except RuntimeError as error:
                        self.send_error_json(409, str(error))
                        return
                self.send_json(result)
                return
            decision = request.get('decision')
            if decision not in ('accepted', 'flagged', 'clear'):
                raise ValueError('Invalid decision')
            note = request.get('note', '')
            if not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Note must be at most 2000 characters')
            with self.server.decision_lock:
                checkpoint = self.server.checkpoints.get(family)
                if decision != 'clear' and request.get('fixups_revision') != checkpoint['revision']:
                    self.send_error_json(409, 'Frame fixups changed; reload before recording acceptance')
                    return
                data = load_decisions(self.server.decisions_path)
                versions = data['decisions'].setdefault(family.id, {})
                if decision == 'clear':
                    versions.pop(family.artifact_sha256, None)
                    if not versions:
                        data['decisions'].pop(family.id, None)
                    result = None
                else:
                    result = {'decision': decision, 'note': note.strip(),
                              'updated_at': datetime.now(timezone.utc).isoformat(),
                              'viewer_revision': VIEWER_REVISION,
                              'manifest_sha256': family.manifest_sha256,
                              'artifact_sha256': family.artifact_sha256}
                    result['fixups_revision'] = checkpoint['revision']
                    result['fixups_snapshot'] = checkpoint['frames']
                    result['guides_snapshot'] = checkpoint.get('guides')
                    result['colors_snapshot'] = checkpoint.get('colors', {})
                    result['landmarks_snapshot'] = checkpoint.get('landmarks', {})
                    result['preview_fixups'] = request.get('preview_fixups', True)
                    result['preview_scale'] = request.get('preview_scale', True)
                    versions[family.artifact_sha256] = result
                save_decisions(data, self.server.decisions_path)
            self.send_json({'decision': result})
        except (ValueError, KeyError, TypeError) as error:
            self.send_error_json(400, str(error))
        except OSError as error:
            self.send_error_json(500, f'Could not read or save review data: {error}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--check', action='store_true', help='Validate and print the queue without serving')
    parser.add_argument('--state-dir', type=Path, help='Directory for decisions and fixup checkpoints; '
                        'defaults to the collection review_state directory or the ordinary viewer state')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--package', type=Path, action='append',
                           help='Review only these manifest paths (repeat for a reversible before/after comparison)')
    selection.add_argument('--collection', type=Path, help='Review only the hash-pinned manifests in this collection')
    arguments = parser.parse_args()
    collection = None
    state_dir = arguments.state_dir or HERE
    if arguments.collection:
        try:
            families, collection = load_collection(arguments.collection)
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.error(str(error))
        excluded = []
        state_dir = arguments.state_dir or arguments.collection.resolve().parent / 'review_state'
        print(f"Collection: {collection['title']}", flush=True)
    elif arguments.package:
        families = []
        excluded = []
        for path in arguments.package:
            path = path.resolve()
            metadata = json.loads(path.read_text())
            families.append(load_family(metadata.get('review_label', metadata['creature']), path,
                                        'comparison package', metadata.get('quality_status', 'review pending')))
        if len({family.id for family in families}) != len(families):
            parser.error('Comparison packages must have distinct creature IDs')
    else:
        families, excluded = build_queue()
    print(f'MM6 acceptance queue: {len(families)} complete families; {len(excluded)} excluded', flush=True)
    if arguments.check:
        for family in families:
            print(f'{family.label}: {family.minimum_sampling:.3f}x, {len(family.manifest["frames"])} frames')
        return
    landmarks_dir = arguments.collection.resolve().parent / 'landmarks' if arguments.collection else None
    server = ReviewServer(('127.0.0.1', arguments.port), families, excluded, state_dir, collection, landmarks_dir)
    print(f'Open http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
