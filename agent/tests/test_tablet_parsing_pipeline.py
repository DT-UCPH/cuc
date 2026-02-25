import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline


class TabletParsingPipelineTest(unittest.TestCase):
    def test_default_glob_includes_ktu2_family(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 2.1.tsv").write_text("", encoding="utf-8")

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=False,
            )
            pipeline = TabletParsingPipeline(config=config)
            targets = pipeline.select_targets()

            self.assertEqual([p.name for p in targets], ["KTU 2.1.tsv"])

    def test_select_targets_missing_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 1.1.tsv").write_text("", encoding="utf-8")
            (src / "KTU 1.2.tsv").write_text("", encoding="utf-8")
            (src / "KTU 1.3.tsv").write_text("", encoding="utf-8")
            (out / "KTU 1.1.tsv").write_text("", encoding="utf-8")

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=False,
            )
            pipeline = TabletParsingPipeline(config=config)
            targets = pipeline.select_targets()

            self.assertEqual([p.name for p in targets], ["KTU 1.2.tsv", "KTU 1.3.tsv"])

    def test_select_targets_explicit(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 1.170.tsv").write_text("", encoding="utf-8")
            (src / "KTU 1.171.tsv").write_text("", encoding="utf-8")

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=False,
            )
            pipeline = TabletParsingPipeline(config=config)
            targets = pipeline.select_targets(explicit_names=["KTU 1.171.tsv", "KTU 1.170.tsv"])

            self.assertEqual([p.name for p in targets], ["KTU 1.170.tsv", "KTU 1.171.tsv"])

    def test_run_dry_run_returns_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)
            (src / "KTU 1.180.tsv").write_text("", encoding="utf-8")

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=False,
            )
            pipeline = TabletParsingPipeline(config=config)
            result = pipeline.run(dry_run=True)

            self.assertEqual(result["targets"], ["KTU 1.180.tsv"])
            self.assertEqual(result["target_count"], 1)
            self.assertEqual(result["bootstrap_target_count"], 1)
            self.assertEqual(result["preserved_target_count"], 0)
            self.assertTrue(result["dry_run"])

    def test_partition_targets_for_bootstrap_preserves_existing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 1.1.tsv").write_text("", encoding="utf-8")
            (src / "KTU 1.2.tsv").write_text("", encoding="utf-8")
            (out / "KTU 1.1.tsv").write_text("id\tsurface form\n", encoding="utf-8")

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=True,
            )
            pipeline = TabletParsingPipeline(config=config)
            targets = pipeline.select_targets()
            bootstrap_targets, preserved_targets = pipeline.partition_targets_for_bootstrap(targets)

            self.assertEqual([p.name for p in targets], ["KTU 1.1.tsv", "KTU 1.2.tsv"])
            self.assertEqual([p.name for p in bootstrap_targets], ["KTU 1.2.tsv"])
            self.assertEqual([p.name for p in preserved_targets], ["KTU 1.1.tsv"])

    def test_run_include_existing_applies_instruction_refinement(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 1.1.tsv").write_text("", encoding="utf-8")
            (out / "KTU 1.1.tsv").write_text(
                "1\thwt\thwt(I)/\thwt (I)\tn.\tword\n",
                encoding="utf-8",
            )

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "missing.sqlite",
                udb_db=root / "missing.sqlite",
                include_existing=True,
            )
            pipeline = TabletParsingPipeline(config=config)
            with (
                patch.object(
                    pipeline,
                    "refine_targets",
                    return_value={"refine_rows": 0, "refine_changed": 0},
                ),
                patch.object(
                    pipeline,
                    "instruction_refine_targets",
                    return_value={
                        "instruction_refine_files": 1,
                        "instruction_refine_rows": 1,
                        "instruction_refine_changed": 1,
                    },
                ) as mock_instruction_refine,
                patch.object(
                    pipeline,
                    "apply_refinement_steps",
                    return_value={"refinement_steps_total_changed": 0},
                ),
                patch.object(
                    pipeline,
                    "regenerate_reports",
                    return_value=0,
                ),
            ):
                result = pipeline.run(dry_run=False)

            mock_instruction_refine.assert_called_once()
            self.assertEqual(result["instruction_refine_files"], 1)
            self.assertEqual(result["instruction_refine_rows"], 1)
            self.assertEqual(result["instruction_refine_changed"], 1)

    def test_run_include_existing_runs_refine_targets_for_preserved_outputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            (src / "KTU 1.1.tsv").write_text("", encoding="utf-8")
            (out / "KTU 1.1.tsv").write_text(
                "1\tyˤšr\t!y!ˤšr[:d\t/ʕ-š-r/\tvb D prefc.\tlegacy gloss\t\n",
                encoding="utf-8",
            )

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "missing.sqlite",
                udb_db=root / "missing.sqlite",
                include_existing=True,
            )
            pipeline = TabletParsingPipeline(config=config)
            with (
                patch.object(
                    pipeline,
                    "refine_targets",
                    return_value={"refine_rows": 1, "refine_changed": 1},
                ) as mock_refine,
                patch.object(
                    pipeline,
                    "instruction_refine_targets",
                    return_value={
                        "instruction_refine_files": 1,
                        "instruction_refine_rows": 1,
                        "instruction_refine_changed": 0,
                    },
                ),
                patch.object(
                    pipeline,
                    "apply_refinement_steps",
                    return_value={"refinement_steps_total_changed": 0},
                ),
                patch.object(
                    pipeline,
                    "regenerate_reports",
                    return_value=0,
                ),
            ):
                result = pipeline.run(dry_run=False)

            mock_refine.assert_called_once()
            called_targets = mock_refine.call_args.args[0]
            self.assertEqual([path.name for path in called_targets], ["KTU 1.1.tsv"])
            self.assertEqual(result["refine_rows"], 1)
            self.assertEqual(result["refine_changed"], 1)

    def test_suffix_payload_collapse_runs_after_known_ambiguities(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "cuc_tablets_tsv"
            out = root / "out"
            src.mkdir(parents=True)
            out.mkdir(parents=True)

            config = PipelineConfig(
                source_dir=src,
                out_dir=out,
                dulat_db=root / "dulat.sqlite",
                udb_db=root / "udb.sqlite",
                include_existing=False,
            )
            pipeline = TabletParsingPipeline(config=config)
            names = [step.name for step in pipeline._refinement_steps]

            self.assertLess(
                names.index("known-ambiguity-expander"),
                names.index("suffix-payload-collapse"),
            )
            self.assertLess(
                names.index("unwrapped-duplicate-pruner"),
                names.index("attestation-reference-disambiguator"),
            )
            self.assertLess(
                names.index("attestation-reference-disambiguator"),
                names.index("l-negation-verb-context"),
            )
            self.assertLess(
                names.index("l-negation-verb-context"),
                names.index("l-functor-vocative-context"),
            )
            self.assertLess(
                names.index("l-functor-vocative-context"),
                names.index("l-kbd-compound-prep"),
            )
            self.assertLess(
                names.index("l-kbd-compound-prep"),
                names.index("l-body-compound-prep"),
            )
            self.assertLess(
                names.index("l-body-compound-prep"),
                names.index("l-preposition-bigram-context"),
            )
            self.assertLess(
                names.index("l-preposition-bigram-context"),
                names.index("k-functor-bigram-context"),
            )
            self.assertLess(
                names.index("k-functor-bigram-context"),
                names.index("ydk-context-disambiguator"),
            )
            self.assertLess(
                names.index("ydk-context-disambiguator"),
                names.index("prefixed-iii-aleph-verb"),
            )
            self.assertLess(
                names.index("prefixed-iii-aleph-verb"),
                names.index("verb-pos-stem"),
            )
            self.assertLess(
                names.index("verb-pos-stem"),
                names.index("verb-form-morph-pos"),
            )
            self.assertLess(
                names.index("verb-form-morph-pos"),
                names.index("verb-form-encoding-split"),
            )
            self.assertLess(
                names.index("verb-form-encoding-split"),
                names.index("verb-l-stem-gemination"),
            )
            self.assertLess(
                names.index("verb-l-stem-gemination"),
                names.index("verb-stem-suffix-marker"),
            )
            self.assertLess(
                names.index("verb-stem-suffix-marker"),
                names.index("verb-n-stem-assimilation"),
            )
            self.assertLess(
                names.index("verb-n-stem-assimilation"),
                names.index("variant-row-unwrapper-post-verb"),
            )
            self.assertLess(
                names.index("variant-row-unwrapper-post-verb"),
                names.index("unwrapped-duplicate-pruner-post-verb"),
            )
            final_schema_index = len(names) - 1 - names[::-1].index("tsv-schema")
            self.assertLess(
                names.index("unwrapped-duplicate-pruner-post-verb"),
                final_schema_index,
            )


if __name__ == "__main__":
    unittest.main()
