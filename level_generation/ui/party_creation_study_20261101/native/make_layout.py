#!/usr/bin/env python3
"""Writes assets_dev/engine/ui/gameplay/character_creation.yml for the party creation screen, approach C2.

Geometry is the mockup's (c2.html), in its 1600x900 browser pixels, converted to the 853.33x480 menu canvas
(x 8/15, MenuDesignScreen BrowserToLogical). The layout holds the screen's regions and fixed labels; NewGameScreen lays
out the repeated rows (roster cards, attribute rows, skill rows) inside them.

    python3 level_generation/ui/party_creation_study_20261101/native/make_layout.py
"""
import os

import yaml

PX = 8 / 15
OUT = os.path.join(os.path.dirname(__file__), "../../../../assets_dev/engine/ui/gameplay/character_creation.yml")
FONT_HEIGHT = {"fondamento": 32, "menu_arrus": 19, "menu_lucida": 17}
# The mockup's Arrus and Lucida faces are the faithful TTFs at size-adjust 120%; Fondamento is unadjusted.
SIZE_ADJUST = {"fondamento": 1.0, "menu_arrus": 1.2, "menu_lucida": 1.2}


def r(value):
    return round(value * PX, 4)


def element(element_id, x, y, w, h, asset=None, text=None, notes=None, interactive=None, z_index=10):
    entry = {
        "id": element_id,
        "anchor": "top_left",
        "offset_x": r(x),
        "offset_y": r(y),
        "width": r(w),
        "height": r(h),
        "z_index": z_index,
        "visible": True,
        # Buttons and fields draw themselves; MenuDesignScreen::drawDesign draws only the static elements.
        "interactive": interactive if interactive is not None
        else bool(asset and "button" in asset or "Field" in element_id),
    }
    if asset:
        entry["asset"] = {"default": asset}
    if text:
        entry["text"] = text
    if notes:
        entry["notes"] = notes
    return entry


def text(value, font, css_px, color, align="left"):
    return {
        "value": value,
        "font": font,
        "color": color,
        "align_x": align,
        "align_y": "middle",
        "scale": round(css_px * SIZE_ADJUST[font] * PX / FONT_HEIGHT[font], 5),
        "pad_x": 0.0,
    }


def main():
    children = [
        element("CharacterCreationBackground", 0, 0, 1600, 900, asset="hud_x2/menus/omenu_title_backdrop.png",
                notes="Use the live dimmed game view instead when entered from Pause.", z_index=0),
        element("CharacterCreationPanel", 4, 4, 1592, 892, asset="hud_x2/menus/omenu_party_frame.png", z_index=2),
        element("CharacterCreationTitle", 58, 30, 330, 58,
                text=text("Create Your Party", "fondamento", 40, "#efe0bc")),
        element("CharacterCreationContinent", 388, 30, 380, 58,
                text=text("{continent} · {ruleset}", "menu_lucida", 15, "#b7b39f"),
                notes="Controller supplies the starting continent and ruleset."),
        element("CharacterCreationPartySummary", 760, 30, 782, 58,
                text=text("{coverage} · {party_count} / 5 adventurers · {ready_count} ready", "menu_lucida", 15,
                          "#b7b39f", "right"),
                notes="Controller supplies the party's skill coverage and readiness."),
        element("CharacterCreationHeadRule", 58, 88, 1484, 1),
        element("CharacterCreationRoster", 58, 100, 206, 694,
                notes="Roster rail: one card per adventurer (130 px, 7 px apart) and the Add card (70 px)."),
        element("CharacterCreationNameLabel", 278, 100, 282, 14, text=text("NAME", "menu_lucida", 12, "#93977f")),
        element("CharacterCreationNameField", 278, 115, 282, 38, asset="hud_x2/menus/omenu_text_field.png",
                text=text("{character_name}", "menu_arrus", 23, "#eadfc6")),
        element("CharacterCreationClassLabel", 278, 159, 282, 14, text=text("CLASS", "menu_lucida", 12, "#93977f")),
        element("CharacterCreationClassValue", 278, 174, 282, 44,
                asset="hud_x2/menus/omenu_button_quiet_default.png",
                notes="Class icon, class name (Fondamento 27 px) and a chevron; opens the class picker."),
        element("CharacterCreationVoiceCard", 278, 224, 282, 80,
                notes="Voice title opens the voice picker; three sample lines below."),
        element("CharacterCreationAttributes", 574, 100, 296, 262,
                notes="Header row (22 px) and seven 34 px attribute rows."),
        element("CharacterCreationAttributesCaption", 574, 100, 120, 22,
                text=text("ATTRIBUTES", "menu_lucida", 13, "#9fa294")),
        element("CharacterCreationRaceCard", 884, 100, 290, 262,
                notes="Race name and the race card lines (PartyCreationSheet raceCardLines)."),
        element("CharacterCreationSkills", 278, 374, 896, 420,
                notes="Header row (34 px) and the learnable skills in three balanced columns."),
        element("CharacterCreationSkillsTitle", 290, 380, 90, 34, text=text("Skills", "fondamento", 25, "#e6d1a8")),
        element("CharacterCreationMasteryTableButton", 966, 383, 108, 28,
                asset="hud_x2/menus/omenu_button_small_default.png",
                text=text("Mastery table", "fondamento", 16, "#cbc5af", "center")),
        element("CharacterCreationPartyBoardButton", 1080, 383, 82, 28,
                asset="hud_x2/menus/omenu_button_small_default.png",
                text=text("Party board", "fondamento", 16, "#cbc5af", "center")),
        element("CharacterCreationDollColumn", 1190, 100, 352, 694),
        element("CharacterCreationDoll", 1219, 112, 294, 635,
                notes="Native paperdoll composition; opens the portrait picker."),
        element("CharacterCreationChangePortraitButton", 1219, 759, 132, 28,
                asset="hud_x2/menus/omenu_button_small_default.png",
                text=text("Change portrait", "fondamento", 16, "#cbc5af", "center")),
        element("CharacterCreationResetCharacterButton", 1357, 759, 74, 28,
                asset="hud_x2/menus/omenu_button_small_default.png",
                text=text("Default", "fondamento", 16, "#cbc5af", "center")),
        element("CharacterCreationRemoveCharacterButton", 1437, 759, 76, 28,
                asset="hud_x2/menus/omenu_button_small_default.png",
                text=text("Remove", "fondamento", 16, "#cbc5af", "center")),
        element("CharacterCreationFooterRule", 58, 810, 1484, 1),
        element("CharacterCreationCancelButton", 58, 820, 124, 44, asset="hud_x2/menus/omenu_button_quiet_default.png",
                text=text("Cancel", "fondamento", 26, "#cbc5af", "center")),
        element("CharacterCreationReadiness", 300, 820, 1000, 44,
                text=text("{party_readiness_message}", "menu_lucida", 15, "#c8c1a8", "center")),
        element("CharacterCreationConfirmButton", 1300, 820, 242, 44,
                asset="hud_x2/menus/omenu_button_primary_default.png",
                text=text("Begin Adventure", "fondamento", 26, "#ffe4ac", "center")),
    ]
    root = {
        "id": "CharacterCreationRoot",
        "anchor": "center",
        "anchor_space": "screen",
        "width": 853.3333,
        "height": 480,
        "z_index": 0,
        "scale": {"min": 0.1, "max": 8.0, "reference_width": 853.3333, "reference_height": 480},
        "notes": "Native menu canvas fitted uniformly by MenuDesignScreen. Generated by "
                 "level_generation/ui/party_creation_study_20261101/native/make_layout.py.",
        "children": children,
    }
    with open(OUT, "w") as handle:
        handle.write("# Generated by level_generation/ui/party_creation_study_20261101/native/make_layout.py.\n")
        yaml.safe_dump({"screen": "CharacterCreation", "elements": [root]}, handle, sort_keys=False, width=120,
                       allow_unicode=True)


if __name__ == "__main__":
    main()
