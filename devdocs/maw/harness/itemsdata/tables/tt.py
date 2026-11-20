# TextTable::parseTabSeparated clone
def parse(path, enc='latin-1'):
    data = open(path, 'rb').read().decode(enc)
    rows = []; row = []; cell = []; q = False; i = 0; n = len(data)
    while i < n:
        c = data[i]
        if c == '"':
            if q and i + 1 < n and data[i+1] == '"':
                cell.append('"'); i += 1
            elif q:
                q = False
            elif not cell:
                q = True
            else:
                cell.append(c)
        elif c == '\r':
            pass
        elif c == '\t' and not q:
            row.append(''.join(cell)); cell = []
        elif c == '\n' and not q:
            row.append(''.join(cell)); cell = []; rows.append(row); row = []
        else:
            cell.append(c)
        i += 1
    if cell or row:
        row.append(''.join(cell)); rows.append(row)
    return rows, q

def raw(path, enc='latin-1'):
    return [l.rstrip('\r').split('\t') for l in open(path, 'rb').read().decode(enc).split('\n')]
