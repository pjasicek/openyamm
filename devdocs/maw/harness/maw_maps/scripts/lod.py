import struct, sys, zlib, os
def entries(path):
    d = open(path,'rb').read()
    assert d[:4] == b'LOD\0', path
    ver = d[4:4+16].split(b'\0')[0]
    # directories at 0x100
    out = []
    dname = d[0x100:0x110].split(b'\0')[0]
    doff, dsize, _, cnt = struct.unpack_from('<IIII', d, 0x110)
    if ver.startswith(b'MMVIII'):
        esz = 0x4C
        for i in range(cnt):
            e = doff + i*esz
            name = d[e:e+0x40].split(b'\0')[0].decode('latin1')
            off, size = struct.unpack_from('<II', d, e+0x40)
            out.append((name, doff+off, size))
    else:
        for i in range(cnt):
            e = doff + i*32
            name = d[e:e+16].split(b'\0')[0].decode('latin1')
            off, size = struct.unpack_from('<II', d, e+16)
            out.append((name, doff+off, size))
    return d, out
def payload(d, off, size):
    raw = d[off:off+size]
    for hdr in (16, 8):
        if len(raw) > hdr+2 and raw[hdr] == 0x78:
            try:
                return zlib.decompress(raw[hdr:])
            except Exception:
                pass
    return raw
if __name__ == '__main__':
    path, outdir = sys.argv[1], sys.argv[2]
    names = set(sys.argv[3:])
    d, es = entries(path)
    for n, off, size in es:
        if names and n.lower() not in names:
            if not names: pass
            continue
        data = payload(d, off, size)
        if outdir != '-':
            open(os.path.join(outdir, n.lower()), 'wb').write(data)
        print(n, size, len(data), data[:8].hex())
