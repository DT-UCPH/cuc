"""Final fallback must validate edited words and retain their provenance."""
import tempfile
import unittest
from pathlib import Path
from pipeline.steps.editorial_morphology_normalizer import EditorialMorphologyNormalizer
from pipeline.steps.unresolvable_token_fallback import UnresolvableTokenFallback
from pipeline.steps.variant_reconstruction_pruner import VariantReconstructionPruner


class EditedReadingFallbackTest(unittest.TestCase):
    def run_steps(self, rows, steps):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'KTU 1.2.tsv'
            path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
            for step in steps:
                step.refine_file(path)
            return path.read_text(encoding='utf-8')

    def test_physical_only_candidate_becomes_unresolved_with_provenance(self):
        for surface, analysis, target in [('im', 'im', 'm'), ('lnh', 'l(I)+nh', 'ln')]:
            result = self.run_steps(
                [f'1\t{surface}\t{analysis}\tlemma\tprep.\tgloss\tEdited reading: {target}'],
                [EditorialMorphologyNormalizer(), UnresolvableTokenFallback()],
            )
            self.assertEqual(result.split('\t')[2:6], ['?', '?', '?', '?'])
            self.assertIn(f'Edited reading: {target}', result)
            self.assertIn('lemma - gloss', result)

    def test_erased_surface_letter_is_normalized_before_fallback(self):
        result = self.run_steps(
            ['1\tgmpn\tg&mpn(III)/\tgpn (III)\tDN m.\tGapnu\tEdited reading: gpn'],
            [EditorialMorphologyNormalizer(), UnresolvableTokenFallback()],
        )
        self.assertEqual(result.split('\t')[2], 'gpn(III)/')

    def test_pruner_prefers_edited_candidate_over_physical_candidate(self):
        result = self.run_steps([
            '1\tim\tim\tlemma\tprep.\tgloss\tEdited reading: m',
            '1\tim\tm\tlemma\tprep.\tgloss\tEdited reading: m',
        ], [VariantReconstructionPruner()])
        self.assertEqual(len(result.splitlines()), 1)
        self.assertEqual(result.split('\t')[2], 'm')
