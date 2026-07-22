# Ugaritic N-Stem Encoding

Use this reference after the lexical stem and conjugation have been established. These markers encode structure; they are not interchangeable decorations.

## Marker Semantics

- `]n]`: written N-stem formative.
- `(]n]`: reconstructed N-stem formative absent from the surface.
- `(n`: reconstructed lexical radical `n` absent as an independent surface consonant.
- `(`: reconstructs exactly the following letter or bracketed marker atom.
- `[`: closes the verbal root; written suffix-conjugation endings follow it.
- `!x!`: prefix-conjugation preformative.
- `&x`: written material not present in the lexical representation.
- `:d`, `:l`, `:r`, and `:pass`: stem labels with their own established meanings. Do not model the N formative with generic `:n`.

## Prefix Conjugation

Place the N formative after the preformative:

- hidden/assimilated formative: `!t!(]n]ṯbr[`;
- visible formative: `!x!]n]...` when the text and project convention require it.

For a root that itself begins with `/n/`, keep the N formative and lexical radical conceptually separate. Do not retain deprecated `](n]` ordering; the canonical reconstructed formative is `(]n]`.

## Suffix Conjugation

Mark the N formative at the beginning of the verbal body:

- written formative before a non-`n` root: `]n]ḫt(ʔ[&u`;
- reconstructed formative: `(]n]ypˤ[t` when no formative `n` is written;
- formative coinciding with root-initial `/n/`: write the formative as `]n]` and reconstruct the lexical radical as `(n`.

The last case is a representational decision: the single written `n` is assigned to the stem formative, while the root-initial `/n/` remains explicit but reconstructed.

## Worked Example: `nšt` from `/n-š-y/`

Canonical analysis: `]n](nš(y[t`

| Segment | Function | Surface |
|---|---|---|
| `]n]` | written N-stem formative | `n` |
| `(n` | reconstructed first root radical | — |
| `š` | written second radical | `š` |
| `(y` | reconstructed weak third radical | — |
| `[` | root boundary | — |
| `t` | written 1cs suffix-conjugation ending | `t` |

The result reconstructs `nšt` and preserves all morphological structure.

## Reject These Near Misses

- `nš(y[t:n`: reconstructs the surface but hides the N-stem structure behind an inappropriate generic label.
- `]n](nšy[t`: reconstructs `nšyt`, because `(n` hides only `n`; it does not also hide `y`.
- `(]n]nš(y[t`: reconstructs `nšt`, but assigns the written `n` to the lexical radical rather than the suffix-conjugation convention above.
- `nš(y[t` with POS `vb N`: omits an explicit N-stem formative.

Surface reconstruction is necessary but insufficient. Validate the DULAT root, N-stem evidence, conjugation, and marker roles independently.

## Migration and Alternatives

Preserve a correct legacy N-stem analysis during token-ID migration. If a split token represents one lexical word, validate the merged surface and retain paired comments rather than forcing each component to reconstruct independently.

Do not preserve a morphologically invalid migrated analysis merely as an alternative. Record genuine uncertainty as separate supported analyses or a clear unresolved row; do not turn a known-invalid encoding into reviewer workload.
