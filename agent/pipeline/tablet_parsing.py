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
from pipeline.steps.aleph_prefix import AlephPrefixFixer
from pipeline.steps.attestation_reference_disambiguator import AttestationReferenceDisambiguator
from pipeline.steps.attestation_sort import AttestationSortFixer
from pipeline.steps.baal_labourer_ktu1 import BaalLabourerKtu1Fixer
from pipeline.steps.baal_plural import BaalPluralGodListFixer
from pipeline.steps.baal_verbal_slash import BaalVerbalSlashFixer
from pipeline.steps.base import RefinementStep
from pipeline.steps.deictic_functor_enclitic_m import DeicticFunctorEncliticMFixer
from pipeline.steps.dulat_gate import DulatMorphGate
from pipeline.steps.feminine_t_singular_split import FeminineTSingularSplitFixer
from pipeline.steps.formula_bigram import FormulaBigramFixer
from pipeline.steps.formula_trigram import FormulaTrigramFixer
from pipeline.steps.generic_parsing_override import GenericParsingOverrideFixer
from pipeline.steps.iii_aleph_case_fixer import IIIAlephCaseFixer
from pipeline.steps.k_functor_bigram_context import KFunctorBigramContextDisambiguator
from pipeline.steps.known_ambiguities import KnownAmbiguityExpander
from pipeline.steps.ktu1_family_homonym_pruner import Ktu1FamilyHomonymPruner
from pipeline.steps.l_body_compound_prep import LBodyCompoundPrepDisambiguator
from pipeline.steps.l_functor_vocative_context import LFunctorVocativeContextDisambiguator
from pipeline.steps.l_kbd_compound_prep import LKbdCompoundPrepDisambiguator
from pipeline.steps.l_negation_verb_context import LNegationVerbContextPruner
from pipeline.steps.l_preposition_bigram_context import LPrepositionBigramContextDisambiguator
from pipeline.steps.nominal_case_ending_yh import NominalCaseEndingYHFixer
from pipeline.steps.nominal_form_morph_pos import NominalFormMorphPosFixer
from pipeline.steps.noun_closure import NounPosClosureFixer
from pipeline.steps.offering_l_prep import OfferingListLPrepFixer
from pipeline.steps.onomastic_gloss import OnomasticGlossOverrideFixer
from pipeline.steps.plural_split import PluralSplitFixer
from pipeline.steps.plurale_tantum_m import PluraleTantumMFixer
from pipeline.steps.post_verb_variant_unwrapper import (
    PostVerbUnwrappedDuplicatePruner,
    PostVerbVariantRowUnwrapper,
)
from pipeline.steps.prefixed_iii_aleph_verb import PrefixedIIIAlephVerbFixer
from pipeline.steps.pronoun_closure import PronounClosureFixer
from pipeline.steps.redirect_reconstruction_comment import RedirectReconstructionCommentFixer
from pipeline.steps.schema_formatter import TsvSchemaFormatter
from pipeline.steps.suffix_fixer import SuffixCliticFixer
from pipeline.steps.suffix_paradigm_normalizer import SuffixParadigmNormalizer
from pipeline.steps.suffix_payload_collapse import SuffixPayloadCollapseFixer
from pipeline.steps.surface_option_propagation import SurfaceOptionPropagationFixer
from pipeline.steps.surface_reconstructability_fixer import SurfaceReconstructabilityFixer
from pipeline.steps.toponym_directional_h import ToponymDirectionalHFixer
from pipeline.steps.unwrapped_duplicate_pruner import UnwrappedDuplicatePruner
from pipeline.steps.variant_row_unwrapper import VariantRowUnwrapper
from pipeline.steps.verb_form_encoding_split import VerbFormEncodingSplitFixer
from pipeline.steps.verb_form_morph_pos import VerbFormMorphPosFixer
from pipeline.steps.verb_l_stem_gemination import VerbLStemGeminationFixer
from pipeline.steps.verb_n_stem_assimilation import VerbNStemAssimilationFixer
from pipeline.steps.verb_pos_stem import VerbPosStemFixer
from pipeline.steps.verb_stem_suffix_marker import VerbStemSuffixMarkerFixer
from pipeline.steps.weak_final_sc import WeakFinalSuffixConjugationFixer
from pipeline.steps.weak_verb import WeakVerbFixer
from pipeline.steps.ydk_context_disambiguator import YdkContextDisambiguator


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for tablet parsing pipeline."""

    source_dir: Path
    out_dir: Path
    dulat_db: Path
    udb_db: Path
    include_existing: bool = False
    source_glob: str = "KTU *.tsv"
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
            TsvSchemaFormatter(),
            NounPosClosureFixer(),
            FormulaTrigramFixer(),
            FormulaBigramFixer(),
            OfferingListLPrepFixer(),
            PluralSplitFixer(gate=self.morph_gate),
            PluraleTantumMFixer(gate=self.morph_gate),
            FeminineTSingularSplitFixer(gate=self.morph_gate),
            BaalLabourerKtu1Fixer(),
            BaalVerbalSlashFixer(),
            BaalPluralGodListFixer(),
            Ktu1FamilyHomonymPruner(dulat_db=self.config.dulat_db),
            SuffixCliticFixer(gate=self.morph_gate),
            ToponymDirectionalHFixer(gate=self.morph_gate),
            DeicticFunctorEncliticMFixer(gate=self.morph_gate),
            SuffixParadigmNormalizer(),
            WeakVerbFixer(),
            WeakFinalSuffixConjugationFixer(),
            AlephPrefixFixer(),
            PronounClosureFixer(),
            SurfaceOptionPropagationFixer(
                corpus_dir=self.config.out_dir,
                allowed_surfaces=SURFACE_OPTION_PROPAGATION_ALLOWLIST,
            ),
            AttestationSortFixer(index=self.attestation_index),
            KnownAmbiguityExpander(),
            OnomasticGlossOverrideFixer(),
            IIIAlephCaseFixer(gate=self.morph_gate),
            NominalCaseEndingYHFixer(gate=self.morph_gate),
            NominalFormMorphPosFixer(gate=self.morph_gate),
            SurfaceReconstructabilityFixer(),
            GenericParsingOverrideFixer(),
            SuffixPayloadCollapseFixer(),
            VariantRowUnwrapper(),
            RedirectReconstructionCommentFixer(),
            UnwrappedDuplicatePruner(),
            AttestationReferenceDisambiguator(index=self.attestation_index),
            LNegationVerbContextPruner(),
            LFunctorVocativeContextDisambiguator(),
            LKbdCompoundPrepDisambiguator(),
            LBodyCompoundPrepDisambiguator(),
            LPrepositionBigramContextDisambiguator(),
            KFunctorBigramContextDisambiguator(),
            YdkContextDisambiguator(),
            PrefixedIIIAlephVerbFixer(),
            VerbPosStemFixer(dulat_db=self.config.dulat_db),
            VerbFormMorphPosFixer(dulat_db=self.config.dulat_db),
            VerbFormEncodingSplitFixer(),
            VerbLStemGeminationFixer(),
            VerbStemSuffixMarkerFixer(),
            VerbNStemAssimilationFixer(),
            PostVerbVariantRowUnwrapper(),
            PostVerbUnwrappedDuplicatePruner(),
            # Keep schema pass last so any content-changing steps still end in
            # strict 7-column/quote-safe TSV for GitHub rendering.
            TsvSchemaFormatter(),
        ]

    def discover_source_files(self) -> List[Path]:
        return sorted(self.config.source_dir.glob(self.config.source_glob))

    def discover_out_files(self) -> List[Path]:
        return sorted(self.config.out_dir.glob(self.config.source_glob))

    def partition_targets_for_bootstrap(
        self, targets: Sequence[Path]
    ) -> tuple[List[Path], List[Path]]:
        """Split targets into files that need bootstrap and files to preserve."""
        needs_bootstrap: List[Path] = []
        preserved_existing: List[Path] = []
        for src in targets:
            out_path = self.config.out_dir / src.name
            if self.config.include_existing and out_path.exists():
                preserved_existing.append(src)
                continue
            needs_bootstrap.append(src)
        return needs_bootstrap, preserved_existing

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
        _entries_by_id, forms_map, lemma_map, suffix_map, forms_morph = refine.load_entries(
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
                lemma_map,
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
        bootstrap_targets, preserved_targets = self.partition_targets_for_bootstrap(targets)
        summary: Dict[str, object] = {
            "targets": [path.name for path in targets],
            "target_count": len(targets),
            "bootstrap_target_count": len(bootstrap_targets),
            "preserved_target_count": len(preserved_targets),
            "dry_run": dry_run,
        }

        if dry_run or not targets:
            return summary

        self.config.out_dir.mkdir(parents=True, exist_ok=True)

        if bootstrap_targets:
            summary.update(self.bootstrap_targets(bootstrap_targets))
        else:
            summary.update(
                {
                    "bootstrap_written": 0,
                }
            )

        # When include_existing is enabled, preserved outputs must still pass through
        # DULAT-backed refinement so stale rows (e.g., legacy gloss payloads) are
        # regenerated from authoritative lexical data.
        refine_targets = targets if self.config.include_existing else bootstrap_targets
        if refine_targets:
            summary.update(self.refine_targets(refine_targets))
        else:
            summary.update(
                {
                    "refine_rows": 0,
                    "refine_changed": 0,
                }
            )
        summary.update(self.instruction_refine_targets(targets))
        summary.update(self.apply_refinement_steps(targets))
        summary["report_exit_code"] = self.regenerate_reports()

        return summary
