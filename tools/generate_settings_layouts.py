#!/usr/bin/env python3
"""Regenerate the Settings menu tab layouts from assets_dev/engine/ui/menu/settings_catalog.yml.

Each section gets assets_dev/engine/ui/gameplay/settings_<section>.yml: the shared menu chrome (taken from the
Gameplay layout), one tab per section and the scrolling rows in catalog order. The Keyboard layout keeps its own
search and binding list; only its tabs and heading are rewritten. Run it after editing the catalog.
"""

import argparse
import copy
import sys
from pathlib import Path

import yaml
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "assets_dev/engine/ui/menu/settings_catalog.yml"
LAYOUTS = ROOT / "assets_dev/engine/ui/gameplay"
LUCIDA = ROOT / "assets_dev/engine/fonts/truetype/openyamm_lucida_faithful.ttf"
CHROME_SOURCE = "gameplay"

# Row metrics in canvas units (853.33 x 480), relative to the scroll viewport.
GROUP_HEIGHT = 18.1333
GROUP_TO_ROW = 25.6
LABEL_X = 1.6
INDENT = 12.0
LABEL_HEIGHT = 14.0752
LABEL_TO_DESCRIPTION = 16.2085
DESCRIPTION_LINE = 11.5168
ROW_GAP = 11.2
GROUP_GAP = 15.4667
CONTROL_RIGHT = 523.7333
DESCRIPTION_SCALE = 0.60235
LUCIDA_HEIGHT = 17
TAB_X = 91.7333
TAB_Y = 124.5835
TAB_PITCH = 39.4667
TAB_HEIGHT = 34.1333

CONTROLS = {
    "toggle": (70.4, 32.158),
    "select": (110.9333, 23.4667),
    # A select-sized field whose click opens a window of its own (the Rules tab's loot filter).
    "window": (110.9333, 23.4667),
    "range": (88.5333, 16.0),
    # A button the game draws itself, the size of Controls' Configure Keyboard.
    "action": (118.6501, 20.2667),
}
RANGE_VALUE_WIDTH = 26.6667
RANGE_VALUE_HEIGHT = 11.7333


def capitalized(value):
    return "".join(part[:1].upper() + part[1:] for part in value.replace("-", "_").split("_"))


def text(value, font, color, scale, align_x="left", pad_x=0.0):
    return {"value": value, "font": font, "color": color, "align_x": align_x, "align_y": "middle", "scale": scale,
            "pad_x": pad_x}


def element(id, x, y, width, height, interactive=False, **extra):
    result = {"id": id, "anchor": "top_left", "offset_x": round(x, 4), "offset_y": round(y, 4),
              "width": round(width, 4), "height": round(height, 4), "z_index": 10, "visible": True,
              "interactive": interactive}
    result.update(extra)
    return result


class DescriptionMeasure:
    def __init__(self):
        self.font = ImageFont.truetype(str(LUCIDA), LUCIDA_HEIGHT)

    def lines(self, value, width):
        """Line count of the runtime word wrap; a single line also may not need the runtime's squeeze to fit."""
        if not value:
            return 0
        lines, line = 1, ""
        for word in value.split():
            candidate = f"{line} {word}" if line else word
            if line and self.font.getlength(candidate) * DESCRIPTION_SCALE > width:
                lines += 1
                line = word
            else:
                line = candidate
        return lines


def setting_rows(prefix, settings, measure):
    rows = []
    groups = []
    y = 0.0
    group = None
    for index, setting in enumerate(settings):
        if setting["group"] != group:
            if group is not None:
                y += GROUP_GAP - ROW_GAP
            group = setting["group"]
            groups.append(element(f"{prefix}Group{len(groups)}", 0.0, y, 525.3333, GROUP_HEIGHT,
                                  text=text(group, "fondamento", "#e0c990", 0.4)))
            y += GROUP_TO_ROW
        id = prefix + capitalized(setting["id"])
        kind = setting["type"]
        x = LABEL_X + (INDENT if setting.get("depends") else 0.0)
        description = setting.get("desc", "")
        if kind == "steps":
            # A full-width slider under its label, with the chosen step named in the centre of the label line.
            line_width = CONTROL_RIGHT - x
            lines = max(1, measure.lines(description, line_width))
            rows.append(element(id + "Label", x, y, 216.7083, GROUP_HEIGHT,
                                text=text(setting["name"], "menu_arrus", "#eadfc6", 0.74105)))
            rows.append(element(id + "Value", x, y, line_width, GROUP_HEIGHT,
                                text=text("{" + setting["id"] + "}", "fondamento", "#e0c990", 0.45, "center")))
            rows.append(element(id + "Control", x + 4, y + 20.5, line_width - 8, 16.0, True))
            rows.append(element(id + "Description", x, y + 40.0, line_width, DESCRIPTION_LINE * lines,
                                text=text(description, "menu_lucida", "#aeb5a5", DESCRIPTION_SCALE)))
            y += 40.0 + DESCRIPTION_LINE * lines + ROW_GAP
            continue
        width, height = CONTROLS[kind]
        if kind == "range":
            control_x = CONTROL_RIGHT - RANGE_VALUE_WIDTH - 8.0 - width
        else:
            control_x = CONTROL_RIGHT - width
        text_width = control_x - 16.0 - x
        lines = measure.lines(description, text_width)
        block = LABEL_TO_DESCRIPTION + DESCRIPTION_LINE * lines if lines else LABEL_HEIGHT
        centre = y + block / 2
        rows.append(element(id + "Label", x, y, text_width, LABEL_HEIGHT,
                            text=text(setting["name"], "menu_arrus", "#eadfc6", 0.74105)))
        rows.append(element(id + "Description", x, y + (LABEL_TO_DESCRIPTION if lines else 0.0), text_width,
                            DESCRIPTION_LINE * lines if lines else LABEL_HEIGHT,
                            text=text(description, "menu_lucida", "#aeb5a5", DESCRIPTION_SCALE)))
        control = element(id + "Control", control_x, centre - height / 2, width, height, True)
        if kind == "toggle":
            control["asset"] = {"default": "hud_x2/menus/omenu_toggle_off.png",
                                "selected": "hud_x2/menus/omenu_toggle_on.png"}
        elif kind in ("select", "window"):
            control["asset"] = {"default": "hud_x2/menus/omenu_text_field.png"}
            control["text"] = text("{" + setting["id"] + "}", "menu_lucida", "#e9dcc0", 0.71529, pad_x=6.9333)
        rows.append(control)
        if kind == "range":
            rows.append(element(id + "Value", CONTROL_RIGHT - RANGE_VALUE_WIDTH, centre - RANGE_VALUE_HEIGHT / 2,
                                RANGE_VALUE_WIDTH, RANGE_VALUE_HEIGHT,
                                text=text("{" + setting["id"] + "}" + setting.get("unit", ""), "menu_lucida",
                                          "#eadfc6", 0.67765)))
        y += block + ROW_GAP
        if index + 1 == len(settings):
            y += GROUP_GAP - ROW_GAP
    return groups + rows, y


def tabs(prefix, sections, current, template):
    result = []
    for index, section in enumerate(sections):
        # Sections that never show together may share a slot.
        index = section.get("slot", index)
        tab = copy.deepcopy(template)
        tab["id"] = prefix + "Tab" + capitalized(section["id"])
        tab["offset_x"] = TAB_X
        tab["offset_y"] = round(TAB_Y + index * TAB_PITCH, 4)
        tab["height"] = TAB_HEIGHT
        tab["text"]["value"] = section["name"]
        tab["text"]["color"] = "#f5dfae" if section["id"] == current else "#bfc1b2"
        result.append(tab)
    return result


def renamed(node, old, new):
    if isinstance(node, dict):
        return {key: renamed(value, old, new) for key, value in node.items()}
    if isinstance(node, list):
        return [renamed(value, old, new) for value in node]
    if isinstance(node, str) and node.startswith(old):
        return new + node[len(old):]
    return node


def rebuild_chrome(root, prefix, sections, section, tab_template):
    children = []
    for child in root["children"]:
        if child["id"].startswith(prefix + "Tab"):
            if child["id"] == prefix + "Tab" + capitalized(sections[0]["id"]):
                children.extend(tabs(prefix, sections, section["id"], tab_template))
            continue
        if child["id"] == prefix + "Heading":
            child["text"]["value"] = section["name"]
        children.append(child)
    root["children"] = children


def layout_text(layout):
    return yaml.dump(layout, sort_keys=False, allow_unicode=True, width=116)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when a layout differs from the catalog")
    args = parser.parse_args()
    catalog = yaml.safe_load(CATALOG.read_text())
    sections = catalog["sections"]
    measure = DescriptionMeasure()
    source_prefix = "Settings" + capitalized(CHROME_SOURCE)
    chrome = yaml.safe_load((LAYOUTS / f"settings_{CHROME_SOURCE}.yml").read_text())
    chrome_root = chrome["elements"][0]
    tab_template = next(child for child in chrome_root["children"] if child["id"].startswith(source_prefix + "Tab"))
    outputs = {}
    for section in sections:
        prefix = "Settings" + capitalized(section["id"])
        path = LAYOUTS / f"settings_{section['id']}.yml"
        if section["id"] == "keyboard":
            layout = yaml.safe_load(path.read_text())
            rebuild_chrome(layout["elements"][0], prefix, sections, section, renamed(tab_template, source_prefix,
                                                                                       prefix))
            outputs[path] = layout_text(layout)
            continue
        layout = renamed(copy.deepcopy(chrome), source_prefix, prefix)
        root = layout["elements"][0]
        rebuild_chrome(root, prefix, sections, section, renamed(tab_template, source_prefix, prefix))
        settings = [setting for setting in catalog["settings"] if setting["section"] == section["id"]]
        rows, height = setting_rows(prefix, settings, measure)
        viewport = next(child for child in root["children"] if child["id"] == prefix + "ScrollViewport")
        if section["id"] == "controls":
            # The controller draws the Configure Keyboard button here, below the last row.
            rows.insert(0, element(prefix + "KeyboardButton", 0.0, height + 6.0, 118.6501, 20.2667, True))
        viewport["children"] = rows
        outputs[path] = layout_text(layout)
    stale = [path for path, value in outputs.items() if not path.exists() or path.read_text() != value]
    if args.check:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.write_text(outputs[path])
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
