#!/usr/bin/env python3
"""Localization tool (devdocs/LOCALIZATION.md): extract the game's English texts, update the languages' .po files,
report and check them, and import existing translations. Run by hand before a release.

  extract                 write assets_dev/languages/templates/<domain>.pot from every text source
  update [lang ...]       merge the templates into languages/<lang>/text/<domain>.po (new, changed, removed texts)
  report [lang ...]       translated, fuzzy and missing counts per area; --list prints the missing entries
  check [lang ...]        placeholders and codes, characters the fonts lack, joined Lua sentences, C++ literals
                          without tr(); --charset FILE writes the characters a language uses (for font subsetting)
  import tsv FILE --lang ID [--context CTX]     English<TAB>translation pairs (PR #25's catalogue)
  import pack DIR --lang ID [--base REV]        translated copies of the game's files (the Chinese pack)
  import mmmerge DIR --lang ID [--audio] [--videos]
                          an MMMerge localization (its "Text localization" tables, *.T.lod text tables and map
                          strings; --audio copies its *.D.lod sounds over ours, --videos transcodes its cutscenes)

The English text is the key. A domain is "engine" (C++, menus, shared tables, rulesets, global events) or a world id
(its map events and presentation); the game reads text/engine*.po for every world and text/<world>.po for that world.
Python 3 with PyYAML, like the other tools.
"""

import argparse
import codecs
import collections
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets_dev"
ENGINE = ASSETS / "engine"
WORLDS = ASSETS / "worlds"
LANGUAGES = ASSETS / "languages"
TEMPLATES = LANGUAGES / "templates"
PENDING_DOMAIN = "engine-pending"
# The translator comment of a translation a model wrote: counted apart by `report` until a person reviews it.
MACHINE_MARK = "machine translation"
# Tables whose short texts are a language's established terms (classes, skills, spells, stats, the original
# interface): `glossary` collects them so new translations use the same words.
GLOSSARY_SOURCES = ("english/Global.txt", "english/class.txt", "english/skill_des.txt", "english/spells.txt",
                    "english/stats.txt", "spells.txt")

# Player-visible columns of the data tables: file below data_tables (or a ruleset's tables), header rows to skip, and
# column indexes. Identifier columns (skill groups, equip stats, internal names) and developer notes stay out.
TABLE_TEXT_COLUMNS = {
    "arcomage_cards.txt": (1, [1]),
    "continent_settings.txt": (1, [1]),
    "decoration_data.txt": (2, [2]),
    "house_animations.txt": (1, [2]),
    "house_data.txt": (2, [5, 6, 7, 23]),
    "items.txt": (2, [2, 10, 16]),
    "map_stats.txt": (3, [1]),
    "monster_data.txt": (2, [1, 17, 21]),   # name; attack 1 and 2 types (Phys, Ener ...), shown by Identify Monster
    "news_topics_profession.txt": (1, [1]),
    "npc.txt": (2, [1]),
    "npc_greet.txt": (1, [1, 2]),
    "npc_names.txt": (1, [0, 1]),
    "npc_news.txt": (1, [1]),
    "npc_professions.txt": (1, [1]),
    "npc_topic.txt": (1, [1]),
    "npc_topic_text.txt": (1, [1]),
    "roster.txt": (2, [1]),
    "special_item_enchants.txt": (3, [1, 16]),
    "spells.txt": (2, [2, 4, 5, 6, 7, 8, 9]),
    "standard_item_enchants.txt": (3, [1]),
    "town_portal_switch.txt": (2, [13]),
    "english/Global.txt": (1, [1]),
    "english/autonote.txt": (1, [1]),
    "english/award_display_aliases.txt": (1, [3]),
    "english/awards.txt": (1, [1]),
    "english/class.txt": (1, [0, 1]),
    "english/history.txt": (1, [1, 3]),
    "english/merchant.txt": (1, [1, 2, 3, 4]),
    "english/mm7_history.txt": (1, [1, 3]),
    "english/place_mon.txt": (1, [1]),
    "english/potion.txt": (1, [1, 2, 3]),
    "english/potnotes.txt": (1, [1, 2, 3]),
    "english/quests.txt": (1, [1]),
    "english/scroll.txt": (1, [1, 3]),
    "english/skill_des.txt": (1, [1, 2, 3, 4, 5]),
    "english/spells.txt": (2, [2, 4, 5, 6, 7, 8, 9]),
    "english/stats.txt": (1, [1]),
    "english/trans.txt": (1, [1]),
}
# The same columns by header name, for ruleset patch files (key, column, value).
PATCH_TEXT_COLUMNS = {
    "items": {"Name", "Not identified name", "Notes"},
    "spells": {"Fire Spells", "Name", "Short Name", "Spell Description", "Normal", "Expert", "Master", "Grand Master"},
    "skill_des": {"Description", "Normal", "Expert", "Master", "GrandMaster"},
    "class": {"Class name", "Class description"},
    "npc_topic": {"Topic"},
    "npc_topic_text": {"Text"},
    "special_item_enchants": {"Name Add", "Description fo special Bonuses and values"},
    "map_stats": {"Name"},
    "monster_data": {"Name"},
    "house_data": {"Name", "Proprieter Name", "Title", "Text"},
    "quests": {"Quest Note Text"},
    "place_mon": {"Name"},
    "character_data": {"Name", "Description"},
}
# Lua calls whose string arguments are shown. A literal joined with .. is a fragment: `check` lists those.
LUA_TEXT_CALLS = r"(?:evt\.(?:StatusText|SimpleMessage|SetMessage|Question|AskQuestion|AskQuestionWithAnswerSteps|" \
                 r"AskChoiceWithAnswerSteps)|\btr|\bsay)"
LUA_REGISTER_CALLS = r"\b(?:Register|register)(?:Global)?(?:NoOp)?Event"
# YAML keys whose string values are player text (world.yml, ruleset.yml, cinematics, certificates, data YAML).
YAML_TEXT_KEYS = {"name", "desc", "description", "title", "text", "label", "summary", "headline", "body", "subtitle",
                  "caption", "hint", "message", "credits", "tooltip", "subtitles", "lines", "english_name", "topic"}
CPP_CALL = re.compile(r"(?<![\w.:>])(?:Engine::)?(trn|trcNoop|trc|trNoop|tr)\s*\(")
CPP_SOURCE_ROOTS = ["game", "engine"]


# ----------------------------------------------------------------------------------------------------------------------
# Text decoding: the original tables hold Windows-1252 bytes inside otherwise UTF-8 text (engine/Utf8Text.h).

def _cp1252_fallback(error):
    byte = error.object[error.start]
    try:
        character = bytes([byte]).decode("cp1252")
    except UnicodeDecodeError:
        character = chr(byte)
    return character, error.start + 1


codecs.register_error("oy_cp1252", _cp1252_fallback)


def decode(data):
    return data.decode("utf-8", errors="oy_cp1252")


def read_text(path):
    return decode(Path(path).read_bytes())


def relative(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


# ----------------------------------------------------------------------------------------------------------------------
# Tokens a translation must keep (engine/TextCatalog.cpp translationMismatch).

TOKEN = re.compile(r"\{[A-Za-z_][^{}\n]{0,62}\}"
                   r"|%%|%[-+#0]*\d*(?:\.\d+)?(?:hh|h|ll|l|z)?[diouxXfFeEgGsc]"
                   r"|%\d\d"
                   r"|\f\d{5}")


def text_tokens(text):
    placeholders, printf, story, colors = [], [], [], []
    for match in TOKEN.finditer(text):
        token = match.group(0)
        if token.startswith("{"):
            placeholders.append(token)
        elif token.startswith("\f"):
            colors.append(token)
        elif re.fullmatch(r"%\d\d", token):
            story.append(token)
        else:
            printf.append(token)
    return sorted(placeholders), printf, sorted(story), sorted(colors)


def mismatch(english, translation):
    want, have = text_tokens(english), text_tokens(translation)
    names = ("placeholders", "printf values", "story codes", "colour codes")
    problems = [f"{name} {' '.join(w) or 'none'} became {' '.join(h) or 'none'}"
                for name, w, h in zip(names, want, have) if w != h]
    return "; ".join(problems)


DECIMAL = re.compile(r"(?<![\d.,])(\d+)\.(\d+)(?![\d.,])")


def decimal_commas(english, translation):
    """The English decimals ("1.5") a translation writes with a comma ("1,5"): every language keeps the point, as the
    numbers the game formats do."""
    return [f"{whole}.{part}" for whole, part in DECIMAL.findall(english)
            if re.search(rf"(?<![\d.,]){whole},{part}(?![\d.,])", translation)]


IDENTIFIER = re.compile(r"\S*(?:[a-z][A-Z]|[A-Za-z]\d|\d[A-Za-z]|_[A-Z])\S*")


def is_text(value):
    """Worth translating: holds a letter outside its placeholders and codes, and is not one identifier-like word
    ("SunButton4", "DB_CeilingLeft": names of objects that some scripts use as event titles)."""
    if not isinstance(value, str):
        return False
    stripped = TOKEN.sub("", value)
    if not any(character.isalpha() for character in stripped):
        return False
    return not IDENTIFIER.fullmatch(value.strip())


# ----------------------------------------------------------------------------------------------------------------------
# .po files

class Entry:
    def __init__(self, msgid, context="", plural=None):
        self.context = context
        self.msgid = msgid
        self.plural = plural
        self.msgstr = [""] if plural is None else ["", ""]
        self.flags = set()
        self.references = []
        self.comments = []      # "#." extracted comments
        self.translator = []    # "# " translator comments
        self.previous = None    # "#| msgid" of a fuzzy match
        self.obsolete = False

    @property
    def key(self):
        return (self.context, self.msgid)

    def translated(self):
        return any(self.msgstr) and "fuzzy" not in self.flags


def _po_quote(text):
    escaped = (text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\t", "\\t").replace("\r", "\\r")
               .replace("\f", "\\f"))
    lines = escaped.split("\n")
    pieces = [line + "\\n" for line in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    if len(pieces) <= 1 and len(escaped) < 70:
        return "\"" + (pieces[0] if pieces else "") + "\""
    return "\"\"\n" + "\n".join("\"" + piece + "\"" for piece in pieces)


_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "f": "\f", "v": "\v", "a": "\a", "b": "\b", "\\": "\\", "\"": "\"",
            "'": "'", "?": "?"}


def _po_unquote(text):
    text = text.strip()
    if len(text) < 2 or text[0] != "\"" or text[-1] != "\"":
        raise ValueError(f"malformed string {text[:40]}")
    body, result, index = text[1:-1], [], 0
    while index < len(body):
        character = body[index]
        if character == "\\" and index + 1 < len(body):
            escape = body[index + 1]
            if escape in _ESCAPES:
                result.append(_ESCAPES[escape])
                index += 2
                continue
            octal = re.match(r"[0-7]{1,3}", body[index + 1:])
            if octal:
                result.append(chr(int(octal.group(0), 8)))
                index += 1 + len(octal.group(0))
                continue
        result.append(character)
        index += 1
    return "".join(result)


def parse_po(text):
    """(header text, entries); obsolete (#~) entries come back with obsolete set."""
    entries, header = [], ""
    entry, field, index = None, None, 0
    pending = Entry("")

    def finish():
        nonlocal entry, pending, header
        if entry is not None:
            if entry.msgid == "" and entry.context == "" and not entry.obsolete:
                header = entry.msgstr[0]
            else:
                entries.append(entry)
        entry, pending = None, Entry("")

    for raw in text.splitlines():
        line = raw.strip()
        obsolete = line.startswith("#~")
        if obsolete:
            line = line[2:].strip()
            if line.startswith("|"):
                continue
        if not line:
            if entry is not None and field and field.startswith("msgstr"):
                finish()
            continue
        if line.startswith("#") and not obsolete:
            if entry is not None and field and field.startswith("msgstr"):
                finish()
            target = pending if entry is None else entry
            if line.startswith("#:"):
                target.references.extend(line[2:].split())
            elif line.startswith("#,"):
                target.flags.update(flag.strip() for flag in line[2:].split(",") if flag.strip())
            elif line.startswith("#."):
                target.comments.append(line[2:].strip())
            elif line.startswith("#|"):
                match = re.match(r"#\|\s*msgid\s+(\".*\")", line)
                if match:
                    target.previous = _po_unquote(match.group(1))
            else:
                target.translator.append(line[1:].strip())
            continue
        if line.startswith("\""):
            value = _po_unquote(line)
            if field == "msgctxt":
                entry.context += value
            elif field == "msgid":
                entry.msgid += value
            elif field == "msgid_plural":
                entry.plural += value
            elif field and field.startswith("msgstr"):
                entry.msgstr[index] += value
            continue
        keyword, _, value = line.partition(" ")
        if keyword in ("msgctxt", "msgid") and entry is not None and field and field.startswith("msgstr"):
            finish()
        if entry is None:
            entry = pending
            entry.msgstr = []
            entry.obsolete = obsolete
        if keyword == "msgctxt":
            entry.context, field = _po_unquote(value), "msgctxt"
        elif keyword == "msgid":
            entry.msgid, field = _po_unquote(value), "msgid"
        elif keyword == "msgid_plural":
            entry.plural, field = _po_unquote(value), "msgid_plural"
        elif keyword == "msgstr":
            entry.msgstr, index, field = [_po_unquote(value)], 0, "msgstr"
        elif keyword.startswith("msgstr["):
            index = int(keyword[7:-1])
            while len(entry.msgstr) <= index:
                entry.msgstr.append("")
            entry.msgstr[index] = _po_unquote(value)
            field = "msgstr"
        else:
            raise ValueError(f"unknown keyword {keyword}")
    finish()
    return header, entries


def write_po(path, header, entries):
    lines = ["msgid \"\"", "msgstr " + _po_quote(header), ""]
    for entry in entries:
        prefix = "#~ " if entry.obsolete else ""
        for comment in entry.translator:
            lines.append(f"# {comment}".rstrip())
        for comment in entry.comments:
            lines.append(f"#. {comment}")
        if entry.references and not entry.obsolete:
            references = sorted(dict.fromkeys(entry.references))
            for start in range(0, len(references), 3):
                lines.append("#: " + " ".join(references[start:start + 3]))
        if entry.flags:
            lines.append("#, " + ", ".join(sorted(entry.flags)))
        if entry.previous is not None and not entry.obsolete:
            lines.append("#| msgid " + _po_quote(entry.previous).replace("\n", "\n#| "))
        block = []
        if entry.context:
            block.append("msgctxt " + _po_quote(entry.context))
        block.append("msgid " + _po_quote(entry.msgid))
        if entry.plural is not None:
            block.append("msgid_plural " + _po_quote(entry.plural))
            for form, value in enumerate(entry.msgstr or ["", ""]):
                block.append(f"msgstr[{form}] " + _po_quote(value))
        else:
            block.append("msgstr " + _po_quote(entry.msgstr[0] if entry.msgstr else ""))
        for statement in block:
            lines.extend(prefix + piece for piece in statement.split("\n"))
        lines.append("")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def template_header():
    return ("Project-Id-Version: OpenYAMM\nMIME-Version: 1.0\nContent-Type: text/plain; charset=UTF-8\n"
            "Content-Transfer-Encoding: 8bit\n")


# ----------------------------------------------------------------------------------------------------------------------
# Tab-separated tables, read by the engine's rules (engine/TextTable.cpp): a leading quote opens a quoted cell only when
# its closing quote comes before the next tab.

def parse_table(text):
    rows, row, cell, quoted, index, line, row_line = [], [], [], False, 0, 1, 1

    def closing(begin):
        position = begin
        while position < len(text):
            if text[position] == "\t":
                return False
            if text[position] == "\"":
                if position + 1 < len(text) and text[position + 1] == "\"":
                    position += 2
                    continue
                return True
            position += 1
        return False

    while index < len(text):
        character = text[index]
        if character == "\"":
            if quoted and index + 1 < len(text) and text[index + 1] == "\"":
                cell.append("\"")
                index += 2
                continue
            if quoted:
                quoted = False
                index += 1
                continue
            if not cell and closing(index + 1):
                quoted = True
                index += 1
                continue
        if not quoted and character == "\t":
            row.append("".join(cell))
            cell = []
            index += 1
            continue
        if not quoted and character in "\r\n":
            if character == "\r" and index + 1 < len(text) and text[index + 1] == "\n":
                index += 1
            row.append("".join(cell))
            rows.append((row_line, row))
            row, cell = [], []
            index += 1
            line += 1
            row_line = line
            continue
        if character == "\n":
            line += 1
        cell.append(character)
        index += 1
    if cell or row:
        row.append("".join(cell))
        rows.append((row_line, row))
    return rows


# ----------------------------------------------------------------------------------------------------------------------
# Extraction

class Template:
    def __init__(self):
        self.domains = collections.defaultdict(dict)   # domain -> {(ctx, msgid): Entry}
        self.joined = []                                # (reference, literal) of Lua fragments

    def add(self, domain, msgid, reference, context="", plural=None, comment=None, ordered=False):
        msgid = msgid.replace("\r\n", "\n").replace("\r", "\n")
        # A pattern of placeholders only ("{day} {month} {year}") is text when the code asks for it: languages order
        # its parts and add their own words.
        if not is_text(msgid) and not (ordered and len(re.findall(r"\{\w+\}", msgid)) >= 2):
            return
        entries = self.domains[domain]
        entry = entries.get((context, msgid))
        if entry is None:
            entry = entries[(context, msgid)] = Entry(msgid, context, plural)
        entry.references.append(reference)
        if comment and comment not in entry.comments:
            entry.comments.append(comment)


def domain_of(path):
    parts = Path(path).resolve().relative_to(ROOT).parts
    if len(parts) > 2 and parts[0] == "assets_dev" and parts[1] == "worlds":
        return parts[2]
    return "engine"


def _cpp_literal_sequence(text, index):
    """Adjacent C++ string literals from index: (value, end index) or (None, index)."""
    pieces, position = [], index
    while True:
        while position < len(text) and text[position] in " \t\r\n":
            position += 1
        if position >= len(text) or text[position] != "\"":
            break
        position += 1
        piece = []
        while position < len(text) and text[position] != "\"":
            if text[position] == "\\" and position + 1 < len(text):
                escape = text[position + 1]
                if escape == "x":
                    digits = re.match(r"[0-9a-fA-F]+", text[position + 2:]).group(0)
                    piece.append(chr(int(digits, 16)))
                    position += 2 + len(digits)
                    continue
                piece.append(_ESCAPES.get(escape, escape))
                position += 2
                continue
            piece.append(text[position])
            position += 1
        pieces.append("".join(piece))
        position += 1
    if not pieces:
        return None, index
    # UTF-8 bytes written as \x escapes in the source become their characters.
    value = "".join(pieces)
    try:
        value = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return value, position


def _cpp_first_argument_literals(text, start):
    """The string literals of a call's first argument (up to its top-level comma or closing parenthesis)."""
    literals, depth, position = [], 0, start
    while position < len(text):
        character = text[position]
        if character == "\"":
            value, position = _cpp_literal_sequence(text, position)
            if value is not None:
                literals.append(value)
            continue
        if character in "([{":
            depth += 1
        elif character in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif character == "," and depth == 0:
            break
        position += 1
    return literals


def extract_cpp(template):
    for root in CPP_SOURCE_ROOTS:
        for path in sorted((ROOT / root).rglob("*")):
            if path.suffix not in (".cpp", ".h") or not path.is_file():
                continue
            text = read_text(path)
            if "tr" not in text:
                continue
            for match in CPP_CALL.finditer(text):
                kind, position = match.group(1), match.end()
                line = text.count("\n", 0, match.start()) + 1
                reference = f"{relative(path)}:{line}"
                first, position = _cpp_literal_sequence(text, position)
                if first is None:
                    if kind == "tr":
                        # tr(condition ? "One text" : "Another"): every literal of the first argument.
                        for literal in _cpp_first_argument_literals(text, match.end()):
                            template.add("engine", literal, reference)
                    continue
                if kind in ("tr", "trNoop"):
                    template.add("engine", first, reference, ordered=True)
                    continue
                comma = re.match(r"\s*,", text[position:])
                if not comma:
                    continue
                second, _ = _cpp_literal_sequence(text, position + comma.end())
                if second is None:
                    continue
                if kind in ("trc", "trcNoop"):
                    template.add("engine", second, reference, context=first, ordered=True)
                else:
                    template.add("engine", first, reference, plural=second, ordered=True)


LUA_LITERAL = re.compile(r"--\[\[.*?\]\]|--[^\n]*|\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'", re.S)


def _lua_unescape(text):
    return re.sub(r"\\(.)", lambda match: _ESCAPES.get(match.group(1), match.group(1)), text)


def lua_literals(text):
    """(start, end, value) of each string literal outside comments."""
    for match in LUA_LITERAL.finditer(text):
        if match.group(0).startswith("--"):
            continue
        raw = match.group(1) if match.group(1) is not None else match.group(2)
        yield match.start(), match.end(), _lua_unescape(raw)


def _call_end(text, start):
    """Index after the closing parenthesis of the call whose '(' is at start (strings and comments skipped)."""
    depth, position = 0, start
    while position < len(text):
        character = text[position]
        if character in "\"'":
            match = LUA_LITERAL.match(text, position)
            position = match.end() if match else position + 1
            continue
        if text.startswith("--", position):
            end = text.find("\n", position)
            position = len(text) if end < 0 else end
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return position + 1
        position += 1
    return len(text)


def extract_lua_file(template, path, domain):
    text = read_text(path)
    literals = list(lua_literals(text))
    shown = set()

    for match in re.finditer(LUA_TEXT_CALLS + r"\s*\(", text):
        end = _call_end(text, match.end() - 1)
        shown.update(index for index, (start, _, _) in enumerate(literals) if match.end() <= start < end)
    for match in re.finditer(LUA_REGISTER_CALLS + r"\s*\(\s*[\w.]+\s*,\s*", text):
        shown.update(index for index, (start, _, _) in enumerate(literals) if start == match.end())
    # The title after a handler (`end, "Title"`): an event's, which the indoor hover shows; a timer's, a load
    # hook's or a chest hook's title only names it in logs.
    registrations = [(match.end(), _call_end(text, match.end() - 1), match.group(1)) for match in
                     re.finditer(r"\b(Register\w*)\s*\(", text)]
    for match in re.finditer(r"\bend\s*,\s*(?=[\"'])", text):
        enclosing = [(begin, name) for begin, end, name in registrations if begin <= match.start() < end]
        if enclosing and re.search(r"Timer|OnLoad|Hook", max(enclosing)[1]):
            continue
        shown.update(index for index, (start, _, _) in enumerate(literals) if start == match.end())
    named_text = r"\b(?:targetName|title|hint|destinationName|completionText|effect)\s*=\s*(?=[\"'])"
    for match in re.finditer(named_text, text):
        shown.update(index for index, (start, _, _) in enumerate(literals) if start == match.end())

    # Literals joined only with each other ("A long " .. "sentence") are one text: the game receives it whole.
    chains, done = [], set()
    for index in sorted(shown):
        if index in done:
            continue
        chain = [index]
        while chain[-1] + 1 < len(literals) and re.fullmatch(
                r"\s*\.\.\s*", text[literals[chain[-1]][1]:literals[chain[-1] + 1][0]]):
            chain.append(chain[-1] + 1)
        done.update(chain)
        chains.append(chain)

    for chain in chains:
        start, end = literals[chain[0]][0], literals[chain[-1]][1]
        value = "".join(literals[index][2] for index in chain)
        line = text.count("\n", 0, start) + 1
        reference = f"{relative(path)}:{line}"
        before, after = text[max(0, start - 4):start], text[end:end + 4]
        if before.rstrip().endswith("..") or after.lstrip().startswith(".."):
            for index in chain:
                if is_text(literals[index][2]):
                    template.joined.append((f"{relative(path)}:{text.count(chr(10), 0, literals[index][0]) + 1}",
                                            literals[index][2]))
            continue
        template.add(domain, value, reference)


def extract_lua(template):
    sources = [(path, "engine") for folder in (ENGINE / "events", ENGINE / "scripts", ENGINE / "behaviors")
               for path in folder.rglob("*.lua")]
    sources += [(path, "engine") for path in (ENGINE / "rulesets").rglob("*.lua")]
    for world in sorted(WORLDS.iterdir()):
        if world.is_dir() and (world / "events").is_dir():
            sources += [(path, world.name) for path in (world / "events").rglob("*.lua")]
    for path, domain in sorted(sources):
        extract_lua_file(template, path, domain)


# Tables whose records continue on lines without an id, joined to the record's text with a line break as
# NpcDialogTable does: the topic text ("text": only the line's first cell) and the greetings ("cells": the line's
# first cell ends the record's last cell, its others follow).
CONTINUATION_TABLES = {"npc_topic_text.txt": "text", "npc_greet.txt": "cells"}


def merge_continuations(name, rows):
    """The records of a table as the game reads them: continuation lines joined to their record."""
    kind = CONTINUATION_TABLES.get(Path(name).name)
    if kind is None:
        return rows
    merged, record = [], None
    for line, row in rows:
        if row and re.fullmatch(r"\s*\+?\d+", row[0]):
            record = (line, list(row))
            merged.append(record)
        elif record is None:
            merged.append((line, row))
        elif row:
            cells = record[1]
            if kind == "text":
                if len(cells) < 2:
                    cells.append("")
                cells[1] = (cells[1] + "\n" if cells[1] else "") + row[0]
            else:
                cells[-1] = (cells[-1] + "\n" if cells[-1] else "") + row[0]
                cells.extend(row[1:])
    return merged


def extract_table(template, path, skip, columns, domain="engine"):
    rows = merge_continuations(path.name, parse_table(read_text(path)))
    for line, row in rows[skip:]:
        for column in columns:
            if column < len(row):
                value = row[column].strip("\r")
                if is_text(value) and not re.fullmatch(r"[\w.\-]*\d[\w.\-]*", value):
                    template.add(domain, value.strip(), f"{relative(path)}:{line}")


def extract_patch(template, path, table, domain="engine", positions=()):
    """A patch's text values: columns named in PATCH_TEXT_COLUMNS, and columns given by position (`#1`) that are
    among the patched table's text columns (`positions`)."""
    names = PATCH_TEXT_COLUMNS.get(table, set())
    if not names and not positions:
        return
    rows = parse_table(read_text(path))
    if not rows or rows[0][1][:3] != ["key", "column", "value"]:
        return
    for line, row in rows[1:]:
        if len(row) < 3:
            continue
        position = re.fullmatch(r"#(\d+)", row[1])
        if row[1] in names or (position and int(position.group(1)) in positions):
            template.add(domain, row[2].strip(), f"{relative(path)}:{line}")


def ruleset_table_files(ruleset):
    """The table each file of a ruleset patches or appends rows to, as its ruleset.yml declares: {path: (table,
    appended)}. A file's name does not tell (`quests_maw.txt` holds rows of `english/quests.txt`)."""
    manifest = ruleset / "ruleset.yml"
    declared = {}
    if manifest.is_file():
        for entry in (yaml.safe_load(read_text(manifest)) or {}).get("tables") or []:
            for key in ("path", "append"):
                if entry.get(key) and entry.get("table"):
                    declared[ruleset / entry[key]] = (entry["table"], key == "append")
    return declared


# A world's own tables (worlds/<id>/data_tables), by header name: the row holding these names is the header.
WORLD_TABLE_TEXT_COLUMNS = {
    "items.txt": {"Name", "Not identified name", "Notes"},
    "monster_data.txt": {"Name", "Type"},
    "decoration_data.txt": {"Hint"},
    "readable_items.txt": {"message text", "Item Name"},
    "english/quests_overlay.txt": {"Quest Note Text"},
    "hirelings.txt": {"name", "attack1_missile", "attack2_missile"},
    "transport_routes.txt": {"DestinationName", "DockName"},
    "service_venues.txt": {"name", "location"},
}


def extract_world_tables(template):
    for world in sorted(WORLDS.iterdir()):
        folder = world / "data_tables"
        if not folder.is_dir():
            continue
        for name, wanted in WORLD_TABLE_TEXT_COLUMNS.items():
            path = folder / name
            if not path.is_file():
                continue
            rows = parse_table(read_text(path))
            header = next((index for index, (_, row) in enumerate(rows[:4])
                           if wanted & {cell.strip() for cell in row}), None)
            if header is None:
                continue
            columns = [index for index, cell in enumerate(rows[header][1]) if cell.strip() in wanted]
            for line, row in rows[header + 1:]:
                for column in columns:
                    if column < len(row):
                        value = row[column].strip("\r")
                        if is_text(value) and not re.fullmatch(r"[\w.\-]*\d[\w.\-]*", value):
                            template.add(world.name, value.strip(), f"{relative(path)}:{line}")


def extract_tables(template):
    extract_world_tables(template)
    for name, (skip, columns) in TABLE_TEXT_COLUMNS.items():
        path = ENGINE / "data_tables" / name
        if path.is_file():
            extract_table(template, path, skip, columns)
    for ruleset in sorted((ENGINE / "rulesets").iterdir()):
        if not ruleset.is_dir():
            continue
        declared = ruleset_table_files(ruleset)
        for path in sorted(ruleset.rglob("*.txt")):
            stem = path.name
            base = re.sub(r"(_patch|_new|\.append|\.columns)?\.txt$", "", stem)
            table_name = ("english/" if "english" in path.parts else "") + base + ".txt"
            appended = False
            if path in declared:
                table_name, appended = declared[path]
                base = Path(table_name).stem
            # A patch (key, column, value rows) by its header, whatever its name: `items.txt` in a ruleset's
            # patches is one, and its column names are not text.
            header = read_text(path).split("\n", 1)[0].rstrip("\r").split("\t")[:3]
            skip, columns = TABLE_TEXT_COLUMNS.get(table_name, (0, []))
            if columns and header != ["key", "column", "value"]:
                # Appended rows come without the table's header lines.
                extract_table(template, path, 0 if appended else skip, columns)
            else:
                extract_patch(template, path, base, positions=columns)


def _walk_yaml(node, path, visit, key=None):
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            _walk_yaml(value_node, path + [key_node.value], visit, key_node.value)
    elif isinstance(node, yaml.SequenceNode):
        for index, item in enumerate(node.value):
            _walk_yaml(item, path + [index], visit, key)
    elif isinstance(node, yaml.ScalarNode):
        visit(path, key, node)


def compose_yaml(path):
    try:
        return yaml.compose(read_text(path))
    except yaml.YAMLError as error:
        print(f"warning: {relative(path)}: {error}", file=sys.stderr)
        return None


def extract_layouts(template):
    for root, domain in [(ENGINE / "ui", "engine")] + [(world / "ui", world.name) for world in sorted(WORLDS.iterdir())
                                                       if (world / "ui").is_dir()]:
        for path in sorted(root.rglob("*.yml")):
            if path.name == "settings_catalog.yml":
                continue
            node = compose_yaml(path)
            if node is None:
                continue

            def visit(keys, key, scalar):
                if len(keys) >= 2 and keys[-1] == "value" and keys[-2] == "text" and scalar.tag.endswith(":str"):
                    template.add(domain, scalar.value, f"{relative(path)}:{scalar.start_mark.line + 1}")
            _walk_yaml(node, [], visit)


def extract_settings(template):
    path = ENGINE / "ui/menu/settings_catalog.yml"
    node = compose_yaml(path)
    if node is None:
        return

    def visit(keys, key, scalar):
        reference = f"{relative(path)}:{scalar.start_mark.line + 1}"
        if keys and keys[0] in ("sections", "settings", "bindings") and key in ("name", "desc", "ruleset_desc", "unit",
                                                                           "group"):
            template.add("engine", scalar.value, reference)
        elif len(keys) == 5 and keys[0] == "settings" and keys[2] == "options" and keys[4] == 1:
            template.add("engine", scalar.value, reference)
    _walk_yaml(node, [], visit)


def extract_text_yaml(template, path, domain, every_string=False):
    node = compose_yaml(path)
    if node is None:
        return

    def visit(keys, key, scalar):
        if not scalar.tag.endswith(":str"):
            return
        if every_string or key in YAML_TEXT_KEYS:
            template.add(domain, scalar.value, f"{relative(path)}:{scalar.start_mark.line + 1}")
    _walk_yaml(node, [], visit)


def extract_yaml_values(template, path, domain, shown):
    """The string values of a YAML file for which shown(keys, key) holds (keys: the path above the value)."""
    node = compose_yaml(path)
    if node is None:
        return

    def visit(keys, key, scalar):
        if scalar.tag.endswith(":str") and shown([str(part) for part in keys], str(key)):
            template.add(domain, scalar.value, f"{relative(path)}:{scalar.start_mark.line + 1}")
    _walk_yaml(node, [], visit)


def extract_yaml(template):
    for ruleset in sorted((ENGINE / "rulesets").iterdir()):
        if (ruleset / "ruleset.yml").is_file():
            extract_text_yaml(template, ruleset / "ruleset.yml", "engine")
            # The ruleset's names for the game's skills (MAW: Learning is Ascension).
            extract_yaml_values(template, ruleset / "ruleset.yml", "engine",
                                lambda keys, key: keys[:1] == ["skillNames"])
        # MAW's legendary affix tooltips, and its dimension map affixes and quest speeches.
        if (ruleset / "data" / "items.yml").is_file():
            extract_yaml_values(template, ruleset / "data" / "items.yml", "engine",
                                lambda keys, key: keys[:1] == ["legendary_affixes"])
        if (ruleset / "data" / "dimension_maps.yml").is_file():
            extract_yaml_values(template, ruleset / "data" / "dimension_maps.yml", "engine",
                                lambda keys, key: key == "text" or key.startswith("text_"))
        texts = ruleset / "data" / "texts.yml"
        if texts.is_file():
            extract_text_yaml(template, texts, "engine", every_string=True)
    for name in ("character_selection.yml", "teacher_ledger.yml", "potion_effects.yml", "race_skills.yml"):
        if (ENGINE / "data_tables" / name).is_file():
            extract_text_yaml(template, ENGINE / "data_tables" / name, "engine")
    if (ENGINE / "ui/certificates.yml").is_file():
        extract_text_yaml(template, ENGINE / "ui/certificates.yml", "engine")
    for world in sorted(WORLDS.iterdir()):
        if not world.is_dir():
            continue
        if (world / "world.yml").is_file():
            extract_text_yaml(template, world / "world.yml", world.name)
        for path in sorted(world.rglob("*.cinematics.yml")):
            extract_text_yaml(template, path, world.name)


def extract_mm9_rude(template):
    """MM9's dialogue tables (worlds/mm9/dialogue/rude, read by game/mm9/Mm9RudeDialogue.cpp): NPC names, the top
    blurbs and every row's prompt and response."""
    import csv
    import io
    folder = WORLDS / "mm9" / "dialogue" / "rude"
    tables = []
    for path in sorted(folder.glob("*.rude")) if folder.is_dir() else []:
        rows = [(line, row) for line, row in enumerate(csv.reader(io.StringIO(read_text(path))), 1)
                if row and row[0].strip().isdigit()]
        tables.append((path, rows))
    # A text the party says (a prompt) that an NPC also says to the party (a response) gets a context of its own
    # where the party says it, so each can address the right side ("What are you talking about?").
    responses = {row[4] for path, rows in tables if path.name not in ("NPCNAME.rude", "TOPBLURB.rude")
                 for _, row in rows if len(row) > 4}
    for path, rows in tables:
        name = path.name
        columns = [1] if name == "NPCNAME.rude" else [2] if name == "TOPBLURB.rude" else [3, 4]
        for line, row in rows:
            for column in columns:
                if column < len(row) and is_text(row[column]):
                    context = "said by the party" if len(columns) == 2 and column == 3 and row[3] in responses else ""
                    template.add("mm9", row[column], f"{relative(path)}:{line}", context=context)


def build_template():
    template = Template()
    extract_cpp(template)
    extract_lua(template)
    extract_mm9_rude(template)
    extract_tables(template)
    extract_layouts(template)
    extract_settings(template)
    extract_yaml(template)
    # A text the shared file has is translated once: world files keep only their own texts.
    shared = {entry.msgid for entry in template.domains["engine"].values()}
    for domain, entries in template.domains.items():
        if domain != "engine":
            for key in [key for key, entry in entries.items() if entry.msgid in shared and not entry.context]:
                del entries[key]
    return template


def cmd_extract(arguments):
    template = build_template()
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    for domain, entries in sorted(template.domains.items()):
        ordered = sorted(entries.values(), key=lambda entry: (entry.references[0], entry.msgid))
        write_po(TEMPLATES / f"{domain}.pot", template_header(), ordered)
        print(f"{relative(TEMPLATES / (domain + '.pot'))}: {len(ordered)} texts")
    stale = [path for path in TEMPLATES.glob("*.pot") if path.stem not in template.domains]
    for path in stale:
        path.unlink()
    if template.joined:
        print(f"{len(template.joined)} Lua texts are joined with .. and cannot be translated; `check` lists them")


# ----------------------------------------------------------------------------------------------------------------------
# Languages

def language_ids(requested):
    if requested:
        return requested
    return sorted(path.name for path in LANGUAGES.iterdir()
                  if path.is_dir() and (path / "language.yml").is_file())


def load_language(language):
    """{domain: (header, [entries])} of a language's text/*.po files."""
    files = {}
    for path in sorted((LANGUAGES / language / "text").glob("*.po")):
        files[path.stem] = parse_po(read_text(path))
    return files


def load_templates():
    if not TEMPLATES.is_dir() or not any(TEMPLATES.glob("*.pot")):
        sys.exit("No templates: run `tools/l10n.py extract` first")
    return {path.stem: parse_po(read_text(path))[1] for path in sorted(TEMPLATES.glob("*.pot"))}


def default_header(language, old_header):
    """A file's own header, or a new one with the language's plural rule from its other files."""
    if old_header:
        return old_header
    plural = "nplurals=2; plural=(n != 1);"
    for path in sorted((LANGUAGES / language / "text").glob("*.po")):
        match = re.search(r"Plural-Forms:\s*([^\\\n\"]+)", read_text(path))
        if match:
            plural = match.group(1).strip()
            break
    return template_header() + f"Language: {language}\nPlural-Forms: {plural}\n"


def cmd_update(arguments):
    templates = load_templates()
    template_texts = {entry.msgid for entries in templates.values() for entry in entries}
    for language in language_ids(arguments.languages):
        files = load_language(language)
        # Every translation the language has, to fill texts that moved between files or arrived from an import.
        old_entries = [(domain, entry) for domain, (_, entries) in files.items() for entry in entries
                       if not entry.obsolete and any(entry.msgstr)]
        already_obsolete = [(domain, entry) for domain, (_, entries) in files.items() for entry in entries
                            if entry.obsolete and entry.msgid not in template_texts]
        by_key, by_text = {}, {}
        for domain, entry in old_entries:
            by_key.setdefault(entry.key, entry)
            by_text.setdefault(entry.msgid, entry)
        used = set()
        totals = collections.Counter()
        result = {}
        for domain, template_entries in templates.items():
            entries = []
            for template_entry in template_entries:
                entry = Entry(template_entry.msgid, template_entry.context, template_entry.plural)
                entry.references = list(template_entry.references)
                entry.comments = list(template_entry.comments)
                old = by_key.get(entry.key) or by_text.get(entry.msgid)
                if old is not None and (old.plural is None) == (entry.plural is None):
                    entry.msgstr = list(old.msgstr)
                    entry.flags = set(old.flags)
                    entry.translator = list(old.translator)
                    entry.previous = old.previous
                    used.add(id(old))
                    totals["kept"] += 1
                else:
                    totals["new"] += 1
                entries.append(entry)
            result[domain] = entries
        # The translator's own entries: a context override of a text the game still has stays in its file.
        for domain, entry in old_entries:
            if id(entry) not in used and entry.context and entry.msgid in template_texts and domain in result:
                result[domain].append(entry)
                used.add(id(entry))
        # A text whose English changed: the closest removed text's translation, marked fuzzy for review.
        removed = [(domain, entry) for domain, entry in old_entries
                   if id(entry) not in used and entry.msgid not in template_texts and domain != PENDING_DOMAIN]
        removed_texts = [entry.msgid for _, entry in removed]
        for entries in result.values():
            for entry in entries:
                if any(entry.msgstr) or not removed_texts:
                    continue
                close = difflib.get_close_matches(entry.msgid, removed_texts, n=1, cutoff=0.8)
                if close:
                    source = removed[removed_texts.index(close[0])][1]
                    if len(source.msgstr) == len(entry.msgstr):
                        entry.msgstr = list(source.msgstr)
                        entry.flags.add("fuzzy")
                        entry.previous = source.msgid
                        totals["fuzzy"] += 1
        # Translations of removed texts stay as obsolete entries of their file; imported translations of texts no
        # template has yet wait in engine-pending.po for the C++ they belong to.
        pending = [entry for domain, entry in old_entries
                   if domain == PENDING_DOMAIN and id(entry) not in used and entry.msgid not in template_texts]
        for domain, entry in removed:
            if id(entry) in used:
                continue
            entry.obsolete = True
            result.setdefault(domain, []).append(entry)
            totals["obsolete"] += 1
        for domain, entry in already_obsolete:
            result.setdefault(domain, []).append(entry)
        result[PENDING_DOMAIN] = pending
        text = LANGUAGES / language / "text"
        for domain, entries in result.items():
            path = text / f"{domain}.po"
            if entries or domain in templates:
                header = files.get(domain, ("", []))[0]
                write_po(path, default_header(language, header), entries)
            elif path.exists():
                path.unlink()
        print(f"{language}: {totals['kept']} kept, {totals['new']} new, {totals['fuzzy']} fuzzy from changed English, "
              f"{totals['obsolete']} newly obsolete, {len(pending)} waiting in {PENDING_DOMAIN}.po")


# ----------------------------------------------------------------------------------------------------------------------
# Report and check

def area_of(reference):
    path = reference.rsplit(":", 1)[0]
    parts = Path(path).parts
    if parts and parts[0] in CPP_SOURCE_ROOTS:
        return "C++"
    if path.endswith("settings_catalog.yml"):
        return "settings"
    if "/ui/" in path:
        return "menus and HUD"
    if "data_tables" in parts:
        return "table " + Path(path).name
    if "rulesets" in parts:
        return "ruleset " + parts[parts.index("rulesets") + 1]
    if "worlds" in parts:
        world = parts[parts.index("worlds") + 1]
        return f"{world} maps" if "maps" in parts else f"{world} other"
    if "events" in parts or "scripts" in parts:
        return "global events"
    return "other"


def cmd_report(arguments):
    templates = load_templates()
    for language in language_ids(arguments.languages):
        files = load_language(language)
        translated = {}
        for _, entries in files.values():
            for entry in entries:
                if not entry.obsolete:
                    translated.setdefault(entry.key, entry)
        areas = collections.defaultdict(collections.Counter)
        missing = []
        for entries in templates.values():
            for template_entry in entries:
                entry = translated.get(template_entry.key)
                area = area_of(template_entry.references[0]) if template_entry.references else "other"
                if entry is not None and entry.translated():
                    state = "translated"
                    if any(line.startswith(MACHINE_MARK) for line in entry.translator):
                        areas[area]["machine"] += 1
                elif entry is not None and any(entry.msgstr):
                    state = "fuzzy"
                else:
                    state = "missing"
                areas[area][state] += 1
                if state != "translated":
                    missing.append((area, state, template_entry))
        total = collections.Counter()
        for counts in areas.values():
            total.update(counts)
        machine = total.pop("machine", 0)
        count = sum(total.values())
        print(f"{language}: {total['translated']} of {count} translated "
              f"({100 * total['translated'] // max(count, 1)} %; {machine} of them machine translations to review), "
              f"{total['fuzzy']} fuzzy, {total['missing']} missing")
        for area, counts in sorted(areas.items(), key=lambda item: -sum(item[1].values())):
            size = sum(value for key, value in counts.items() if key != "machine")
            print(f"  {area:32} {counts['translated']:6} / {size:<6} {counts['fuzzy']:5} fuzzy")
        if arguments.list:
            for area, state, entry in sorted(missing, key=lambda item: (item[0], item[2].references)):
                first = entry.msgid.replace("\n", "\\n")
                print(f"  [{state}] {entry.references[0] if entry.references else '?'}: {first[:100]}")


def _ttf_characters(path):
    """The characters a TrueType or OpenType font maps (cmap formats 4 and 12)."""
    import struct
    data = Path(path).read_bytes()
    tables = struct.unpack(">H", data[4:6])[0]
    cmap = None
    for index in range(tables):
        tag, _, offset, _ = struct.unpack(">4sIII", data[12 + 16 * index:28 + 16 * index])
        if tag == b"cmap":
            cmap = offset
    if cmap is None:
        return set()
    characters = set()
    count = struct.unpack(">H", data[cmap + 2:cmap + 4])[0]
    for index in range(count):
        _, _, offset = struct.unpack(">HHI", data[cmap + 4 + 8 * index:cmap + 12 + 8 * index])
        table = cmap + offset
        form = struct.unpack(">H", data[table:table + 2])[0]
        if form == 4:
            segments = struct.unpack(">H", data[table + 6:table + 8])[0] // 2
            ends = struct.unpack(f">{segments}H", data[table + 14:table + 14 + 2 * segments])
            starts_at = table + 16 + 2 * segments
            starts = struct.unpack(f">{segments}H", data[starts_at:starts_at + 2 * segments])
            for start, end in zip(starts, ends):
                characters.update(range(start, min(end, 0xfffe) + 1))
        elif form == 12:
            groups = struct.unpack(">I", data[table + 12:table + 16])[0]
            for group in range(groups):
                start, end, _ = struct.unpack(">III", data[table + 16 + 12 * group:table + 28 + 12 * group])
                characters.update(range(start, end + 1))
    return characters


def font_coverage(language):
    """{face: set of characters it can draw} of the faces the language uses (its pack's descriptors over the game's)."""
    faces = {}
    for root in (ENGINE / "fonts/truetype", LANGUAGES / language / "engine/fonts/truetype"):
        for path in sorted(root.glob("*.yml")):
            faces[path.stem] = path
    coverage = {}
    for name, path in faces.items():
        try:
            descriptor = yaml.safe_load(read_text(path)) or {}
        except yaml.YAMLError:
            continue
        # A pack's descriptor may name a font file of the game's (as the game reads both through one folder).
        font = next((folder / str(descriptor.get("file", "")) for folder in (path.parent, ENGINE / "fonts/truetype")
                     if (folder / str(descriptor.get("file", ""))).is_file()), None)
        if font is None:
            print(f"warning: {relative(path)}: font file {descriptor.get('file')} not found", file=sys.stderr)
            continue
        drawable = _ttf_characters(font)
        if descriptor.get("encoding") == "utf-8":
            listed = descriptor.get("characters_file")
            listed_path = next((folder / listed for folder in (path.parent, ENGINE / "fonts/truetype")
                                if listed and (folder / listed).is_file()), None)
            drawable &= {ord(character) for character in read_text(listed_path)} if listed_path else set()
        else:
            # A legacy face holds the Windows-1252 characters only.
            drawable &= {ord(bytes([byte]).decode("cp1252", errors="ignore") or "\0") for byte in range(32, 256)}
        coverage[name] = drawable
    return coverage


SENTENCE_LITERAL = re.compile(r"\"([A-Z][a-z']+(?: [A-Za-z'%{}.,!?:-]+){2,}[.!?:]?)\"")
NOT_SHOWN = re.compile(r"std::cout|std::cerr|TRACE|Trace|trace|throw |error\s*=|LOG|failures?\.|\bfail\(|"
                       r"assert|static_assert|#include|\btr(?:[cn]|Noop)?\(|localize(?:Known)?\(")


def cmd_check(arguments):
    problems = 0
    for language in language_ids(arguments.languages):
        files = load_language(language)
        characters = collections.Counter()
        for domain, (_, entries) in files.items():
            for entry in entries:
                if entry.obsolete or not entry.translated():
                    continue
                for form, value in enumerate(entry.msgstr):
                    if not value:
                        continue
                    english = entry.plural if entry.plural is not None and form > 0 else entry.msgid
                    problem = mismatch(english, value)
                    if problem and entry.plural is not None and form == 0:
                        problem = mismatch(entry.plural, value)
                    commas = decimal_commas(english, value)
                    if commas and not problem:
                        problem = f"decimals {' '.join(commas)} written with a comma"
                    if problem:
                        problems += 1
                        where = entry.references[0] if entry.references else domain + ".po"
                        print(f"{language}: {where}: {problem}: {entry.msgid[:60]!r}")
                    characters.update(character for character in value if character not in "\n\t\f")
        if arguments.charset:
            # The faces also draw what stays English (untranslated text, numbers, names): every Windows-1252
            # character joins the ones the translations use.
            listed = set(characters) | {bytes([byte]).decode("cp1252", errors="ignore") for byte in range(32, 256)}
            listed.discard("")
            Path(arguments.charset).write_text("".join(sorted(listed)), encoding="utf-8")
            print(f"{language}: {len(listed)} characters written to {arguments.charset}")
        coverage = font_coverage(language)
        if coverage and characters:
            lacking = collections.Counter()
            for character, count in characters.items():
                if ord(character) < 32:
                    continue
                for face, drawable in coverage.items():
                    if ord(character) not in drawable:
                        lacking[face] += 1
            for face, count in sorted(lacking.items()):
                problems += 1
                print(f"{language}: font {face} lacks {count} of the {len(characters)} characters the translations use")
    # Lua sentences joined from pieces, and C++ sentences shown without tr().
    template = Template()
    extract_lua(template)
    for reference, value in template.joined:
        print(f"joined: {reference}: {value!r} (one sentence with tr() and placeholders can be translated)")
    if arguments.cpp:
        literals = 0
        for folder in ("game/ui", "game/gameplay", "game/items", "game/rules", "game/party"):
            for path in sorted((ROOT / folder).rglob("*.cpp")):
                for number, line in enumerate(read_text(path).splitlines(), 1):
                    if NOT_SHOWN.search(line):
                        continue
                    for match in SENTENCE_LITERAL.finditer(line):
                        literals += 1
                        if arguments.list:
                            print(f"literal: {relative(path)}:{number}: {match.group(1)!r}")
        print(f"{literals} English sentence literals in game code outside tr() (candidates; --list shows them)")
    print(f"{problems} problems" if problems else "No problems in the translations")
    return 1 if problems else 0


# ----------------------------------------------------------------------------------------------------------------------
# Import

def _machine_draft(entry):
    return any(line.startswith(MACHINE_MARK) for line in entry.translator)


class Imported:
    def __init__(self, language, replace=False):
        self.language = language
        # A reviewed correction: replaces the existing translation instead of keeping it.
        self.replace = replace
        # A translator's own file: a translation equal to the English is deliberate ("MAW", "{points} HP").
        self.identical = False
        self.pairs = collections.defaultdict(collections.Counter)   # (context, english) -> Counter(translation)
        self.sources = collections.defaultdict(list)                # (context, english, translation) -> references
        self.review = []
        self.plurals = {}                                            # (context, english) -> forms

    def add(self, english, translation, reference, context=""):
        english = english.replace("\r\n", "\n")
        translation = translation.replace("\r\n", "\n")
        # A pattern of placeholders only ("{month} {day}, {year}") is extracted from the code too; a translator's file
        # orders it.
        pattern = self.identical and len(re.findall(r"\{\w+\}", english)) >= 2
        if not (is_text(english) or pattern) or not translation.strip():
            return
        # A source that keeps the English counts only for a short name (it may be untranslated text otherwise).
        if english == translation and len(english.split()) > 3:
            return
        # MMMerge's placeholder names of unused rows ("_misc197", "_artifact570").
        if re.fullmatch(r"_\w+(?:/\w+)?\d+", translation.strip()):
            self.review.append(f"refused {reference}: placeholder {translation!r} for {english[:80]!r}")
            return
        problem = mismatch(english, translation)
        if problem:
            self.review.append(f"refused {reference}: {problem}: {english[:80]!r} -> {translation[:80]!r}")
            return
        self.pairs[(context, english)][translation] += 1
        self.sources[(context, english, translation)].append(reference)

    def add_plural(self, entry, reference):
        """A plural text's forms, written as they are (the language's form count)."""
        if not all(form.strip() for form in entry.msgstr):
            return
        for index, form in enumerate(entry.msgstr):
            problem = mismatch(entry.msgid if index == 0 else entry.plural, form)
            if problem:
                self.review.append(f"refused {reference}: {problem}: {entry.msgid[:80]!r} -> {form[:80]!r}")
                return
        self.plurals[(entry.context, entry.msgid)] = list(entry.msgstr)

    def write(self, label):
        """Merge into the language's files: texts the templates have go to their domain, the rest wait in
        engine-pending.po. Returns the number of translations written."""
        templates = load_templates()
        domains = {}
        for domain, entries in templates.items():
            for entry in entries:
                domains.setdefault(entry.msgid, domain)
        files = load_language(self.language)
        # A text in several world files (mm6.po and mm7.po both have it) is one key with an entry in each.
        existing = collections.defaultdict(list)
        for domain, (_, entries) in files.items():
            for entry in entries:
                existing[entry.key].append(entry)
        added = collections.defaultdict(list)
        written = 0
        for (context, english), translations in sorted(self.pairs.items()):
            choice, _ = translations.most_common(1)[0]
            # A short name the original interface table translates: that one, not a map line's or an item row's
            # ("Fire" is "Oheň" there, "Vystřel!" in a cannon scene).
            if len(english.split()) <= 3:
                interface = [text for text in translations if text != english and any(
                    "global.txt" in source.lower() or "mapstats" in source.lower()
                    for source in self.sources[(context, english, text)])]
                choice = interface[0] if interface else choice
            if len(translations) > 1:
                others = "; ".join(f"{text!r} ({', '.join(self.sources[(context, english, text)][:3])})"
                                   for text in translations if text != choice)
                self.review.append(f"several translations of {english[:80]!r}: chose {choice!r} "
                                   f"({translations[choice]} times); others: {others}")
            # Sources that keep the English (a name) outvote only item rows, whose ids are shifted in some
            # archives ("Armageddon" read as "Haleine de Dragon"); a translation from any other table wins.
            if choice == english and not self.identical:
                trusted = [(count, text) for text, count in translations.items() if text != english and any(
                    "ItemsTxt" not in source for source in self.sources[(context, english, text)])]
                if not trusted:
                    continue
                choice = max(trusted)[1]
            entries = existing.get((context, english))
            if not entries:
                entry = Entry(english, context)
                added[domains.get(english, PENDING_DOMAIN)].append(entry)
                entries = [entry]
            for entry in entries:
                # A machine draft gives way to a translator's file (import po) and loses its review mark.
                draft = self.identical and _machine_draft(entry)
                if entry.translated() and not draft and not (self.replace and entry.msgstr[0] != choice):
                    if entry.msgstr[0] != choice:
                        self.review.append(f"kept the existing translation of {english[:80]!r}: "
                                           f"{entry.msgstr[0]!r}, not {choice!r}")
                    continue
                entry.msgstr = [choice]
                entry.flags.discard("fuzzy")
                entry.translator = [line for line in entry.translator
                                    if not line.startswith(("imported", MACHINE_MARK))] + [f"imported from {label}"]
                written += 1
        for (context, english), forms in sorted(self.plurals.items()):
            for entry in existing.get((context, english), []):
                if entry.translated() and not self.replace and not _machine_draft(entry):
                    continue
                entry.msgstr = forms
                entry.flags.discard("fuzzy")
                entry.translator = [line for line in entry.translator
                                    if not line.startswith(("imported", MACHINE_MARK))] + [f"imported from {label}"]
                written += 1
        for domain, entries in added.items():
            header, current = files.get(domain, ("", []))
            files[domain] = (header, current + entries)
        text = LANGUAGES / self.language / "text"
        for domain, (header, entries) in files.items():
            write_po(text / f"{domain}.po", default_header(self.language, header), entries)
        # Outside the pack: the game reads nothing but language.yml, text/ and the overlay folders there.
        review = ROOT / "output" / "l10n" / f"{self.language}-import-review.txt"
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text("\n".join(self.review) + "\n", encoding="utf-8")
        print(f"{self.language}: {written} translations imported from {label}; {len(self.review)} points in "
              f"{relative(review)}")


def _translated_keys(language):
    files = load_language(language)
    return files, {entry.key for _, entries in files.values() for entry in entries
                   if not entry.obsolete and entry.translated()}


def cmd_todo(arguments):
    """The untranslated texts of a language as JSON for a translator (person or model)."""
    _, translated = _translated_keys(arguments.language)
    pattern = re.compile(arguments.refs) if arguments.refs else None
    rows = []
    for domain, entries in load_templates().items():
        for entry in entries:
            if entry.key in translated or (pattern and not any(pattern.search(ref) for ref in entry.references)):
                continue
            rows.append({"domain": domain, "context": entry.context, "msgid": entry.msgid, "plural": entry.plural,
                         "references": entry.references[:4], "notes": entry.comments})
    rows = rows[:arguments.limit] if arguments.limit else rows
    text = json.dumps(rows, ensure_ascii=False, indent=1)
    if arguments.out:
        Path(arguments.out).write_text(text + "\n", encoding="utf-8")
        print(f"{arguments.language}: {len(rows)} untranslated texts in {arguments.out}")
    else:
        print(text)


def cmd_glossary(arguments):
    """{English: translation} of a language's established short terms (GLOSSARY_SOURCES and the C++ texts with a
    class, skill, mastery or spell context)."""
    files, _ = _translated_keys(arguments.language)
    terms = {}
    for _, entries in files.values():
        for entry in entries:
            if entry.obsolete or not entry.translated() or entry.plural is not None:
                continue
            short = len(entry.msgid) <= 40 and len(entry.msgid.split()) <= 4 and "\n" not in entry.msgid
            source = any(any(name in ref for name in GLOSSARY_SOURCES) for ref in entry.references) or \
                entry.context in ("class", "skill", "mastery", "spell")
            if short and source and is_text(entry.msgid):
                terms.setdefault(entry.msgid, entry.msgstr[0])
    text = json.dumps(dict(sorted(terms.items())), ensure_ascii=False, indent=1)
    if arguments.out:
        Path(arguments.out).write_text(text + "\n", encoding="utf-8")
        print(f"{arguments.language}: {len(terms)} terms in {arguments.out}")
    else:
        print(text)


def cmd_todo_po(arguments):
    """The untranslated texts of a language as a .po file for its translator, with the language's header; they fill
    it and it comes back through `import po`."""
    language = arguments.language
    files, translated = _translated_keys(language)
    header = next((h for h, _ in files.values() if h), "") or default_header(language, "")
    nplurals = _plural_count(header)
    pattern = re.compile(arguments.refs) if arguments.refs else None
    entries = []
    for domain, template_entries in load_templates().items():
        if (domain in arguments.skip_domain) or (arguments.domain and domain not in arguments.domain):
            continue
        for template_entry in template_entries:
            if template_entry.key in translated:
                continue
            if pattern and not any(pattern.search(ref) for ref in template_entry.references):
                continue
            entry = Entry(template_entry.msgid, template_entry.context, template_entry.plural)
            entry.references = list(template_entry.references)
            entry.comments = list(template_entry.comments)
            entry.msgstr = [""] * (1 if template_entry.plural is None else nplurals)
            entries.append(entry)
    write_po(Path(arguments.out), header, entries)
    print(f"{language}: {len(entries)} untranslated texts in {arguments.out}")


def import_po(arguments):
    """A translator's filled-in .po file (from `todo --po`): its translated entries, as human translations."""
    _, entries = parse_po(read_text(Path(arguments.file)))
    imported = Imported(arguments.lang, replace=arguments.replace)
    imported.identical = True
    for entry in entries:
        if entry.obsolete or not entry.translated():
            continue
        if entry.plural is None:
            imported.add(entry.msgid, entry.msgstr[0], Path(arguments.file).name, entry.context)
        else:
            imported.add_plural(entry, Path(arguments.file).name)
    imported.write(Path(arguments.file).name)


_PY_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")


def cmd_conflicts(arguments):
    """The short texts (names, labels) the last import found translated several ways, with the translation it chose
    and the others, as a .po file a translator corrects and returns with `import po --replace`."""
    import ast
    language = arguments.language
    review = ROOT / "output" / "l10n" / f"{language}-import-review.txt"
    files, _ = _translated_keys(language)
    current = {entry.key: entry for _, entries in files.values() for entry in entries
               if not entry.obsolete and entry.translated() and entry.plural is None}
    header = next((h for h, _ in files.values() if h), "") or default_header(language, "")
    out = []
    for line in read_text(review).splitlines() if review.is_file() else []:
        if not line.startswith("several translations of "):
            continue
        literals = [match for match in _PY_LITERAL.finditer(line)]
        if len(literals) < 3:
            continue
        english = ast.literal_eval(literals[0].group(0))
        if len(english.split()) > arguments.max_words or ("", english) not in current:
            continue
        others = []
        for match in literals[2:]:
            rest = line[match.end():]
            sources = re.match(r"\s*\(([^)]*)\)", rest)
            others.append(f"{ast.literal_eval(match.group(0))}  ({sources.group(1) if sources else ''})")
        entry = Entry(english)
        entry.msgstr = list(current[("", english)].msgstr)
        entry.references = list(current[("", english)].references)
        entry.translator = ["also translated as:"] + [f"  {other}" for other in others]
        out.append(entry)
    write_po(Path(arguments.out), header, out)
    print(f"{language}: {len(out)} texts translated several ways in {arguments.out}")


def _plural_count(header):
    match = re.search(r"nplurals\s*=\s*(\d+)", header)
    return int(match.group(1)) if match else 2


def import_machine(arguments):
    """Translations a model wrote ([{context, msgid, msgstr: text or [forms]}]), marked for review. Only texts the
    language lacks are filled; an entry that changes placeholders or codes is refused."""
    language = arguments.lang
    rows = json.loads(Path(arguments.file).read_text(encoding="utf-8"))
    templates = load_templates()
    files = load_language(language)
    template_entries = {entry.key: (domain, entry) for domain, entries in templates.items() for entry in entries}
    existing = {entry.key: entry for _, entries in files.values() for entry in entries if not entry.obsolete}
    nplurals = _plural_count(next((header for header, _ in files.values() if header), ""))
    written, refused = 0, []
    for row in rows:
        key = (row.get("context") or "", row["msgid"])
        if key not in template_entries:
            refused.append(f"not in the templates: {key[1][:80]!r}")
            continue
        domain, template_entry = template_entries[key]
        forms = row["msgstr"] if isinstance(row["msgstr"], list) else [row["msgstr"]]
        expected = 1 if template_entry.plural is None else nplurals
        if len(forms) != expected or not all(isinstance(form, str) and form.strip() for form in forms):
            refused.append(f"{len(forms)} forms, {expected} needed: {key[1][:80]!r}")
            continue
        problem = next((issue for issue in (mismatch(template_entry.msgid if index == 0 else template_entry.plural,
                                                     form) for index, form in enumerate(forms)) if issue), None)
        if problem:
            refused.append(f"{problem}: {key[1][:80]!r} -> {forms[0][:80]!r}")
            continue
        entry = existing.get(key)
        # A human translation stays; an earlier machine translation is replaced by the newer one.
        if entry is not None and entry.translated() and \
                not any(line.startswith(MACHINE_MARK) for line in entry.translator):
            continue
        if entry is None:
            entry = Entry(template_entry.msgid, template_entry.context, template_entry.plural)
            entry.references = list(template_entry.references)
            entry.comments = list(template_entry.comments)
            header, current = files.get(domain, ("", []))
            files[domain] = (header, current + [entry])
            existing[key] = entry
        entry.msgstr = forms
        entry.flags.discard("fuzzy")
        entry.translator = [line for line in entry.translator if not line.startswith(MACHINE_MARK)] + \
                           [f"{MACHINE_MARK} ({arguments.label}), review"]
        written += 1
    text = LANGUAGES / language / "text"
    for domain, (header, entries) in files.items():
        write_po(text / f"{domain}.po", default_header(language, header), entries)
    for line in refused:
        print(f"{language}: refused {line}")
    print(f"{language}: {written} machine translations written, {len(refused)} refused")


def _read_tsv_pairs(text):
    """English<TAB>translation lines, quoted when they span lines (PR #25's catalogue)."""
    for _, row in parse_table(text):
        if len(row) >= 2 and row[0] and not row[0].startswith("#"):
            yield row[0], row[1]


def import_tsv(arguments):
    imported = Imported(arguments.lang)
    for path in arguments.files:
        for english, translation in _read_tsv_pairs(read_text(path)):
            imported.add(english.replace("\\n", "\n"), translation.replace("\\n", "\n"), relative(path),
                         arguments.context or "")
    imported.write(", ".join(Path(path).name for path in arguments.files))


def _git_show(revision, path):
    result = subprocess.run(["git", "-C", str(ROOT), "show", f"{revision}:{path}"], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def import_pack(arguments):
    """Pairs each English text with its translation by comparing the pack's copies of the game's files with the
    English files of the release they were made from."""
    pack = Path(arguments.directory)
    package_roots = {"engine": "assets_dev/engine", "rules": "assets_dev/engine/rulesets"}
    for world in WORLDS.iterdir():
        package_roots[world.name] = f"assets_dev/worlds/{world.name}"
    imported = Imported(arguments.lang, replace=arguments.replace)
    templates = load_templates()
    known = {entry.msgid for entries in templates.values() for entry in entries}
    skipped = collections.Counter()
    for package, base in package_roots.items():
        folder = pack / package
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix not in (".txt", ".lua", ".yml"):
                continue
            rel = path.relative_to(folder).as_posix()
            if rel.startswith("fonts/"):
                continue
            original = _git_show(arguments.base, f"{base}/{rel}")
            translated = path.read_bytes()
            if original is None or original == translated:
                continue
            reference = f"{base}/{rel}"
            english, other = decode(original), decode(translated)
            if path.name == "ui_text.txt":
                continue
            if path.suffix == ".txt":
                left = merge_continuations(rel, parse_table(english))
                right = merge_continuations(rel, parse_table(other))
                if [len(row) for _, row in left] != [len(row) for _, row in right]:
                    skipped["tables whose rows differ"] += 1
                    imported.review.append(f"skipped {reference}: its rows and cells differ from the English")
                    continue
                for (line, row), (_, translated_row) in zip(left, right):
                    for cell, translated_cell in zip(row, translated_row):
                        if cell.strip() in known:
                            imported.add(cell.strip(), translated_cell.strip(), f"{reference}:{line}")
            elif path.suffix == ".lua":
                left, right = list(lua_literals(english)), list(lua_literals(other))
                if len(left) != len(right):
                    skipped["scripts whose code differs"] += 1
                    imported.review.append(f"skipped {reference}: its string literals differ in number")
                    continue
                for (start, _, value), (_, _, translated_value) in zip(left, right):
                    if value in known:
                        line = english.count("\n", 0, start) + 1
                        imported.add(value, translated_value, f"{reference}:{line}")
            else:
                try:
                    left, right = yaml.safe_load(english), yaml.safe_load(other)
                except yaml.YAMLError:
                    continue

                def leaves(node, key=()):
                    if isinstance(node, dict):
                        for name, value in node.items():
                            yield from leaves(value, key + (name,))
                    elif isinstance(node, list):
                        for index, value in enumerate(node):
                            yield from leaves(value, key + (index,))
                    else:
                        yield key, node
                translated_leaves = dict(leaves(right))
                for key, value in leaves(left):
                    if isinstance(value, str) and value in known and isinstance(translated_leaves.get(key), str):
                        imported.add(value, translated_leaves[key], reference)
    overlay = pack / "engine/data_tables/english/ui_text.txt"
    if overlay.is_file():
        for line in read_text(overlay).splitlines():
            if line.startswith("#") or "\t" not in line:
                continue
            english, translation = line.split("\t", 1)
            english, translation = english.replace("\\n", "\n"), translation.replace("\\n", "\n")
            if english.endswith("*"):
                imported.review.append(f"prefix pattern {english!r}: needs a tr() template")
                continue
            imported.add(english, translation, "ui_text.txt")
    for reason, count in skipped.items():
        print(f"skipped {count} {reason}")
    imported.write(f"{pack.name} (base {arguments.base})")


# ----------------------------------------------------------------------------------------------------------------------
# MMMerge localizations (LocRU and the like): id-keyed text tables, LOD archives with translated tables, map strings,
# sounds, and VID archives with cutscenes.

# "Text localization" files: our table, its key ("id": the first cell, "index": the data rows in order) and the column
# of each field the file translates ("" for a file with one text field).
MMMERGE_TABLES = {
    "2DEvents": ("house_data.txt", "id", {"Name": 5, "Proprieter Name": 6, "Title": 7, "Enter text": 23}),
    "AutonoteTxt": ("english/autonote.txt", "id", {"": 1}),
    "AwardsTxt": ("english/awards.txt", "id", {"": 1}),
    "ClassDescriptions": ("english/class.txt", "index", {"": 1}),
    "ClassNames": ("english/class.txt", "index", {"": 0}),
    "ItemsTxt": ("items.txt", "id", {"Name": 2, "NotIdentifiedName": 10, "Notes": 16}),
    "MapStats": ("map_stats.txt", "id", {"Name": 1}),
    "MessageScrolls": ("english/scroll.txt", "index", {"": 1}),
    "Monsters": ("monster_data.txt", "id", {"Name": 1}),
    "NPCData": ("npc.txt", "id", {"Name": 1}),
    "NPCGreet1": ("npc_greet.txt", "id", {"0": 1}),
    "NPCGreet2": ("npc_greet.txt", "id", {"1": 2}),
    "NPCNews": ("npc_news.txt", "id", {"": 1}),
    "NPCText": ("npc_topic_text.txt", "id", {"": 1}),
    "NPCTopic": ("npc_topic.txt", "id", {"": 1}),
    "PlaceMonTxt": ("english/place_mon.txt", "id", {"": 1}),
    "QuestsTxt": ("english/quests.txt", "id", {"": 1}),
    "SpcItemsTxtNames": ("special_item_enchants.txt", "index", {"NameAdd": 1}),
    "SpcItemsTxtStats": ("special_item_enchants.txt", "index", {"BonusStat": 16}),
    "StdItemsTxtNames": ("standard_item_enchants.txt", "index", {"NameAdd": 1}),
    "TransTxt": ("english/trans.txt", "id", {"": 1}),
    "GlobalTxt": ("english/Global.txt", "id", {"": 1}),
}
# "Text localization" files that are translated copies of our table, row by row (the random names of peasants).
MMMERGE_COPY_TABLES = {"NPCNames": "npc_names.txt"}
# Translated copies of the game's tables inside the *.T.lod, laid out like ours: keyed by id, or row by row.
MMMERGE_LOD_TABLES = {
    "global.txt": ("english/Global.txt", "id"),
    "spells.txt": ("english/spells.txt", "id"),
    "stats.txt": ("english/stats.txt", "index"),
    "skilldes.txt": ("english/skill_des.txt", "index"),
    "history.txt": ("english/history.txt", "id"),
    "merchant.txt": ("english/merchant.txt", "index"),
    "npcnews.txt": ("npc_news.txt", "id"),
}
MMMERGE_ENGLISH_STRINGS = ROOT / "reference/mmerge_data_forus/Data/mmmerge.T.lod"


def lod_files(path):
    """{name: bytes} of an MM8 LOD archive's chapter: 76-byte entries; each record has a 96-byte header with the packed
    size at +68 and the unpacked size at +88 (0: stored), then zlib data."""
    import struct
    import zlib
    data = Path(path).read_bytes()
    if data[:4] != b"LOD\0":
        raise ValueError(f"{path} is not a LOD archive")
    _, directory, _, _, count = struct.unpack_from("<16sIIII", data, 0x100)
    files = {}
    for index in range(count):
        base = directory + index * 76
        name = data[base:base + 64].split(b"\0")[0].decode("latin-1")
        offset = directory + struct.unpack_from("<I", data, base + 64)[0]
        packed, unpacked = struct.unpack_from("<I", data, offset + 68)[0], struct.unpack_from("<I", data, offset + 88)[0]
        blob = data[offset + 96:offset + 96 + packed]
        files[name] = zlib.decompress(blob) if unpacked else blob
    return files


def vid_files(path):
    """{name: (offset, size)} of a VID archive: a count, then 40-byte names with their offsets."""
    import struct
    data = Path(path).read_bytes()
    count = struct.unpack_from("<I", data, 0)[0]
    entries = []
    for index in range(count):
        base = 4 + index * 44
        entries.append((data[base:base + 40].split(b"\0")[0].decode("latin-1"),
                        struct.unpack_from("<I", data, base + 40)[0]))
    offsets = sorted({offset for _, offset in entries} | {len(data)})
    return {name: (offset, offsets[offsets.index(offset) + 1] - offset) for name, offset in entries}, data


# The table names of an MMMerge "LocalizeTables" file (rows of several tables) as their "Text localization" stems.
MMMERGE_STRUCT_TABLES = {"NPCText": "NPCText", "NPCTopic": "NPCTopic", "TransTxt": "TransTxt", "Houses": "2DEvents",
                         "GlobalTxt": "GlobalTxt", "MapStats": "MapStats", "NPCDataTxt": "NPCData"}


def _localized_rows(text, table=None):
    """(id, field, text) of an MMMerge "Text localization" file; of one table's rows for a "LocalizeTables" file."""
    rows = parse_table(text)
    if not rows:
        return
    header = rows[0][1]
    if header[:2] == ["Table (of Game struct)", "Id"]:
        for _, row in rows[1:]:
            if table is not None and (not row or row[0].strip() != table):
                continue
            if len(row) >= 4 and row[1].strip().lstrip("-").isdigit():
                yield int(row[1]), row[2].strip(), row[3]
        return
    for _, row in rows[1:]:
        if row and row[0].strip().isdigit():
            for column, field in enumerate(header[1:], 1):
                if column < len(row):
                    yield int(row[0]), field.strip(), row[column]


def _data_rows(table):
    skip = TABLE_TEXT_COLUMNS[table][0]
    rows = merge_continuations(table, parse_table(read_text(ENGINE / "data_tables" / table)))
    return [row for _, row in rows[skip:] if any(c.strip() for c in row)]


def _decode_mixed(data, encoding):
    """Text whose lines are in the localization's code page, or some already in UTF-8 (the Czech one mixes both)."""
    lines = []
    for line in data.split(b"\n"):
        try:
            decoded = line.decode("utf-8")
            # Code-page bytes that happen to form UTF-8 decode to other scripts ("Píšťaly": U+D69D, "DÓŁ": U+04E3):
            # these archives' own UTF-8 lines hold Latin letters and punctuation only.
            if any(ord(character) > 0x24f and not 0x2000 <= ord(character) <= 0x206f for character in decoded):
                raise UnicodeDecodeError("utf-8", line, 0, len(line), "not this line's encoding")
            lines.append(decoded)
        except UnicodeDecodeError:
            lines.append(line.decode(encoding, errors="replace"))
    return "\n".join(lines)


def _clean_mmmerge(text):
    # Cells that were not read as quoted keep the doubled quotes of the export.
    return text.replace("\"\"", "\"").strip()


def import_mmmerge(arguments):
    source = Path(arguments.directory)
    encoding = arguments.encoding
    imported = Imported(arguments.lang)
    label = f"{source.name} (MMMerge localization)"

    # Id-keyed text tables: one file per table in "Text localization" (at any depth: some archives nest it in
    # Data/), and "LocalizeTables" files holding rows of several tables.
    def add_rows(stem, text, reference, table=None):
        table_file, key, fields = MMMERGE_TABLES[stem]
        rows = _data_rows(table_file)
        by_id = {row[0].strip(): row for row in rows if row and row[0].strip()}
        for ident, field, value in _localized_rows(text, table):
            if field not in fields or not value.strip():
                continue
            row = by_id.get(str(ident)) if key == "id" else (rows[ident] if 0 <= ident < len(rows) else None)
            column = fields[field]
            if row and column < len(row):
                imported.add(row[column].strip(), _clean_mmmerge(value), f"{reference}:{ident}")

    for folder in sorted(source.rglob("Text localization")):
        for path in sorted(folder.glob("*.txt")):
            stem = re.sub(r"^[A-Za-z]{2}_", "", path.stem)
            if stem in MMMERGE_COPY_TABLES:
                table = MMMERGE_COPY_TABLES[stem]
                skip, columns = TABLE_TEXT_COLUMNS[table]
                ours = [row for _, row in parse_table(read_text(ENGINE / "data_tables" / table))[skip:]]
                theirs = [row for _, row in parse_table(_decode_mixed(path.read_bytes(), encoding))[skip:]]
                for row, other in zip(ours, theirs):
                    for column in columns:
                        if column < len(row) and column < len(other):
                            imported.add(row[column].strip(), _clean_mmmerge(other[column]), path.name)
                continue
            if stem not in MMMERGE_TABLES:
                imported.review.append(f"skipped {path.name}: no table mapping")
                continue
            add_rows(stem, _decode_mixed(path.read_bytes(), encoding), path.name)
    for path in sorted(source.rglob("*LocalizeTables.txt")):
        text = _decode_mixed(path.read_bytes(), encoding)
        for table, stem in MMMERGE_STRUCT_TABLES.items():
            add_rows(stem, text, f"{path.name}/{table}", table)

    # Text tables and map strings in the *.T.lod archives.
    english_strings = {path.name.lower(): path for path in MMMERGE_ENGLISH_STRINGS.glob("*")
                       if path.suffix.lower() == ".str"}
    for lod in sorted(source.rglob("*.T.lod")):
        files = lod_files(lod)
        for name, data in sorted(files.items()):
            lower = name.lower()
            if lower in MMMERGE_LOD_TABLES:
                table, key = MMMERGE_LOD_TABLES[lower]
                skip, columns = TABLE_TEXT_COLUMNS[table]
                ours = [row for _, row in merge_continuations(
                    table, parse_table(read_text(ENGINE / "data_tables" / table)))[skip:]]
                theirs = [row for _, row in merge_continuations(
                    table, parse_table(_decode_mixed(data, encoding)))[skip:]]
                if key == "id":
                    theirs_by_id = {row[0].strip(): row for row in theirs if row and row[0].strip()}
                    pairs = [(row, theirs_by_id.get(row[0].strip())) for row in ours if row and row[0].strip()]
                else:
                    pairs = list(zip(ours, theirs))
                for row, other in pairs:
                    for column in columns:
                        if other and column < len(row) and column < len(other):
                            imported.add(row[column].strip(), _clean_mmmerge(other[column]), f"{lod.name}/{name}")
            elif lower.endswith(".str") and lower in english_strings:
                english = decode(english_strings[lower].read_bytes()).replace("\r\n", "\n").split("\n")
                translated = data.split(b"\0")
                for strings in (english, translated):
                    if strings and not strings[-1]:
                        strings.pop()
                if abs(len(english) - len(translated)) > 1:
                    imported.review.append(f"skipped {lod.name}/{name}: {len(translated)} strings, English has "
                                           f"{len(english)}")
                    continue
                if len(english) != len(translated):
                    imported.review.append(f"{lod.name}/{name}: one string more or less than English; paired the "
                                           f"first {min(len(english), len(translated))}")
                for index, (text, other) in enumerate(zip(english, translated)):
                    imported.add(text.strip(), _decode_mixed(other, encoding).strip(), f"{lod.name}/{name}#{index}")
    imported.write(label)

    if arguments.audio:
        _import_mmmerge_audio(source, arguments.lang)
    if arguments.videos:
        _import_mmmerge_videos(source, arguments.lang)


# ----------------------------------------------------------------------------------------------------------------------
# A localized MM9 (the official Czech or Polish CD Projekt release): its data tables, extracted from DATA.REZ and
# RUDE.REZ with tools/mm9_import_discovery/extract_rez.py, are the English ones (mm9/extracted) with the texts
# translated, so they pair file by file, row by row and cell by cell.

MM9_ENGLISH = ROOT / "mm9" / "extracted"


def _mm9_normalized(text):
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text.replace("…", "...")).strip()


def mm9_localized_pairs(directory, encoding):
    """{normalized English: Counter(translation)} of a localized MM9's DATA/DATA and RUDE/RUDE folders."""
    import csv
    import io
    pairs = collections.defaultdict(collections.Counter)

    def add(english, translation):
        english, translation = english.strip(), translation.strip()
        if is_text(english) and translation and english != translation:
            pairs[_mm9_normalized(english)][translation.replace("\r\n", "\n")] += 1

    def rows(text, name):
        if name.lower().endswith((".csv", ".rude")):
            return [row for row in csv.reader(io.StringIO(text)) if row]
        return [line.split("\t") for line in text.split("\n")]

    for folder in ("DATA/DATA", "RUDE/RUDE"):
        for path in sorted((Path(directory) / folder).glob("*")):
            english_path = MM9_ENGLISH / folder / path.name
            if not path.is_file() or not english_path.is_file() or path.name == "CREDITS.txt":
                continue
            english = rows(english_path.read_bytes().decode("cp1252", "replace").replace("\r\n", "\n"), path.name)
            local = rows(path.read_bytes().decode(encoding, "replace").replace("\r\n", "\n"), path.name)
            if len(english) != len(local) or path.name == "BOOK AND SCROLL TEXT.csv":
                # Rows keyed by their ids (a book's id, a conversation row's NPC, node and choice).
                # A conversation row is known by its NPC, its node and where its choice leads (the Czech release
                # numbers some nodes' choices differently).
                single = path.name in ("TOPBLURB.rude", "NPCNAME.rude", "BOOK AND SCROLL TEXT.csv")

                def key_of(row):
                    return (row[0],) if single else (row[0], row[1], tuple(row[5:]))

                keyed, seen = {}, collections.Counter()
                for row in local:
                    key = key_of(row)
                    keyed[(key, seen[key])] = row
                    seen[key] += 1
                seen = collections.Counter()
                matched = []
                for row in english:
                    key = key_of(row)
                    matched.append((row, keyed.get((key, seen[key]))))
                    seen[key] += 1
            else:
                matched = list(zip(english, local))
            for row, other in matched:
                if other is not None and len(row) == len(other):
                    for english_cell, local_cell in zip(row, other):
                        add(english_cell, local_cell)
    return pairs


def import_mm9(arguments):
    pairs = mm9_localized_pairs(arguments.directory, arguments.encoding)
    label = f"imported from {arguments.label}"
    path = LANGUAGES / arguments.lang / "text" / "mm9.po"
    header, entries = parse_po(read_text(path))
    counts = collections.Counter()
    for entry in entries:
        if entry.obsolete or entry.plural is not None:
            continue
        translations = pairs.get(_mm9_normalized(entry.msgid))
        if not translations:
            continue
        choice = translations.most_common(1)[0][0]
        machine = "machine translation" in " ".join(entry.translator)
        if entry.translated() and not machine and not arguments.replace:
            counts["kept"] += 1
            continue
        if mismatch(entry.msgid, choice):
            counts["refused"] += 1
            continue
        entry.msgstr = [choice]
        entry.translator = [label]
        entry.flags.discard("fuzzy")
        counts["imported"] += 1
    write_po(path, header, entries)
    print(f"{arguments.lang}: {len(pairs)} texts in the localization; {counts['imported']} imported, "
          f"{counts['kept']} human translations kept, {counts['refused']} refused (placeholders or codes)")


def _our_media(directory, suffix):
    """{lower-case name: path relative to its package root} of our media, e.g. 'zm147a.wav': 'engine/audio/zm147a.wav'."""
    found = {}
    roots = [(ENGINE / directory, Path("engine") / directory)]
    roots += [(world / directory, Path("worlds") / world.name / directory) for world in sorted(WORLDS.iterdir())]
    for root, package in roots:
        for path in sorted(root.rglob(f"*{suffix}")) if root.is_dir() else []:
            found.setdefault(path.name.lower() if suffix == ".wav" else path.stem.lower(),
                             package / path.relative_to(root))
    return found


def _import_mmmerge_audio(source, language):
    ours = _our_media("audio", ".wav")
    copied = skipped = 0
    for lod in sorted(source.rglob("*.D.lod")):
        for name, data in lod_files(lod).items():
            target = ours.get(name.lower())
            if not name.lower().endswith(".wav") or target is None or data[:4] != b"RIFF":
                skipped += 1
                continue
            path = LANGUAGES / language / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            copied += 1
    print(f"{language}: {copied} sounds over the game's ({skipped} other files in the data LODs left out)")


def _import_mmmerge_videos(source, language):
    """Cutscenes only (videos/Cutscenes): the house and transition loops have no speech. A later archive in name
    order wins (mmmerge.*.vid over mm7.*.vid over the base one), as the game loads them."""
    import shutil
    import tempfile
    ours = _our_media("videos", ".ogv")
    chosen = {}
    for vid in sorted(source.rglob("*.vid"), key=lambda path: (path.name.count("."), path.name)):
        entries, data = vid_files(vid)
        for name, (offset, size) in entries.items():
            target = ours.get(Path(name).stem.lower())
            if target is not None and "Cutscenes" in target.parts and size > 0:
                chosen[target] = (name, data[offset:offset + size])
    with tempfile.TemporaryDirectory() as work:
        for kind in ("bik", "smk"):
            raw, out = Path(work) / f"in_{kind}", Path(work) / f"out_{kind}"
            raw.mkdir()
            out.mkdir()
            names = {}
            for target, (name, blob) in chosen.items():
                # The extension says Bink, the header may say Smacker: the header decides.
                actual = "bik" if blob[:3] == b"BIK" else "smk"
                if actual == kind:
                    (raw / f"{target.stem}.{kind}").write_bytes(blob)
                    names[target.stem] = target
            if not names:
                continue
            subprocess.run([str(ROOT / f"tools/transcode_{kind}.sh"), "-i", str(raw), "-o", str(out)], check=True)
            for stem, target in names.items():
                result = out / f"{stem}.ogv"
                if result.is_file():
                    path = LANGUAGES / language / target
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(result, path)
                    print(f"{language}: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("extract")
    for name in ("update", "report", "check"):
        command = commands.add_parser(name)
        command.add_argument("languages", nargs="*")
        if name in ("report", "check"):
            command.add_argument("--list", action="store_true")
        if name == "check":
            command.add_argument("--charset")
            command.add_argument("--cpp", action="store_true", help="also count C++ sentence literals outside tr()")
    todo = commands.add_parser("todo", help="untranslated texts as JSON")
    todo.add_argument("language")
    todo.add_argument("--refs", help="only texts with a source reference matching this regular expression")
    todo.add_argument("--limit", type=int)
    todo.add_argument("--out")
    todo.add_argument("--po", action="store_true", help="write a .po file for a translator instead of JSON")
    todo.add_argument("--domain", action="append", help="only these domains (engine, mm6...)")
    todo.add_argument("--skip-domain", action="append", default=[], help="leave these domains out")
    glossary = commands.add_parser("glossary", help="a language's established terms as JSON")
    glossary.add_argument("language")
    glossary.add_argument("--out")
    importer = commands.add_parser("import")
    sources = importer.add_subparsers(dest="source", required=True)
    tsv = sources.add_parser("tsv")
    tsv.add_argument("files", nargs="+")
    tsv.add_argument("--lang", required=True)
    tsv.add_argument("--context")
    pack = sources.add_parser("pack")
    pack.add_argument("directory")
    pack.add_argument("--lang", required=True)
    pack.add_argument("--base", default="v1.21")
    pack.add_argument("--replace", action="store_true",
                      help="replace existing translations (a newer version of the same pack)")
    mmmerge = sources.add_parser("mmmerge")
    mmmerge.add_argument("directory")
    mmmerge.add_argument("--lang", required=True)
    mmmerge.add_argument("--encoding", default="cp1251", help="code page of the localization's texts")
    mmmerge.add_argument("--audio", action="store_true")
    mmmerge.add_argument("--videos", action="store_true")
    mm9 = sources.add_parser("mm9", help="a localized MM9's tables (DATA.REZ and RUDE.REZ extracted)")
    mm9.add_argument("directory", help="folder holding DATA/DATA and RUDE/RUDE (extract_rez.py output)")
    mm9.add_argument("--lang", required=True)
    mm9.add_argument("--encoding", default="cp1250", help="code page of the localization's texts")
    mm9.add_argument("--label", required=True, help="the release, e.g. 'the Czech MM9 (CD Projekt, 2002)'")
    mm9.add_argument("--replace", action="store_true", help="replace human translations too")
    po = sources.add_parser("po")
    po.add_argument("file")
    po.add_argument("--lang", required=True)
    po.add_argument("--replace", action="store_true", help="replace existing translations (a reviewed file)")
    conflicts = commands.add_parser("conflicts", help="texts an import found translated several ways, as .po")
    conflicts.add_argument("language")
    conflicts.add_argument("--max-words", type=int, default=4)
    conflicts.add_argument("--out", required=True)
    machine = sources.add_parser("machine")
    machine.add_argument("file")
    machine.add_argument("--lang", required=True)
    machine.add_argument("--label", default="Claude")
    arguments = parser.parse_args()
    if arguments.command == "extract":
        return cmd_extract(arguments)
    if arguments.command == "update":
        return cmd_update(arguments)
    if arguments.command == "report":
        return cmd_report(arguments)
    if arguments.command == "check":
        return cmd_check(arguments)
    if arguments.command == "todo":
        return cmd_todo_po(arguments) if arguments.po else cmd_todo(arguments)
    if arguments.command == "glossary":
        return cmd_glossary(arguments)
    if arguments.command == "conflicts":
        return cmd_conflicts(arguments)
    if arguments.source == "machine":
        return import_machine(arguments)
    if arguments.source == "po":
        return import_po(arguments)
    if arguments.source == "tsv":
        return import_tsv(arguments)
    if arguments.source == "mmmerge":
        return import_mmmerge(arguments)
    if arguments.source == "mm9":
        return import_mm9(arguments)
    return import_pack(arguments)


if __name__ == "__main__":
    sys.exit(main() or 0)
