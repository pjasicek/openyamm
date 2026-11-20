from pathlib import Path
import unittest
from unittest.mock import patch

import l10n


class LuaTextExtractionTests(unittest.TestCase):
    def extracted(self, source):
        template = l10n.Template()
        with patch.object(l10n, "read_text", return_value=source), \
                patch.object(l10n, "relative", return_value="sample.lua"):
            l10n.extract_lua_file(template, Path("sample.lua"), "engine")
        return {entry.msgid for entry in template.domains["engine"].values()}

    def test_nested_lookup_keys_are_not_display_text(self):
        self.assertEqual(self.extracted(
            'evt.SetMessage(evt.RulesTopic("internal_topic_key") or "Fallback text")'), {"Fallback text"})

    def test_literal_sentences_and_separate_text_arguments_remain(self):
        self.assertEqual(self.extracted(
            'evt.SetMessage("A complete " .. "sentence.")\n'
            'evt.Question("A question?", "Answer one", "Answer two")'),
            {"A complete sentence.", "A question?", "Answer one", "Answer two"})


if __name__ == "__main__":
    unittest.main()
