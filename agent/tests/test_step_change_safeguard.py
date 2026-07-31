"""Tests for the refinement step-change-ratio safeguard and its exemption.

The safeguard catches *linguistic* steps that change an unexpectedly large
fraction of rows. A pure structural formatter (`tsv-schema`) legitimately
rewrites almost every row without touching the linguistic payload, so it sets
``enforce_change_ratio = False`` and the safeguard must skip it. The schema
formatter's own counting must also keep ``rows_changed <= rows_processed`` so
the ratio is a true fraction.
"""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.base import RefinementStep, StepResult
from pipeline.steps.nominal_feature_completion import NominalFeatureCompletionFixer
from pipeline.steps.schema_formatter import TsvSchemaFormatter
from pipeline.steps.variant_row_unwrapper import VariantRowUnwrapper
from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline


class _FakeStep(RefinementStep):
    def __init__(
        self,
        *,
        changed: int,
        processed: int,
        enforce: bool,
        max_change_ratio: float | None = None,
    ) -> None:
        self._changed = changed
        self._processed = processed
        self.enforce_change_ratio = enforce
        self.max_change_ratio = max_change_ratio

    @property
    def name(self) -> str:
        return "fake-step"

    def refine_row(self, row):
        return row

    def refine_file(self, path: Path) -> StepResult:
        return StepResult(
            file=path.name, rows_processed=self._processed, rows_changed=self._changed
        )


def _pipeline(out_dir: Path) -> TabletParsingPipeline:
    config = PipelineConfig(
        source_dir=out_dir,
        out_dir=out_dir,
        dulat_db=out_dir / "dulat.sqlite",
        udb_db=out_dir / "udb.sqlite",
        include_existing=False,
        allow_large_step_changes=False,
        max_step_change_ratio=0.25,
    )
    return TabletParsingPipeline(config=config)


class SafeguardExemptionTest(unittest.TestCase):
    def _run(self, *, enforce: bool):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir)
            (out / "KTU 1.test.tsv").write_text("x", encoding="utf-8")
            pipeline = _pipeline(out)
            pipeline._refinement_steps = [
                _FakeStep(changed=97, processed=100, enforce=enforce)
            ]
            return pipeline.apply_refinement_steps([Path("KTU 1.test.tsv")])

    def _run_with_step_limit(self, *, limit: float):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir)
            (out / "KTU 1.test.tsv").write_text("x", encoding="utf-8")
            pipeline = _pipeline(out)
            pipeline._refinement_steps = [
                _FakeStep(changed=44, processed=100, enforce=True, max_change_ratio=limit)
            ]
            return pipeline.apply_refinement_steps([Path("KTU 1.test.tsv")])

    def test_enforced_step_over_ratio_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            self._run(enforce=True)

    def test_exempt_step_over_ratio_does_not_raise(self) -> None:
        details = self._run(enforce=False)
        self.assertEqual(details["step_fake-step_changed"], 97)

    def test_step_specific_ratio_can_exceed_global_default(self) -> None:
        details = self._run_with_step_limit(limit=0.50)
        self.assertEqual(details["step_fake-step_changed"], 44)

    def test_step_specific_ratio_still_enforces_its_ceiling(self) -> None:
        with self.assertRaises(RuntimeError):
            self._run_with_step_limit(limit=0.40)


class SchemaFormatterCountingTest(unittest.TestCase):
    def test_formatter_is_exempt(self) -> None:
        self.assertFalse(TsvSchemaFormatter().enforce_change_ratio)
        self.assertTrue(RefinementStep.enforce_change_ratio)

    def test_variant_unwrapper_is_exempt(self) -> None:
        self.assertFalse(VariantRowUnwrapper().enforce_change_ratio)

    def test_nominal_completion_has_guarded_clean_bootstrap_ceiling(self) -> None:
        self.assertEqual(NominalFeatureCompletionFixer.max_change_ratio, 0.50)

    def test_changed_never_exceeds_processed(self) -> None:
        # Non-canonical input: bad header, un-normalized separator, a data row
        # with doubled quotes, and a short-column data row.
        content = (
            "id\tsurface\n"  # header-like, not canonical
            "#KTU 1.1 I:1\n"  # separator needing normalization
            '1\tab\tab[\t/a-b/\tvb G suffc.\t""x""\n'  # data row, quote fixup
            "2\tcd\tcd/\n"  # short-column data row
            "\n"  # blank line — passed through, not counted
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")
            result = TsvSchemaFormatter().refine_file(path)
            self.assertLessEqual(result.rows_changed, result.rows_processed)
            self.assertGreater(result.rows_processed, 0)

    def test_formatter_is_idempotent_on_canonical_output(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.1 I:1\t\t\t\t\t\t\n"
            "1\tab\tab[\t/a-b/\tvb G suffc. 3 m. sg.\tto do\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")
            first = TsvSchemaFormatter().refine_file(path)
            second = TsvSchemaFormatter().refine_file(path)
            self.assertEqual(second.rows_changed, 0, "formatter must be idempotent")
            self.assertLessEqual(first.rows_changed, first.rows_processed)


if __name__ == "__main__":
    unittest.main()
