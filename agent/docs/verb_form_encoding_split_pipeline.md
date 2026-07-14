# Verb Form Encoding Split Pipeline

## Goal

Align verbal POS form labels with analysis encoding conventions:

- finite forms (`prefc.`, `suffc.`, `impv.`) use `[...]`
- non-finite forms (`inf.`, `act. ptcpl.`, `pass. ptcpl.`, `ptcpl.`) use `[/...]`

## Step

`pipeline/steps/verb_form_encoding_split.py` (`VerbFormEncodingSplitFixer`)

## Strategy

1. Target only verbal POS rows (`vb ...`, excluding `vb. n.`).
2. Parse slash-separated POS options in a variant.
3. Classify each option as finite, non-finite, or neutral.
4. If one option class is incompatible with current analysis marker:
   - normalize analysis marker (`[` <-> `[/`) to match the class.
5. If a single variant mixes finite and non-finite options:
   - duplicate that variant internally into two aligned options:
     - finite POS with finite analysis marker
     - non-finite POS with non-finite analysis marker
6. Deduplicate identical emitted variants.

## Example

Input:

`rgm[` + `vb G suffc. / vb G impv. / vb G inf. / vb G pass. ptcpl.`

Output:

- `rgm[` + `vb G suffc. / vb G impv.`
- `rgm[/` + `vb G inf. / vb G pass. ptcpl.`

