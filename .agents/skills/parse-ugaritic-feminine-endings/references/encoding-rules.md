# Ugaritic Feminine Ending Rules

Read these rules as a decision table, not as a surface-spelling substitution recipe. The declared DULAT lexeme and reviewed morphology control the analysis.

## Marker Semantics

- `(` introduces lexeme material not separately realized in the written form.
- `/` introduces the nominal ending.
- `=` marks the feminine plural ending in `/t=`.
- `+` introduces a pronominal suffix.
- `~` introduces an enclitic.
- `&` introduces written material absent from the paradigmatic lexeme.

## Lexemes Ending in `t`

When a feminine lexeme ends in `t`, encode that consonant twice functionally but once on the surface: `(t` records it as lexical material and the material after `/` records the nominal ending.

| Morphology | Pattern | Example |
|---|---|---|
| Singular | `stem(t/t` | `mhmr(t/t` |
| Singular + suffix | `stem(t/t+suffix` | `bm(t/t+h=` |
| Singular + enclitic | `stem(t/t~enclitic` | `ḥrḥr(t/t~m` |
| Feminine plural | `stem(t/t=` | `msd(t/t=` |
| Plural + suffix | `stem(t/t=+suffix` | `ˤrp(t/t=+k` |
| Plural + enclitic | `stem(t/t=~enclitic` | `ṭ(t/t=~m` |
| Absolute dual in written `-tm` | `stem(t/tm` | `rḥ(t/tm` |

The absolute dual `rḥtm` is therefore `rḥ(t/tm`, analogically to singular `rḥ(t/t`. The `/t` is the feminine marker and `m` completes the written absolute-dual ending.

Keep homonym tags on the lexeme side: `hw(t(I)/t`, `qr(t(I)/tm`, `psl(t(I)/tm`.

## Lexemes Not Ending in `t`

Do not add `(t` when the DULAT lexeme does not end in `t`:

- singular feminine ending: `stem/t`;
- feminine plural: `stem/t=`;
- absolute dual written `-tm`: `stem/tm`.

A feminine noun can also have an irregular or masculine plural without visible `t`. Do not replace such an ending solely from the POS gender.

## Construct Duals and Unwritten Material

Do not invent an unwritten dual `m`. A construct dual can have only the realized `t` ending, for example `šp(t/t+h` or `kla(t/t`. Use `/tm` only when the absolute dual and its written `m` are supported.

## Suffixes, Enclitics, and Allographs

Keep suffix and enclitic boundaries distinct:

- `/t+h` is a feminine ending followed by a suffix;
- `/t~m` is a feminine singular followed by enclitic `m`;
- `/t=~m` is feminine plural followed by enclitic `m`;
- `/tm` is the absolute-dual ending, not an enclitic analysis.

Preserve surface-only allographs while correcting the ending. For example, retain the `&` material in `am&h(t/t=`. Do not simplify exceptional extended forms such as `il(t(I)/&ht` into the regular template.

## Feminine Divine Names

Apply the same lexical-overlap rule to feminine divine names whose DULAT lexeme ends in `t`, for example:

- `ˤn(t(I)/t` for `ʕnt (I)`;
- `aṯr(t(II)/t` for `ảṯrt (II)`;
- `ˤṯtr(t(I)/t` for `ʕṯtrt (I)`.

Confirm the lexeme and Roman-numeral homonym before changing the ending. Female gender by itself does not imply that a divine name has a separable `/t` ending.

## Split Tokens After Migration

A tokenization migration can split one historically reviewed word across two rows. When comments say `MERGE WITH THE NEXT` or `MERGE WITH THE PREVIOUS`, the full merged analysis may intentionally appear on both component rows. For `mh` + `mrt` representing `mhmrt`, both rows can carry `mhmr(t/t`.

Preserve the original explanatory comment. Do not replace the second component with `?` merely because that component is not an independent DULAT entry. Reconstruct and validate the merged surface rather than each component in isolation.

## Common False Positives

Do not automatically change:

- feminine nouns with masculine or irregular plural morphology;
- construct duals without written `m`;
- special allographic or extended endings;
- alternative analyses represented by duplicate rows;
- rows whose declared lexeme is uncertain or `?`;
- forms where DULAT and reviewed POS genuinely leave singular, dual, or plural unresolved.

When POS and a cited DULAT form conflict, inspect the lexical entry or local DULAT cache. Change POS only when the evidence is decisive, and record the reason in the existing comment rather than deleting editorial history.

