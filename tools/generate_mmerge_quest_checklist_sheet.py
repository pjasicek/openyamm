#!/usr/bin/env python3
import csv
import datetime
import html
import os
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTS_PATH = ROOT / "assets_dev/engine/data_tables/english/quests.txt"
OUTPUT_PATH = ROOT / "docs/mmerge_quest_testing_checklist.xlsx"
CSV_OUTPUT_PATH = ROOT / "docs/mmerge_quest_testing_checklist.csv"

STATUS_VALUES = ["untested", "works", "blocked", "needs retest", "skip"]
PRIORITY_VALUES = ["baseline", "side", "optional", "blocked by design"]

MM8_MAIN_QBITS = {
    3, 5, 9, 11, 13, 14, 15, 16, 17, 18, 25, 36, 41, 42, 43, 44, 46, 48, 50, 52, 54, 85, 91, 284,
}
MM8_PROMOTION_QBITS = {39, 68, 70, 72, 74, 76, 78, 80, 82}

MM7_MAIN_QBITS = {
    513, 514, 515, 516, 517, 518, 528, 587, 588, 589, 590, 591, 606, 607, 616, 635, 642, 643, 658,
    663, 664, 665,
}
MM7_PROMOTION_QBITS = {
    530, 531, 533, 534, 536, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 554,
    556, 557, 559, 560, 561, 566, 567, 613, 615, 618, 620, 621, 634, 636, 637, 639, 640,
}

MM6_MAIN_QBITS = {
    1105, 1106, 1110, 1112, 1113, 1114, 1119, 1186, 1187, 1188, 1189, 1190, 1224, 1225, 1259,
}
MM6_COUNCIL_PROMOTION_QBITS = {
    1122, 1129, 1131, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1142, 1143, 1144, 1145, 1146, 1169,
}


def column_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def clean_text(value):
    if value is None:
        return ""
    value = str(value).replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return value.strip()


def xml_text(value):
    return html.escape(clean_text(value), quote=False)


def cell_xml(row_index, column_index, value, style=None, formula=False):
    ref = f"{column_name(column_index)}{row_index}"
    style_attr = f' s="{style}"' if style is not None else ""
    if formula:
        return f'<c r="{ref}"{style_attr}><f>{xml_text(value)}</f></c>'
    if isinstance(value, int):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    if isinstance(value, float):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    value = clean_text(value)
    if value == "":
        return f'<c r="{ref}"{style_attr}/>'
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{xml_text(value)}</t></is></c>'


def row_xml(row_index, values, style=None, cell_styles=None, formulas=None):
    cell_styles = cell_styles or {}
    formulas = formulas or set()
    cells = []
    for column_index, value in enumerate(values, 1):
        cells.append(cell_xml(row_index, column_index, value, cell_styles.get(column_index, style), column_index in formulas))
    return f'<row r="{row_index}">{"".join(cells)}</row>'


def worksheet_xml(name, rows, widths, freeze_row=None, auto_filter_ref=None, validations=None, conditional_formats=None):
    max_row = len(rows)
    max_col = max((len(row[0]) for row in rows), default=1)
    dimension = f"A1:{column_name(max_col)}{max_row}"
    cols_xml = []
    for index, width in enumerate(widths, 1):
        cols_xml.append(f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>')

    views_xml = ""
    if freeze_row:
        y_split = freeze_row
        top_left = f"A{freeze_row + 1}"
        views_xml = (
            '<sheetViews><sheetView workbookViewId="0">'
            f'<pane ySplit="{y_split}" topLeftCell="{top_left}" activePane="bottomLeft" state="frozen"/>'
            '<selection pane="bottomLeft"/>'
            '</sheetView></sheetViews>'
        )
    else:
        views_xml = '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'

    sheet_rows = []
    for row_index, (values, style, cell_styles, formulas) in enumerate(rows, 1):
        sheet_rows.append(row_xml(row_index, values, style, cell_styles, formulas))

    auto_filter_xml = f'<autoFilter ref="{auto_filter_ref}"/>' if auto_filter_ref else ""

    validations_xml = ""
    if validations:
        entries = []
        for ref, values in validations:
            escaped = ",".join(values)
            entries.append(
                '<dataValidation type="list" allowBlank="1" showErrorMessage="1" '
                f'sqref="{ref}"><formula1>"{xml_text(escaped)}"</formula1></dataValidation>'
            )
        validations_xml = f'<dataValidations count="{len(entries)}">{"".join(entries)}</dataValidations>'

    conditional_xml = ""
    if conditional_formats:
        parts = []
        for ref, rules in conditional_formats:
            rule_xml = []
            for priority, formula, dxf_id in rules:
                rule_xml.append(
                    f'<cfRule type="expression" priority="{priority}" dxfId="{dxf_id}">'
                    f'<formula>{xml_text(formula)}</formula></cfRule>'
                )
            parts.append(f'<conditionalFormatting sqref="{ref}">{"".join(rule_xml)}</conditionalFormatting>')
        conditional_xml = "".join(parts)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<dimension ref="{dimension}"/>'
        f'{views_xml}'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<cols>{"".join(cols_xml)}</cols>'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        f'{auto_filter_xml}'
        f'{conditional_xml}'
        f'{validations_xml}'
        '</worksheet>'
    )


def styles_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="5">
    <font><sz val="10"/><name val="Arial"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
    <font><b/><sz val="16"/><color rgb="FF17324D"/><name val="Arial"/></font>
    <font><b/><sz val="12"/><color rgb="FF17324D"/><name val="Arial"/></font>
    <font><b/><sz val="10"/><color rgb="FF17324D"/><name val="Arial"/></font>
  </fonts>
  <fills count="10">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF17324D"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFEAF2F8"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF2F5F7"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE8F5E9"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFEBEE"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF8E1"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFECEFF1"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDDE7F0"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="3">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color rgb="FFD9E2EA"/></left><right style="thin"><color rgb="FFD9E2EA"/></right><top style="thin"><color rgb="FFD9E2EA"/></top><bottom style="thin"><color rgb="FFD9E2EA"/></bottom><diagonal/></border>
    <border><bottom style="medium"><color rgb="FF17324D"/></bottom></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="9">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"><alignment vertical="top"/></xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFill="1" applyFont="1" applyBorder="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="3" borderId="0" xfId="0" applyFill="1" applyFont="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="9" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="4" fillId="4" borderId="1" xfId="0" applyFill="1" applyFont="1" applyBorder="1"><alignment horizontal="center" vertical="top"/></xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="4" fillId="0" borderId="2" xfId="0" applyFont="1" applyBorder="1"><alignment vertical="center"/></xf>
  </cellXfs>
  <dxfs count="5">
    <dxf><fill><patternFill patternType="solid"><fgColor rgb="FFF2F5F7"/></patternFill></fill></dxf>
    <dxf><fill><patternFill patternType="solid"><fgColor rgb="FFE8F5E9"/></patternFill></fill></dxf>
    <dxf><fill><patternFill patternType="solid"><fgColor rgb="FFFFEBEE"/></patternFill></fill></dxf>
    <dxf><fill><patternFill patternType="solid"><fgColor rgb="FFFFF8E1"/></patternFill></fill></dxf>
    <dxf><fill><patternFill patternType="solid"><fgColor rgb="FFECEFF1"/></patternFill></fill></dxf>
  </dxfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def load_quest_rows():
    with QUESTS_PATH.open(newline="", encoding="cp1252") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def world_for_qbit(qbit):
    if qbit <= 511:
        return "MM8"
    if qbit <= 999:
        return "MM7"
    if qbit <= 1300:
        return "MM6"
    return "Cross-Continent"


def track_for_qbit(qbit):
    if qbit in MM8_MAIN_QBITS or qbit in MM7_MAIN_QBITS or qbit in MM6_MAIN_QBITS:
        return "Main"
    if qbit in MM8_PROMOTION_QBITS:
        return "Promotion"
    if qbit in MM7_PROMOTION_QBITS:
        return "Promotion"
    if qbit in MM6_COUNCIL_PROMOTION_QBITS:
        return "Council / Promotion"
    if qbit >= 1301:
        return "Cross-Continent"
    return "Side"


def related_qbits_for(row):
    text = f"{row.get('Quest Note Text', '')} {row.get('Notes', '')}"
    qbits = set()
    for match in re.finditer(r"\b(?:Q\s*Bit|Qbit|Qbits|quest|Quest|quests|Quests)\s+(\d{1,4})(?:\s*-\s*(\d{1,4}))?", text):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if 1 <= start <= 1719 and 1 <= end <= 1719 and end - start <= 20:
            for qbit in range(start, end + 1):
                qbits.add(qbit)
    own_qbit = int(row["Q Bit"])
    qbits.discard(own_qbit)
    return ", ".join(str(qbit) for qbit in sorted(qbits))


def is_player_facing(row):
    text = clean_text(row.get("Quest Note Text", ""))
    return bool(text and text != "0" and text.lower() != "congratulations")


def build_checklist_rows(raw_rows):
    rows = []
    for source in raw_rows:
        if not is_player_facing(source):
            continue
        qbit = int(source["Q Bit"])
        world = world_for_qbit(qbit)
        track = track_for_qbit(qbit)
        priority = "baseline" if track in {"Main", "Promotion", "Council / Promotion", "Cross-Continent"} else "side"
        rows.append({
            "World": world,
            "Track": track,
            "Status": "untested",
            "Priority": priority,
            "QBit": qbit,
            "Quest": clean_text(source["Quest Note Text"]),
            "Source Notes": clean_text(source["Notes"]),
            "Related QBits": related_qbits_for(source),
            "Original Owner": clean_text(source["Author"]),
            "Tester": "",
            "Build / Commit": "",
            "Test Date": "",
            "Save / Scenario": "",
            "Evidence / Bug": "",
            "Tester Notes": "",
        })
    world_order = {"MM8": 0, "MM7": 1, "MM6": 2, "Cross-Continent": 3}
    track_order = {"Main": 0, "Council / Promotion": 1, "Promotion": 1, "Side": 2, "Cross-Continent": 3}
    rows.sort(key=lambda row: (world_order[row["World"]], track_order[row["Track"]], row["QBit"]))
    return rows


def build_registry_rows(raw_rows):
    rows = []
    for source in raw_rows:
        qbit = int(source["Q Bit"])
        rows.append([
            qbit,
            world_for_qbit(qbit),
            "yes" if is_player_facing(source) else "no",
            clean_text(source["Quest Note Text"]),
            clean_text(source["Notes"]),
            clean_text(source["Owner"]),
        ])
    return rows


def write_csv(checklist_rows):
    headers = list(checklist_rows[0].keys())
    with CSV_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(checklist_rows)


def build_readme_sheet(generated_date, checklist_count):
    rows = [
        (["MMerge Quest Testing Checklist", "", "", "", ""], 3, {}, set()),
        ([f"Generated {generated_date} from {QUESTS_PATH.relative_to(ROOT)}", "", "", "", ""], 4, {}, set()),
        (["Purpose", "Editable Google Sheets import for MM8, MM7, MM6, and MMerge-specific quest testing.", "", "", ""], 2, {1: 8}, set()),
        (["Import", "Upload the .xlsx to Google Drive, open with Google Sheets, then keep Quest Checklist as the source tab.", "", "", ""], 2, {1: 8}, set()),
        (["Use", "Filter by World, Track, Priority, or Status. Update Status plus Tester, Build / Commit, Test Date, Evidence / Bug, and Tester Notes.", "", "", ""], 2, {1: 8}, set()),
        (["Rows", checklist_count, "player-facing quest rows", "", ""], 2, {1: 8}, set()),
        (["Status legend", "", "", "", ""], 4, {}, set()),
        (["untested", "Not checked in OpenYAMM yet.", "", "", ""], 2, {1: 6}, set()),
        (["works", "Completed in OpenYAMM from normal play.", "", "", ""], 2, {1: 6}, set()),
        (["blocked", "Cannot complete because of an engine, event, or content issue.", "", "", ""], 2, {1: 6}, set()),
        (["needs retest", "Previously changed or uncertain; verify again on a current build.", "", "", ""], 2, {1: 6}, set()),
        (["skip", "Intentionally not part of the current faithful baseline.", "", "", ""], 2, {1: 6}, set()),
        (["Baseline gates", "", "", "", ""], 4, {}, set()),
    ]
    gates = [
        "MM8 main story completable.",
        "MM7 main story completable on Light path.",
        "MM7 main story completable on Dark path.",
        "MM6 main story completable.",
        "Every MM8 promotion completable.",
        "Every MM7 promotion completable, including Light/Dark second promotions.",
        "Every MM6 promotion completable.",
        "Every listed quest-critical dungeon/event interaction works with mouse and keyboard.",
        "Quest state survives save/load and continent travel.",
    ]
    for gate in gates:
        rows.append(([gate, "", "", "", ""], 2, {}, set()))
    return rows


def build_summary_sheet():
    rows = [
        (["MMerge Quest Testing Summary", "", "", "", "", "", "", ""], 3, {}, set()),
        (["World", "Total", "Untested", "Works", "Blocked", "Needs Retest", "Skip", "Remaining"], 1, {}, set()),
    ]
    worlds = ["MM8", "MM7", "MM6", "Cross-Continent"]
    for offset, world in enumerate(worlds, 3):
        values = [
            world,
            f'COUNTIF(\'Quest Checklist\'!A:A,A{offset})',
            f'COUNTIFS(\'Quest Checklist\'!A:A,A{offset},\'Quest Checklist\'!C:C,"untested")',
            f'COUNTIFS(\'Quest Checklist\'!A:A,A{offset},\'Quest Checklist\'!C:C,"works")',
            f'COUNTIFS(\'Quest Checklist\'!A:A,A{offset},\'Quest Checklist\'!C:C,"blocked")',
            f'COUNTIFS(\'Quest Checklist\'!A:A,A{offset},\'Quest Checklist\'!C:C,"needs retest")',
            f'COUNTIFS(\'Quest Checklist\'!A:A,A{offset},\'Quest Checklist\'!C:C,"skip")',
            f'B{offset}-D{offset}-G{offset}',
        ]
        rows.append((values, 2, {1: 6}, {2, 3, 4, 5, 6, 7, 8}))
    all_row = len(worlds) + 3
    values = [
        "All",
        f"SUM(B3:B{all_row - 1})",
        f"SUM(C3:C{all_row - 1})",
        f"SUM(D3:D{all_row - 1})",
        f"SUM(E3:E{all_row - 1})",
        f"SUM(F3:F{all_row - 1})",
        f"SUM(G3:G{all_row - 1})",
        f"SUM(H3:H{all_row - 1})",
    ]
    rows.append((values, 7, {1: 8}, {2, 3, 4, 5, 6, 7, 8}))
    rows.append((["", "", "", "", "", "", "", ""], None, {}, set()))
    rows.append((["By Track", "", "", "", "", "", "", ""], 4, {}, set()))
    rows.append((["Track", "Total", "Untested", "Works", "Blocked", "Needs Retest", "Skip", "Remaining"], 1, {}, set()))
    track_start = len(rows) + 1
    tracks = ["Main", "Council / Promotion", "Promotion", "Side", "Cross-Continent"]
    for index, track in enumerate(tracks, track_start):
        values = [
            track,
            f'COUNTIF(\'Quest Checklist\'!B:B,A{index})',
            f'COUNTIFS(\'Quest Checklist\'!B:B,A{index},\'Quest Checklist\'!C:C,"untested")',
            f'COUNTIFS(\'Quest Checklist\'!B:B,A{index},\'Quest Checklist\'!C:C,"works")',
            f'COUNTIFS(\'Quest Checklist\'!B:B,A{index},\'Quest Checklist\'!C:C,"blocked")',
            f'COUNTIFS(\'Quest Checklist\'!B:B,A{index},\'Quest Checklist\'!C:C,"needs retest")',
            f'COUNTIFS(\'Quest Checklist\'!B:B,A{index},\'Quest Checklist\'!C:C,"skip")',
            f'B{index}-D{index}-G{index}',
        ]
        rows.append((values, 2, {1: 6}, {2, 3, 4, 5, 6, 7, 8}))
    return rows


def build_checklist_sheet(checklist_rows):
    headers = list(checklist_rows[0].keys())
    rows = [(headers, 1, {}, set())]
    for item in checklist_rows:
        rows.append(([item[header] for header in headers], 2, {3: 6, 4: 6, 5: 6}, set()))
    return rows


def build_registry_sheet(registry_rows):
    headers = ["QBit", "World", "Player Facing", "Quest Note Text", "Notes", "Owner"]
    rows = [(headers, 1, {}, set())]
    for item in registry_rows:
        rows.append((item, 2, {1: 6, 2: 6, 3: 6}, set()))
    return rows


def workbook_xml(sheet_names):
    sheets = []
    for index, name in enumerate(sheet_names, 1):
        sheets.append(f'<sheet name="{xml_text(name)}" sheetId="{index}" r:id="rId{index}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<workbookPr date1904="false"/>'
        f'<sheets>{"".join(sheets)}</sheets>'
        '</workbook>'
    )


def workbook_rels_xml(sheet_names):
    rels = []
    for index, _name in enumerate(sheet_names, 1):
        rels.append(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{len(sheet_names) + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(rels)}'
        '</Relationships>'
    )


def content_types_xml(sheet_names):
    sheets = []
    for index, _name in enumerate(sheet_names, 1):
        sheets.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        f'{"".join(sheets)}'
        '</Types>'
    )


def package_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def doc_props_xml(generated_date):
    timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>MMerge Quest Testing Checklist</dc:title>
  <dc:creator>OpenYAMM tooling</dc:creator>
  <cp:lastModifiedBy>OpenYAMM tooling</cp:lastModifiedBy>
  <dc:description>Generated {xml_text(generated_date)} from assets_dev/engine/data_tables/english/quests.txt.</dc:description>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>'''


def app_props_xml(sheet_names):
    names = "".join(f"<vt:lpstr>{xml_text(name)}</vt:lpstr>" for name in sheet_names)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>OpenYAMM</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheet_names)}</vt:i4></vt:variant></vt:vector></HeadingPairs>
  <TitlesOfParts><vt:vector size="{len(sheet_names)}" baseType="lpstr">{names}</vt:vector></TitlesOfParts>
</Properties>'''


def write_workbook(checklist_rows, registry_rows):
    generated_date = datetime.date.today().isoformat()
    sheets = [
        ("README", build_readme_sheet(generated_date, len(checklist_rows)), [22, 90, 20, 20, 20], None, None, [], []),
        ("Summary", build_summary_sheet(), [24, 12, 12, 12, 12, 16, 12, 14], 2, "A2:H13", [], []),
        (
            "Quest Checklist",
            build_checklist_sheet(checklist_rows),
            [14, 20, 15, 14, 9, 70, 70, 24, 16, 18, 20, 14, 24, 24, 50],
            1,
            f"A1:O{len(checklist_rows) + 1}",
            [
                (f"C2:C{len(checklist_rows) + 1}", STATUS_VALUES),
                (f"D2:D{len(checklist_rows) + 1}", PRIORITY_VALUES),
            ],
            [
                (
                    f"A2:O{len(checklist_rows) + 1}",
                    [
                        (1, '$C2="untested"', 0),
                        (2, '$C2="works"', 1),
                        (3, '$C2="blocked"', 2),
                        (4, '$C2="needs retest"', 3),
                        (5, '$C2="skip"', 4),
                    ],
                )
            ],
        ),
        (
            "QBit Registry",
            build_registry_sheet(registry_rows),
            [9, 14, 14, 75, 75, 18],
            1,
            f"A1:F{len(registry_rows) + 1}",
            [],
            [],
        ),
    ]
    sheet_names = [sheet[0] for sheet in sheets]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml(sheet_names))
        archive.writestr("_rels/.rels", package_rels_xml())
        archive.writestr("docProps/core.xml", doc_props_xml(generated_date))
        archive.writestr("docProps/app.xml", app_props_xml(sheet_names))
        archive.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(sheet_names))
        archive.writestr("xl/styles.xml", styles_xml())
        for index, (name, rows, widths, freeze_row, auto_filter_ref, validations, conditional_formats) in enumerate(sheets, 1):
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                worksheet_xml(name, rows, widths, freeze_row, auto_filter_ref, validations, conditional_formats),
            )


def main():
    raw_rows = load_quest_rows()
    checklist_rows = build_checklist_rows(raw_rows)
    registry_rows = build_registry_rows(raw_rows)
    write_csv(checklist_rows)
    write_workbook(checklist_rows, registry_rows)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(checklist_rows)} quest rows)")
    print(f"Wrote {CSV_OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
