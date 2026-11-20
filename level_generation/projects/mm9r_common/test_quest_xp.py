"""Tests of the rework's quest XP caps (quest_xp.py, quest_xp_audit.py).

    python3 -m pytest level_generation/projects/mm9r_common/test_quest_xp.py
"""
from __future__ import annotations

import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(COMMON))

import quest_xp  # noqa: E402
import quest_xp_audit  # noqa: E402
from quest_xp import balanced_experience, experience_lua, experience_note  # noqa: E402

PROFILE = """format_version: 1
awards:
- script: npc88.scr
  routine: promo
  original: 63000
  xp: 37500
  key: 227
- script: ilshealerroom.scr
  routine: OnPromo
  original: 63000
  xp: 55500
  key: null
- script: npc129.scr
  routine: priest
  original: 63000
  xp: 37500
  key: 252
"""


def profile(tmp_path: Path) -> Path:
    path = tmp_path / "profile.yml"
    path.write_text(PROFILE, encoding="utf-8")
    return path


def test_key_and_original_pick_the_balanced_amount(tmp_path):
    path = profile(tmp_path)
    assert balanced_experience(63000, key=227, path=path) == 37500
    # the key alone is not enough: another amount under that key is not in the profile
    assert balanced_experience(5000, key=227, path=path) == 5000


def test_keyless_entry_matches_by_script_and_routine(tmp_path):
    path = profile(tmp_path)
    assert balanced_experience(63000, script="ilshealerroom.scr", routine="OnPromo", path=path) == 55500
    assert balanced_experience(63000, key=299, script="ILSHEALERROOM.SCR", routine="onpromo", path=path) == 55500
    assert balanced_experience(63000, path=path) == 63000


def test_script_fallback_covers_a_rework_key_that_differs_from_the_profile(tmp_path):
    path = profile(tmp_path)
    assert balanced_experience(63000, key=261, path=path) == 63000
    assert balanced_experience(63000, key=261, script="npc129.scr", routine="priest", path=path) == 37500


def test_award_not_in_the_profile_keeps_its_amount(tmp_path):
    path = profile(tmp_path)
    assert balanced_experience(2000, key=471, path=path) == 2000
    assert experience_note(2000, key=471, path=path) == ""
    assert experience_lua(2000, key=471, path=path) == "MM9.giveExperience(2000)"


def test_capped_award_carries_the_original_in_a_comment(tmp_path):
    path = profile(tmp_path)
    assert experience_lua(63000, key=227, path=path) == \
        "MM9.giveExperience(37500) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml"
    assert experience_note(63000, key=227, path=path) == " -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml"


def test_real_profile_has_the_agreed_caps():
    by_key, by_script = quest_xp.load_profile()
    assert len(by_script) == 59
    assert balanced_experience(63000, key=227) == 37500           # second-tier promotion
    assert balanced_experience(24500, key=137) == 16500           # first-tier promotion
    assert balanced_experience(63000, script="ilshealerroom.scr", routine="OnPromo") == 55500   # the Lich
    assert balanced_experience(14000, key=80) == 12500            # Mountain Pass
    assert balanced_experience(14000, key=176) == 14000           # its second branch's key is not in the profile


def test_audit_resolves_every_site_and_accounts_for_every_profile_entry():
    sites = quest_xp_audit.scan_sites()
    entries = quest_xp_audit.profile_entries()
    assert sites and all(isinstance(site["original"], int) for site in sites)
    unmatched = [e for e in entries if not any(quest_xp_audit.matches(e, s) for s in sites)]
    for entry in unmatched:
        assert (entry["script"], entry["routine"], entry["original"]) in quest_xp_audit.UNMATCHED_REASONS, entry
    # no site pays an original amount the profile caps without the cap
    for site in sites:
        capped = [e for e in entries if quest_xp_audit.matches(e, site)]
        if capped:
            assert site["balanced"] == capped[0]["xp"], site
