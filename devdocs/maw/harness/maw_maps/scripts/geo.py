"""Parse MM7/MM8-layout ODM and BLV geometry for diffing (MMMerge stores all maps in MM8 layout)."""
import struct
from collections import Counter


def s(data, off, n):
    return data[off:off + n].split(b'\0')[0].decode('latin1')


def parse_odm(path):
    d = open(path, 'rb').read()
    m = {'kind': 'odm'}
    m['name'] = s(d, 0, 32)
    m['file'] = s(d, 0x20, 32)
    m['ver'] = s(d, 0x40, 16)
    m['sky'] = s(d, 0x60, 32)
    m['tileset'] = s(d, 0x80, 32)
    m['tile_lookup'] = d[0xA0:0xB0].hex()
    off = 0xB4  # MM8 layout
    T = 128 * 128
    m['height'] = d[off:off + T]; off += T
    m['tile'] = d[off:off + T]; off += T
    m['attr'] = d[off:off + T]; off += T
    nn = struct.unpack_from('<i', d, off)[0]; off += 4
    off += 0x20000 + 0x10000 + nn * 12
    bc = struct.unpack_from('<i', d, off)[0]; off += 4
    hdr = off
    off += bc * 0xBC
    bms = []
    for i in range(bc):
        h = hdr + i * 0xBC
        name1 = s(d, h, 32); name2 = s(d, h + 32, 32)
        nv = struct.unpack_from('<I', d, h + 0x44)[0]
        nf = struct.unpack_from('<I', d, h + 0x4C)[0]
        nb = struct.unpack_from('<I', d, h + 0x5C)[0]
        pos = struct.unpack_from('<3i', d, h + 0x70)
        bb = struct.unpack_from('<6i', d, h + 0x7C)
        verts = [struct.unpack_from('<3i', d, off + k * 12) for k in range(nv)]
        off += nv * 12
        fo = off
        tn = fo + nf * 0x134 + nf * 2
        faces = []
        for k in range(nf):
            f = fo + k * 0x134
            n = d[f + 0x12E]
            vids = struct.unpack_from('<%dh' % n, d, f + 0x20)
            faces.append({
                'attr': struct.unpack_from('<I', d, f + 0x1C)[0],
                'verts': tuple(verts[v] if 0 <= v < nv else None for v in vids),
                'tex': s(d, tn + k * 10, 10),
                'cog': struct.unpack_from('<h', d, f + 0x122)[0],
                'event': struct.unpack_from('<h', d, f + 0x124)[0],
                'trig': struct.unpack_from('<h', d, f + 0x126)[0],
                'dU': struct.unpack_from('<h', d, f + 0x112)[0],
                'dV': struct.unpack_from('<h', d, f + 0x114)[0],
                'ptype': d[f + 0x12F],
            })
        off = tn + nf * 10 + nb * 8
        bms.append({'i': i, 'name': name1, 'name2': name2, 'pos': pos, 'bbox': bb, 'verts': verts,
                    'faces': faces})
    m['bmodels'] = bms
    ec = struct.unpack_from('<i', d, off)[0]; off += 4
    ents = []
    eo = off; off += ec * 0x20; no = off; off += ec * 32
    for k in range(ec):
        e = eo + k * 0x20
        did, flags = struct.unpack_from('<HH', d, e)
        pos = struct.unpack_from('<3i', d, e + 4)
        yaw = struct.unpack_from('<i', d, e + 16)[0]
        cog, ev, trig, f1a, evar, f1e = struct.unpack_from('<HHHhhh', d, e + 20)
        ents.append({'i': k, 'name': s(d, no + k * 32, 32), 'desc': did, 'flags': flags, 'pos': pos, 'yaw': yaw,
                     'cog': cog, 'event': ev, 'trig': trig, 'evar': evar})
    m['entities'] = ents
    idc = struct.unpack_from('<i', d, off)[0]; off += 4 + idc * 2 + T * 4
    sc = struct.unpack_from('<i', d, off)[0]; off += 4
    sp = []
    for k in range(sc):
        o = off + k * 24
        pos = struct.unpack_from('<3i', d, o)
        r, t, idx, a = struct.unpack_from('<4H', d, o + 12)
        g = struct.unpack_from('<I', d, o + 20)[0]
        sp.append({'i': k, 'pos': pos, 'radius': r, 'type': t, 'index': idx, 'attr': a, 'group': g})
    off += sc * 24
    m['spawns'] = sp
    m['tail'] = len(d) - off
    return m


def parse_blv(path):
    d = open(path, 'rb').read()
    m = {'kind': 'blv'}
    fds, srd, srld, dds = struct.unpack_from('<4i', d, 0x68)
    off = 0x88
    vc = struct.unpack_from('<i', d, off)[0]; off += 4
    verts = [struct.unpack_from('<3h', d, off + k * 6) for k in range(vc)]
    off += vc * 6
    fc = struct.unpack_from('<i', d, off)[0]; off += 4
    fh = off; off += fc * 0x60
    fdat = off; off += fds
    tno = off; off += fc * 10
    fpc = struct.unpack_from('<i', d, off)[0]; off += 4
    fpo = off; off += fpc * 0x24; fpn = off; off += fpc * 10
    extras = []
    for k in range(fpc):
        e = fpo + k * 0x24
        v = struct.unpack_from('<18h', d, e)
        extras.append({'face_id': v[6], 'cog': v[12], 'event': v[13] & 0xFFFF, 'f1c': v[14], 'name': s(d, fpn + k * 10, 10)})
    faces = []
    cur = fdat
    for k in range(fc):
        h = fh + k * 0x60
        attr = struct.unpack_from('<I', d, h + 0x2C)[0]
        fx, bmp, sec, bsec = struct.unpack_from('<HHHh', d, h + 0x48)
        bbox = struct.unpack_from('<6h', d, h + 0x50)
        ptype, n = d[h + 0x5C], d[h + 0x5D]
        vids = struct.unpack_from('<%dH' % n, d, cur)
        cur += (n + 1) * 2 * 6
        ex = extras[fx] if fx < len(extras) else None
        faces.append({'i': k, 'attr': attr, 'sector': sec, 'back': bsec, 'bbox': bbox, 'ptype': ptype,
                      'verts': tuple(verts[v] if v < vc else None for v in vids), 'tex': s(d, tno + k * 10, 10),
                      'extra': fx, 'event': ex['event'] if ex else 0, 'cog': ex['cog'] if ex else 0})
    m['faces'] = faces
    m['extras'] = extras
    m['verts'] = verts
    sc = struct.unpack_from('<i', d, off)[0]; off += 4
    m['sector_count'] = sc
    secsz = 0x78
    sectors = []
    for k in range(sc):
        o = off + k * secsz
        sectors.append({'flags': struct.unpack_from('<i', d, o)[0], 'bbox': struct.unpack_from('<6h', d, o + secsz - 0x14 - 0x4) if False else None})
    off += sc * secsz + srd + srld
    dc = struct.unpack_from('<i', d, off)[0]; off += 4
    m['door_count'] = dc
    ec = struct.unpack_from('<i', d, off)[0]; off += 4
    eo = off; off += ec * 0x20; no = off; off += ec * 32
    ents = []
    for k in range(ec):
        e = eo + k * 0x20
        did, flags = struct.unpack_from('<HH', d, e)
        pos = struct.unpack_from('<3i', d, e + 4)
        yaw = struct.unpack_from('<i', d, e + 16)[0]
        cog, ev, trig, f1a, evar, f1e = struct.unpack_from('<HHHhhh', d, e + 20)
        ents.append({'i': k, 'name': s(d, no + k * 32, 32), 'desc': did, 'flags': flags, 'pos': pos, 'yaw': yaw,
                     'cog': cog, 'event': ev, 'trig': trig, 'evar': evar})
    m['entities'] = ents
    lc = struct.unpack_from('<i', d, off)[0]; off += 4
    lights = []
    for k in range(lc):
        o = off + k * 0x14
        p = struct.unpack_from('<3h', d, o)
        r = struct.unpack_from('<h', d, o + 6)[0]
        rgb = tuple(d[o + 8:o + 11])
        lights.append({'pos': p, 'radius': r, 'rgb': rgb, 'type': d[o + 11]})
    off += lc * 0x14
    m['lights'] = lights
    u9 = struct.unpack_from('<i', d, off)[0]; off += 4 + u9 * 8
    m['bsp_nodes'] = u9
    spc = struct.unpack_from('<i', d, off)[0]; off += 4
    sp = []
    for k in range(spc):
        o = off + k * 24
        pos = struct.unpack_from('<3i', d, o)
        r, t, idx, a = struct.unpack_from('<4H', d, o + 12)
        g = struct.unpack_from('<I', d, o + 20)[0]
        sp.append({'i': k, 'pos': pos, 'radius': r, 'type': t, 'index': idx, 'attr': a, 'group': g})
    off += spc * 24
    m['spawns'] = sp
    oc = struct.unpack_from('<i', d, off)[0]; off += 4 + oc * 12
    m['outline_count'] = oc
    m['tail'] = len(d) - off
    return m
