"""The engine tables as a MAW game reads them: engine/data_tables/<table> with the MAW ruleset's contributions applied
in ruleset.yml's order (override, append, appendColumns, replace), as GameDataLoader::applyActiveRulesetTable and
ContentTableComposer do. Shared by the MAW guide's modules."""

from functools import lru_cache
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / 'assets_dev'
TABLES = ASSETS / 'engine' / 'data_tables'
WORLDS = ASSETS / 'worlds'
MAW = ASSETS / 'engine' / 'rulesets' / 'maw'
ROW_KEY = -1  # keyColumn "row": the row's zero-based number in the file


def decode(data: bytes) -> str:
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('cp1252', errors='replace')


def parse_tab_separated(text: str) -> list[list[str]]:
    """Engine::TextTable::parseTabSeparated: tabs split cells, a leading quote closed before the next tab opens a
    quoted cell (which may span lines), CRs are dropped and an empty line is a row of one empty cell."""
    rows, row, cell = [], [], []
    quoted = False
    index, size = 0, len(text)

    def closes_before_tab(start: int) -> bool:
        i = start
        while i < size:
            if text[i] == '\t':
                return False
            if text[i] == '"':
                if i + 1 < size and text[i + 1] == '"':
                    i += 2
                    continue
                return True
            i += 1
        return False

    while index < size:
        ch = text[index]
        if ch == '"':
            if quoted and index + 1 < size and text[index + 1] == '"':
                cell.append('"')
                index += 1
            elif quoted:
                quoted = False
            elif not cell and closes_before_tab(index + 1):
                quoted = True
            else:
                cell.append(ch)
        elif ch == '\r':
            pass
        elif ch == '\t' and not quoted:
            row.append(''.join(cell))
            cell = []
        elif ch == '\n' and not quoted:
            row.append(''.join(cell))
            rows.append(row)
            row, cell = [], []
        else:
            cell.append(ch)
        index += 1
    if cell or row:
        row.append(''.join(cell))
        rows.append(row)
    return rows


def read_rows(path: Path) -> list[list[str]]:
    return parse_tab_separated(decode(path.read_bytes()))


def cell(row: list[str], index: int) -> str:
    return row[index].strip() if 0 <= index < len(row) else ''


@lru_cache(maxsize=None)
def ruleset() -> dict:
    return yaml.safe_load((MAW / 'ruleset.yml').read_text())


def _key_column(value) -> int:
    return ROW_KEY if value == 'row' else int(value)


def _apply_overrides(rows: list[list[str]], patch: list[list[str]], key_column: int, header_row: int) -> None:
    if not patch or [cell(patch[0], i) for i in range(3)] != ['key', 'column', 'value']:
        raise ValueError('override patch must start with a key, column, value header')
    by_key, repeated = {}, set()
    if key_column != ROW_KEY:
        for index, row in enumerate(rows):
            key = cell(row, key_column)
            if index != header_row and key:
                if key in by_key:
                    repeated.add(key)
                by_key.setdefault(key, index)
    header = rows[header_row] if header_row < len(rows) else []
    columns = {}
    for index in range(len(header)):
        name = cell(header, index)
        if name:
            columns[name] = -1 if name in columns else index
    for line in patch[1:]:
        key, column = cell(line, 0), cell(line, 1)
        if not key and not column:
            continue
        if key_column == ROW_KEY:
            row_index = int(key)
            while row_index >= len(rows):
                rows.append([])
        else:
            if key not in by_key or key in repeated:
                raise ValueError(f'override key {key!r} must match exactly one row')
            row_index = by_key[key]
        column_index = int(column[1:]) if column.startswith('#') else columns.get(column, -1)
        if column_index < 0 or column_index == key_column:
            raise ValueError(f'override column {column!r} is unknown')
        row = rows[row_index]
        row.extend([''] * (column_index + 1 - len(row)))
        row[column_index] = line[2] if len(line) > 2 else ''


def _append_columns(rows: list[list[str]], added: list[list[str]], key_column: int, header_row: int) -> None:
    names = added[0]
    width = len(rows[header_row])
    by_key = {cell(row, key_column): row for row in added[1:]}

    def values(source):
        return [cell(source, i) if source is not None else '' for i in range(len(names)) if i != key_column]

    for index, row in enumerate(rows):
        source = names if index == header_row else by_key.get(cell(row, key_column))
        del row[width:]
        row.extend([''] * (width - len(row)))
        row.extend(values(source))


@lru_cache(maxsize=None)
def _engine_table(name: str) -> tuple:
    rows = read_rows(TABLES / name)
    for entry in ruleset().get('tables') or []:
        if entry.get('world') or entry['table'] != name:
            continue
        patch = read_rows(MAW / entry['path'])
        if entry['mode'] == 'replace':
            rows = patch
            continue
        key_column = _key_column(entry['keyColumn'])
        header_row = int(entry.get('headerRow', 0))
        _apply_overrides(rows, patch, key_column, header_row)
        if entry.get('append'):
            rows.extend(read_rows(MAW / entry['append']))
        if entry.get('appendColumns'):
            _append_columns(rows, read_rows(MAW / entry['appendColumns']), key_column, header_row)
    return tuple(tuple(row) for row in rows)


def table(name: str) -> list[list[str]]:
    """The rows of engine/data_tables/<name> under MAW (a fresh copy)."""
    return [list(row) for row in _engine_table(name)]


def as_int(text: str, default: int = 0) -> int:
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return default


def numbered_rows(name: str) -> list[list[str]]:
    """The rows whose first cell is a number (the data rows of the MM tables), cells trimmed."""
    return [[c.strip() for c in row] for row in table(name) if row and row[0].strip().isdigit()]


# Continent ids as bolster_maps.txt and TrainerDirectory name them.
CONTINENTS = {1: 'Jadame', 2: 'Antagarich', 3: 'Enroth', 5: 'Chedian'}


@lru_cache(maxsize=None)
def maps() -> dict[int, dict]:
    """map_stats.txt rows under MAW by id: {name, file, continent}."""
    continents = {int(row[0]): as_int(row[2]) for row in numbered_rows('bolster_maps.txt') if len(row) > 2}
    result = {}
    for row in numbered_rows('map_stats.txt'):
        if len(row) > 2 and row[2]:
            map_id = int(row[0])
            result[map_id] = {'id': map_id, 'name': row[1], 'file': row[2].lower(),
                              'continent': continents.get(map_id, 0)}
    return result


@lru_cache(maxsize=None)
def houses() -> dict[int, dict]:
    """house_data.txt rows under MAW by id: {type, map (map id), name}."""
    result = {}
    for row in numbered_rows('house_data.txt'):
        row += [''] * (6 - len(row))
        result[int(row[0])] = {'id': int(row[0]), 'type': row[2], 'map': as_int(row[3]), 'name': row[5]}
    return result
