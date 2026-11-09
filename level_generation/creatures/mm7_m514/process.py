"""Clean accepted rat sheets and export reversible placement at two physical pixels per logical pixel."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent


def extract(image, core_tolerance=24, protect_cool_purple=False, protect_burgundy=False):
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        rgba = np.array(image)
        labels, count = ndimage.label(rgba[:, :, 3] > 0)
        maxima = ndimage.maximum(rgba[:, :, 3], labels, np.arange(count + 1))
        rgba[(rgba[:, :, 3] > 0) & (maxima[labels] <= 1)] = 0
        return Image.fromarray(rgba)
    rgb = np.asarray(image.convert('RGB'), dtype=float) / 255
    excess = np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]
    # Natural pink-gray tail is protected by this rat-specific 24/255 foreground tolerance.
    core = excess <= core_tolerance/255
    if protect_cool_purple:
        core |= (rgb[:,:,2] > rgb[:,:,0]*1.3) & (rgb[:,:,2] > rgb[:,:,1]*1.4) & (rgb[:,:,1] > rgb[:,:,0]*.35)
    if protect_burgundy:
        core |= (rgb[:,:,0] > rgb[:,:,2]*1.4) & (rgb[:,:,2] > rgb[:,:,1]*.9) & (excess < .4)
    background = (excess > .8) & (rgb[:, :, 0] > .9) & (rgb[:, :, 2] > .9)
    distance, indices = ndimage.distance_transform_edt(~core, return_indices=True)
    _, bg_indices = ndimage.distance_transform_edt(~background, return_indices=True)
    foreground = rgb[indices[0], indices[1]]
    matte = rgb[bg_indices[0], bg_indices[1]]
    vector = foreground - matte
    alpha = np.clip(np.sum((rgb-matte)*vector, axis=2)/np.maximum(np.sum(vector*vector, axis=2), 1e-8), 0, 1)
    alpha[core] = 1
    alpha[background | (distance > 7)] = 0
    recovered = (rgb-(1-alpha[:, :, None])*matte)/np.maximum(alpha[:, :, None], 1/255)
    limit = np.minimum(foreground[:, :, 0], foreground[:, :, 2])-foreground[:, :, 1]+2/255
    spill = np.maximum(0, np.minimum(recovered[:, :, 0], recovered[:, :, 2])-recovered[:, :, 1]-limit)
    recovered[:, :, 0] -= spill
    recovered[:, :, 2] -= spill
    recovered[core] = rgb[core]
    recovered[alpha == 0] = 0
    return Image.fromarray(np.round(np.dstack((np.clip(recovered, 0, 1), alpha))*255).astype(np.uint8))


def contour_score(image, protect_cool_purple=False):
    rgba = np.asarray(image)
    rgb = rgba[:, :, :3].astype(float)
    alpha = rgba[:, :, 3]/255
    band = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= .5) <= 3) | (alpha < 1))
    protected = (rgb[:,:,2] > rgb[:,:,0]*1.3) & (rgb[:,:,2] > rgb[:,:,1]*1.4) & (rgb[:,:,1] > rgb[:,:,0]*.35) & protect_cool_purple
    score = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2])-rgb[:, :, 1])*alpha*band*~protected
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return dict(maximum=float(score[y, x]), above_32=int((score > 32).sum()), protected_cool_material_pixels=int((protected & band).sum()), worst_xy=[int(x), int(y)])


def repair_contour(image, protect_warm=True, neutralize_green=True, protect_cool_purple=False):
    """Repair demonstrated purple flecks and green whisker fringes, preserving warm bare tail pixels."""
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    alpha = rgba[:, :, 3]
    band = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= 128) <= 3) | (alpha < 255))
    r, g, b = rgb.transpose(2, 0, 1)
    warm_tail = (r > b+8) & (r > g+8) & protect_warm
    protected_purple = (b > r*1.3) & (b > g*1.4) & (g > r*.35) & protect_cool_purple
    purple = np.maximum(0, np.minimum(r, b)-g-8)*band*~warm_tail*~protected_purple
    rgb[:, :, 0] -= purple
    rgb[:, :, 2] -= purple
    if protect_cool_purple:
        # Purple cloth and blue boot highlights are real. Resolve their contaminated boundary hue
        # from the nearest opaque interior instead of treating the material itself as key spill.
        interior = ndimage.distance_transform_edt(alpha >= 128) > 3
        _, nearest = ndimage.distance_transform_edt(~interior, return_indices=True)
        target = rgb[nearest[0], nearest[1]]
        luma = rgb @ np.array([.2126,.7152,.0722])
        target_luma = target @ np.array([.2126,.7152,.0722])
        corrected = target * (luma/np.maximum(target_luma,1))[:,:,None]
        repair = protected_purple & band
        rgb[repair] = corrected[repair]
        r, g, b = rgb.transpose(2, 0, 1)
        valid_cool = (b > r*1.3) & (b > g*1.4) & (g > r*.35)
        residual = np.maximum(0,np.minimum(r,b)-g-8)*band*~valid_cool
        rgb[:,:,0] -= residual
        rgb[:,:,2] -= residual
    r, g, b = rgb.transpose(2, 0, 1)
    # Light gray whiskers picked up green perpendicular residuals during magenta unmixing.
    # Olive fur has a low blue component and is excluded, as are warm pink tail highlights.
    whisker = neutralize_green & band & (g > np.maximum(r, b)+8) & (abs(r-b) < 18) & (b >= r*.9)
    gray = rgb @ np.array([.2126, .7152, .0722])
    rgb[whisker] = gray[whisker, None]
    rgba[:, :, :3] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
    return Image.fromarray(rgba)


def green_material_mask(image):
    """Soft material coverage on enhanced green pixels; keeps warm fur, skin and bones protected."""
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    r, g, b = rgb.transpose(2, 0, 1)
    saturation = (g-np.maximum(r,b))/np.maximum(g,1)
    weight = np.clip((saturation-.03)/.12,0,1)
    weight = weight*weight*(3-2*weight)
    weight[rgba[:, :, 3] == 0] = 0
    return Image.fromarray(np.round(weight*255).astype(np.uint8))


def repair_material_edge_hue(image, exclude_magenta_interior=False):
    """Resolve demonstrated excess magenta against the nearest opaque material interior."""
    rgba=np.array(image)
    rgb=rgba[:,:,:3].astype(float)
    alpha=rgba[:,:,3]
    distance=ndimage.distance_transform_edt(alpha>=254)
    interior=distance>3
    if exclude_magenta_interior:
        interior &= np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1] <= 0
    if not interior.any():
        return image
    _,nearest=ndimage.distance_transform_edt(~interior,return_indices=True)
    target=rgb[nearest[0],nearest[1]]
    excess=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
    target_excess=np.minimum(target[:,:,0],target[:,:,2])-target[:,:,1]
    affected=(alpha>0)&(distance<=3)&(excess>np.maximum(target_excess,0)+4)
    luma=rgb@np.array([.2126,.7152,.0722])
    target_luma=target@np.array([.2126,.7152,.0722])
    corrected=target*(luma/np.maximum(target_luma,1))[:,:,None]
    rgb[affected]=corrected[affected]
    # Thin fingertips/ears may have no three-pixel opaque core. A nearby warm, low-excess
    # sample keeps their repair from borrowing burgundy cloth across a narrow gap.
    r,g,b=rgb.transpose(2,0,1)
    healthy=(alpha>=254)&(g>b+4)&(r>g+4)&(g>25)
    if healthy.any():
        nearby,indices=ndimage.distance_transform_edt(~healthy,return_indices=True)
        warm=rgb[indices[0],indices[1]]
        warm_luma=warm@np.array([.2126,.7152,.0722])
        correction=warm*(luma/np.maximum(warm_luma,1))[:,:,None]
        affected=(alpha>0)&(distance<=3)&(nearby<=6)&(np.minimum(r,b)-g>16)&(r>b*1.25)&(luma>40)
        rgb[affected]=correction[affected]
    rgba[:,:,:3]=np.round(np.clip(rgb,0,255)).astype(np.uint8)
    return Image.fromarray(rgba)


def repair_green_steel_edge(image):
    """Remove demonstrated green fringe beside neutral metal, preserving genuine green cloth."""
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    alpha = rgba[:, :, 3]
    distance = ndimage.distance_transform_edt(alpha >= 254)
    interior = distance > 3
    if not interior.any():
        return image
    _, nearest = ndimage.distance_transform_edt(~interior, return_indices=True)
    target = rgb[nearest[0], nearest[1]]
    neutral = (target.max(axis=2)-target.min(axis=2)) < .30*np.maximum(target.max(axis=2), 1)
    neutral &= np.minimum(target[:, :, 0], target[:, :, 2]) <= target[:, :, 1]
    excess = rgb[:, :, 1]-np.maximum(rgb[:, :, 0], rgb[:, :, 2])
    affected = (alpha > 0) & (distance <= 3) & neutral & (excess > 8)
    luma = rgb @ np.array([.2126, .7152, .0722])
    target_luma = target @ np.array([.2126, .7152, .0722])
    corrected = target*(luma/np.maximum(target_luma, 1))[:, :, None]
    rgb[affected] = corrected[affected]
    rgba[:, :, :3] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
    return Image.fromarray(rgba)


def repair_blue_cloth(image):
    """Correct generated blue dwarf cloth to the accepted native green base; keep steel neutral."""
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    r, g, b = rgb.transpose(2, 0, 1)
    alpha = rgba[:, :, 3] / 255
    chroma = (b-r) / np.maximum(b, 1)
    blue = (b-g) / np.maximum(b, 1)
    seed = (chroma > .48) & (blue > .18) & (alpha > .5)
    labels, _ = ndimage.label(seed)
    keep = np.bincount(labels.ravel()) >= 80
    keep[0] = False
    support = ndimage.distance_transform_edt(~keep[labels]) <= 4
    weight = np.clip((chroma-.20)/.25, 0, 1) * np.clip((blue-.06)/.12, 0, 1) * support
    weight = ndimage.gaussian_filter(weight*alpha, .45) / np.maximum(ndimage.gaussian_filter(alpha, .45), 1e-8)
    target = np.stack((g*.70, b*.78, g*.68), axis=2)
    rgba[:, :, :3] = np.round(np.clip(rgb+(target-rgb)*weight[:, :, None], 0, 255)).astype(np.uint8)
    return Image.fromarray(rgba)


def repair_bark(image, height_fraction):
    """Recolor demonstrated pink bark spill above the mouth from nearby intact brown bark."""
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    r, g, b = rgb.transpose(2, 0, 1)
    region = np.indices(r.shape)[0] < image.height*height_fraction
    affected = region & (rgba[:, :, 3] > 0) & (r > g*1.08) & (b > g*.79) & (r > 35)
    healthy = region & (rgba[:, :, 3] >= 192) & (r > g*1.12) & (b < g*.72) & (g > 15)
    if affected.any():
        assert healthy.any()
        _, indices = ndimage.distance_transform_edt(~healthy, return_indices=True)
        reference = rgb[indices[0], indices[1]]
        luminance = rgb @ np.array([.2126,.7152,.0722])
        ref_luminance = reference @ np.array([.2126,.7152,.0722])
        corrected = reference * (luminance/np.maximum(ref_luminance,1))[:, :, None]
        rgb[affected] = corrected[affected]
        rgba[:, :, :3] = np.round(np.clip(rgb,0,255)).astype(np.uint8)
    return Image.fromarray(rgba), Image.fromarray(affected.astype(np.uint8)*255)


def apply_variant(image, mask, variant):
    if variant['exact_bypass']:
        return image.copy()
    rgba = np.array(image)
    rgb = rgba[:, :, :3].astype(float)
    weights = np.array(mask)/255
    if 'regions' in variant:
        result = rgb.copy()
        for region in variant['regions']:
            weight = weights[:, :, region['channel'], None]
            if 'tone_ramp' in region:
                shade = rgb @ np.array([.2126,.7152,.0722])
                ramp = region['tone_ramp']
                colors = np.array(ramp['colors'])
                target = np.stack([np.interp(shade, ramp['shade_points'], colors[:,c])
                                   for c in range(3)], axis=2)
            else:
                target = rgb @ np.array(region['rgb_matrix'])
            result += (target-rgb)*weight
    else:
        target = rgb @ np.array(variant['rgb_matrix'])
        weight = weights[:, :, None]
        result = rgb*(1-weight)+target*weight
    rgba[:, :, :3] = np.round(np.clip(result,0,255)).astype(np.uint8)
    return Image.fromarray(rgba)


def composite(image, color):
    background = Image.new('RGBA', image.size, (*color, 255))
    background.alpha_composite(image)
    return background.convert('RGB')


def connected_pose_cells(sheet, batch, core_tolerance, protect_cool_purple=False, protect_burgundy=False,
                         owner_rectangles=None):
    """Isolate separated complete poses when generated wings cross nominal grid boundaries."""
    clean = extract(sheet, core_tolerance, protect_cool_purple, protect_burgundy)
    rgba = np.array(clean)
    labels, count = ndimage.label(rgba[:, :, 3] >= 64)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    major = np.argsort(sizes)[-len(batch['frames']):]
    assert sizes[major].min() > 500, 'Missing or fragmented major pose; inspect raw sheet.'
    main = np.isin(labels, major)
    _, nearest = ndimage.distance_transform_edt(~main, return_indices=True)
    ownership = labels[nearest[0], nearest[1]]
    by_cell = {}
    for label in major:
        ys, xs = np.where(labels == label)
        col = min(batch['columns']-1,int(xs.mean()*batch['columns']/sheet.width))
        row = min(batch['rows']-1,int(ys.mean()*batch['rows']/sheet.height))
        index = row*batch['columns']+col
        assert index < len(batch['frames']) and index not in by_cell, 'Ambiguous pose ownership; inspect raw sheet.'
        isolated = rgba.copy()
        isolated[ownership != label] = 0
        # Reviewed raw-sheet regions can keep a detached prop with its native pose.
        for owner, rectangles in (owner_rectangles or {}).items():
            assert owner in batch['frames']
            for left, top, right, bottom in rectangles:
                isolated[top:bottom, left:right] = (rgba[top:bottom, left:right]
                    if owner == batch['frames'][index] else 0)
        im = Image.fromarray(isolated)
        box = im.getbbox()
        assert box[0]>0 and box[1]>0 and box[2]<sheet.width and box[3]<sheet.height, (
            f"Pose {batch['frames'][index]} reaches raw sheet boundary: {box}, sheet {sheet.size}")
        rect = [max(0,box[0]-4),max(0,box[1]-4),min(sheet.width,box[2]+4),min(sheet.height,box[3]+4)]
        by_cell[index] = (im.crop(rect),rect)
    return [by_cell[i] for i in range(len(batch['frames']))]


def run(root=HERE, tone=.82, selected_only=False):
    for directory in ['cleaned', 'aligned_2x', 'masks_2x', 'review']:
        (root / directory).mkdir(exist_ok=True)
    batches = json.loads((root / 'batches.json').read_text())
    generations = json.loads((root / 'generation.json').read_text())['batches']
    source = json.loads((root / 'sources.json').read_text())
    config = json.loads((root / 'config.json').read_text()) if (root / 'config.json').exists() else {}
    core_tolerance = config.get('core_magenta_tolerance', 24)
    protect_cool_purple = config.get('protect_cool_purple', False)
    protect_burgundy = config.get('protect_burgundy', False)
    protect_warm = config.get('protect_warm_contours', True)
    neutralize_green = config.get('neutralize_green_contours', True)
    preserve_rgb = config.get('preserve_delivered_rgb', False)
    def clean_contour(image):
        return image if preserve_rgb else repair_contour(image, protect_warm, neutralize_green, protect_cool_purple)
    logical_width, logical_height = source['logical_canvases'][0]
    registration = {}
    audit = {}
    for key, batch in batches.items():
        if selected_only and not generations.get(key, {}).get('selected'):
            continue
        sheet = Image.open(root / generations[key]['selected'])
        if key in config.get('reviewed_right_whisker_taper', {}):
            setting = config['reviewed_right_whisker_taper'][key]
            rgba = np.array(sheet.convert('RGBA'))
            width = setting['width']
            assert rgba[:, -width:, 3].max() <= setting['maximum_alpha']
            rgba[:, -width:, 3] = np.round(rgba[:, -width:, 3] * np.linspace(1, 0, width)).astype(np.uint8)
            sheet = Image.fromarray(rgba)
        if key in config.get('clear_alpha1_border_batches', []):
            rgba = np.array(sheet.convert('RGBA'))
            border = np.zeros(rgba.shape[:2], dtype=bool)
            border[[0, -1], :] = True
            border[:, [0, -1]] = True
            limit = config.get('reviewed_border_alpha_limits', {}).get(key, 1)
            assert rgba[:, :, 3][border].max() <= limit, 'Reviewed empty border has changed'
            rgba[border] = 0
            sheet = Image.fromarray(rgba)
        cols, rows = batch['columns'], batch['rows']
        if key in config.get('reviewed_gutter_alpha_limits', {}):
            rgba = np.array(sheet.convert('RGBA'))
            gutter = np.zeros(rgba.shape[:2], dtype=bool)
            for column in range(1, cols):
                boundary = round(column*sheet.width/cols)
                gutter[:, boundary-1:boundary+1] = True
            for row in range(1, rows):
                boundary = round(row*sheet.height/rows)
                gutter[boundary-1:boundary+1, :] = True
            limit = config['reviewed_gutter_alpha_limits'][key]
            assert rgba[:, :, 3][gutter].max() <= limit, 'Reviewed empty gutter has changed'
            rgba[gutter] = 0
            sheet = Image.fromarray(rgba)
        factor = 2*batch['cell_size'][0]*cols/(sheet.width*batch['reference_scale'])
        native_factor = factor
        connected = config.get('connected_pose_calibration') and key not in config.get('fixed_grid_batches', [])
        cells = connected_pose_cells(sheet,batch,core_tolerance,protect_cool_purple,protect_burgundy,
            config.get('connected_owner_rectangles', {}).get(key)) if connected else None
        calibration = 1.0
        if cells:
            ratios = []
            for name,(cell,rect) in zip(batch['frames'],cells):
                box = cell.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                nb = source['sources'][name]['visible_bounds']
                ratios.extend([(nb[2]-nb[0])*2/((box[2]-box[0])*factor),
                               (nb[3]-nb[1])*2/((box[3]-box[1])*factor)])
            calibration = float(np.median(ratios))
            factor *= calibration
        for i, name in enumerate(batch['frames']):
            if name in batch.get('reference_only_frames', []):
                continue
            x0, x1 = round(i%cols*sheet.width/cols), round((i%cols+1)*sheet.width/cols)
            y0, y1 = round(i//cols*sheet.height/rows), round((i//cols+1)*sheet.height/rows)
            nominal_x, nominal_y = x0,y0
            if cells:
                clean, (x0,y0,x1,y1) = cells[i]
            else:
                clean = extract(sheet.crop((x0,y0,x1,y1)), core_tolerance, protect_cool_purple, protect_burgundy)
            bounds = clean.getchannel('A').getbbox()
            assert bounds and bounds[0] > 0 and bounds[1] > 0 and bounds[2] < clean.width and bounds[3] < clean.height
            # One fixed tone grade for every pose, preserving hue and fine shading.
            rgba = np.array(clean)
            rgba[:, :, :3] = np.round(rgba[:, :, :3]*tone).astype(np.uint8)
            clean = clean_contour(Image.fromarray(rgba))
            if config.get('material_edge_hue_repair'):
                clean = repair_material_edge_hue(clean, config.get('exclude_magenta_interior',False))
            if config.get('ivory_spark_grade'):
                # Restore the native pale light ramp without changing dim motes or cool sparks.
                rgba = np.array(clean)
                rgb = rgba[:, :, :3].astype(float)
                r, g, b = rgb.transpose(2, 0, 1)
                weight = np.clip((r-150)/60, 0, 1)*np.clip((r-b)/60, 0, 1)*(r >= g)
                target = rgb.copy()
                target[:, :, 1] = np.maximum(g, r*.90)
                target[:, :, 2] = np.maximum(b, r*.68)
                rgba[:, :, :3] = np.round(rgb+(target-rgb)*weight[:, :, None]).astype(np.uint8)
                clean = Image.fromarray(rgba)
            if name in config.get('bark_spill_frames', {}):
                clean, repair_mask = repair_bark(clean, config['bark_spill_frames'][name])
                repair_mask.save(root / f'review/{name}_bark_repair_mask.png')
            if config.get('green_material_grade'):
                rgba = np.array(clean)
                weight = np.array(green_material_mask(clean))[:, :, None]/255
                rgb = rgba[:, :, :3].astype(float)
                graded = rgb*np.array(config['green_material_grade'])
                rgba[:, :, :3] = np.round(np.clip(rgb*(1-weight)+graded*weight,0,255)).astype(np.uint8)
                clean = Image.fromarray(rgba)
            if config.get('blue_cloth_base_repair'):
                clean = repair_green_steel_edge(repair_blue_cloth(clean))
            if name in config.get('frame_material_recolors', {}):
                # Repair an alternate delivered material color without changing alpha or detail.
                spec = config['frame_material_recolors'][name]
                rgba = np.array(clean)
                rgb = rgba[:, :, :3].astype(float)
                r, g, b = rgb.transpose(2, 0, 1)
                if spec['selector'] == 'purple':
                    chroma = (np.minimum(r, b)-g)/np.maximum(np.maximum(r, b), 1)
                elif spec['selector'] == 'red':
                    chroma = (r-g)/np.maximum(r, 1)
                elif spec['selector'] == 'cyan':
                    chroma = (np.minimum(g, b)-r)/np.maximum(np.maximum(g, b), 1)
                elif spec['selector'] == 'green':
                    chroma = (g-np.maximum(r, b))/np.maximum(g, 1)
                else:
                    raise ValueError(spec['selector'])
                low, high = spec['thresholds']
                weight = np.clip((chroma-low)/(high-low), 0, 1)
                weight = (weight*weight*(3-2*weight))[:, :, None]
                if 'bounds_px' in spec:
                    left, top, right, bottom = spec['bounds_px']
                    assert 0 <= left < right <= clean.width and 0 <= top < bottom <= clean.height
                    support = np.zeros(rgb.shape[:2])
                    support[top:bottom, left:right] = 1
                    weight *= support[:, :, None]
                target = rgb @ np.array(spec['rgb_matrix'])
                rgba[:, :, :3] = np.round(np.clip(rgb+(target-rgb)*weight, 0, 255)).astype(np.uint8)
                clean = Image.fromarray(rgba)
            clean.save(root / f'cleaned/{name}.png')
            audit[name] = dict(cleaned=contour_score(clean))
            resized = clean.convert('RGBa').resize((round(clean.width*factor), round(clean.height*factor)),
                                                    Image.Resampling.LANCZOS).convert('RGBA')
            # Filtering can mix adjacent warm and cool edge colors. Restrict repair to contour excess.
            rgba = np.array(resized)
            rgb = rgba[:, :, :3].astype(np.int16)
            contour = (rgba[:, :, 3] > 0) & ((ndimage.distance_transform_edt(rgba[:, :, 3] >= 128) <= 3)
                                            | (rgba[:, :, 3] < 255))
            spill = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2])-rgb[:, :, 1]-26)*contour
            if preserve_rgb:
                spill[:] = 0
            rgb[:, :, 0] -= spill
            rgb[:, :, 2] -= spill
            rgba[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
            resized = clean_contour(Image.fromarray(rgba))
            if config.get('material_edge_hue_repair'):
                resized = repair_material_edge_hue(resized, config.get('exclude_magenta_interior',False))
            if config.get('blue_cloth_base_repair'):
                resized = repair_green_steel_edge(resized)
            x, y = [value*2 for value in batch['native_window'][:2]]
            if cells:
                x += round((sheet.width/cols/2)*(native_factor-factor)+(x0-nominal_x)*factor)
                y += round((sheet.height/rows/2)*(native_factor-factor)+(y0-nominal_y)*factor)
            native_bounds = Image.open(root / f'native/{name}.png').getbbox()
            solid = np.asarray(resized)[:, :, 3] >= 128
            baseline = int(np.where(solid)[0].max())+1
            baseline_correction = native_bounds[3]*2-(y+baseline)
            y += baseline_correction
            placement_delta = config.get('reviewed_placement_translation_px', {}).get(name, [0, 0])
            x += placement_delta[0]
            y += placement_delta[1]
            left, top = min(0, x), min(0, y)
            right, bottom = max(logical_width*2, x+resized.width), max(logical_height*2, y+resized.height)
            aligned = Image.new('RGBA', (right-left, bottom-top))
            aligned.paste(resized, (x-left, y-top))
            aligned.save(root / f'aligned_2x/{name}.png')
            mask = green_material_mask(aligned) if config.get('green_material_grade') else Image.new('L',aligned.size)
            mask.save(root / f'masks_2x/{name}.png')
            registration[name] = dict(batch=key, raw_size=list(sheet.size), raw_rect=[x0, y0, x1, y1],
                scale=factor, common_batch_scale_correction=calibration, translate=[x, y], canvas_origin_px=[left, top], raw_clip=False,
                native_baseline_correction_px=baseline_correction,
                reviewed_placement_translation_px=placement_delta,
                method='Inverse common reference window; shared sheet scale; native alpha baseline translation.')
    (root / 'registration.json').write_text(json.dumps(registration, indent=2)+'\n')
    (root / 'review/cleaned_edge_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    names = list(registration)
    # Common native-space crop across ALL frames, never fit each sprite to the contact tile.
    boxes = [record['visible_bounds'] for record in source['sources'].values()]
    window = (0, min(box[1] for box in boxes)-12, logical_width+14, logical_height+19)
    tile_height = window[3]-window[1]
    row_height = tile_height*2+42
    contact = Image.new('RGB', (1080, ((len(names)+3)//4)*row_height), (42, 42, 42))
    draw = ImageDraw.Draw(contact)
    for i, name in enumerate(names):
        x, y = i%4*270, i//4*row_height
        native = Image.open(root / f'native/{name}.png').crop(window)
        aligned = Image.open(root / f'aligned_2x/{name}.png')
        origin = registration[name]['canvas_origin_px']
        restored = aligned.crop(tuple(window[j]*2-origin[j%2] for j in range(4)))
        restored = restored.convert('RGBa').resize(native.size, Image.Resampling.LANCZOS).convert('RGBA')
        contact.paste(composite(native, (42, 42, 42)), (x, y+20))
        contact.paste(composite(restored, (230, 230, 230)), (x, y+tile_height+32))
        draw.text((x+3, y+3), name+' native / restored', fill='white')
    contact.save(root / 'review/all_comparison.png')
    settings = dict(matte_rgb=[255, 0, 255], core_magenta_excess=core_tolerance, protect_cool_purple=protect_cool_purple, protect_warm_contours=protect_warm, neutralize_green_contours=neutralize_green, maximum_background_distance_px=7,
                    tone_rgb_multiplier=tone, connected_pose_calibration=config.get('connected_pose_calibration',False), green_material_grade=config.get('green_material_grade'), bark_spill_frames=config.get('bark_spill_frames', {}), resize='premultiplied-alpha Lanczos', masks=('enhanced green material coverage in R8' if config.get('green_material_grade') else 'zero R8; one native palette'),
                    registration=('connected pose extraction, common batch scale calibration, native baseline translation' if config.get('connected_pose_calibration') else 'common source window and sheet scale; native alpha baseline translation'), export_scale=2,
                    contour_repair='purple excess limited to 8 outside protected materials; protected cool-color contours take nearest opaque-interior hue preserving luminance; warm and green flags above')
    if config.get('blue_cloth_base_repair'):
        settings['blue_cloth_base_repair'] = 'Before resize: enhanced saturated blue connected cloth support, RGB target [0.70G,0.78B,0.68G], soft coverage, alpha unchanged; neutral steel protected. Green fringe adjacent to neutral opaque steel takes nearest interior hue at original luminance before and after resizing.'
    if preserve_rgb:
        settings['contour_repair'] = 'Delivered RGB preserved; edge scores require visual review and targeted correction only.'
    if config.get('frame_material_recolors'):
        settings['frame_material_recolors'] = config['frame_material_recolors']
    if config.get('ivory_spark_grade'):
        settings['ivory_spark_grade'] = dict(red_ramp=[150,210], warm_ramp=60, green_floor=.90, blue_floor=.68,
                                            scope='enhanced bright warm pixels; alpha unchanged')
    if protect_burgundy:
        settings['burgundy_foreground_protection'] = 'R > 1.4B, B > 0.9G and magenta excess < 0.4; retains dark red cloth interiors.'
    if config.get('material_edge_hue_repair'):
        settings['material_edge_hue_repair'] = 'Within 3px opaque contour, excess > max(nearest interior excess,0)+4 takes nearest interior hue at original luminance; alpha unchanged. Before and after resize.'
        settings['exclude_magenta_interior'] = config.get('exclude_magenta_interior',False)
    (root / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print(f'Cleaned and aligned {len(registration)} frames')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=HERE)
    parser.add_argument('--tone', type=float, default=.82)
    parser.add_argument('--selected-only', action='store_true', help='Process partial accepted batches for review only.')
    args = parser.parse_args()
    run(args.project.resolve(), args.tone, args.selected_only)
