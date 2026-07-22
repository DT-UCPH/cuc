# Reviewed Migration Invariants

## Inputs

- The raw target and automatic target must derive from the same TF version.
- The automatic target must be current before reviewed migration begins.
- A partial reviewed file remains bounded by its original first and last reviewed references.
- A reviewed file with a sign-span column keeps eight columns and receives target-version sign spans.

## Material That Must Survive

- every still-valid reviewed analysis and alternative row;
- DULAT headword and homonym selection;
- reviewed POS and gloss when alignment is unchanged;
- every nonempty editorial comment, including citations and uncertainty;
- inline legacy `#` analysis notes, moved into the comment column;
- duplicate alternatives that differ materially in analysis, lexeme, POS, gloss, or comment.

Appending `Migrated from legacy reviewed tokenization.` does not replace the original comment. Preserve the original first, then append migration provenance with ` | `.

## Alignment Cases

### Unchanged token

Refresh the ID and sign span; preserve reviewed linguistic fields and comment.

### Editorial spelling-only change

Preserve the reviewed interpretation and append `Token changed from previous version.`.

### Old tokens joined into one target token

Use automatic fallback only when the old analyses cannot validly describe the joined token. Carry all source comments into the target row and mark the fallback as migrated.

### One old token split into target tokens

First try a justified positional split of analysis, DULAT, POS, and gloss. If this is impossible, do not silently discard the old interpretation. Review the combined form and distinguish a whole-word physical split from true lexical resegmentation.

The known `ḫršnr` to `ḫršn` + `r` case is true lexical resegmentation: retain the original comment on both rows and analyze the second component as `&gr(I)/`, not `?`.

### Whole lexical word across two physical tokens

Repeat the complete analysis on both rows. Put `MERGE WITH THE NEXT: ...` on the first and `MERGE WITH THE PREVIOUS.` on the second. Validate reconstruction against the concatenated surfaces.

## Acceptance Checks

- Header and all data rows have the expected seven- or eight-column schema.
- IDs and sign spans match target raw TF rows.
- References remain in order and within the reviewed bounds.
- Every old comment survives unless explicitly superseded.
- Structured merge annotations are paired, adjacent, analysis-identical, and reconstructable.
- Every migrated unresolved row was inspected rather than accepted in bulk.
- Lint introduces no new errors after ID-stable comparison.

