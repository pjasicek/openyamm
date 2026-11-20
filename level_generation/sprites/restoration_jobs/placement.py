"""Native-coordinate placement diagnostics. Flags require review, never automatic regeneration."""
import numpy as np

CHECKS_VERSION = 2


def apply_layout_override(job, layout, raw_sha256):
    """Explicitly map a mislaid returned sheet; preserve frozen native sizes/asset identities."""
    if layout['raw_sha256'] != raw_sha256 or len(layout.get('reason', '').strip()) < 20:
        raise ValueError('Layout override needs matching raw master hash and a concrete reason')
    if set(layout['cells']) != set(job['assets']):
        raise ValueError('Layout override must account for exactly the job assets')
    width, height = layout['sheet_size']
    if width <= 0 or height <= 0:
        raise ValueError('Layout sheet dimensions must be positive')
    cells = []
    for cell in job['cells']:
        override = layout['cells'][cell['asset']]
        box, rectangle = override['cell'], override['native_rectangle']
        if (len(box) != 4 or len(rectangle) != 4 or not np.isfinite(box + rectangle).all()
                or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)
                or rectangle[2] <= rectangle[0] or rectangle[3] <= rectangle[1]):
            raise ValueError('Invalid source cell or native sampling rectangle')
        # Native empty margins may extend outside the returned image; sampling gives transparent padding.
        cells.append(dict(cell, cell=box, native_rectangle=rectangle))
    return dict(job, sheet_size=layout['sheet_size'], cells=cells, layout_override=layout)


def bounds(mask, factor=1):
    yy, xx = np.nonzero(mask)
    if not len(xx):
        return None
    return [float(v / factor) for v in (xx.min(), yy.min(), xx.max() + 1, yy.max() + 1)]


def inspect_placement(native, enhanced, regions=()):
    """Compare opaque geometry, separately from faint outlines. Coordinates are native pixels.

    Optional named regions describe visually identified rigid supports/landmarks. They are not
    inferred from labels: a suspended lamp or soft effect must not acquire an invented ground base.
    """
    original = np.array(native.convert('RGBA'))[:, :, 3] >= 192
    restored = np.array(enhanced.convert('RGBA'))[:, :, 3] >= 192
    expected, actual = bounds(original), bounds(restored, 2)
    report = dict(native_solid_bounds=expected, enhanced_solid_bounds=actual, regions={})
    warnings = []
    tolerance = max(2, max(native.size) * .02)
    if expected and not actual:
        warnings.append('missing_opaque_geometry')
    elif expected and actual:
        delta = np.array(actual) - expected
        report['solid_bounds_delta'] = delta.tolist()
        if abs(delta).max() > tolerance:
            warnings.append('opaque_bounds_drift_review_supports_and_proportions')
    for region in regions:
        name = region['name']
        x0, y0, x1, y1 = region['box']
        if not (0 <= x0 < x1 <= native.width and 0 <= y0 < y1 <= native.height):
            raise ValueError(f'Invalid native landmark region: {name}')
        source = original[y0:y1, x0:x1]
        target = restored[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
        sb, tb = bounds(source), bounds(target, 2)
        if not sb:
            raise ValueError(f'Landmark {name} has no opaque native support; inspect region selection')
        residual = (np.array(tb) - sb).tolist() if tb else None
        coverage = float(target.sum() / (4 * source.sum()))
        report['regions'][name] = dict(box=region['box'], native_bounds=sb, enhanced_bounds=tb,
                                       residual=residual, solid_coverage_ratio=coverage)
        if tb is None or max(abs(v) for v in residual) > tolerance or not .70 <= coverage <= 1.45:
            warnings.append(f'opaque_landmark_drift:{name}')
    return report, warnings


def inspect_motion(frames):
    # Compare errors relative to EACH native frame, retaining intentional bobbing/motion.
    names = {name for frame in frames.values() for name in frame['placement']['regions']}
    warnings = []
    for name in sorted(names):
        residuals = [frame['placement']['regions'][name]['residual'] for frame in frames.values()
                     if name in frame['placement']['regions']]
        if len(residuals) > 1 and all(r is not None for r in residuals):
            if np.ptp(np.array(residuals), axis=0).max() > 3:
                warnings.append(f'animation_support_drift:{name}')
    return warnings


def validate_review(checks, review, animated):
    """Require specific visual evidence and disposition of every current warning."""
    if checks.get('checks_version') != CHECKS_VERSION:
        raise ValueError('Reprocess with current placement checks before accepting')
    required = ['master_detail', 'light', 'dark', 'placement', 'supports'] + (['motion'] if animated else [])
    for field in required:
        if len(review.get(field, '').strip()) < 20:
            raise ValueError(f'Review needs concrete {field} evidence (at least 20 characters)')
    if review.get('anchor_kind') not in ('grounded', 'suspended', 'water', 'effect', 'ui', 'native_other'):
        raise ValueError('Declare the observed anchor_kind; do not infer grounding from bottom alignment')
    decisions = review.get('warnings', {})
    if set(decisions) != set(checks.get('warnings', [])):
        raise ValueError('Review must address every current warning exactly; stale/blanket approval is invalid')
    if any(len(note.strip()) < 20 for note in decisions.values()):
        raise ValueError('Each warning needs concrete visual evidence, not a generic approval')
