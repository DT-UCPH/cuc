# Variant Row Unwrapper Pipeline

## Goal

Replace legacy semicolon-packed variant payloads in `out/*.tsv` with one option per row.

Old style (single row, many options):

- `id=152465`
- `surface=pn`
- `col3=pn(m/m; pn`
- `col4=pnm; pn`
- `col5=n. m. pl. tant.; functor`
- `col6=face; lest`

New style (multiple rows, same `id` + `surface`, one option each).

## Step

- Step: `VariantRowUnwrapper` (`pipeline/steps/variant_row_unwrapper.py`)
- Follow-up safety step: `UnwrappedDuplicatePruner` (`pipeline/steps/unwrapped_duplicate_pruner.py`)
- Pipeline position: both run at the end of content-changing refinements, immediately before the
  last `TsvSchemaFormatter`.

## Rules

1. Split `col3`-`col6` by semicolon into aligned variant slots.
2. Emit one output row per slot while preserving:
   - `id` (`col1`)
   - `surface form` (`col2`)
   - `comments` (`col7`)
3. If one column has a single value while others have multiple, reuse that single value for each emitted row.
4. Drop duplicate emitted rows that have identical `(id, surface, col3, col4, col5, col6)`.

## Alignment Detail

- Preserve explicit empty slots inside packed semicolon fields (for example `;;...`).
- Trim only trailing empty slots.
- If gloss slots are compact but POS slots encode alignment empties, gloss values are projected
  onto the non-empty POS slots to keep option alignment stable.

## Linter checks

- Packed variant rows are rejected in `out/*.tsv`.
- Duplicate unwrapped payload rows are rejected:
  same `(id, surface, col3, col4, col5, col6)`.
