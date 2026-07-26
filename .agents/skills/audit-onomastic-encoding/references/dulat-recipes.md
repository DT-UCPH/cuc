# DULAT and EUPT query recipes, and known traps

## EUPT carries its own token-level morphology — use it

`modules_cache.sqlite` is a second, independent authority alongside DULAT, and
its most valuable layer is **not** the prose. `module_records.data_json` for
`EUPT_vocalisation` holds a `words[]` array with one entry per token:

```json
{"form": "[ḥûšīki", "morph": "G-Imp. 2.f.Sg.", "lemma": "ḥwš", "homonym": ""}
```

13,258 words corpus-wide, 12,680 with a `morph` tag and 12,646 with a `lemma` —
so EUPT independently supplies stem, conjugation, person, gender, number, case,
state, and lemma. Reading only `content_text` throws all of this away.

Coverage is densest exactly where reviewed work is thinnest: KTU 1.14 = 1306
words, 1.15 = 2438, 1.16 = 1518.

Run the aligner (needs the current cache; the repo-local snapshot predates the
EUPT layer and the script says so):

```bash
CUC_MODULES_DB=<path>/modules_cache.sqlite \
  python3 <skill-dir>/scripts/eupt_align.py 1.14 III,IV
```

### EUPT tag mapping — `GN` is a false friend

| EUPT | German | ours |
|---|---|---|
| **`GN`** | **Gottesname** | **`DN`** |
| `ON` | Ortsname | `GN` / `TN` |
| `PN` | Personenname | `PN` |
| `St.cs.` | Status constructus | `cstr.` |
| `G-SK` | Suffixkonjugation | `vb G suffc.` |
| `G-PKL` / `G-PKK` / `G-PKx` | Präfixkonj. lang / kurz / unbestimmt | `vb G prefc.` |
| `G-Ptz.akt.` | Partizip aktiv | `vb G act. ptcpl.` |
| `Gp-` | G passive | `vb Gpass` |
| `Poss.Suff. 3.m.Sg.` | — | `+ 3 m. sg. suff.` |
| `EP -m` | Enklitische Partikel | `+ encl. -m` |

Mapping EUPT `GN` onto our `GN` would silently convert every deity into a place
name. Verified: EUPT tags `il` GN 157×, `bˁl` 179×, `aṯrt` 45×; `kptr`, `ṣpn`,
`udm` are `ON`; `krt` is `PN` 112×.

### A bare case tag is not a denial of proper-noun status

EUPT often gives only `Gen.f.Sg.` where it elsewhere tags the same lemma `ON`
(e.g. `udm`: `ON` 11×, bare case 9×). Treat `ours = DN/PN/GN` vs
`EUPT = bare case` as **uninformative**, not a conflict — otherwise you
manufacture false positives. `eupt_align.py` encodes this in `_uninformative()`.

### EUPT line numbering can run one behind KTU

`eupt_align.py` keys strictly on `(column, line)`, so a numbering offset drops
tokens into the `no-eupt-match` bucket rather than reporting a disagreement.
Confirmed at KTU 1.14: the formula `km tsm ʕṯtrt tsmh` sits at corpus VI:28 but
EUPT VI:27, so the aligner found the III:42 instance and missed the VI:28 one.

When a lexeme is corrected at one attestation, grep the tablet for the same
surface and check its parallels by hand — do not trust the aligner to have
caught them all. Widening the match to ±1 line would also work, at the cost of
false pairings in repetitive poetry.

### EUPT commentary is typed

`EUPT_commentary` records are prefixed with their category: `gr` (Grammatik),
`rek` (Rekonstruktion), `lx` (Lexikon), sometimes combined (`lx / gr`). A `gr`
note is a morphological argument and is worth reading in full before overriding
EUPT's own `morph` tag.



The DULAT cache resolves via `agent/project_paths.py` (`CUC_DULAT_DB`, else
`agent/local_sources/dulat_cache.sqlite`). Never hard-code an absolute path.

```python
import sqlite3, sys
sys.path.insert(0, "agent")
from project_paths import get_project_paths
con = sqlite3.connect(f"file:{get_project_paths().default_dulat_db()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
```

Relevant tables: `entries` (lemma, homonym, pos, gender, summary), `senses`
(number, definition), `stems`, `forms` (text, morphology), `attestations`
(citation, ug, translation, sense_definition), `lemmas`, `translations`.

## 1. What senses does this lexeme have?

```sql
SELECT s.number, s.definition
FROM senses s JOIN entries e ON e.entry_id = s.entry_id
WHERE e.lemma_lower = ? AND e.homonym = ?
ORDER BY s.number;
```

Sense numbers are the vocabulary the gloss column uses. `ym (II)` has sense 1
"Sea" and sense 2 "DN, the sea god", so the gloss `2) DN` is a *reference to
sense 2*, not free text. Reuse DULAT's definition wording; do not paraphrase.

## 2. Does DULAT read a name at this exact line?

```sql
SELECT e.lemma, e.homonym, a.ug, a.translation, a.sense_definition
FROM attestations a JOIN entries e ON e.entry_id = a.entry_id
WHERE a.citation LIKE '%1.4 VI:12%';
```

Citations are `CAT <text> <col>:<line>`. A hit settles the reading. A miss is
*not* evidence against it — many lines are simply not cited. When there is no
citation, fall back to the nearest cited parallel and say so in the comment.

## 3. Is this surface a listed form of that entry?

```sql
SELECT f.text, f.morphology FROM forms f
JOIN entries e ON e.entry_id = f.entry_id
WHERE e.lemma_lower = ? AND e.homonym = ?;
```

This settles paradigm questions that surface spelling cannot. `ảl (III)` "ram"
lists `ỉlm` as its **plural** — so `ilm` in `ṯrm w mri ilm` can be "rams" and
not only "gods", which is exactly how DULAT reads the parallel at 1.22 I:13.

## Traps

### The onomastic override key must carry the homonym

`agent/data_sources/onomastic_gloss_overrides.tsv` expands the linter's POS
allowlist so a lexeme DULAT types as `n.` may take a `DN` POS. The lookup key is
`(lemma, homonym)`. A bare `ym` row does **not** match rows declaring `ym (II)`,
and every such row fails with:

```
POS token 'DN m. sg. abs. nom.' not allowed for ym (II); choose one of: n
```

Write the key exactly as the rows declare it — `ym (II)`, `bʕl (II)`, `ỉl (I)`.
This single missing homonym silently cost 35 lint errors across 1.1/1.2/1.4.

### The cache's `gender` column narrows dual gender — check `raw_notes`

`entries.gender` holds a single value; it cannot represent DULAT's `m./f.`
Printed DULAT `pỉt n. m./f.` is stored as `gender = 'm.'`, and no entry in the
cache contains a `/` in that column. The true string survives in the entry's
`raw_notes` (inside the `data` JSON), e.g. `<b>pỉt</b> n. m./f.`:

```python
import json, re
j = json.loads(row["data"])
notes = j.get("raw_notes")
notes = " ".join(notes) if isinstance(notes, list) else (notes or "")
gender = re.search(r"\b(?:n|adj|subst)\.\s*((?:m|f|c)\.(?:\s*/\s*(?:m|f|c)\.)*)",
                   re.sub(r"<[^>]+>", "", notes))
```

This is **narrow, not systemic** — 15 entries cache-wide, all recoverable:
`ʕqb`, `ʕšr(t) I`, `ḏnb(t)`, `grn I`, `ḫlpn I`, `ḫpn I`, `ḫṭ`, `mdbḥ`, `mḥt`,
`mškb(t)`, `pỉt`, `rmṣ`, `slḫ I`, `špš` (f./m.), `ṯq`.

Consequence for lint: `Noun POS gender mismatch` is a **false positive** for these
lexemes. `lint.py` already skips any gender that is not exactly `m.`/`f.`/`c.`
(see the `entry_gender_index` build), so populating the index from `raw_notes`
would suppress them correctly — the linter logic is right, the source field is
lossy. Confirmed case: id 155451 (`pitm`, KTU 1.2 IV:5) analysed `n. f. du.` is
correct and flagged only because of the narrowing.

Do **not** assume every gender-mismatch error is this bug. Of 37 in the reviewed
tree only 1 is; the other 36 are genuine corpus-vs-DULAT disagreements, led by
`ks/śủ` (15, DULAT f. vs corpus m.) and `ảbn` (7, DULAT f. vs corpus m.).

### A precedent is not evidence unless it is principled

Copying an existing row's encoding is the fastest way to stay consistent and
also the fastest way to spread a defect. Two cases from one session:

* `riš(I)/t=` + `n. m.` looked like 13 precedents licensing a masculine `/t=`.
  They only escape the check because a following `+suffix` stops the regex; the
  rule really is `/t=` ⇒ `f. pl.`
* `!y!]ṯ](yṯb[` (id 160206) looked like the encoding for `yṯṯb` Gt. But the Gt
  infix is **`t`**; there is no Gṯ stem. Where the infix assimilates to a
  following radical it must be written as lexical `t` realised as `ṯ`:
  **`!y!](t&ṯ](yṯb[`**. Only those two rows used `]ṯ]`, against 64 correct
  `]t]` — a 2-vs-64 split is a defect, not a convention.

Before citing a row as precedent, check it against the conventions doc or the
population. `awk -F'\t' '$4 ~ /<pattern>/'` over `reviewed/*.tsv` costs nothing
and tells you whether you are following a rule or an outlier.

### Clitic tails in POS (fixed — do not re-introduce)

A POS like `DN m. sg. abs. gen. + encl. -m` used to fail the allowlist even when
`DN` was licensed, because the affix tail was not normalised away before the
head comparison. `POS_AFFIX_TAIL_RE` in `agent/linter/lint.py` now strips it in
`normalize_pos_option_for_validation`, alongside the existing gender/number/
state/case stripping. That was **348 of 740** reviewed-tree errors — 47%.

If you touch that normaliser, keep the guarantee that a genuinely wrong head
still fails once the tail is removed (`vb G suffc. 3 m. sg.` must not validate
against `n`); `tests/test_linter_pos_normalization.py` asserts this.

### The linter only strips `sign span` inside a directory named `reviewed`

`file_has_reviewed_sign_span_column()` returns `False` unless
`path.parent.name == "reviewed"`. Reviewed TSVs have 8 columns; automatic output
has 7. Lint a reviewed file from a scratch directory named anything else and
every column shifts by one — you get hundreds of bogus "Unknown DULAT token in
column 4" errors, on the baseline as well as the candidate, so the diff looks
plausible while being entirely meaningless.

Always create `<tmp>/base/reviewed/` and `<tmp>/cur/reviewed/`.

### Compare ERROR counts, not totals

Most lint output is INFO. Normalise away absolute paths and row numbers before
diffing, and expect two spurious deltas whenever you add an option row:

- `Surface X parsed inconsistently: …` — mechanical, lists every id.
- `choose one of: n` → `choose one of: dn, n` — the hint text changes when an
  override lands; the underlying error is the same one.

## Column layout

| idx | reviewed        | automatic       |
|----:|-----------------|-----------------|
| 0   | id              | id              |
| 1   | surface form    | surface form    |
| 2   | **sign span**   | analysis        |
| 3   | analysis        | DULAT           |
| 4   | DULAT           | POS             |
| 5   | POS             | gloss           |
| 6   | gloss           | comments        |
| 7   | comments        | —               |

Second-option rows repeat id, surface, and sign span verbatim and vary only the
analysis onward.
