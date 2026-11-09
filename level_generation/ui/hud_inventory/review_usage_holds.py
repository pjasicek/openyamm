"""Record the bounded 1,882-file reference review, not a future unknown-file exclusion rule.

These are restoration-scope decisions, never runtime deletion approvals. Run once against
the original usage_scope.json holds. The resulting exact-path/hash manifest is authoritative;
new unknown files still require review. Runtime-positive evidence always wins in the overlay.
"""
import collections
import json
from pathlib import Path
import re

from audit_usage_scope import OUT, ROOT, sha

REVIEW = OUT / 'usage_hold_review.json'
EVIDENCE = [
    'game/gameplay/GameplayScreenRuntime.cpp',
    'game/gameplay/GameplayInteractionController.cpp',
    'game/gameplay/MercenaryRecruitmentRuntime.cpp',
    'game/ui/GameplayHudRenderer.cpp',
    'game/ui/GameplayPartyOverlayRenderer.cpp',
    'game/ui/GameplayUiRuntime.cpp',
    'game/ui/screens/NewGameScreen.cpp',
    'game/tables/CharacterDollTable.cpp',
    'assets_dev/engine/data_tables/character_data.txt',
    'assets_dev/engine/data_tables/items.txt',
    'assets_dev/engine/ui/gameplay/gameplay_mobile.yml',
    'assets_dev/engine/ui/gameplay/spellbook.yml',
]


def resolve(row):
    """Categorize this reviewed cohort; caller freezes every path and byte hash."""
    name = Path(row['source_path']).stem.lower()
    treatment = row['historical_treatment']
    if row['references'] or row['dynamic_evidence']:
        raise ValueError('Not an unresolved reference-audit hold')
    if re.fullmatch(r'context_.+_(default|pressed)|interact_pressed', name):
        return ('dynamic_consumer_candidate', 'context_button_state',
                'GameplayInteractionController::contextActionIconIdFromMetadata forms context_ + kind; '
                'GameplayHudRenderer::loadContextActionIcon appends _default/_pressed. '
                'Protect the metadata-addressable family, including fallback interact_pressed.')
    if treatment == 'player_portrait_frames':
        if not re.fullmatch(r'7pc(?:09|11|21|22)-\d{2}', name):
            raise ValueError(f'Unreviewed portrait family: {name}')
        return ('excluded_unreferenced_art', 'unselected_portrait_prefix',
                'These four 7pc prefixes are absent from character_data column 19. NewGameScreen and '
                'MercenaryRecruitmentRuntime choose table prefixes; GameplayUiRuntime replaces only the '
                'last two frame digits. Its numeric fallback is PC, not 7pc. Preserve native files for old saves.')
    if treatment == 'paperdoll_parts':
        return ('excluded_unreferenced_art', 'unselected_paperdoll_part',
                'CharacterDollTable reads explicit asset columns 8-14,17,18; these names have no table or '
                'authored runtime reference. Paperdoll rendering uses those selected assets, not a directory census.')
    if treatment == 'fitted_equipment_variants' or re.fullmatch(r'(?:7)?item\d+v\d.*', name):
        return ('excluded_unreferenced_art', 'unselected_equipment_layer',
                'GameplayScreenRuntime::resolveEquippedItemHudTextureName joins items.iconName with v1-v5 '
                'and optional a only. Held b/c/a1 layers are not generated; held ordinary v/a variants '
                'have no matching item-table base (item330, 7item64). No direct reference bypasses this rule.')
    if re.fullmatch(r'item\d+|belt\d+b|coin(?:lg|mid|sm)|rat-tail|raygun1a|thybone', name):
        return ('excluded_unreferenced_art', 'unselected_item_art',
                'Not an iconName in the merged items table, not a supported equipped suffix, and no '
                'authored runtime reference. World pickups resolve item definitions, not arbitrary icon-directory entries.')
    if treatment == 'ui_animation_family':
        if not re.fullmatch(r'terra\d{3}', name):
            raise ValueError(f'Unreviewed animation: {name}')
        return ('excluded_unreferenced_art', 'obsolete_three_digit_rest_sky',
                'GameplayPartyOverlayRenderer::formatRestSkyTextureName requests terra%04d. '
                'These terra000-terra239 three-digit names are a separate unused sequence, not those four-digit frames.')
    if re.fullmatch(r'(?:ascend|descend|menu|use)_(?:default|pressed)|context_disabled', name):
        return ('excluded_unreferenced_art', 'unselected_modern_ui_alternative',
                'No authored UI or runtime reference. Mobile UI selects ascend_compact/descend_compact '
                'states; context actions select context_<kind> states and interact fallback. '
                'These are modern alternatives, not incorrectly labelled original MM6/MM7 artwork.')
    if treatment in {'legacy_ui_art', 'spellbook_page', 'ui_background', 'ui_frame_or_panel', 'ui_state_set'}:
        return ('excluded_unreferenced_art', 'unselected_legacy_interface',
                'Reviewed legacy interface/spellbook/animation/old character-creation art with no current '
                'table, authored UI or literal consumer reference. Checked dynamic consumers: table-selected '
                'paperdolls and portrait prefixes, item v1-v5/a suffixes, formatted NPC/PC frames, '
                'four-digit rest sky, HGLAS hourglass, IRA journal frames and context button states. '
                'Not selected for restoration under the runtime-backed-only scope; native compatibility files remain.')
    if name in {'ib-foot-a', 'ib-foot-b', 'ib-foot-c', 'ib-l-a', 'ib-t-a', 'maketop'}:
        return ('excluded_unreferenced_art', 'unselected_pcx_interface',
                'PCX copies of old interface panels; no current table/UI/loader-name reference. '
                'Do not restore or delete these compatibility originals.')
    raise ValueError(f'Unreviewed hold: {row["source_path"]}')


def main():
    if REVIEW.exists():
        raise SystemExit('Review manifest already exists; do not replace the frozen reviewed cohort.')
    usage = json.loads((OUT / 'usage_scope.json').read_text())
    holds = [r for r in usage['files'] if r['status'] == 'usage_audit_hold']
    assert len(holds) == 1882, 'This review is specifically the original 1,882-file hold cohort'
    decisions = []
    for row in holds:
        assert row['source_path'].startswith('assets_dev/engine/icons/')
        status, rule, reason = resolve(row)
        decisions.append(dict(source_path=row['source_path'], source_sha256=row['source_sha256'],
                              status=status, rule=rule, reason=reason))
    document = dict(cohort_size=len(decisions),
                    scope='Current restoration selection only; no runtime deletion or old-save migration.',
                    statuses=dict(collections.Counter(r['status'] for r in decisions)),
                    rules=dict(collections.Counter(r['rule'] for r in decisions)),
                    evidence_hashes={p: sha(ROOT / p) for p in EVIDENCE}, files=decisions)
    REVIEW.write_text(json.dumps(document, indent=2) + '\n')
    print(json.dumps({k: v for k, v in document.items() if k not in ('files', 'evidence_hashes')}, indent=2))


if __name__ == '__main__':
    main()
