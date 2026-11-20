import struct, sys, zlib, os
p, outdir = sys.argv[1], sys.argv[2]
want = [w.lower() for w in sys.argv[3:]]
os.makedirs(outdir, exist_ok=True)
d = open(p, 'rb').read()
doff, dsize, _, count = struct.unpack_from('<iiii', d, 0x110)
for i in range(count):
    e = doff + i * 0x4C
    n = d[e:e + 64].split(b'\0')[0].decode()
    off, size = struct.unpack_from('<ii', d, e + 64)
    if want and n.lower() not in want:
        continue
    blob = d[doff + off:doff + off + size]
    packed = struct.unpack_from('<i', blob, 0x44)[0]
    data = zlib.decompress(blob[0x60:0x60 + packed]) if packed else blob[0x60:]
    open(os.path.join(outdir, n), 'wb').write(data)
    print(n, size, len(data))
