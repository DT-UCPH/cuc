"""Tests for extracting fallback forms from `entries.text` forms blocks."""

import unittest

from pipeline.config.dulat_entry_forms_fallback import extract_forms_from_entry_text


class DulatEntryFormsFallbackTest(unittest.TestCase):
    def test_extracts_italic_form_tokens_from_forms_block(self) -> None:
        text = (
            "<b>¶ Forms:</b> G suffc. <i>ġly</i>; prefc. <i>yġly</i>; inf. <i>ġly</i>. "
            "D suffc. <i>ġltm</i>; prefc. <i>tġly</i>, <i>tġl</i> (?). <br><b>G</b>."
        )
        self.assertEqual(
            extract_forms_from_entry_text(text),
            ("ġly", "yġly", "ġltm", "tġly", "tġl"),
        )

    def test_returns_empty_when_no_forms_block(self) -> None:
        self.assertEqual(extract_forms_from_entry_text("<b>G</b> something else"), ())

    def test_merges_word_break_markers_between_italic_tokens(self) -> None:
        text = (
            "<b>¶ Forms:</b> prefc. <i>ytn</i>{.}<i>hm</i>, <i>ytnn</i>, "
            "<i>ytn</i>{.}<i>nn</i>; impv. <i>tn</i>. <br><b>G</b>."
        )
        forms = extract_forms_from_entry_text(text)
        self.assertIn("ytnhm", forms)
        self.assertIn("ytnnn", forms)
        self.assertNotIn("hm", forms)
        self.assertNotIn("nn", forms)

    def test_truncates_before_examples_and_ignores_example_tokens(self) -> None:
        text = (
            "<b>¶ Forms:</b> sg. <i>ảrḫ</i>; pl. <i>ảrḫt</i>. "
            "Cow: <i>k lb ảrḫ l ʕglh</i> ... (// <i>ảlp</i>)."
        )
        forms = extract_forms_from_entry_text(text)
        self.assertEqual(forms, ("ảrḫ", "ảrḫt"))
        self.assertNotIn("ảlp", forms)

    def test_merges_restoration_marker_italic_splits(self) -> None:
        text = (
            "<b>¶ Forms:</b> sg. <i>mtnt</i>; du. <i>mtntm</i>, "
            "<i>mt</i>&lt;<i>n</i>&gt;<i>tm</i> (1.130:19)."
        )
        forms = extract_forms_from_entry_text(text)
        self.assertIn("mtnt", forms)
        self.assertIn("mtntm", forms)
        self.assertNotIn("mt", forms)
        self.assertNotIn("tm", forms)

    def test_preserves_non_ascii_letters_without_collapsing_forms(self) -> None:
        text = "<b>¶ Forms:</b> sg. <i>śśw</i>; f. <i>śśwt</i>; pl. <i>sswm</i>, <i>śśwm</i>."
        forms = extract_forms_from_entry_text(text)
        self.assertIn("śśw", forms)
        self.assertIn("śśwt", forms)
        self.assertIn("sswm", forms)
        self.assertIn("śśwm", forms)
        self.assertNotIn("wm", forms)
        self.assertNotIn("wt", forms)


if __name__ == "__main__":
    unittest.main()
