# Attestation Reference Disambiguator Pipeline

## Goal
Resolve row-level ambiguities when DULAT references make one option uniquely
attested at the exact tablet section.

## Inputs
- `out/KTU *.tsv` rows (already unwrapped to one option per row).
- DULAT attestations (`sources/dulat_cache.sqlite`).
- Section labels from separator rows (e.g. `# KTU 1.3 I:1`).

## Rule
For each contiguous token group (`line_id` + `surface`) inside one section:
1. Collect all option rows in the group.
2. Compare each option's DULAT head token against DULAT citations for the
   current section reference.
3. If exactly one option matches, keep it and drop the others.
4. If zero or multiple options match, keep the group unchanged.

## Safety
- No free-text heuristics.
- No manual edits in `out/`.
- No change unless reference evidence is unique.

## Example
At `KTU 1.3 I:1`, `ảl (I)` is attested and `ảl (II)` is not, so:
- keep `al(I)` / `ảl (I)`
- drop `al(II)` / `ảl (II)`
