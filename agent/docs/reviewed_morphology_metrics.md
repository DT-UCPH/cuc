# Reviewed Morphology Metrics

This document defines the metrics emitted by `scripts/score_reviewed_morphology.py`.

## Scope

The scorer compares the `morphological parsing` column in:

- reviewed gold files under `../reviewed/`
- automatic parses under `../auto_parsing/<version>/`

The evaluation unit is a token `id`, not a TSV row.

For each `id`, the scorer builds:

- `G_i`: the reviewed set of morphology analyses
- `A_i`: the automatic set of morphology analyses

Important details:

- option order does not matter
- duplicate analyses for the same `id` are removed before scoring
- scoring is string-exact after TSV normalization; there is no structural canonicalization yet
- the main metrics are computed over reviewed token ids only
- auto-only ids are reported separately as `extra_auto_ids`, but do not affect the aggregate scores
- if a reviewed id is missing from the auto file, it is scored as `A_i = {}` for that id

## Example

If the reviewed file contains:

- `G_i = {a1, a2}`

and the automatic file contains:

- `A_i = {a2, a1, a3}`

then:

- the set is not an exact match
- both reviewed options are recovered
- one extra option is present: `a3`
- precision is `2 / 3`
- recall is `2 / 2 = 1`

## Per-Id Metrics

Each reviewed token id produces the following values.

### `exact_set_match`

`True` when `A_i == G_i`.

This is the strictest per-id criterion. A token only passes when the automatic parser returns exactly the same set of morphology options as the reviewed gold.

### `precision`

`|A_i ∩ G_i| / |A_i|`

How many automatic options for this id are correct.

Special case:

- if `A_i` is empty and `G_i` is non-empty, precision is `0`
- if both sets are empty, precision is treated as `1`

### `recall`

`|A_i ∩ G_i| / |G_i|`

How much of the reviewed gold set is recovered by the automatic parser.

Special case:

- if `G_i` is empty, recall is treated as `1`

### `f1`

`2 * |A_i ∩ G_i| / (|A_i| + |G_i|)`

Balanced overlap score for one token id.

### `jaccard`

`|A_i ∩ G_i| / |A_i ∪ G_i|`

Intersection over union for the option sets.

### `coverage`

`True` when `G_i - A_i` is empty.

This answers a candidate-generation question: did the automatic parser include every reviewed option, even if it also produced extras?

### `extra_count`

`|A_i - G_i|`

How many options were overgenerated for this id.

### `missing_count`

`|G_i - A_i|`

How many reviewed options were missed for this id.

### `option_count_error`

`abs(|A_i| - |G_i|)`

How far the ambiguity size is from the reviewed set size, regardless of which specific options matched.

## Aggregate Metrics

Aggregate metrics are averages or corpus totals over reviewed token ids.

### `exact_set_accuracy`

Average of `exact_set_match`.

Interpretation:

- `1.0` means every reviewed id has exactly the same option set in auto output
- this metric is harsh and drops quickly when a system overgenerates

### `macro_precision`

Mean of per-id precision.

Each reviewed id contributes equally, regardless of how many options it has.

### `macro_recall`

Mean of per-id recall.

Useful for seeing whether the parser tends to miss reviewed options on a per-token basis.

### `macro_f1`

Mean of per-id F1.

This is usually the most useful single summary when you want a balanced per-token agreement score and reviewed ids should carry equal weight.

### `macro_jaccard`

Mean of per-id Jaccard similarity.

This is similar to macro F1 but slightly harsher on extra options.

### `micro_precision`

`total true-positive options / total auto options`

This pools all reviewed ids together before scoring. Tokens with more options affect the score more strongly than in macro averaging.

### `micro_recall`

`total true-positive options / total reviewed options`

This is the corpus-level recovery rate of reviewed morphology options.

### `micro_f1`

`2 * total true-positive options / (total auto options + total reviewed options)`

Corpus-level overlap score.

### `gold_coverage`

Average of per-id `coverage`.

This is the share of reviewed ids for which the automatic parser included every reviewed morphology option.

### `mean_extra_options`

Mean of per-id `extra_count`.

How much spurious ambiguity the automatic parser adds on average.

### `mean_missing_options`

Mean of per-id `missing_count`.

How many reviewed options are missed on average.

### `mean_option_count_error`

Mean of per-id `option_count_error`.

How far the parser's ambiguity width is from reviewed gold, without considering which specific options matched.

## Ambiguous vs Unambiguous Gold

The report also emits separate summaries for:

- unambiguous gold ids: `|G_i| = 1`
- ambiguous gold ids: `|G_i| > 1`

This split matters because the parser may do well on single-option tokens while failing to preserve the full reviewed ambiguity set on genuinely ambiguous ones.

## Report Artifacts

The scorer can emit:

- console summary
- JSON payload with per-file and per-id details

From inside `agent/`:

```bash
./.venv/bin/python scripts/score_reviewed_morphology.py
```

From the repository root:

```bash
agent/.venv/bin/python agent/scripts/score_reviewed_morphology.py --json
```

The script defaults to the repository `reviewed/` folder and the latest available `auto_parsing/<version>/` directory.

## Current Limitations

- Comparison is string-based. Equivalent analyses written in different notations will count as mismatches.
- Auto-only ids are not part of the main aggregate score, because the evaluation universe is the reviewed gold set.
- Reviewed `.txt` files are accepted when they follow the same tabular layout as reviewed `.tsv` files.
