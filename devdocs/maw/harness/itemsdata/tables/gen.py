import sys, os, hashlib, difflib, re
sys.path.insert(0, sys.argv[1])
import tt

TDIR, S, D, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
HIST = os.path.join(TDIR, 'mawfirst')
WS = ' \t\n\v\f\r'  # C++ std::isspace in the C locale; 0x85 is not whitespace there


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def nlines(p):
    return open(p, 'rb').read().count(b'\n')


def rows_of(p):
    return tt.parse(p)[0]


def c(r, i):
    return r[i].strip(WS) if i < len(r) else ''


def keyed(rows):
    out = {}
    for r in rows:
        k = c(r, 0)
        if k.isdigit():
            out[int(k)] = r
    return out


def esc(s):
    s = s.replace('\x85', '\\x85').replace('\x92', '\\x92').replace('\x96', '\\x96').replace('\x93', '\\x93')
    s = s.replace('\x94', '\\x94')
    return s.replace('|', '\\|')


def q(s):
    return '`' + esc(s) + '`' if s != '' else '`(empty)`'


def wdiff(a, b):
    ta = re.findall(r'\s+|[^\s]+', a)
    tb = re.findall(r'\s+|[^\s]+', b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    parts = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            seg = ''.join(ta[i1:i2])
            if len(seg) > 40:
                seg = (seg[:12] + '...' + seg[-12:]) if parts else ('...' + seg[-20:])
            parts.append(seg)
        else:
            if i2 > i1:
                parts.append('[-' + ''.join(ta[i1:i2]) + '-]')
            if j2 > j1:
                parts.append('{+' + ''.join(tb[j1:j2]) + '+}')
    s = ''.join(parts)
    if s.endswith('...'):
        pass
    return esc(s)


commits = [l.rstrip('\n').split('\t') for l in open(os.path.join(TDIR, 'commits.tsv'))]


def hist_versions(name):
    vs = []
    for h, date, subj in commits:
        p = os.path.join(HIST, 'h_' + h, name)
        vs.append((h, date, subj, rows_of(p) if os.path.exists(p) else None))
    return vs


def introduced(vs, getter, final):
    # earliest commit from which getter(version) == final continuously up to the last version
    first = None
    for h, date, subj, rows in vs:
        v = getter(rows) if rows is not None else None
        if v == final:
            if first is None:
                first = (h, date)
        else:
            first = None
    return first


out = []
w = out.append

# ---------------------------------------------------------------- load
bI, mI, oI = rows_of(S + '/base/ITEMS.txt'), rows_of(S + '/maw/ITEMS.txt'), rows_of(D + '/items.txt')
bR, mR, oR = rows_of(S + '/base/rnditems.txt'), rows_of(S + '/maw/rnditems.txt'), rows_of(D + '/random_items.txt')
bS, mS, oS = rows_of(S + '/base/SPCITEMS.TXT'), rows_of(S + '/maw/SPCITEMS.TXT'), rows_of(D + '/special_item_enchants.txt')
B, M, O = keyed(bI), keyed(mI), keyed(oI)
HDR = [c(bI[1], i) for i in range(17)]
OHDR = [c(oI[1], i) for i in range(len(oI[1]))]
assert [c(mI[1], i) for i in range(17)] == HDR

w('# MAW item tables against base MMMerge')
w('')
w('Generated from the extracted tables; values are cell values after the trimming OpenYAMM applies')
w('(`getCell`: ASCII whitespace only). Windows-1252 bytes are shown as `\\x85`, `\\x92`.')
w('Notes cells are shown as word diffs: `[-removed-]{+added+}`, unchanged runs shortened with `...`.')
w('"Commit" is the first MAW commit of `Data/zMaw.T.lod` from which the row (or cell) has held its final MAW value.')
w('')

# ---------------------------------------------------------------- 1 provenance
w('## 1. Provenance')
w('')
w('| Set | File | md5 | Lines |')
w('|---|---|---|---|')
for label, base_dir, names in [
        ('MAW ef23ee17 `Data/zMaw.T.lod`', S + '/maw', ['ITEMS.txt', 'rnditems.txt', 'SPCITEMS.TXT']),
        ('Base `reference/mmerge_data_forus/Data/mmmerge.T.lod/`', S + '/base',
         ['ITEMS.txt', 'rnditems.txt', 'SPCITEMS.TXT', 'STDITEMS.TXT']),
        ('OpenYAMM `assets_dev/engine/data_tables/`', D,
         ['items.txt', 'random_items.txt', 'special_item_enchants.txt', 'standard_item_enchants.txt'])]:
    for n in names:
        p = base_dir + '/' + n
        w('| %s | %s | `%s` | %d |' % (label, n, md5(p), nlines(p)))
w('')
dp = os.path.join(TDIR, 'datapatch')
dpm = {n: md5(os.path.join(dp, n)) for n in ['ITEMS.txt', 'rnditems.txt', 'SPCITEMS.TXT', 'STDITEMS.TXT']}
same = all(dpm[n] == md5(S + '/base/' + n) for n in dpm)
w('- `reference/mmerge_datapatch/Data/mmmerge.T.lod` (md5 `%s`)'
  % md5('/home/pjasicek/github/OpenYAMM/reference/mmerge_datapatch/Data/mmmerge.T.lod'))
w('  holds the same four tables byte for byte' + (' (identical md5s).' if same else ' (DIFFERENT md5s).'))
w('  No newer base MMMerge copy is available locally, so "probably base update" in 1.1 is a judgement from')
w('  content and MAW history, not a comparison against a newer MMMerge.')
w('- All files are CRLF, tab separated. Base and OpenYAMM ITEMS keep Windows-1252 punctuation (`\\x85`, `\\x92`);')
w('  the MAW ITEMS, rnditems and SPCITEMS are pure ASCII.')
w('- `special_item_enchants.txt` and `standard_item_enchants.txt` are byte-identical to base SPCITEMS/STDITEMS.')
w('  MAW does not ship STDITEMS.TXT, so standard enchants are unchanged by MAW.')
w('')
# history summary
for name in ['ITEMS.txt', 'rnditems.txt', 'SPCITEMS.TXT']:
    vs = []
    for h, date, subj in commits:
        p = os.path.join(HIST, 'h_' + h, name)
        vs.append((h, date, md5(p) if os.path.exists(p) else None))
    present = [v for v in vs if v[2]]
    distinct = []
    for v in present:
        if not distinct or distinct[-1][2] != v[2]:
            distinct.append(v)
    w('- MAW history of %s: first in `%s` (%s), %d distinct versions, last change `%s` (%s).'
      % (name, present[0][0], present[0][1], len(distinct), distinct[-1][0], distinct[-1][1]))
w('- `Data/zMaw.T.lod` has %d commits (`%s` %s to `%s` %s); ef23ee17 itself does not touch it.'
  % (len(commits), commits[0][0], commits[0][1], commits[-1][0], commits[-1][1]))
w('')
w('### 1.1 MAW design or base-version difference?')
w('')
w('The first MAW ITEMS.txt (`15714657`, "artifacts description updated") equals base except artifact Notes and')
w('item 1574; the first rnditems.txt (`c2e0e17e`) equals base except 146, 272-278 and 283; the first SPCITEMS.TXT')
w('(`e9cbec6a`) keeps base rows 1-73 and appends seven draft rows 74-80 (`of Fire Resistance`, `of Air')
w('Resistance`, ..., `of Magic Resistance`), later replaced by the current 74-80. So MAW started from this base,')
w('and every other difference arrived in later MAW commits. Most changes are clearly MAW design (artifact buffs,')
w('armour/belt stats, potion renames, crafting items, enchant weights, new enchants). Rows that look like base')
w('fixes or tool artefacts rather than MAW design:')
w('')
w('- Text only, 13 rows (3.8): Windows-1252 `\\x85`/`\\x92` replaced by space/apostrophe or dropped. All arrive in')
w('  one commit (`b2705582`, 2025-08-23) that also makes the whole MAW ITEMS.txt pure ASCII: an editor/tool')
w('  re-encode (or a newer base); no gameplay content. Safe to skip or take.')
w('- 1372 The DeathBlade: the base row is an MMMerge test item ("For testing... remove before final release");')
w('  MAW blanks it to an `_artifact570` placeholder. Probably base cleanup, not MAW design.')
w('- 1574 `Catalyst potion` (Value 500) -> `Empty Message Scroll` (Value 0), present from MAW\'s first ITEMS: the')
w('  row sits in the empty message-scroll block (1575-1578 are `Empty Message Scroll`, Value 0). Probably base')
w('  cleanup.')
w('- 1637 Sacred Spear: Notes lose a lore clause and "(+1D9 if used two-handed)", while 1641 Trident keeps its')
w('  "(+1D6 if used two-handed)". Unclear: text fix in base or MAW removing the two-handed spear note.')
w('- 1621 Jeweled Dagger Mod1 `1d2` -> `2d2` (`befd51e0`): the only non-artifact weapon dice change. Unclear;')
w('  `1d2` on a 300-gold Time of Wonders dagger looks like a data error that MAW (or a newer base) corrected.')
w('')

# ---------------------------------------------------------------- items diff data
item_vs = hist_versions('ITEMS.txt')
changed = {}
for k in sorted(B):
    d = [(i, c(B[k], i), c(M[k], i)) for i in range(17) if c(B[k], i) != c(M[k], i)]
    if d:
        changed[k] = d
raw_only = [k for k in B if k not in changed and B[k][:17] != M[k][:17]]


def item_intro(k):
    fin = tuple(c(M[k], i) for i in range(17))
    return introduced(item_vs, lambda rows: (lambda kk: tuple(c(kk[k], i) for i in range(17)) if k in kk else None)(
        keyed(rows)), fin)


intro = {k: item_intro(k) for k in changed}
CP = re.compile('[\x85\x92]')


def is_encoding_only(k):
    d = changed[k]
    if any(i != 16 for i, a, b in d):
        return False
    a, b = d[0][1], d[0][2]
    return re.sub(r'[\x85\x92]', '', a).replace(' ', '').replace("'", '') == b.replace(' ', '').replace("'", '')


groups = []
armour = [k for k in changed if c(B[k], 4) == 'Armor' and all(i in (6, 7) for i, a, b in changed[k])
          and c(B[k], 8) not in ('Artifact', 'Relic', 'Special')]
belts = [k for k in changed if c(B[k], 4) == 'Belt' and c(B[k], 8) not in ('Artifact', 'Relic', 'Special')]
potions = [k for k in changed if c(B[k], 4) == 'Bottle' and k != 290 and not is_encoding_only(k)]
crafting = [k for k in changed if 1041 <= k <= 1070]
mapitem = [k for k in changed if k == 290]
removed = [k for k in changed if c(M[k], 2).startswith('_artifact') or (c(M[k], 1) == 'null' and c(B[k], 1) != 'null')]
artifacts = [k for k in changed if c(B[k], 8) in ('Artifact', 'Relic') and k not in removed]
encoding = [k for k in changed if is_encoding_only(k) and k not in artifacts]
used = set(armour + belts + potions + crafting + mapitem + removed + artifacts + encoding)
other = [k for k in changed if k not in used]
GROUPS = [('Body armour (Mod1/Mod2)', armour), ('Belts', belts), ('Potions', potions),
          ('Crafting items (1041-1070)', crafting), ('Map item 290', mapitem), ('Artifacts and relics', artifacts),
          ('Removed items', removed), ('Text only: Windows-1252 punctuation removed', encoding), ('Other', other)]

# ---------------------------------------------------------------- 2 format / alignment
w('## 2. Format and id alignment (base MMMerge vs OpenYAMM)')
w('')
w('### 2.1 items.txt')
w('')
bids, oids = sorted(B), sorted(O)
w('- Loader: `GameDataLoader::loadItemTable` -> `ItemTable::load` (`game/tables/ItemTable.cpp`). Rows are keyed by')
w('  the numeric `Item #` in column 0 (`parseItemId`: digits only); non-numeric rows (title, header, blank) are')
w('  skipped, row order does not matter, the table is sized to the largest id. Columns are read by position:')
w('  0-16 = the 17 MMMerge columns, 17 `package_id`, 18 `canonical_id`, 19 `source_item_id`, 20 `content_flags`;')
w('  the parser also reads optional positions 21-44 (tier, use action, set, effect profile, class roots, required')
w('  Might/Accuracy, inventory size, ...), which no engine row fills.')
w('- Base: %d id rows (0-%d, contiguous), header of 17 columns. MAW: %d id rows (0-%d), same 17-column header.'
  % (len(bids), bids[-1], len(M), max(M)))
w('- OpenYAMM: %d id rows (0-%d, contiguous). Header = base header + `%s`.'
  % (len(oids), oids[-1], '`, `'.join(OHDR[17:])))
w('  %d rows carry the extra columns:' % sum(1 for k in O if len(O[k]) > 17))
w('  the spellbook rows 400-498 (`World:mm8`), 1202-1300 (`World:mm7`), 1902-2018 (`World:mm6`) with only')
w('  `content_flags` set, and the OpenYAMM-only row 2201 (`Blaster Shotgun`, `package_id=engine`,')
w('  `content_flags=ScatterBlaster`). All other rows have 17 cells.')
w('- Ids line up 1:1 for 0-2200 (same item in the same id, same column order). MAW has no rows beyond 2200 and no')
w('  missing ids. MM9 items are not in this table: they are appended from `worlds/mm9` (id range 10000-10999).')
w('- Base has one trailing 15-cell blank row; MAW does not (no effect: non-numeric rows are skipped).')
bo = {k: [(i, c(B[k], i), c(O[k], i)) for i in range(17) if c(B[k], i) != c(O[k], i)] for k in B}
bo = {k: v for k, v in bo.items() if v}
w('- OpenYAMM changed %d base rows (cells in columns 0-16), plus added row 2201 and the extra columns above:' % len(bo))
w('')
w('| Item # | Name | Changed cells (base -> OpenYAMM) | MAW touches row? |')
w('|---|---|---|---|')
for k in sorted(bo):
    mt = 'yes: ' + ', '.join(HDR[i] for i, a, b in changed[k]) if k in changed else 'no'
    w('| %d | %s | %s | %s |' % (k, esc(c(B[k], 2)), '; '.join('%s: %s -> %s' % (HDR[i], q(a), q(b)) for i, a, b in bo[k]), mt))
w('')
w('  These are case normalisations (`gold`/`misc`/`armor`/`cloak`) and one Equip Stat fix (`Ania Selving` Bow ->')
w('  Missile). No MAW-changed cell overlaps them (MAW only changes Notes on 1307, 2030, 2045).')
w('- Patch generator: key by Item #, copy columns 0-16 cell by cell, never whole rows (a whole-row copy from MAW')
w('  would revert the Equip Stat fixes above on 1307, 2030 and 2045 and drop columns 17-20).')
w('')

w('### 2.2 random_items.txt')
w('')
bRk, oRk, mRk = keyed(bR), keyed(oR), keyed(mR)
w('- Loader: `ItemTable::load`, second loop. Rows keyed by numeric column 0; only columns 2-7 (treasure levels 1-6)')
w('  are read into `randomTreasureWeights`; `Pic File` and the trailing name column are ignored.')
w('- Base, MAW and OpenYAMM: %d / %d / %d id rows (1-%d), same header (`Item #`, `Pic File`, `1`..`6`), same'
  % (len(bRk), len(mRk), len(oRk), max(oRk)))
w('  title row and the same footer block (see 4.1). No row for 0 or 2201 (2201 therefore has all weights 0).')
rch_pre = [k for k in bRk if any(c(bRk[k], i) != c(mRk[k], i) for i in range(9))]
bro = {k: v for k, v in ((k, [(i, c(bRk[k], i), c(oRk[k], i)) for i in range(9) if c(bRk[k], i) != c(oRk[k], i)])
                         for k in bRk) if v}
cols_touched = sorted({i for v in bro.values() for i, a, b in v})
bro_kinds = {}
for k, v in bro.items():
    key = tuple((a, b) for i, a, b in v)
    bro_kinds.setdefault(key, []).append(k)


def ranges(ks):
    ks = sorted(ks)
    out_r = []
    s = p = ks[0]
    for x in ks[1:]:
        if x == p + 1:
            p = x
            continue
        out_r.append('%d' % s if s == p else '%d-%d' % (s, p))
        s = p = x
    out_r.append('%d' % s if s == p else '%d-%d' % (s, p))
    return ', '.join(out_r)


w('- OpenYAMM changed %d base rows, all spellbooks, only in weight columns (levels) %s. Ids:'
  % (len(bro), ', '.join(c(bR[2], i) for i in cols_touched)))
w('  %s.' % ranges(bro))
w('')
w('| Base -> OpenYAMM weights (changed levels) | Rows |')
w('|---|---|')
for key, ks in sorted(bro_kinds.items(), key=lambda x: min(x[1])):
    w('| %s | %s |' % ('; '.join('%s -> %s' % (a, b) for a, b in key), ranges(ks)))
w('')
w('  OpenYAMM re-weights the per-world spellbook copies. MAW also changes spellbook rows: %s (see 4.3).'
  % ', '.join(str(k) for k in sorted(set(rch_pre) & set(bro))))
w('')

w('### 2.3 special_item_enchants.txt and standard_item_enchants.txt')
w('')
w('- Loader: `SpecialItemEnchantTable::load` (`game/items/ItemEnchantTables.cpp`). Keyed by position: every row')
w('  whose column 0 and column 1 are both non-empty and whose column 0 is not `Bonus Stat` becomes the next entry;')
w('  `get(id)` returns entry `id - 1`, so ids are the same 1-based indices as MAW\'s `Bonus2`.')
w('  Columns read: 0 text, 1 suffix (also parsed to `SpecialItemEnchantKind` by exact lower-case match), 2-13 slot')
w('  weights W1 W2 Miss Arm Shld Helm Belt Cape Gaunt Boot Ring Amul, 14 Value (`x2` = multiplier), 15 Lvl (first')
w('  char), 16 description.')
w('- Our file equals base, so our entries 1-73 = SPCITEMS 1-73 exactly (first data row is line 5, entry 73 is line 77).')
w('- Ids 74-80 are **not free** in our loader: the footer comment rows `Treasure Level` / `A= 3 to 4` / `B= 3 to 5`')
w('  / `C= 4 to 5` have text in both column 0 and 1 and load as junk entries 74-77 (kind `None`, all weights 0, so')
w('  never rolled; `D= 5 to 6` has an empty column 1 and is skipped). The sums row (`\\t\\t505\\t505...`) is skipped.')
w('  Appending MAW 74-80 at the end of our file would give them ids 78-84. They must be inserted after entry 73')
w('  (before the blank/sums/footer rows), or the footer rows removed. With MAW\'s file layout the footer becomes')
w('  junk entries 81-84.')
w('- `parseSpecialEnchantKind` only knows the 72 vanilla suffixes; `of Sparking` (73) and all MAW suffixes 74-80')
w('  (`Paladins\'`, `WarriorMage\'`, ...) parse to kind `None`. `chooseSpecialEnchantId` skips kind `None`, so they')
w('  would never be generated and have no effect until kinds/effects are added in code.')
w('- Random enchant chances per treasure level are not read from any table: they are constants in')
w('  `game/items/ItemEnchantRuntime.cpp` (standard 0/40/40/40/40/75, special 0/0/10/15/20/25, weapon special')
w('  0/0/10/20/30/50), equal to the rnditems footer. The A-D level bands are hard-coded in `isSpecialRarityAllowed`.')
w('- Standard enchants: `StandardItemEnchantTable::load`, same row rule, positional; ours = base STDITEMS; MAW has none.')
w('')

# ---------------------------------------------------------------- 3 items diff
w('## 3. ITEMS.txt: base -> MAW')
w('')
n_cells = sum(len(v) for v in changed.values())
w('%d rows changed, %d cells. MAW-only rows: none. Base-only rows: none. Rows whose only difference is outside'
  % (len(changed), n_cells))
w('the trimmed value: %d.' % len(raw_only))
w('')
w('| Group | Rows | Cells |')
w('|---|---|---|')
for g, ks in GROUPS:
    w('| %s | %d | %d |' % (g, len(ks), sum(len(changed[k]) for k in ks)))
colcount = {}
for v in changed.values():
    for i, a, b in v:
        colcount[HDR[i]] = colcount.get(HDR[i], 0) + 1
w('')
w('Changed cells by column: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(colcount.items(), key=lambda x: -x[1])) + '.')
w('')


def cells_text(k, full_notes=False):
    parts = []
    for i, a, b in changed[k]:
        if i == 16 and not full_notes:
            parts.append('Notes: ' + wdiff(a, b))
        elif i == 16:
            parts.append('Notes: %s -> %s' % (q(a), q(b)))
        else:
            parts.append('%s: %s -> %s' % (HDR[i], q(a), q(b)))
    return '; '.join(parts)


def ch(k, i):
    a, b = c(B[k], i), c(M[k], i)
    return '%s (unchanged)' % a if a == b else '%s -> %s' % (a, b)


def intro_text(k):
    x = intro.get(k)
    return '%s %s' % x if x else '?'


for g, ks in GROUPS:
    if not ks:
        continue
    w('### 3.%d %s' % (GROUPS.index((g, ks)) + 1, g))
    w('')
    if g.startswith('Body armour'):
        w('| Item # | Name | Skill | Mod1 | Mod2 | Commit |')
        w('|---|---|---|---|---|---|')
        for k in sorted(ks):
            w('| %d | %s | %s | %s | %s | %s |' % (k, esc(c(B[k], 2)), c(B[k], 5), ch(k, 6), ch(k, 7), intro_text(k)))
    elif g == 'Belts':
        w('| Item # | Name | Mod1 | Mod2 | Commit |')
        w('|---|---|---|---|---|')
        for k in sorted(ks):
            w('| %d | %s | %s | %s | %s |' % (k, esc(c(B[k], 2)), ch(k, 6), ch(k, 7), intro_text(k)))
    elif g in ('Crafting items (1041-1070)', 'Map item 290', 'Removed items'):
        w('Base rows are placeholders or replaced wholesale; full MAW rows (columns 1-16):' if g != 'Removed items'
          else 'Full rows, base -> MAW:')
        w('')
        w('| Item # | Side | Pic | Name | Value | Equip | Skill | Mod1 | Mod2 | Mat | ID | Unid name | Spr | VarA | VarB '
          '| X | Y | Commit |')
        w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        for k in sorted(ks):
            for side, r in (('base', B[k]), ('MAW', M[k])):
                w('| %d | %s | %s | %s |' % (k, side, ' | '.join(esc(c(r, i)) for i in range(1, 16)),
                                            intro_text(k) if side == 'MAW' else ''))
        w('')
        w('Notes (full):')
        w('')
        for k in sorted(ks):
            w('- %d base: %s' % (k, q(c(B[k], 16))))
            w('  MAW: %s' % q(c(M[k], 16)))
    else:
        w('| Item # | Name (base) | Changed cells (base -> MAW) | Commit |')
        w('|---|---|---|---|')
        for k in sorted(ks):
            w('| %d | %s | %s | %s |' % (k, esc(c(B[k], 2)), cells_text(k), intro_text(k)))
    w('')
    if g == 'Body armour (Mod1/Mod2)':
        un = [k for k in sorted(B) if c(B[k], 4) == 'Armor' and k not in changed
              and c(B[k], 8) not in ('Artifact', 'Relic', 'Special')]
        w('Unchanged non-artifact `Armor` rows: %s (%s).' % (ranges(un), ', '.join(
            '%d %s %s/%s' % (k, esc(c(B[k], 2)), c(B[k], 6), c(B[k], 7)) for k in un)))
        w('')
    if g == 'Belts':
        w('All 15 non-artifact belts change. Artifact belts: 1326 and 1337 also get Mod1/Mod2 (listed under artifacts);')
        w('537 Berserker Belt keeps Mod1/Mod2 `0`/`0` (Notes change only).')
        w('')
    if g == 'Crafting items (1041-1070)':
        w('Ids 1041-1050 and 1068-1070 stay `_potion/reagent` placeholders in MAW. 1022-1023 (Power Stone) are in')
        w('"Other". Material column values: 5 for the ten gems, 1/2/3/4 for the special crafting items.')
        w('')

# ---------------------------------------------------------------- 3.x patch onto ours
w('### 3.10 As a patch onto OpenYAMM items.txt')
w('')
w('- Mapping: same Item #, same column names and positions for columns 0-16 (ours = base header + 4 extra columns).')
w('  The patch is exactly the %d cells above; no id remapping.' % n_cells)
touched_extra = [k for k in changed if len(O[k]) > 17 and any(c(O[k], i) for i in range(17, len(O[k])))]
w('- MAW-touched rows with OpenYAMM extra columns (17-20) set: %s. Keep 17-20 as they are.'
  % (', '.join(map(str, touched_extra)) if touched_extra else 'none'))
three = []
for k, v in changed.items():
    for i, a, b in v:
        o = c(O[k], i)
        if o != a:
            three.append((k, i, a, o, b))
w('- Three-way cells where OpenYAMM already differs from base: %d.' % len(three))
if three:
    w('')
    w('| Item # | Column | Base | Ours | MAW |')
    w('|---|---|---|---|---|')
    for k, i, a, o, b in sorted(three):
        w('| %d | %s | %s | %s | %s |' % (k, HDR[i], q(a), q(o), q(b)))
w('- MAW-touched rows that OpenYAMM also changed (different cells, so no overwrite if patched by cell):')
w('  %s.' % ', '.join('%d (ours: %s; MAW: %s)' % (k, ', '.join(HDR[i] for i, a, b in bo[k]),
                                       ', '.join(HDR[i] for i, a, b in changed[k])) for k in sorted(bo) if k in changed))
w('- Result: applying MAW cell by cell overwrites no OpenYAMM fix. Text-only rows replace our Windows-1252')
w('  punctuation with ASCII (no gameplay effect).')
w('- Engine-side conflicts outside items.txt (not cell conflicts): item 290 is potion 70 `Protection from Magic` in')
w('  `engine/data_tables/potion_settings.txt`, so making it a Map needs that row removed or remapped; the potion')
w('  renames 224-263 (and value/unidentified-name/sprite changes 252-261) change what the potion ids mean, so')
w('  `potion_settings.txt`, the mixing table and potion effects must follow MAW\'s potion design, not just names.')
w('')
w('Compact patch for all non-Notes cells (`id: Column=value`):')
w('')
w('```')
for k in sorted(changed):
    nn = [(i, b) for i, a, b in changed[k] if i != 16]
    if nn:
        w('%d: %s' % (k, '; '.join('%s=%s' % (HDR[i], b if b != '' else '(empty)') for i, b in nn)))
w('```')
w('')
notes_ids = sorted(k for k in changed if any(i == 16 for i, a, b in changed[k]))
w('Notes cells to take verbatim from MAW (%d): %s.' % (len(notes_ids), ranges(notes_ids)))
w('')

# ---------------------------------------------------------------- 4 rnditems
w('## 4. rnditems.txt: base -> MAW')
w('')
w('### 4.1 Title, header and footer blocks')
w('')
nonid_b = [[c(r, i) for i in range(len(r))] for r in bR if not c(r, 0).isdigit()]
nonid_m = [[c(r, i) for i in range(len(r))] for r in mR if not c(r, 0).isdigit()]
w('- Non-item rows identical in base and MAW (after trimming): %s. Raw text identical: %s.'
  % ('yes' if nonid_b == nonid_m else 'NO',
     'yes' if [r for r in bR if not c(r, 0).isdigit()] == [r for r in mR if not c(r, 0).isdigit()] else 'no'))
w('- The file has no ring/amulet or other extra tables; after the item list (ending at 2200) there are four blank')
w('  rows and this block, unchanged by MAW and equal to OpenYAMM\'s random_items.txt and code constants:')
w('')
w('```')
started = False
for r in bR:
    if c(r, 0).startswith('Bonus chance'):
        started = True
    if started and any(c(r, i) for i in range(len(r))):
        w('\t'.join(c(r, i) for i in range(9)).rstrip('\t'))
w('```')
w('')
rch = {}
for k in sorted(bRk):
    d = [(i, c(bRk[k], i), c(mRk[k], i)) for i in range(9) if c(bRk[k], i) != c(mRk[k], i)]
    if d:
        rch[k] = d
rnd_vs = hist_versions('rnditems.txt')


def rintro(k):
    fin = tuple(c(mRk[k], i) for i in range(9))
    return introduced(rnd_vs, lambda rows: (lambda kk: tuple(c(kk[k], i) for i in range(9)) if k in kk else None)(
        keyed(rows)), fin)


w('### 4.2 Changed item rows')
w('')
w('%d rows changed, %d cells; all in weight columns %s. No MAW-only or base-only ids. Item names refer to'
  % (len(rch), sum(len(v) for v in rch.values()),
     ', '.join(sorted({c(bR[2], i) for v in rch.values() for i, a, b in v}))))
w('MAW ITEMS.txt names where they differ.')
w('')
w('| Item # | Name (MAW ITEMS) | Base L1-6 | MAW L1-6 | Ours L1-6 | Commit |')
w('|---|---|---|---|---|---|')
for k in sorted(rch):
    bw = ' '.join(c(bRk[k], i) for i in range(2, 8))
    mw = ' '.join(c(mRk[k], i) for i in range(2, 8))
    ow = ' '.join(c(oRk[k], i) for i in range(2, 8))
    x = rintro(k)
    w('| %d | %s | %s | %s | %s | %s |' % (k, esc(c(M[k], 2)), bw, mw, '= base' if ow == bw else ow,
                                          '%s %s' % x if x else '?'))
w('')
other_cols = [(k, i) for k, v in rch.items() for i, a, b in v if i not in range(2, 8)]
if other_cols:
    w('Non-weight cells changed: ' + ', '.join('%d col %d' % x for x in other_cols))
    w('')
w('### 4.3 As a patch onto OpenYAMM random_items.txt')
w('')
ov = [k for k in rch if k in bro]
w('- Same ids, same column positions (2-7 = levels 1-6). Rows touched by both OpenYAMM and MAW: %s.'
  % (', '.join(map(str, ov)) if ov else 'none'))
w('')
w('| Item # | Level | Base | Ours | MAW | Status |')
w('|---|---|---|---|---|---|')
nconf = 0
for k in ov:
    for i in range(2, 8):
        a, o, b = c(bRk[k], i), c(oRk[k], i), c(mRk[k], i)
        if a == o and a == b:
            continue
        if o == a:
            st = 'MAW only'
        elif b == a:
            st = 'ours only (keep ours)'
        elif o == b:
            st = 'same change'
        else:
            st = '**conflict**'
            nconf += 1
        w('| %d | %s | %s | %s | %s | %s |' % (k, c(bR[2], i), a, o, b, st))
w('')
w('- Patch = the MAW L1-6 values above for %d rows; %d cell(s) conflict with an OpenYAMM change (both sides moved'
  % (len(rch), nconf))
w('  level 4 of the Invisibility spellbooks in opposite directions); a patch generator must not blindly overwrite')
w('  them. Everything else applies without touching an OpenYAMM change. The footer needs no patch.')
w('')

# ---------------------------------------------------------------- 5 SPCITEMS
w('## 5. SPCITEMS.TXT: base -> MAW')
w('')
SH = ['Bonus Stat', 'Name Add', 'W1', 'W2', 'Miss', 'Arm', 'Shld', 'Helm', 'Belt', 'Cape', 'Gaunt', 'Boot', 'Ring',
      'Amul', 'Value', 'Lvl', 'Description']


def spc_entries(rows):
    e = []
    for li, r in enumerate(rows):
        if c(r, 0) == '' or c(r, 1) == '' or c(r, 0) == 'Bonus Stat':
            continue
        e.append((li + 1, r))
    return e


eb, em, eo = spc_entries(bS), spc_entries(mS), spc_entries(oS)
real_b = [x for x in eb if not c(x[1], 0).startswith(('Treasure Level', 'A=', 'B=', 'C=', 'D='))]
real_m = [x for x in em if not c(x[1], 0).startswith(('Treasure Level', 'A=', 'B=', 'C=', 'D='))]
spc_vs = hist_versions('SPCITEMS.TXT')


def sintro(idx):
    fin = tuple(c(real_m[idx - 1][1], i) for i in range(17))

    def get(rows):
        e = [x for x in spc_entries(rows) if not c(x[1], 0).startswith(('Treasure Level', 'A=', 'B=', 'C=', 'D='))]
        return tuple(c(e[idx - 1][1], i) for i in range(17)) if len(e) >= idx else None
    return introduced(spc_vs, get, fin)


w('Base has %d enchant rows (ids 1-%d), MAW %d (1-%d). Header rows are identical. Ids are 1-based positions.'
  % (len(real_b), len(real_b), len(real_m), len(real_m)))
w('')
w('### 5.1 Changed rows 1-%d' % len(real_b))
w('')
sch = []
for idx in range(1, len(real_b) + 1):
    rb, rm = real_b[idx - 1][1], real_m[idx - 1][1]
    d = [(i, c(rb, i), c(rm, i)) for i in range(17) if c(rb, i) != c(rm, i)]
    if d:
        sch.append((idx, d))
scount = {}
for idx, d in sch:
    for i, a, b in d:
        scount[SH[i]] = scount.get(SH[i], 0) + 1
w('%d of %d rows changed, %d cells. By column: %s.' % (len(sch), len(real_b), sum(len(d) for i, d in sch),
                                                       ', '.join('%s %d' % kv for kv in scount.items())))
w('Suffix text (column 1, the kind key in our parser) changed on: %s.'
  % (', '.join(str(i) for i, d in sch if any(j == 1 for j, a, b in d)) or 'no row'))
w('')
w('| Id | Suffix (base) | Changed cells (base -> MAW) | Commit |')
w('|---|---|---|---|')
for idx, d in sch:
    x = sintro(idx)
    w('| %d | %s | %s | %s |' % (idx, esc(c(real_b[idx - 1][1], 1)),
                                 '; '.join('%s: %s -> %s' % (SH[i], q(a), q(b)) for i, a, b in d),
                                 '%s %s' % x if x else '?'))
w('')
w('Slot weights as full vectors for the changed rows (W1 W2 Miss Arm Shld Helm Belt Cape Gaunt Boot Ring Amul):')
w('')
w('```')
for idx, d in sch:
    rb, rm = real_b[idx - 1][1], real_m[idx - 1][1]
    w('%2d %-22s base %s | MAW %s' % (idx, c(rb, 1), ' '.join('%2s' % c(rb, i) for i in range(2, 14)),
                                     ' '.join('%2s' % c(rm, i) for i in range(2, 14))))
w('```')
w('')
w('### 5.2 New rows 74-%d (full)' % len(real_m))
w('')
w('| Id | Bonus Stat | Name Add | W1 | W2 | Miss | Arm | Shld | Helm | Belt | Cape | Gaunt | Boot | Ring | Amul | Value '
  '| Lvl | Description | Commit |')
w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for idx in range(len(real_b) + 1, len(real_m) + 1):
    r = real_m[idx - 1][1]
    x = sintro(idx)
    w('| %d | %s | %s |' % (idx, ' | '.join(esc(c(r, i)) for i in range(17)), '%s %s' % x if x else '?'))
w('')
w('Raw MAW lines (quotes as in the file):')
w('')
w('```')
rawm = open(S + '/maw/SPCITEMS.TXT', 'rb').read().decode('latin-1').split('\n')
for idx in range(len(real_b) + 1, len(real_m) + 1):
    li = real_m[idx - 1][0]
    w(rawm[li - 1].rstrip('\r').rstrip('\t'))
w('```')
w('')
w('### 5.3 Non-enchant rows')
w('')
tail_b = [[c(r, i) for i in range(len(r))] for li, r in enumerate(bS) if li + 1 > real_b[-1][0]]
tail_m = [[c(r, i) for i in range(len(r))] for li, r in enumerate(mS) if li + 1 > real_m[-1][0]]


def show(rows):
    return ['\t'.join(x).rstrip('\t') for x in rows]


w('Rows after the last enchant, base vs MAW (trimmed, blank rows shown as empty lines):')
w('')
w('```')
for line in difflib.unified_diff(show(tail_b), show(tail_m), 'base', 'MAW', lineterm='', n=10):
    w(line)
w('```')
w('')
w('The sums row (`505 505 505 345 ...`) is unchanged although MAW changed weights, so it is stale in MAW; no')
w('loader reads it. MAW drops the `D= 5 to 6` comment row and pads blank rows to 19 tabs.')
w('')
w('### 5.4 As a patch onto OpenYAMM special_item_enchants.txt')
w('')
w('- Rows 1-73: ours = base, so the %d changed rows above apply by position unchanged (ours line N = base line N).'
  % len(sch))
w('- Rows 74-80: insert the seven MAW lines directly after line 77 (`of Sparking`), before the blank, sums and')
w('  footer rows. Ids then match MAW `Bonus2` 74-80, and the footer junk entries move from 74-77 to 81-84.')
w('  Alternatively drop the footer comment rows (they are documentation only).')
w('- Kinds: the MAW suffixes of 74-80 parse to `SpecialItemEnchantKind::None`; until the parser and effects are')
w('  extended they are never rolled (`chooseSpecialEnchantId` skips `None`) and grant nothing on items that')
w('  carry them.')
known = set(re.findall(r'normalized == "([^"]+)"', open(sys.argv[5]).read().split('SpecialItemEnchantKind parseSpecialEnchantKind')[1].split('\n}')[0]))
for idx, d in sch:
    for i, a, b in d:
        if i == 1:
            w('- Id %d: suffix `%s` (kind %s) -> `%s` (kind %s in our parser). Patching it removes'
              % (idx, a, 'known' if a.lower() in known else 'None', b, 'known' if b.lower() in known else 'None'))
            w('  the base effect from every item with enchant %d; nothing replaces it until MAW\'s effect is coded.'
              % idx)
w('- MAW suffixes 74-80 known to our parser: %s.' % (', '.join(c(real_m[i - 1][1], 1) for i in range(74, len(real_m) + 1)
                                                      if c(real_m[i - 1][1], 1).lower() in known) or 'none'))
w('')

open(OUT, 'w').write('\n'.join(out) + '\n')
print('written', OUT, len(out), 'lines')
print('groups', [(g, sorted(ks)) for g, ks in GROUPS])
print('raw_only', raw_only)
