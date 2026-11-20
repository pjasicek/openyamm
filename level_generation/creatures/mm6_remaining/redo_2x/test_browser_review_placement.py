"""Mechanical browser coverage cannot substitute for watched visual review."""
import unittest

from freeze_review import validate_browser_review


class BrowserReviewAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.playback = dict(status='passed', manifest_sha256='current',
                             bindings=[dict(all_frames_seen=True)], visual_acceptance=False)
        self.decision = dict(checks=dict(watched_playback=True))

    def test_mechanical_success_does_not_establish_watched_review(self):
        for checks in ({}, {'watched_playback': False}, {'watched_playback': 'true'}):
            with self.subTest(checks=checks), self.assertRaisesRegex(AssertionError, 'watched_playback'):
                validate_browser_review(dict(checks=checks), self.playback, 'current')

    def test_declared_review_still_requires_current_complete_mechanical_evidence(self):
        for change in (dict(manifest_sha256='old'), dict(bindings=[]),
                       dict(bindings=[dict(all_frames_seen=False)]), dict(status='failed')):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                validate_browser_review(self.decision, dict(self.playback, **change), 'current')

    def test_explicit_watched_review_is_distinct_from_mechanical_record(self):
        validate_browser_review(self.decision, self.playback, 'current')
        self.assertFalse(self.playback['visual_acceptance'])


if __name__ == '__main__':
    unittest.main()
