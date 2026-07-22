# KTU Editorial Sign Semantics

Treat the sign span as editorial evidence, not as morphological analysis syntax. Keep four
layers distinct:

1. **Sign span:** KTU markup preserving physical and editorial information.
2. **Normalized physical surface:** letters assigned to the TF token and reconstructed by the
   analysis.
3. **Corrected lexical lookup:** a conservative alias used only to find DULAT candidates.
4. **Analysis:** the selected lexeme aligned against the normalized physical surface.

## Safe Automatic Treatment

| KTU notation | Meaning | Automatic treatment |
| --- | --- | --- |
| `[[x]]` | erased sign(s), line(s), or correction | Remove `x` only from corrected lexical lookup; retain physical `x` for alignment. |
| `{x}` | redundant sign | Remove `x` only from corrected lexical lookup; retain physical `x` for alignment. |
| `<x>` | missing sign supplied editorially | Keep `x` in the normalized reading; do not create a corrected alias merely because of the brackets. |
| `[x]`, `[`, `]` | restored damaged passage or break boundary | Keep readable/restored letters in the normalized reading; delimiters do not create morphology. |
| `+`, `(+)` | physical or indirect fragment join | Treat as layout evidence; do not create a lexical alias. |
| `(...)` | special editorial remark | Do not infer lexical content automatically. |
| `\` | line continued by editors | Treat as layout evidence; do not create a lexical alias. |
| italic continuation marker | line continued by the scribe | Treat as editorial/layout evidence unless TF exposes an independently validated letter reading. |
| `xx . xx`, `x.x` | word divider | Preserve an internal divider in the sign span when it occurs inside a TF token, but do not use it to invent an alias. |

Only `[[...]]` and `{...}` support automatic corrected-lookup removal, and only after all
letters in the sign span normalize exactly to the TF physical surface. Reject mismatching,
ambiguous, empty, one-letter, parenthetical, or divider-crossing corrected aliases.

## Align After Lexical Selection

Do not translate `[[x]]` or `{x}` directly to `&x`. First use the corrected lookup to retrieve
linguistically viable DULAT candidates, select among homonyms with textual and lexical
evidence, then align the selected lexeme against the physical surface. The alignment produces
`&` only when the written surface contains material outside the selected lexical form.

Examples:

- `g[[m]]pn`: physical `gmpn`, corrected lookup `gpn`, selected `gpn (III)`, analysis
  `g&mpn(III)/`.
- `aṯ{t}rt`: physical `aṯtrt`, corrected lookup `aṯrt`, selected `ảṯrt (II)`, analysis
  `aṯ&tr(t(II)/t`.
- `<n>ḫtu`: physical and lookup reading `nḫtu`; DULAT morphology identifies an N-stem suffix
  form, yielding `]n]ḫt(ʔ[&u`. The angle brackets themselves do not imply `]n]`.

Validate the final analysis against the normalized physical surface, not the corrected lookup
and not the raw sign-span punctuation. Preserve the full sign span in reviewed TSVs.
