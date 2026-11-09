"""Prepare geometric coastline masks and material atlases for the MM7/MM8 Blender calibration."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, label, binary_erosion
from shoreline import rounded_water

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from prepare import texture_index


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2)+'\n')


def png(path, pixels):
    Image.fromarray(np.round(np.clip(pixels, 0, 1)*255).astype('uint8')).save(path)


def main():
    recipe = json.loads((HERE/'recipe.json').read_text())
    rows = []
    for world, stem in recipe['maps']:
        settings = {**recipe,**recipe['worlds'][world]}
        source = BASE/'maps'/world/stem
        data = json.loads((source/'scene.json').read_text())
        out = HERE/'maps'/world/stem
        out.mkdir(parents=True, exist_ok=True)
        size = recipe['master_size']
        atlas = np.array(Image.open(source/'terrain.png').resize((size,size),Image.Resampling.BOX), dtype=np.float32)/255
        # Water identity comes from terrain tile families and native shore keys, never water RGB coloration.
        _,native = texture_index(world)
        tile_size = size//128
        masks,water_sources = {},{}
        for tile,mapping in data['tile_mapping'].items():
            name = mapping['name'].lower()
            mask = np.zeros((tile_size,tile_size),bool)
            if name.endswith('wtrtyl'):
                mask[:] = True
            elif 'wtr' in name:
                path = native[name]
                water_sources[str(path)] = sha(path)
                pixels = np.array(Image.open(path).convert('RGBA'))
                key = ((pixels[:,:,0]>=245)&(pixels[:,:,1]<=10)&(pixels[:,:,2]>=245))
                key |= ((pixels[:,:,0]<=10)&(pixels[:,:,1]>=245)&(pixels[:,:,2]>=245))|(pixels[:,:,3]<128)
                assert key.any() and not key.all(), 'Native shore key missing: '+name
                mask = np.array(Image.fromarray(key.astype('uint8')*255).resize((tile_size,tile_size),Image.Resampling.BOX))>=128
            masks[int(tile)] = mask
        water = np.zeros((size,size),bool)
        for index,tile in enumerate(data['tile_map']):
            y,x = divmod(index,128)
            water[y*tile_size:(y+1)*tile_size,x*tile_size:(x+1)*tile_size] = masks[tile]
        png(out/'water_raw_key_mask.png',water.astype(float))
        # Native shore keys use stippled coverage. Recover that coverage before tracing the bank contour.
        water = gaussian_filter(water.astype(np.float32),recipe['native_key_dither_blur_master_pixels'])>recipe['native_key_coverage_threshold']
        assert water.any() and (~water).any()
        wet = distance_transform_edt(water)
        dry = distance_transform_edt(~water)
        signed = wet-dry
        limit = recipe['shore_max_shift_master_pixels']
        new_water = rounded_water(water,recipe['shore_smoothing_master_pixels'],limit)
        # Only the coastal band may change, including where the traced ocean contour meets the image boundary.
        fixed = np.abs(signed)>limit+1
        new_water[fixed] = water[fixed]
        rounded = distance_transform_edt(new_water)-distance_transform_edt(~new_water)
        rounded += recipe['water_expansion_x2_pixels']*2
        new_water = rounded>0
        new_water[fixed] = water[fixed]
        rounded = distance_transform_edt(new_water)-distance_transform_edt(~new_water)
        feather = recipe['shore_feather_master_pixels']
        coverage = np.clip(.5+rounded/(2*feather),0,1)
        coverage = coverage*coverage*(3-2*coverage)
        distance = distance_transform_edt(new_water)/2
        stops = recipe['worlds'][world]['water_stops_x2_pixels']
        color = np.stack([np.interp(distance,[s[0] for s in stops],[s[1][c]/255 for s in stops])
                          for c in range(3)], axis=2).astype(np.float32)
        rng = np.random.default_rng(20260927)
        grain = gaussian_filter(rng.standard_normal((size,size)).astype(np.float32),.7)
        grain /= grain.std()
        swell = gaussian_filter(rng.standard_normal((size,size)).astype(np.float32),3)
        swell /= swell.std()
        depth_texture = np.minimum(distance/30,1)
        color *= 1+depth_texture[:,:,None]*(.08*grain[:,:,None]+.04*swell[:,:,None])
        # Extend actual land colors into the rounded coastal fringe, then blend the tile material boundaries.
        nearest = distance_transform_edt(water, return_distances=False, return_indices=True)
        land = atlas.copy()
        land[water] = atlas[nearest[0][water],nearest[1][water]]
        land = gaussian_filter(land,(recipe['material_blend_master_pixels'],)*2+(0,))
        gray = land @ np.array([.2126,.7152,.0722],dtype=np.float32)
        land = gray[:,:,None]+(land-gray[:,:,None])*recipe['worlds'][world]['land_saturation']
        land *= recipe['worlds'][world]['land_color_gain']
        # Same multi-scale light grain as the approved trial, applied only to the land material.
        field = np.zeros((size,size),np.float32)
        rng = np.random.default_rng(20260928)
        for sigma,weight in [(0,.25),(1,.5),(3,.35),(9,.15)]:
            band = rng.standard_normal((size,size),dtype=np.float32)
            if sigma:
                band = gaussian_filter(band,sigma)
            field += (band-band.mean())/band.std()*weight
        field = np.clip(field/field.std(),-2.5,2.5)
        field -= field[~water].mean()
        land *= 1+field[:,:,None]*recipe['land_noise_strength']
        png(out/'land_color.png',land)
        png(out/'water_color.png',color)
        png(out/'water_mask.png',coverage)
        png(out/'water_original_mask.png',water.astype(float))
        height = np.array(data['height_map'],dtype=float).reshape(128,128)/4
        height = gaussian_filter(height,settings['normal_smoothing_terrain_cells'])*settings['normal_relief_scale']
        dy,dx = np.gradient(height,4)
        normals = np.stack([-dx,dy,np.ones_like(dx)],axis=2)
        normals /= np.linalg.norm(normals,axis=2)[:,:,None]
        save(out/'normals.json',normals.reshape(-1,3).tolist())
        # Native textures give the second game-specific building lighting pass an unmodified palette source.
        textures = {}
        for name in data['materials']:
            path = native[name]
            cache = HERE/'textures'/world/(name+'.png')
            cache.parent.mkdir(parents=True,exist_ok=True)
            Image.open(path).convert('RGBA').save(cache)
            textures[name] = {'path':str(cache),'source':str(path),'source_sha256':sha(path),'sha256':sha(cache)}
        old_edge = water ^ binary_erosion(water)
        new_edge = new_water ^ binary_erosion(new_water)
        displacement = max(float(distance_transform_edt(~old_edge)[new_edge].max()),
                           float(distance_transform_edt(~new_edge)[old_edge].max()))/2
        changed = water ^ new_water
        assert np.max(np.abs(signed[changed]),initial=0)<=limit+2, 'Contour rasterization exceeded the movement bound'
        report = dict(world=world,stem=stem,name=data['name'],x2_size=json.loads((source/'export.json').read_text())['x2_size'],
                      source=str(source),directory=str(out.relative_to(HERE)),
                      source_scene_sha256=sha(source/'scene.blend'),source_data_sha256=sha(source/'scene.json'),
                      recipe_sha256=sha(HERE/'recipe.json'),textures=textures,water_mask_sources=water_sources,
                      masks={n:sha(out/n) for n in ['land_color.png','water_color.png','water_mask.png','water_original_mask.png','water_raw_key_mask.png','normals.json']},
                      shoreline_changed_pixels_x2_equivalent=int(changed.sum())/4,
                      shoreline_max_boundary_distance_x2_pixels=displacement,
                      shoreline_allowed_signed_distance_x2_pixels=limit/2,
                      original_art_used_as_pixels=False)
        save(out/'prepared.json',report)
        rows.append({k:v for k,v in report.items() if k not in ['textures','masks']})
        print('PREPARED',world,stem,'shore maximum boundary distance',displacement,flush=True)
    save(HERE/'scope.json',dict(count=len(rows),records=rows))


if __name__ == '__main__':
    main()
