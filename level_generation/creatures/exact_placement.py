"""Exact native-to-shared-canvas placement, including legacy registration bases.

A registration can retain its historical integer reference coordinates. Export
translates its whole canvas once into exact native coordinates, without resampling.
"""


def native_offset(canvas, size, anchor='bottom-center'):
    if anchor not in ('bottom-center', 'center'):
        raise ValueError(f'Unsupported native anchor: {anchor}')
    return [(canvas[0] - size[0]) / 2,
            (canvas[1] - size[1]) / (2 if anchor == 'center' else 1)]


def export_placement(canvas, size, reference_offset, canvas_origin, tier=2, anchor='bottom-center'):
    exact = native_offset(canvas, size, anchor)
    physical = [(exact[i] - reference_offset[i]) * tier for i in range(2)]
    if any(v != int(v) for v in physical):
        raise ValueError('Export tier cannot represent native anchor correction exactly')
    correction = [int(v) for v in physical]
    return exact, [canvas_origin[i] + correction[i] for i in range(2)], correction


def validate_manifest(manifest, registration):
    """Check mapping independently of anatomical accuracy; return all frame failures."""
    errors = []
    tier = manifest['pixels_per_logical_pixel']
    canvas = manifest['logical_canvas']
    anchor = manifest.get('anchor', 'bottom-center')
    expected_pivot = [canvas[0] / 2, canvas[1] / (2 if anchor == 'center' else 1)]
    if manifest.get('logical_pivot') != expected_pivot:
        errors.append('package: logical pivot')
    for name, frame in manifest['frames'].items():
        reference = frame.get('registration_native_offset', frame['native_offset'])
        exact, origin, _ = export_placement(canvas, frame['source_canvas'], reference,
                                            registration[name]['canvas_origin_px'], tier,
                                            anchor)
        if frame['native_offset'][:2] != exact or frame['aligned_canvas_origin_px'] != origin:
            errors.append(name + ': native origin')
        rect = frame['crop_in_aligned_px']
        if frame['crop_origin_px'] != [origin[i] + rect[i] for i in range(2)]:
            errors.append(name + ': crop origin')
        if frame['atlas_xywh'][2:] != [rect[2]-rect[0], rect[3]-rect[1]]:
            errors.append(name + ': crop dimensions')
    return errors


def validate_landmark_usage(annotation, registration):
    """Reject explicitly disqualified anchors/scale points in annotated registrations.

    This checks recorded review decisions, not anatomical correspondence. Older
    annotation formats without named point lists cannot be certified by this check.
    Only calibrations contributing to the exported frames are relevant.
    """
    errors = []
    frames = annotation.get('frames', {})
    active_batches = {row.get('calibration_group', row['batch']) for row in registration.values()}
    for name, row in registration.items():
        points = frames.get(name, {})
        labels = points.get('landmarks')
        if not isinstance(labels, list) or points.get('job') != row['batch']:
            continue
        diagnostic = set(points.get('diagnostic_landmarks', [])) | set(row.get('diagnostic_landmarks', []))
        if labels and labels[0] in diagnostic:
            errors.append(name + ': translation anchor marked diagnostic: ' + labels[0])
    for batch, specification in annotation.get('calibration', {}).items():
        if batch not in active_batches:
            continue
        points = specification if 'native' in specification else frames.get(specification.get('frame'), {})
        labels = points.get('landmarks')
        if not isinstance(labels, list):
            continue
        diagnostic = set(points.get('diagnostic_landmarks', []))
        # A calibration frame may be superseded as artwork while still owning
        # the sheet's scale; its annotation remains authoritative in that case.
        for index in specification.get('pair', []):
            if index < 0 or index >= len(labels):
                errors.append(batch + ': calibration point index out of range')
            elif labels[index] in diagnostic:
                errors.append(batch + ': scale point marked diagnostic: ' + labels[index])
    return errors


def validate_animation_bindings(manifest):
    """Compare exported sequences to saved native frame groups, including legacy Goblin groups."""
    errors = []
    bindings = manifest['native_group_bindings']
    for palette, actions in manifest['animations_by_palette'].items():
        for action, animation in actions.items():
            label = f'{palette}/{action}'
            group_name = animation['native_group']
            # These are the two existing manifest schemas, not guessed filename conventions.
            if palette in bindings:
                source = bindings[palette]['actions'][action]
            else:
                source = bindings.get(group_name)
            if source is None:
                errors.append(label + ': missing native group')
                continue
            if source['sprite_name'] != group_name:
                errors.append(label + ': native group name')
            if set(animation['views']) != {str(v) for v in range(8)}:
                errors.append(label + ': view coverage')
            if group_name.lower() == 'null':
                if not animation.get('no_image') or any(animation['views'].values()):
                    errors.append(label + ': native no-image action')
                continue
            if animation.get('no_image'):
                errors.append(label + ': unexpected no-image action')
            if animation['native_length_raw'] != source.get('animation_length_raw', 0):
                errors.append(label + ': native animation length')
            expected_duration = sum(frame['frame_length_raw'] * 62.5 for frame in source['frames'])
            if animation['sequence_ms'] != expected_duration:
                errors.append(label + ': sequence duration')
            for view, steps in animation['views'].items():
                if len(steps) != len(source['frames']):
                    errors.append(label + '/' + view + ': frame count')
                    continue
                for index, (step, frame) in enumerate(zip(steps, source['frames'])):
                    flags = frame['flags']
                    mirrored = f'Mirror{view}' in flags
                    stored_view = 8-int(view) if mirrored else int(view)
                    name = frame['texture_name'].lower() + ('' if 'Image1' in flags else str(stored_view))
                    expected = (name, mirrored, frame['frame_length_raw'] * 62.5, frame.get('scale', 1.0))
                    actual = (step['frame'], step['mirrored'], step['duration_ms'],
                              step.get('native_scale', animation.get('native_frame_scale')))
                    if actual != expected or name not in manifest['frames']:
                        errors.append(f'{label}/{view}/{index}: native frame, mirror, duration or scale')
    base = next(p for p, variant in manifest['variants'].items() if variant.get('exact_base_bypass'))
    if manifest['animations'] != manifest['animations_by_palette'][base]:
        errors.append('package: base animation alias')
    return errors
