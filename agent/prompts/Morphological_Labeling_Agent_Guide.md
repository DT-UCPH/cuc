# Ugaritic Morphological Labeling Guide for LLM Agents

This guide defines how to produce morphological labeling for a new unlabeled Ugaritic file, using:

- `agent/Tagging conventions.md` (authoritative tagging policy),
- attested practice in checked project files (for example `data/KTU_1.3 Martjin_Tania_checked.txt`),
- lexical and form evidence from:
  - `sources/dulat_cache.sqlite` (DULAT),
  - `sources/udb_cache.sqlite` (UDB, secondary check).

Use this guide as an execution protocol, not as general background.

Companion files:

- `agent/Morphological_Labeling_Quick_Checklist.md` (fast execution checklist),
- `agent/Ugaritic_Morphology_Reference.md` (feature and stem reference from `linter/morphology.py`).

---

## 1. Task Definition and Output Contract

Input line (unlabeled) is expected to contain at least:

1. `col1`: token ID (integer),
2. `col2`: surface token.

Raw sources may also be in `cuc_tablets_tsv` format:

- separator rows like `#---------------------------- KTU 1.5 I:1`,
- token rows as 3 columns: `id<TAB>surface<TAB>surface` (third column is a placeholder, not a parse).

When working directly in `cuc_tablets_tsv`:

- preserve separator rows,
- keep `col1` and `col2` unchanged,
- replace placeholder `col3` with morphological parse and add `col4/col5/col6`.

Output line must preserve `col1` and `col2` exactly and use this structured schema:

3. `col3`: semicolon-separated morphological parsing variants.
4. `col4`: semicolon-separated DULAT entry sets aligned to `col3` variants.
   - if a variant contains multiple lexemes (word + suffix/clitic), separate those lexeme entries by comma.
5. `col5`: semicolon-separated POS sets aligned to `col3` variants.
   - for multi-lexeme variants, separate POS morpheme slots by comma in the same order as `col4`.
   - if one morpheme still has multiple POS options, separate those options by `/` inside that morpheme slot.
   - for noun POS slots with DULAT gender available, include gender explicitly as `n. m.` or `n. f.` (for example `n. f.`, `n. m./DN`).
   - for adjective POS slots with DULAT gender available, include gender explicitly as `adj. m.` or `adj. f.`.
   - for pluralia tantum nouns, add `pl. tant.` in the same noun POS slot (or `pl. tant.?` for tentative cases) and keep this marker out of comments.
6. `col6`: semicolon-separated gloss sets aligned to `col3` variants.
   - for multi-lexeme variants, separate gloss items by comma in the same order as `col4`.
7. Optional comment after `#` for residual notes only (translation rationale, uncertainty, text-critical notes).
8. For fully unresolved tokens, use `?` consistently in `col3`, `col4`, `col5`, and `col6` for that variant.
9. For repeated long surface sequences (formulaic parallels), keep `col3/col4/col5/col6` aligned across occurrences unless you record an explicit reason for divergence in comments.

Mandatory invariant:

- each `col3` semicolon variant must reconstruct exactly to `col2` surface.
- if a variant does not reconstruct, treat it as an error and repair the parse before finalizing.
- exception: unresolved placeholder variants marked as `?` in `col3` are exempt from reconstructability checks.

Separator hierarchy (must be consistent across columns):

- `;` separates parsing variants.
- `,` separates morphemes/lexeme slots within a variant.
- `/` separates POS options for the same morpheme (in `col5`).
- If a DULAT POS label itself contains `/` (for example `det. / rel. functor`, `emph./det. encl. morph.`), rewrite it with `or` in `col5` (for example `det. or rel. functor`, `emph. or det. encl. morph.`). Reserve `/` only for real POS-option separators.

Do not normalize or rewrite `col1`/`col2` beyond pre-agreed orthography policy.
Do not duplicate structured `DULAT/POS/gloss` payload in comments.

Linter mode for this format:

- raw source: `python linter/lint.py 'cuc_tablets_tsv/KTU 1.5.tsv' --input-format cuc_tablets_tsv --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`
- labeled file: `python linter/lint.py 'out/KTU 1.5.tsv' --input-format labeled --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`
- mixed project runs: `python linter/lint.py 'out/KTU 1.5.tsv' --input-format auto --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`.
- token-id to KTU header lookup: `python3 scripts/token_ref_index.py --id 139891 --glob 'out/KTU 1.*.tsv'`

---

## 2. Character and Orthography Policy

### 2.1 Columns 2-3 conventions (project-side)

- Use `ˤ` for ayin in columns 2-3.
- Do not use `ʿ`/`ʕ` in columns 2-3.
- Use `a i u` (not DULAT diacritic aleph letters) in columns 2-3.
- `ʔ` is allowed in analysis when reconstructed (typically in verbal radicals), usually in sequences like `(ʔ`.

### 2.2 DULAT-side conventions (lookup-side)

DULAT may encode:

- aleph letters as `ả ỉ ủ`,
- ayin as `ʕ`,
- embedded homonym notation either:
  - in separate `homonym` column, or
  - directly in lemma text (for example `ltn (I)`).

Always normalize both sides before matching.

### 2.3 Broken characters

- `x` means broken/missing character in project data.
- If token is only `x` characters, skip lexical lookup for that token.
- For UDB concordance probing:
  - if token contains a single `x` (but not `x`-only), replace `x` with `-` and query UDB concordance,
  - if token contains `xx...` (two or more consecutive `x`), replace each consecutive run with `—` and query UDB concordance.
- Normalize ayin variants (`ʿ/ʕ/ˤ`) during lookup to avoid false negatives.
- If UDB concordance returns low ambiguity (`<=3` matches), promote alternatives into explicit semicolon variants in `col3/col4/col5/col6`.
- If UDB concordance is broad (`>3` matches), keep best-supported baseline parse and document the ambiguity briefly in comment.

---

## 3. Morphological Symbol Semantics

### 3.1 Core reconstruction symbols

- `(` = sign in lexeme/paradigm but absent in surface realization.
- `&` = sign in surface but absent in lexeme/paradigm.
- Substitution must be encoded as `(X&Y` (opening parenthesis precedes ampersand for the same substitution event).
- If multiple consecutive letters are reconstructed, each reconstructed letter must be marked separately with `(`.
  - Invalid: `š(lyṭ/`
  - Valid: `š(l(y(ṭ/`

Important:

- Do not flag `&` and `(` as substitution pair if separated by other lexical letters.
- Example (valid, non-adjacent): `!t!p&ph(y[n+h` (`&p` and `(y` are not one substitution pair).

### 3.2 POS-closing markers

- Noun/adjective lexeme: `/`
- Verb lexeme: `[`
- Deverbal nominal form (infinitive/participle in nominal use): `[/`
- Prepositions/particles/pronouns: no POS closing marker.

Examples:

- `il(I)/` (noun),
- `!t!qtl[` (verb),
- `qtl[/` (deverbal participle/infinitive used nominally).

### 3.3 Affixes and clitics

- Pronominal suffixes: `+` (for example `mlk/+h`).
- `=` can disambiguate homographic suffix series (`=`, `==`, etc.).
- Postclitic consonants: `~` before clitic consonant (`!y!rgm[~n`).

### 3.4 Prefix/stem marking

- Prefix-conjugation preformative between `!!` (for example `!t!qtl[`).
- Weak-initial `/y-.../` prefix forms must keep hidden root-initial `y` as `(y`:
  - `!y!(ytn[`, `!t!(ytn[`, `!a!(ytn[`, `!y!(yṯb[`.
  - If analysis has `!y!`/`!t!`/`!a!`/`!n!` with `/y-.../`, missing `(y` is invalid.
- Stem augment/infix marker between `]]` (for example `]š]qtl[`).
- Additional explicit stem markers may occur as `:d`, `:l`, `:pass`.
- `]š]` marks Š-family stem behavior.
- `]t]` marks Xt-family behavior (Gt, Št, Dt, Lt, Nt).

Markers do not have to appear immediately after `[`. They can appear after tense/person material (for example `kl(l[t:d`, `ṣm(t[t:d`).

### 3.5 Weak-final SC `-t` forms

- For finite non-prefix verbs from weak-final roots (`/...-...-y/`, `/...-...-w/`) where surface ends with `t`, encode suffix-conjugation ending as `[t` (not `t[`).
- Preferred pattern: `nš(y[t:n` for `/n-š-y/` (SC 1c), rather than substitution-style `nš(y&t[:n`.
- This rule does not apply to deverbal nominal forms marked `[/...` (for example participles).

### 3.6 Feminine `-t` handling in nouns/adjectives

- For feminine noun lexemes ending in `-t`, use `...(t/t` in feminine singular and `...(t/t=` in feminine plural.
  - Example: `am(t/t` (sg), `am(t/t=` (pl).
- For nouns where singular does not have feminine `-t` but plural does, use `.../t=` in plural.
  - Example: `gg/t=`.
- For adjectives and participles, feminine singular is `.../t` and feminine plural is `.../t=`.
  - Example: `kbd/t` (f.sg), `kbd/t=` (f.pl).

---

## 4. DULAT and UDB Data Access

### 4.1 DULAT database and key tables

Path: `sources/dulat_cache.sqlite`

Primary tables used:

- `entries(entry_id, lemma, homonym, pos, ...)`
- `forms(entry_id, text, morphology, ...)`
- `translations(entry_id, text, ...)`
- `dulat_reverse_refs(norm_ref, entry_id, payload)`  (reverse mention index by CAT/KTU reference)
- `attestations(entry_id, ug, translation, citation, kind)`  (entry attestations/citations)

Recommended checks:

- lemma-level disambiguation: `entries`
- attested-form and stem evidence: `forms`
- direct surface-to-entry candidate retrieval: `forms.text`
- gloss/context: `translations`
- line-level disambiguation hints: `dulat_reverse_refs` + `attestations.citation`

### 4.2 UDB database and key table

Path: `sources/udb_cache.sqlite`

Primary table:

- `concordance(word, ...)`
- `ktu_to_dulat(ktu_ref, entry_id, payload)` (reverse mention index by line/tablet reference)
- `reverse_index(norm_ref, target)` (reference -> UDB page/anchor map)
- `cuc_lines(id, ..., ktu_ref, ...)` (line text keyed by KTU/CAT reference)

UDB is secondary (coverage/info), not primary lexical authority.

### 4.3 Lookup strategy (required order)

1. Query `forms` by normalized surface (and by normalized reconstructed subparts where relevant) to get entry candidates.
2. Query `entries` by reconstructed lexeme to validate candidate headword class and homonym.
3. Before finalizing a candidate, enforce standalone-vs-clitic priority:
   - if token is standalone in analysis, prefer non-clitic lemmas over `-x` clitic lemmas,
   - prefer clitic lemmas only when analysis explicitly encodes clitic behavior (`+`, `~`, or post-verbal clitic tail).
4. For verbs, ensure root-style lookup as `/q-t-l/` (DULAT stores verbs as roots).
5. If candidates remain >1, apply reverse-reference narrowing:
   - map current token to a normalized line ref (`CAT 1.x C:L`),
   - fetch reverse mentions for that ref (`dulat_reverse_refs`/`ktu_to_dulat` or `/api/references/?ref=...`),
   - intersect lexical candidates from steps 1-4 with mention `entry_id` set.
6. Use `translations` (reference translation, if provided) to disambiguate remaining homonym candidates.
7. If two consecutive tokens remain unresolved, retry by combining them into one search unit and repeat steps 1-6.

This prevents false positives where standalone tokens like `d/k/m` are mapped to `-d/-k/-m`.

### 4.4 Local DULAT+UDB server workflow (recommended)

If the local web app is running (default: `http://127.0.0.1:8000`), use it as a fast evidence layer before direct DB inspection.

Primary endpoints:

- `GET /concordance/?word=...`  
  UDB concordance HTML. Supports pattern probing used for broken forms.
- `GET /api/concordance/?word=...`  
  JSON concordance for exact words (not wildcard-pattern probing).
- `GET /api/entries/?q=...`  
  DULAT entry search (lemma/headword/root candidates, POS, summary).
- `GET /api/references/?ref=...`  
  Line-level DULAT mentions by CAT reference (useful for contextual disambiguation).
- `GET /api/udb/lookup/?ref=...`  
  UDB anchor/lookup by CAT reference.
- `GET /api/openapi.json`  
  Confirm parameter names and endpoint behavior.

Practical probing rules:

1. Broken `x` handling for concordance:
   - single `x` -> `-`
   - `xx...` run -> `—`
2. Query UDB concordance first (`/concordance/?word=...`) and collect candidate matches.
3. For each candidate match, query `/api/entries/?q=<candidate>` to retrieve DULAT options.
4. Normalize ayin variants in queries (`ʿ/ʕ/ˤ`) if no direct hit appears.
5. Promote low-ambiguity findings (`<=3` concordance matches) into structured semicolon variants (`col3-6`).
6. If concordance is broad (`>3` matches), keep baseline parse and add concise uncertainty note.

### 4.5 Reverse-Reference / Mentions Workflow (high-value disambiguation)

Use this whenever one token still has multiple DULAT entries after normal lexical filtering.

Data sources:

- DULAT DB: `dulat_reverse_refs.norm_ref -> entry_id (+ payload JSON)`
- UDB DB: `ktu_to_dulat.ktu_ref -> entry_id (+ payload JSON)`
- API shortcut: `GET /api/references/?ref=1.2 III 12` (returns `mentions[]`)

Reference normalization:

- preferred canonical key: `CAT 1.2 III:12`
- API accepts loose input (`1.2 III 12`) and normalizes internally.
- when querying DB directly, test both `CAT ...` and `KTU ...` keys.

Decision rule:

1. Build lexical candidate set from `forms + entries` lookup.
2. Build mention candidate set for the current line reference.
3. Intersect sets:
   - one entry left -> prefer it as primary variant,
   - multiple entries left -> keep semicolon variants,
   - zero entries -> do not force; reverse index coverage is partial.
4. Mark weak-evidence cases in comment only when needed.

Generic tie-breakers (apply after lexical + mention filtering):

5. If candidates remain tied, prefer the entry whose exact surface form in `forms` carries matching morphology
   (for example `suff., pn.` for suffixed prepositional uses).
6. Use global mention frequency (`dulat_reverse_refs` + `ktu_to_dulat`) as a soft prior:
   - very common entries outrank rare ones when both are otherwise valid.
7. Use tablet-family distribution as a soft prior for proper names:
   - if a `PN/TN/DN` candidate is attested almost only in one tablet family (for example `4.x`)
     and current line is outside that family, down-rank it;
   - do not force if evidence remains mixed.

Example pattern:

- Surface `ˤmy` often maps to `ʕm (I)` [prep.] vs `ʕm (II)` [n.].
- When DULAT `forms` indicates `ʕmy suff., pn.` and corpus mentions overwhelmingly favor `ʕm (I)`,
  choose `ʕm (I)` unless line context clearly demands the rare noun reading.

SQL examples:

- DULAT reverse mentions:
  - `SELECT entry_id, payload FROM dulat_reverse_refs WHERE norm_ref='CAT 1.2 III:12';`
- UDB reverse mentions:
  - `SELECT entry_id, payload FROM ktu_to_dulat WHERE ktu_ref IN ('CAT 1.2 III:12','KTU 1.2 III:12');`

### 4.6 Modules + Notarius Workflow (translation/stem refinement)

Use module resources as a second-pass disambiguation layer after lexical matching.

Module sources:

- Web UI: `/modules/`, `/modules/TCS/`, `/modules/Smith/`
- DB: `sources/modules_cache.sqlite`
  - `modules(id, title, ...)`
  - `module_records(module_id, record_id, ref_norm, content_text, ...)`
  - `module_refs(record_id, ref_norm, ref_display, ref_system)`

Practical use:

1. Use `module_refs` to confirm whether a line/tablet/column has TCS or Smith coverage.
2. Use `module_records.content_text` to read the local translation/commentary context for that section.
3. Apply translation-driven disambiguation only when:
   - DULAT lexical options remain >1,
   - reverse mentions do not fully resolve the tie.

Important limitation:

- In current cache, many TCS/Smith refs are tablet- or column-level, not always single-line granular.
- Therefore treat module text as contextual evidence, not deterministic per-token ground truth.

Notarius (verb-focused reference):

- Source HTML: `sources/notarius.compact.html`
- Extracted evidence (recommended): `sources/notarius_evidence_claims.json`, `sources/notarius_evidence_context.json`
- Supporting script: `scripts/notarius_refinement_pass.py`

Use Notarius evidence to prioritize checks for:

- stem family alternatives (G vs N vs Xt/Št),
- infinitive vs participle behavior,
- passive readings and predicative uses.

Keep Notarius-driven alternatives explicit as structured variants when DULAT-valid; otherwise keep as comment-only philological note.

Important implementation detail:

- Wildcard/pattern behavior is driven by `/concordance/` (HTML endpoint).  
  Do not assume `/api/concordance/` accepts wildcard-like probes.

---

## 5. Step-by-Step Labeling Procedure (Deterministic)

For each token line:

1. Keep `col1`, `col2` unchanged.
2. Propose candidate analyses using surface morphology.
3. Build reconstructed lexeme from candidate analysis:
   - strip `!...!`, `]... ]` wrappers,
   - interpret `(` / `&` pairs,
   - strip clitic tails (`+...`, `~...`) for headword lookup,
   - for verbs: if reconstructed root starts with `a/i/u`, convert initial vowel to `ʔ` for DULAT root matching.
4. Determine lexical class from analysis:
   - contains `[` -> verbal/deverbal pathway,
   - contains `/` without `[` -> nominal pathway.
5. Query DULAT `forms` by normalized surface to collect initial entry candidates.
6. Query by reconstructed lexeme/root to validate and narrow candidates:
   - verbs must be checked as roots (`/q-t-l/` style),
   - apply POS constraints from analysis.
7. If homonym number is in analysis (for example `(I)`), enforce it during candidate filtering.
8. If candidates remain >1, apply reverse-mentions narrowing for this line reference:
   - query `/api/references/?ref=<tablet col line>` or DB reverse tables,
   - intersect lexical candidates with mention `entry_id`s,
   - keep only intersected candidates when intersection is non-empty.
9. For deverbals (`[/`):
   - check both verbal root candidate and nominal candidate.
   - if both exist and both fit homonym, treat as ambiguity case.
   - if only nominal exists but `[` is present, flag mismatch (verb-marked parse but only noun attested in DULAT for that homonym).
10. Parse clitics separately:
   - parts after `+`,
   - post-`[` tail segments (except pure stem markers like `:d`, `:l`, `:pass`),
   - ignore clitic segments that reconstruct to empty lexeme.
11. Apply fixed formula priors for `l` homonym disambiguation when sequence matches:
   - `tbʕ w l yṯb ỉlm` -> choose `l(II)` (`adv.`, `not`),
   - `ỉdk l ytn ...` -> choose `l(III)` (`functor`, `truly/certainly`).
   Treat these as high-confidence defaults unless local textual evidence explicitly overrides.
12. If a reference translation is provided, use it to break residual homonym ties.
13. If token `n` and token `n+1` are both unresolved after normal checks:
    - concatenate their surfaces,
    - attempt `forms` lookup on the combined surface,
    - if a valid entry is found, annotate as merged analysis with comment note.
14. Validate stem markers against DULAT form morphology:
   - default is `G` if unmarked,
   - if DULAT has no `G` for this verb, some stem marker must be present (`]š]`, `]t]`, `:d`, `:l`, `:pass`, etc.),
   - if marker is present, DULAT must contain compatible stem family.
15. Emit `col3` variants (`variant1; variant2; ...`).
16. Emit aligned `col4` DULAT entries:
    - one semicolon group per `col3` variant,
    - comma-separated within a group when the variant has multiple lexemes.
17. Emit aligned `col5` POS tags:
    - one semicolon group per `col3` variant,
    - comma-separated within a group for multi-lexeme variants,
    - if unresolved, keep POS options within one lexeme slot separated by `/`.
18. Emit aligned `col6` glosses:
    - one semicolon group per `col3` variant,
    - comma-separated within a group for multi-lexeme variants.
19. Keep comments for residual non-structured notes only:
    - translation evidence,
    - text-critical uncertainty,
    - rationale for disambiguation (`DN/PN/n`, stem choice, segmentation).

Formatting rules:

- `col3/col4/col5/col6` must have matching semicolon-group counts.
- Within each semicolon group, `col4/col5/col6` comma-item counts should match.
- Within each POS comma-item in `col5`, use `/` (not `,`) for alternative POS options.
- Use compact gloss text only (no HTML/article dumps).
- For `DN/TN/PN/GN`, prefer canonical proper-name glosses (for example `Ugarit`, `Baalu`, `El`, `ʿAnatu`).

---

## 6. Homonym and POS Rules

### 6.1 Homonym handling

- Always include homonym index when DULAT distinguishes homographs.
- Applies to lexical words and particles/pronouns.
- Example: `-h(I)` (pronominal) vs `-h(II)` (adverb).

### 6.2 POS-driven validity checks

- Verb analysis should contain `[`.
- Noun/adjective/proper-name analysis should contain `/`.
- Pronouns/particles/prepositions may be unclosed (no `/` or `[`).
- Deverbal nominal forms use `[/`.

### 6.3 Ambiguity reporting

If multiple DULAT candidates remain after homonym + POS + stem filtering:

- report all candidates as:
  - `lemma(homonym) [POS] — gloss`
- do not collapse silently.

### 6.4 Proper-name disambiguation (`DN` / `PN` / `n.`)

When DULAT POS mixes classes (for example `n., DN`), resolve by local translation context:

1. If translation uses a proper deity/location/person name, choose `DN`/`TN`/`PN`.
2. If translation uses title/common noun sense, choose `n.`.
3. Do not switch homonym prematurely; first resolve within the same homonym when it already contains mixed POS.
4. If translations disagree materially, keep baseline parse and add a second structured variant only when both readings are DULAT-valid.

Examples:

- `bʕl (II) [n., DN]`: `DN` for “Baʿlu”, `n.` for “lord/master”.
- `ỉl (I)`: `DN` for “El”, `n.` for generic “god/divine”.
- `ṣpn [TN, DN]`: `TN` for mountain/place usage unless translation/commentary explicitly indicates deity usage.

---

## 7. Complex Case Cookbook (Generic Patterns)

Use these patterns on any tablet; do not depend on tablet-specific IDs.

### 7.1 Reconstructed radical with substitution

- Pattern: analysis contains both reconstruction and substitution marks (for example `(ʔ&i`) in a deverbal form (`[/`).
- Rule:
  - keep reconstructed radical in the verbal root pathway,
  - treat substitution as a local grapheme event,
  - query DULAT by normalized root (`/C-C-C/`), not by the raw surface token.

### 7.2 III-aleph and case-vowel alternation

- Pattern: aleph/case material appears across reconstructed and surface sides (`(u`, `&i`, etc.).
- Rule:
  - keep reconstructed element with the lexeme/root side,
  - keep `&` element as surface-only evidence,
  - avoid forcing lexical split if the form remains morphologically coherent.

### 7.3 Non-adjacent `&` and `(` (not a substitution pair)

- Pattern: an `&` segment and a `(` segment appear in the same token but are separated by other letters.
- Rule:
  - do not trigger substitution-order errors unless the two marks describe the same local segment.

### 7.4 Multiple stem indicators in one verb

- Pattern: two stem indicators co-occur (for example Š-family + Xt-family behavior).
- Rule:
  - allow combined-stem interpretation when DULAT stem evidence supports it,
  - do not flag as inconsistent merely because more than one indicator appears.

### 7.5 Deverbal with both `[` and `/`

- Pattern: form is marked as `[/`.
- Rule:
  - check both verb-root and nominal pathways,
  - enforce homonym constraints where specified,
  - if only nominal survives but verbal marker remains, flag POS/morph mismatch.

### 7.6 Post-verbal clitic after `[`

- Pattern: clitic material follows the verbal core after `[`.
- Rule:
  - parse head verb and clitic separately,
  - use verbal root normalization for DULAT lookup,
  - validate clitic as an independent morph element.

### 7.7 Aleph-vocalic alternation across project vs DULAT orthography

- Pattern: project-side `a/i/u` corresponds to DULAT aleph-bearing transliteration.
- Rule:
  - preserve project notation in column 3,
  - normalize during lookup only,
  - keep comments aligned with DULAT headword spelling.

### 7.8 Verb homonyms

- Pattern: same reconstructed root maps to multiple homonym entries.
- Rule:
  - enforce explicit homonym marker from analysis first,
  - if still ambiguous, resolve using aligned translation context and notes.

### 7.9 Broken host + visible clitic

- Pattern: host token is mostly broken (`x...`) but enclitic/pronominal suffix is still visible (for example trailing `+k`-type behavior).
- Rule:
  - annotate visible clitic in structured columns if defensible,
  - keep host unresolved if concordance ambiguity is broad,
  - document broad ambiguity briefly as `UDB concordance ...`.

### 7.10 `/y-t-n/` imperative/short `tn`

- Pattern: surface is short `tn` but lexical pathway is `/y-t-n/`.
- Rule:
  - keep hidden initial radical as `(y`,
  - when imperative context is supported, allow no preformative marker: `!!(ytn[`,
  - do not force prefix preformative unless context demands prefix conjugation.

### 7.11 Formula-level `l` disambiguation

- Pattern A (negation formula): `tbʕ w l yṯb ỉlm`
  - enforce `l(II)` (`adv.`, gloss `not`).
- Pattern B (journey-opening formula): `ỉdk l ytn pnm ...`
  - enforce `l(III)` (`functor`, gloss `truly/certainly`).
- These two formula rules outrank generic frequency priors for `l(I/II/III)` unless a local edition note explicitly justifies an override.

### 7.12 Ambiguous `yX...` prefix forms across two roots

- Pattern: same surface `yX...` can be analyzed either as weak-initial `/y-.../` (with hidden `(y`) or as a consonantal root without initial `y`.
- Rule:
  - keep two explicit semicolon variants when both are lexically supported.
  - Example: `!y!(yṯb[;!y!ṯb[` with `/y-ṯ-b/;/ṯ-b/`.
  - resolve primary reading using line context and translation/commentary, but preserve defensible alternate if still viable.

### 7.13 Nouns with sg/pl same-form behavior

- Pattern: DULAT form inventory attests both singular and plural for the same written noun form (for example `hmlt`).
- Rule:
  - keep lexeme identification explicit in `col3` and keep plural ending split explicit,
  - use `.../m` for `-m` plural endings (for example `nš(m/m`),
  - use `.../t=` for feminine plural `-t` endings (for example `hml(t/t=`),
  - mark the noun POS in `col5` with `pl. tant.` (or `pl. tant.?` when tentative),
  - keep plurale-tantum marking out of comments,
  - linter must validate these split endings for marked pluralia tantum nouns.

---

## 8. Stem-Marker Compatibility Matrix (Project Level)

Use DULAT `forms.morphology` stem evidence.

- `]š]` -> requires one of: `Š`, `Št`, `Špass`
- `]t]` -> requires one of: `Gt`, `Št`, `Dt`, `Lt`, `Nt`
- `:d` -> requires one of: `D`, `Dt`
- `:l` -> requires one of: `L`, `Lt`
- `:pass` -> requires `Špass` (or project-approved passive mapping)
- no explicit stem marker:
  - acceptable if DULAT has `G`,
  - otherwise missing-marker error.

Reference stem inventory from `linter/morphology.py` includes:

- `G, Gt, Gpass., N, D, Dpass., tD, Dt, L, Lt, tL, Lpass., R, Š, Špass., Št`

---

## 9. Variant and Comment Handling

Variant parsing candidates may appear in comments during draft work:

- `# OR: ...`
- `# or ...`
- `# variant ...`

When present (draft state):

- parse each comma/semicolon-separated variant candidate,
- apply same lexical/stem/POS checks,
- stop variant parsing at `DULAT:`, `???`, or next `#` block.

Do not treat arbitrary comment text as morphological alt-form unless variant trigger is present.

Finalization rule:

- Promote recognized variant parses into `col3` (semicolon-separated).
- Populate aligned `col4/col5/col6` for each promoted variant.
- Remove duplicate `DULAT:` and inline `OR:` morphology payload from comments after promotion.
- Final comments must not use `OR:`; alternatives must live in structured columns only.
- Final comments must not repeat DULAT headword/POS/gloss already present in `col4/col5/col6`.
- When citing concordance evidence, write `UDB concordance ...`, not `server ...`.
- `DULAT: NOT FOUND` is acceptable only when `col4/col5/col6` are empty for that token.

---

## 10. Quality Control Checklist Before Finalizing a File

For each token:

1. `col1`, `col2` preserved from source.
2. Tabs intact (`id<TAB>surface<TAB>analysis`).
3. POS marker present when required (`/`, `[`, `[/`).
4. `(` and `&` used with correct directionality for true substitution pairs.
5. Multi-letter reconstruction uses per-letter `(` (no collapsed form like `š(lyṭ/`).
6. Homonym number applied when required.
7. Clitic parts (`+`, `~`) validated separately.
8. Stem markers validated against DULAT stem evidence.
9. DULAT entry is unique or ambiguity is explicitly documented.
10. No placeholder uncertainty markers left unresolved (`Merge`, `???`, `todo`) unless intentionally flagged.
11. Comments use DULAT orthography; analysis uses project orthography.
12. Consecutive unresolved token pairs were tested as merged surface candidates.
13. Standalone tokens were not mapped to clitic lemmas unless morphology explicitly requires clitic reading.
14. Mixed POS proper-name entries (`n., DN`, `TN, DN`, etc.) were resolved against line-level translation context.
15. `col3/col4/col5/col6` semicolon-group counts are aligned.
16. For each semicolon group, comma-item counts in `col4/col5/col6` are aligned.
17. Comments no longer duplicate structured DULAT/POS/gloss content.

---

## 11. Minimal SQL Snippets for Agent Tooling

Lookup entry by normalized lemma:

```sql
SELECT entry_id, lemma, homonym, pos
FROM entries
WHERE lemma = ?;
```

Get forms and stem evidence:

```sql
SELECT text, morphology
FROM forms
WHERE entry_id = ?;
```

Get translation/gloss:

```sql
SELECT text
FROM translations
WHERE entry_id = ?
ORDER BY rowid
LIMIT 1;
```

Check UDB presence (secondary):

```sql
SELECT 1
FROM concordance
WHERE word = ?
LIMIT 1;
```

Lookup DULAT candidates by surface form:

```sql
SELECT f.entry_id, e.lemma, e.homonym, e.pos, f.text, f.morphology
FROM forms f
JOIN entries e ON e.entry_id = f.entry_id
WHERE f.text = ?;
```

Lookup translation for homonym disambiguation:

```sql
SELECT e.entry_id, e.lemma, e.homonym, e.pos, t.text
FROM entries e
LEFT JOIN translations t ON t.entry_id = e.entry_id
WHERE e.lemma = ?;
```

---

## 12. Final Instruction to the Labeling Agent

When labeling a new file:

- prioritize reconstructing lexeme/paradigm visibility over phonological reconstruction,
- use DULAT as primary lexical authority,
- enforce homonym/POS/stem consistency deterministically,
- surface unresolved ambiguity explicitly in comments rather than guessing,
- preserve source token identity (`col1`, `col2`) exactly.

---

## 13. Practical Workflow: Using User-Supplied Translations to Improve Parsing

This section formalizes what to do in a second-pass review when literary translations and notes are supplied by the user.

### 13.1 Translation source stack (practical priority)

Use all available translation layers, but do not let any single translation override morphology without DULAT support:

1. Line/word anchoring data for the current tablet (`<tablet>.json`, UDB line variants, CUC line alignment).
2. DULAT (`entries`, `forms`, `translations`) as lexical-morphological authority.
3. User-supplied translations:
   - primary literary translation (A),
   - secondary/alternative translation (B),
   - commentary/notes edition(s),
   - philological dictionary notes (when provided).
4. Existing in-file word-by-word comments in the target labeling file.

### 13.2 Alignment protocol (must be done before editing parses)

For each suspicious token:

1. Anchor token by `id` and CUC line context.
2. Cross-check the same local segment against UDB line text/witnesses.
3. If CUC and UDB numeration appears shifted, align by local token sequence and neighboring anchors, not line number alone.
4. Read the immediate translation segment in the primary and alternative translations.
5. Check commentary/notes for emendations, restored letters, alternate segmentation, and stem/POS claims.
6. Classify discrepancy type:
   - lexical (different headword),
   - POS (noun vs verb/preposition/particle),
   - stem (G vs D/Š/Xt/etc.),
   - proper-name class (`DN/PN/TN` vs common noun),
   - segmentation (one token vs two-token composite),
   - purely interpretive (no morphology impact).

Only the first four types justify morphological change.

### 13.3 Promotion rule: when to convert comment-only alternative into explicit structured variants

Upgrade to explicit semicolon variants in `col3/col4/col5/col6` if all conditions hold:

1. Alternative is morphologically expressible in project notation.
2. Alternative has at least one DULAT-compatible lexical target (entry or plausible stem/root pathway).
3. Translation/commentary disagreement is specific to this line/token (not generic stylistic wording).
4. Alternative affects morphology/POS/stem/segmentation, not only literary nuance.

If published interpretations diverge and both readings are DULAT-attested, keep both as explicit semicolon variants; order variants by strongest lexical/stem evidence and retain the other published reading as secondary.

Keep as comment-only if:

1. Difference is purely interpretive or stylistic.
2. Alternative lacks DULAT support and requires heavy conjecture.
3. Line is too broken and no defensible morphological form can be proposed.

### 13.4 How to write translation-backed comments

Use compact, auditable references:

- `Translation A line 12`
- `Translation B note 7`
- `Commentary C p. 45 n. 3`
- `Dictionary note / attestation reference`

Preferred comment order:

1. Source reference and certainty tag:
   - `conjectural`,
   - `supported by note`,
   - `line-level variant`.

Do not include `DULAT: lemma [POS] — gloss` in comments when it is already encoded in `col4/col5/col6`.
Do not include `OR:` in comments; encode alternatives as additional semicolon variants in structured columns.

When a decision is mainly `DN/PN/n` resolution, add a short rationale:

- `TCS/UNP: proper-name usage`,
- `TCS/UNP: title/common-noun usage`.

### 13.5 Confidence tags (required for difficult alternatives)

Add one of these when introducing non-trivial alternatives:

- `supported` - DULAT + line-specific translation note agree.
- `plausible` - DULAT supports but commentary is indirect.
- `conjectural` - commentary suggests it, but no direct DULAT form attestation.

### 13.6 Practical pattern examples (tablet-agnostic)

1. Lexical sense split with same surface
   - baseline: noun parse from direct form match.
   - promoted variant: alternate noun/adj lemma with different homonym.
   - condition: both are DULAT-valid and translations diverge in the same line.

2. Verb vs function-word ambiguity
   - baseline: verbal parse (`...[`).
   - promoted variant: preposition/particle/adverb parse without verbal marker.
   - condition: commentary explicitly reads a syntactic (not verbal) function.

3. Stem reassignment
   - baseline: unmarked/G-style verbal parse.
   - promoted variant: marked stem parse (`:d`, `:l`, `]š]`, `]t]`, `:pass`).
   - condition: translation note + DULAT stem evidence indicate non-G reading.

4. Restoration-driven alternative
   - baseline: reading from preserved graphemes.
   - promoted OR (conjectural): restored grapheme via `( ... )` leading to different lemma/root.
   - condition: explicit note support and clear uncertainty tag.

5. Segmentation alternative
   - baseline: token treated as one lexeme.
   - promoted variant: split/merge segmentation across adjacent tokens.
   - condition: combined/split form yields better DULAT + translation alignment.

### 13.7 Token-combination fallback with translations

When two adjacent tokens remain unresolved:

1. Use translation phrasing and notes to test whether they represent one lexical item.
2. Attempt combined-form lookup in DULAT `forms`.
3. If resolved, keep main parse and note:
   - `# merged with previous/next token per translation note ...`
4. If unresolved, retain separate tokens and add:
   - `# unresolved segmentation; OR merged reading ...`

### 13.8 Do-not-do rules in translation-driven pass

1. Do not replace a stable parse with a literary paraphrase that has no DULAT path.
2. Do not add comment-only `OR:` for translation nuance; promote only morphology-impacting alternatives into structured columns.
3. Do not delete previous evidence; append new references and keep audit trail.
4. Do not promote conjectural alternatives without marking them as such.

### 13.9 Fast decision protocol for high-frequency ambiguous lexemes

For recurring ambiguous lexemes (for example `bʕl`, `ỉl`, `ṣpn`):

1. Apply one decision policy per local context pattern.
2. Batch-review all occurrences after first-pass edits.
3. Keep comments concise and consistent across instances.

---

## 14. Appendix A (Optional): Project-Specific Worked Examples

This appendix is optional and may be skipped when working on other tablets/projects. It exists only as a concrete reference set from prior work.

1. `9510 sid s(ʔ&id[/` - reconstructed radical with substitution; lookup target `/s-ʔ-d/`.
2. `9527 mri mr(u[/&i` - reconstructed vs surface case-vowel alternation.
3. `9548 tpphnh !t!p&ph(y[n+h` - non-adjacent `&` and `(` should not trigger substitution-order error.
4. `9842 tštḥwy !t!]š]]t]ḥwy(II)[` - combined stem indicators in one verbal form.
5. `10049 rkb rkb(I)[/` - deverbal requiring dual verb/noun pathway check.
6. `10132 atm !!at(w[~m(II)` - post-verbal clitic split from head verb.
7. `139819 yˤn !y!ˤn(y(I)[` - homonym-enforced verbal disambiguation.
8. `139777 š &š` - CUC marks this token as uncertain/excised; keep token order and mark unresolved lexical slots as `?` in `col3/col4/col5/col6`, with a short note.
