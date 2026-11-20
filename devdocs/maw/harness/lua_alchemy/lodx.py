import struct, sys, zlib, os
path, out = sys.argv[1], sys.argv[2]
d = open(path,'rb').read()
dofs, dsize, _, n = struct.unpack_from('<IIII', d, 0x100+16)
p = dofs
for i in range(n):
    name = d[p:p+64].split(b'\0')[0].decode()
    ofs, size = struct.unpack_from('<II', d, p+64)
    p += 76
    blob = d[dofs+ofs: dofs+ofs+size]
    cs = struct.unpack_from('<I', blob, 0x44)[0]
    us = struct.unpack_from('<I', blob, 0x58)[0]
    data = zlib.decompress(blob[0x60:0x60+cs]) if us else blob[0x60:]
    open(os.path.join(out, name), 'wb').write(data)
    print(name, cs, us, len(data))
