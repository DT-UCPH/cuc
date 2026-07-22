---
name: parse-ugaritic-passive-participle
description: Audit and correct Ugaritic G-stem passive-participle (`pass. ptcpl.`) encodings in reviewed or automatic TSV files. Use for firm passive-participle analyses, suspected parser over-generation on strong roots, III-ʔ case-aleph spellings, II-ʔ/III-y/geminate diagnostics, `-t`/`-m` endings, or del Olmo (DULAT) vs. Notarius disagreements over adjective/patient-noun vs. passive participle. Do not assert a passive participle from a bare consonantal skeleton or from a passive translation alone.
---

# Parse Ugaritic Passive Participles

The G passive participle is morphologically under-marked: on a strong root it is spelled identically to the G-passive SC, the stative SC, a stative adjective, and often the active reading. Establish it from syntax and diathesis, and confirm it orthographically only where the consonantal text carries information. Keep formal identification and semantic voice as two separate decisions.

## Establish the Analysis

1. Read `references/passive-participle-encoding.md` completely.
2. Inspect the full TSV row, the surrounding clause, comments, parallels, and the DULAT form/POS.
3. Do **not** assign a firm `pass. ptcpl.` on the strength of a bare skeleton. On a strong triradical root, require a syntactic diagnostic (§2.3: attributive to a non-prominent antecedent, converb, predicative with `-u`/`d`/`l`/`ˁm`). Otherwise keep `pass. ptcpl.?` or a competing noun/finite reading.
4. Where orthography helps, apply the §2.2.2 grapheme diagnostics: II-ʔ middle vowel, III-ʔ case aleph (u=nom, i=gen, a=acc), retained III-y/w glide, plene geminate, `-t`/`-m` ending.
5. Record voice/aspect semantics (present passive, resultative, optative) in the gloss/comment only, never in the morphological string.

## Audit the Scope

Resolve this skill's directory from its `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/audit_passive_participle.py reviewed
python3 <skill-dir>/scripts/audit_passive_participle.py auto_parsing/0.2.8
python3 <skill-dir>/scripts/audit_passive_participle.py --id 154983 "reviewed/KTU 1.2.tsv"
```

The audit reports two deterministic findings on firm `pass. ptcpl.` rows:

- `no-orthographic-diagnostic` — a strong-root passive participle that alphabetic writing cannot mark; verify it against the clause or demote it. This is the class the parser over-generates (`rgm`, `ˤdb`, `ptḥ`).
- `iii-aleph-case-mismatch` — a III-ʔ realized case aleph whose vowel contradicts the labelled case.

Neither finding decides a reading; each marks a row to confirm. The same III-ʔ check runs in the repository linter (`iii_aleph_case_mismatch`).

## Correct Conservatively

- Demote skeleton-only strong-root participles to `pass. ptcpl.?` or the noun/finite reading unless syntax establishes the passive.
- Keep the II-ʔ / III-ʔ aleph distinct from the radical; align a III-ʔ case aleph with the labelled case.
- Retain the III-y/w glide and write geminates plene for a firm passive participle.
- For lexicalized patient-nouns (`mrủ`, `šbyn`), keep the DULAT noun reading and note participial origin in the comment only.
- Encode a genuine researcher disagreement (DULAT adjective/noun vs. Notarius passive participle) as **alternative rows**, not a replacement; use `?` for the DULAT column and gloss of a reading with no DULAT lemma.
- Preserve IDs, readings, alternatives, glosses, comments, and migration provenance.
- Fix productive parser or linter defects at their source and add focused tests. Do not regenerate automatic TSVs or commit unless requested.

## Validate

1. Re-run `audit_passive_participle.py` on the changed scope.
2. Verify each changed analysis reconstructs the surface.
3. Run the III-ʔ agreement tests (`tests/test_linter_iii_aleph_case_agreement.py`) and the verb-stem linter tests.
4. Run the repository linter; separate new findings from its existing baseline.
5. Inspect the scoped diff for semantic overreach and unrelated normalization.
6. Report deterministic changes separately from interpretive candidates.
