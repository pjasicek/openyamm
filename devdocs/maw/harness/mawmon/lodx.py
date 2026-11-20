import struct, zlib, sys, os
path, out = sys.argv[1], sys.argv[2]
d = open(path, 'rb').read()
os.makedirs(out, exist_ok=True)
base = struct.unpack_from('<I', d, 0x110)[0]
count = struct.unpack_from('<I', d, 0x11C)[0]
for i in range(count):
    e = 0x120 + i*0x4C
    name = d[e:e+64].split(b'\0')[0].decode('latin1')
    off, size = struct.unpack_from('<II', d, e+64)
    rec = d[base+off: base+off+size]
    payload = rec[0x60:]
    data = zlib.decompress(payload) if payload[:1] == b'\x78' else payload
    print(name, size, len(data))
    open(os.path.join(out, name), 'wb').write(data)
