import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "review-automatic-parsing"
    / "scripts"
    / "sources_lookup.py"
)
SPEC = spec_from_file_location("sources_lookup", SCRIPT)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourcesLookupReferenceTests(unittest.TestCase):
    def test_column_reference_uses_current_ktu_cache_key(self):
        self.assertEqual(MODULE.to_ref("1.14:IV:35"), "KTU 1.14 IV:35")
        self.assertEqual(MODULE.to_dulat_ref("1.14:IV:35"), "KTU 1.14 IV:35")

    def test_columnless_line_maps_to_cache_column_i(self):
        self.assertEqual(MODULE.to_ref("2.10:7"), "KTU 2.10 I:7")
        self.assertEqual(MODULE.to_dulat_ref("2.10:7"), "KTU 2.10:7")

    def test_dulat_line_scope_is_exact(self):
        query, params = MODULE.dulat_scope_query("KTU 2.22:4")
        self.assertIn("where norm_ref=? order", query)
        self.assertEqual(params, ("KTU 2.22:4",))

    def test_dulat_tablet_scope_includes_line_and_column_refs(self):
        query, params = MODULE.dulat_scope_query("KTU 2.22")
        self.assertIn("norm_ref like ?", query)
        self.assertEqual(params, ("KTU 2.22", "KTU 2.22:%", "KTU 2.22 %"))


if __name__ == "__main__":
    unittest.main()
