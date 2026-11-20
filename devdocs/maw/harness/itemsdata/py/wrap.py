import sys, re, textwrap
p = sys.argv[1]
out = []
for line in open(p).read().split('\n'):
    m = re.match(r'^(\s*)([\w.]+): "(.*)"\s*$', line)
    if len(line) > 120 and m:
        ind, key, val = m.groups()
        val = val.replace('\\"', '"')
        out.append('%s%s: >-' % (ind, key))
        for w in textwrap.wrap(val, width=118 - len(ind) - 2, break_long_words=False, break_on_hyphens=False):
            out.append(ind + '  ' + w)
    else:
        out.append(line)
open(p, 'w').write('\n'.join(out))
