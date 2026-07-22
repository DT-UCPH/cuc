# Split-Token Model

## Whole Lexical Word Across Physical Tokens

Use this model when adjacent token surfaces concatenate into one analyzed word and the division is physical or editorial rather than lexical.

Required properties:

- first token comment contains `MERGE WITH THE NEXT`;
- immediately following token contains `MERGE WITH THE PREVIOUS`;
- both tokens carry the same complete analysis alternatives;
- the analysis reconstructs to the concatenated surfaces;
- DULAT, POS, and gloss remain compatible across the pair;
- the first comment explains the combined form and preserves editorial evidence.

Example: `mh` + `mrt` representing `mhmrt` can carry `mhmr(t/t` on both rows.

## Genuine Lexical Resegmentation

Use this model when one legacy token becomes two independently analyzed lexemes. Do not add MERGE annotations. Each row needs an analysis appropriate to its own surface and lexical role.

Example: legacy `ḫršnr` becomes `ḫršn` with `ḫršn(I)/` and `r` with `&gr(I)/`. The original comment must survive; `r` is not automatically unresolved merely because its lexical material is reconstructed.

## Unresolved Migration Fallback

Use `?` only when reviewed, automatic, DULAT, contextual, and combined-surface evidence do not justify an analysis. Retain `DULAT: NOT FOUND` and `Migrated from legacy reviewed tokenization.` along with the original comment.

An unresolved fallback is a review queue item, not proof that the migration is complete.

## Pair Boundaries

- Duplicate alternative rows with the same token ID count as one physical token.
- The partner must be the immediately adjacent distinct token ID.
- A paired token cannot point across an intervening token.
- Triple splits require explicit adjacent structure; do not infer a chain from vague `Split` comments.
- Rows containing broken `x` surfaces may be impossible to reconstruct mechanically and require contextual review.

## Comment Preservation

Generic provenance never replaces an original note. Preserve citations, alternative readings, uncertainty, and reviewer reasoning verbatim inside the new comment field. When one source token splits, duplicating its comment onto both target rows is safer than silently attaching it only to a component whose role changed.

