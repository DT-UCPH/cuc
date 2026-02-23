"""Reusable pipeline for parsing KTU tablets into structured out/*.tsv files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import scripts.bootstrap_tablet_labeling as bootstrap
import scripts.refine_results_mentions as refine
from lint_reports.generator import LintReportGenerator
from pipeline.config.surface_option_allowlist import SURFACE_OPTION_PROPAGATION_ALLOWLIST
from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.instruction_refiner import InstructionRefiner
from pipeline.steps.attestation_sort import AttestationSortFixer
from pipeline.steps.baal_labourer_ktu1 import BaalLabourerKtu1Fixer
from pipeline.steps.baal_plural import BaalPluralGodListFixer
from pipeline.steps.base import RefinementStep
from pipeline.steps.dulat_gate import DulatMorphGate
from pipeline.steps.feminine_t_singular_split import FeminineTSingularSplitFixer
from pipeline.steps.formula_bigram import FormulaBigramFixer
from pipeline.steps.formula_trigram import FormulaTrigramFixer
from pipeline.steps.generic_parsing_override import GenericParsingOverrideFixer
from pipeline.steps.known_ambiguities import KnownAmbiguityExpander
from pipeline.steps.ktu1_family_homonym_pruner import Ktu1FamilyHomonymPruner
from pipeline.steps.noun_closure import NounPosClosureFixer
from pipeline.steps.offering_l_prep import OfferingListLPrepFixer
from pipeline.steps.onomastic_gloss import OnomasticGlossOverrideFixer
from pipeline.steps.plural_split import PluralSplitFixer
from pipeline.steps.schema_formatter import TsvSchemaFormatter
from pipeline.steps.suffix_fixer import SuffixCliticFixer
from pipeline.steps.surface_option_propagation import SurfaceOptionPropagationFixer
from pipeline.steps.weak_final_sc import WeakFinalSuffixConjugationFixer
from pipeline.steps.weak_verb import WeakVerbFixer


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for tablet parsing pipeline."""

    source_dir: Path
    out_dir: Path
    dulat_db: Path
    udb_db: Path
    include_existing: bool = False
    source_glob: str = "KTU 1.*.tsv"
    max_step_change_ratio: float = 0.25
    allow_large_step_changes: bool = False


class TabletParsingPipeline:
    """Runs bootstrap, refinement, and report regeneration for tablets."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.instruction_refiner = InstructionRefiner(dulat_db=self.config.dulat_db)
        self.morph_gate = DulatMorphGate(self.config.dulat_db)
        self.attestation_index = DulatAttestationIndex.from_sqlite(self.config.dulat_db)
        self._refinement_steps: List[RefinementStep] = [
            # AlephPrefixFixer disabled: changes (ʔ in analysis break DULAT
            # lexeme extraction, causing net increase in lint issues.
            # Will re-enable after linter lexeme extraction is updated.
            TsvSchemaFormatter(),
            NounPosClosureFixer(),
            FormulaTrigramFixer(),
            FormulaBigramFixer(),
            OfferingListLPrepFixer(),
            PluralSplitFixer(gate=self.morph_gate),
            FeminineTSingularSplitFixer(gate=self.morph_gate),
            BaalLabourerKtu1Fixer(),
            BaalPluralGodListFixer(),
            Ktu1FamilyHomonymPruner(dulat_db=self.config.dulat_db),
            SuffixCliticFixer(gate=self.morph_gate),
            WeakVerbFixer(),
            WeakFinalSuffixConjugationFixer(),
            SurfaceOptionPropagationFixer(
                corpus_dir=self.config.out_dir,
                allowed_surfaces=SURFACE_OPTION_PROPAGATION_ALLOWLIST,
            ),
            AttestationSortFixer(index=self.attestation_index),
            KnownAmbiguityExpander(),
            OnomasticGlossOverrideFixer(),
            GenericParsingOverrideFixer(),
            # Keep schema pass last so any content-changing steps still end in
            # strict 7-column/quote-safe TSV for GitHub rendering.
            TsvSchemaFormatter(),
        ]

    def discover_source_files(self) -> List[Path]:
        return sorted(self.config.source_dir.glob(self.config.source_glob))

    def discover_out_files(self) -> List[Path]:
        return sorted(self.config.out_dir.glob(self.config.source_glob))

    def select_targets(self, explicit_names: Optional[Sequence[str]] = None) -> List[Path]:
        source_files = self.discover_source_files()
        source_by_name = {item.name: item for item in source_files}

        if explicit_names:
            names = sorted(set(name.strip() for name in explicit_names if name and name.strip()))
            return [source_by_name[name] for name in names if name in source_by_name]

        if self.config.include_existing:
            return source_files

        out_names = {item.name for item in self.discover_out_files()}
        return [item for item in source_files if item.name not in out_names]

    def bootstrap_targets(self, targets: Sequence[Path]) -> Dict[str, int]:
        forms_map = bootstrap.load_dulat_forms(self.config.dulat_db)
        written = 0
        for src in targets:
            dst = self.config.out_dir / src.name
            bootstrap.process_file(src, dst, forms_map)
            written += 1
        return {"bootstrap_written": written}

    def refine_targets(self, targets: Sequence[Path]) -> Dict[str, int]:
        _entries_by_id, forms_map, _lemma_map, suffix_map, forms_morph = refine.load_entries(
            self.config.dulat_db
        )
        reverse_mentions, entry_ref_count, entry_tablets, entry_family_count = (
            refine.load_reverse_mentions(
                self.config.dulat_db,
                self.config.udb_db,
            )
        )

        rows_total = 0
        changed_total = 0
        for src in targets:
            out_file = self.config.out_dir / src.name
            rows, changed = refine.refine_file(
                out_file,
                out_file,
                forms_map,
                suffix_map,
                forms_morph,
                reverse_mentions,
                entry_ref_count,
                entry_tablets,
                entry_family_count,
            )
            rows_total += rows
            changed_total += changed

        return {
            "refine_rows": rows_total,
            "refine_changed": changed_total,
        }

    def instruction_refine_targets(self, targets: Sequence[Path]) -> Dict[str, int]:
        target_out_files = [self.config.out_dir / src.name for src in targets]
        result = self.instruction_refiner.refine_files(target_out_files)
        return {
            "instruction_refine_files": result.files,
            "instruction_refine_rows": result.rows,
            "instruction_refine_changed": result.changed,
        }

    def regenerate_reports(self) -> int:
        generator = LintReportGenerator(
            out_dir=self.config.out_dir,
            reports_dir=Path("reports"),
            dulat_db=self.config.dulat_db,
            udb_db=self.config.udb_db,
            linter_path=Path("linter") / "lint.py",
        )
        return generator.run()

    def apply_refinement_steps(self, targets: Sequence[Path]) -> Dict[str, int]:
        """Run all registered refinement steps on target output files."""
        target_out_files = [self.config.out_dir / src.name for src in targets]
        total_changed = 0
        step_details: Dict[str, int] = {}
        for step in self._refinement_steps:
            step_changed = 0
            step_rows = 0
            for path in target_out_files:
                result = step.refine_file(path)
                step_changed += result.rows_changed
                step_rows += result.rows_processed

            if (
                step_rows > 0
                and not self.config.allow_large_step_changes
                and (float(step_changed) / float(step_rows)) > self.config.max_step_change_ratio
            ):
                ratio = float(step_changed) / float(step_rows)
                raise RuntimeError(
                    "Refinement safeguard tripped for step '%s': %d/%d rows changed (%.2f%%),"
                    " above max %.2f%%."
                    % (
                        step.name,
                        step_changed,
                        step_rows,
                        ratio * 100.0,
                        self.config.max_step_change_ratio * 100.0,
                    )
                )
            step_details[f"step_{step.name}_changed"] = step_changed
            total_changed += step_changed
        step_details["refinement_steps_total_changed"] = total_changed
        return step_details

    def run(
        self, explicit_names: Optional[Sequence[str]] = None, dry_run: bool = False
    ) -> Dict[str, object]:
        targets = self.select_targets(explicit_names=explicit_names)
        summary: Dict[str, object] = {
            "targets": [path.name for path in targets],
            "target_count": len(targets),
            "dry_run": dry_run,
        }

        if dry_run or not targets:
            return summary

        self.config.out_dir.mkdir(parents=True, exist_ok=True)

        summary.update(self.bootstrap_targets(targets))
        summary.update(self.refine_targets(targets))
        summary.update(self.instruction_refine_targets(targets))
        summary.update(self.apply_refinement_steps(targets))
        summary["report_exit_code"] = self.regenerate_reports()

        return summary
