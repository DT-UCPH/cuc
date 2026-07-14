# Suffix Payload Collapse Pipeline

## Goal

When a parsing variant already encodes clitic/suffix behavior in column 3
(`+`, `~`, `[...` forms), columns 4-6 should keep host-lexeme metadata only.

Example:

- input: `g/+h | g, -h (I) | n. m., pers. pn. | (loud) voice, his /her`
- output: `g/+h | g | n. m. | (loud) voice`

## Step

- Step: `SuffixPayloadCollapseFixer` (`pipeline/steps/suffix_payload_collapse.py`)
- Pipeline position: after `SuffixCliticFixer` + `SuffixParadigmNormalizer`.

## Rule

For each aligned variant slot:

1. Detect clitic-bearing analysis (`+x`, `~x`, or bracketed clitic-like tail).
2. Detect suffix-linked DULAT payload in col4 (`, -x...`).
3. Collapse payload to host metadata:
   - col4: keep text before first comma,
   - col5: strip trailing suffix-function tail segments,
   - col6: strip trailing suffix gloss tails (`my`, `your(s)`, `his /her...`, `our`, `to`,
     `yes`, `Sun`, `und das (ist) so!`, etc.).

## Safety

- Variant alignment is preserved (`col3` unchanged).
- Only variants with both clitic evidence (col3) and suffix payload marker in col4 are rewritten.
- Variants without suffix payload in col4 are left unchanged.
