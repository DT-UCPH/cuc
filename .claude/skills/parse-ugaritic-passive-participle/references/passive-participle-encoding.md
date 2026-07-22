# Ugaritic G-Stem Passive-Participle Encoding

This reference operationalizes Chapter 2, "The Ugaritic passive participle", of Tania Notarius's draft monograph (`agent/local_sources/notarius.compact.html`). The local Wikipedia snapshot (`agent/data_sources/Ugaritic - Wikipedia.html`) supplies only the traditional *qatūl* shorthand; use it as a compact cross-check, not as evidence.

## The Central Constraint

The passive participle is **morphologically under-marked**. Ugaritic alphabetic writing does not distinguish the G passive participle from many homographic forms — the G-passive suffix conjugation, the stative suffix conjugation, stative adjectives, and (on strong roots) even the active reading (§2.2.1). The passive reading is therefore established **syntactically and semantically**, on the basis of diathesis, and only *sometimes* confirmed orthographically.

Consequence for tooling: **never assert a firm `pass. ptcpl.` from a bare consonantal skeleton.** A strong triradical root spells the *qatūl/qatīl* pattern identically to several other forms, so a strong-root passive participle rests entirely on the clause. The automatic parser over-generates exactly here (e.g. `rgm[/` "word", `ˤdb[/`, `ptḥ[/`); prefer the competing noun/finite reading unless syntax decides.

## Evidence Boundary

Treat as deterministic enough for tooling:

- The productive pattern is adjectival *qatūl* or *qatīl* (long second vowel); *qatul*, *qutal*, and *qutil* are excluded by most secure data, and *qatil* is inconsistent only with `brr` (§2.2.3a).
- The orthographic diagnostics in the table below hold at the level of the individual grapheme and are safe to check mechanically.
- Endings: word-final `-t` marks a feminine participle (singular or plural); word-final `-m` marks a masculine plural participle — but `-m` is also enclitic/adverbial, so it is not decisive alone (§2.2.2 (7)).

Do **not** turn these into hard parser rules:

- The choice between *qatūl* and *qatīl* (both long) is not recoverable from the consonantal text; the project notation does not encode it, so do not invent a marker for it.
- Whether a given patient-noun (e.g. `mrủ` "fatling", `šbyn` "captive") is a synchronic participle or a lexicalized noun is a lexical judgement (§2.3.2). Tania classes these as "highly lexicalized nominals". When the reading is the noun, encode it as a noun: attach it to its DULAT **noun** lemma and close it with `/` (e.g. `mr(u(I)/&i`), **never** with the deverbal `[/`. Record the participial origin in a comment only.
- Semantic labels (present passive, resultative, optative; §2.4) belong in the gloss/comment, never in the morphological string.

## Stem, Voice, and Lemma Attachment

Two encoding facts frame everything below; keep them straight before parsing.

- **The passive *stem* carries `:pass`.** An internal-passive stem — `Gpass`, `Dpass`, `Lpass`, `Špass` — is marked by `:pass` after the root and any endings: `!t!(ʔ&usp[:pass` (Gpass prefc.), `prš[&a:pass` (Gpass suffc.), `nb[t===:pass`. Every passive-stem row must carry `:pass`; a `Gpass`/`Dpass`/… label without it is an error. `:pass` is a sibling of the other stem markers `:d` (D), `:l` (L), `:r` (R).
- **The passive *participle* is a G-stem form and takes no `:pass`.** `vb G pass. ptcpl.` is the qatūl participle of the **G** stem; its voice is in the participial pattern, not the stem, so it is *not* the `Gpass` stem and does *not* take `:pass` (reviewed practice: every `pass. ptcpl.` row is `:pass`-free; every `Gpass` stem row carries `:pass`). A row labelled `Gpass ptcpl.` is a contradiction — decide whether it is the G passive participle (`G pass. ptcpl.`, no `:pass`) or a Gpass-stem form (add `:pass`, drop the participle framing).
- **Nouns and verbs stay separate, on their own lemmata.** A verb or verbal form (participle, infinitive) attaches to a verb root `/x-y-z/` and closes with `[` or `[/`. A noun, adjective, or lexicalized patient-noun attaches to its own DULAT **noun** lemma and closes with `/` — **never** `[/`. `[/` on a noun POS, or on a noun lemma, is an error, regardless of the form's deverbal origin.

## Orthographic Diagnostics (§2.2.2)

Each row is a place where the consonantal text *does* carry information. Marker key: `[` verbal-root boundary, `[/` deverbal (participle/infinitive) boundary on a **verb root**, `:pass` passive-stem marker, `(x` reconstructed lexical radical absent from the surface, `&x` written sign absent from the lexeme.

| # | Root class | Diagnostic | Example | Encoding note |
|---|---|---|---|---|
| 3 | II-ʔ | middle aleph vowel is decisive | `lủk` "sent" (ptcpl) vs. `lỉk` "he sent" (active SC) vs. `lảk` "was sent" (G-pass SC) | keep the written middle aleph `u`/`i`/`a` distinct from the radical |
| 4 | III-ʔ | final aleph spells the **case**: u→nom, i→gen, a→acc | ptcpl. nom. `mrủ` (`…/&u`) vs. G-pass SC 3ms `pršả` (`…&a`) | the realized case aleph is `/&u`, `/&i`, `/&a` |
| 5 | III-y/w | consonantal glide is retained | `kly`, `mḥy`, `ṣpyt`, `blym` | write the `y`; excludes *qatul*/*qutal* by triphthong contraction |
| 6 | geminate | written **plene** (both radicals) | ptcpl. `brr` "purified", `ktt` "powdered" vs. stative SC `br` written defectively | both radicals present ⇒ long second vowel |
| 7 | any | `-t` feminine, `-m` masc. plural endings | `ṣpyt`/`ṣpym` "embroidered" | `-t` reliable; `-m` also enclitic/adverbial |
| 1 | syllabic | `ḫa-ri-mu` "desecrated" (RS 20:123) ⇒ *qatīl/qatil* | — | corroborates the pattern; not in the alphabetic corpus |

The III-ʔ case rule (#4) is checked mechanically by the linter (`iii_aleph_case_mismatch` in `agent/linter/lint.py`) and by `scripts/audit_passive_participle.py`.

## Reject These

- A firm `pass. ptcpl.` whose only support is the bare skeleton on a strong root — prefer the noun/finite reading until the clause decides (§2.2.1). There is no form-level `?` marker (uncertainty is marked on the stem, e.g. `Gt?`), so do not write `pass. ptcpl.?`.
- A `Gpass`/`Dpass`/`Lpass`/`Špass` (passive-stem) row whose encoding lacks `:pass`.
- A `[/` deverbal boundary on a noun/adjective POS, or attached to a noun lemma — encode the noun with `/` on its noun lemma instead.
- A III-ʔ participle whose realized case aleph disagrees with the labelled case (e.g. `…/&i` labelled `nom.`).
- A III-y participle written without its glide, or a geminate participle written defectively (would point to a short-vowel stative reading instead).
- Semantic voice terms (`passive`, `resultative`, `optative`) placed in the morphological string.

## Syntactic Support (§2.3)

When orthography is silent, the passive reading is carried by syntax. Ask, in order:

1. Is the form **attributive** to a non-prominent antecedent (part of a list, object, or governed by a preposition — never the subject or vocative)? (§2.3.1)
2. Is it a **converb** — non-initial, subject- or object-controlled, introducing resultative or depictive secondary predication? This is the prototypical passive-participle function. (§2.3.3)
3. Is it a lexicalized **patient-noun** (keep the noun reading; note participial origin only)? (§2.3.2)
4. Is it **predicative**, disambiguated by a nominative `-u` ending, a `d`-relative marker, negation by `l`, or an argument introduced by `ˁm`? (§§2.3.4–2.3.5)

If the consonantal form admits more than one answer, keep the morphological ambiguity as a competing reading (a second row) rather than converting a discourse tendency into a deterministic parse. Where two researchers disagree (del Olmo/DULAT vs. Notarius), encode both readings as alternative rows; use `?` for the DULAT column and gloss of a reading that has no DULAT lemma, per `lexicon_and_grammar/tagging_conventions_cuc.md`.
