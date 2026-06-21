## Discussion outcomes (what was decided / clarified)

### Parsing conventions

* **Homograph disambiguation for suffixes (h=, t==, etc.)**

  * Intended use: disambiguation for gender/number/person where applicable.
  * Current state: not consistently applied; often genuinely hard in Ugaritic due to lack of vowels.
  * Practical stance: can be postponed and revisited later (Martijn to advise on policy).

* **Homographic particles vs. DULAT numbering**

  * No “double marking” like `+h(I)=` / `+h(I)==`.
  * If DULAT splits a suffix into multiple lexemes: use the DULAT number(s) **or** the project’s disambiguation marking — not both in the same token.

* **Stems and reconstructed patterns (:d, :pass, etc.)**

  * Earlier practice existed but was simplified for the research assistant.
  * Current preference: reconstruct stems broadly (important for Tania’s research), treated differently from reconstructing invisible consonants/vowels.
  * Note: N-stem assimilation may be marked by adding `n` where relevant.

* **Aleph/case-ending notation and “&”**

  * `rp(u&/m` in docs was an error; correct form should encode both dictionary form and surface realization (e.g. `rp(u&u/m`).
  * For III-ʾ nouns: keep the pattern “dictionary form + surface case vowel”, e.g.
    `ks(u/&u`, `ks(u/&i`, `ks(u/&a`.
  * Order inconsistency (`/&` vs `&/`) is acknowledged; leaning toward making it consistent (tentatively `&/`), but the key correction is the missing vowel (`rp(u&u/m`).

* **Duplicate marking in forms like `šm(m(I)/m`**

  * Rationale accepted: keep lexeme shape as in DULAT inside the root segment, while still marking the plural ending.
  * Candidate for later review under a “pluralia tantum / special plurals” sweep.

* **Inconsistent operator usage (e.g., `l(I)+y` vs `l(I)/y`, and `hwt(I)/` vs `hw(t(I)/t`)**

  * Treated as inconsistency, not meaningfully different analyses.
  * Preferred forms: `l(I)+y` and `hw(t(I)/t`.

* **Active participles used as agent nouns**

  * Working decision: parse them as participles (even when semantically “noun-like”).
  * This decision is explicitly revisitable.

* **Using alternatives**

  * You’re not required to follow DULAT everywhere; Tropper and Bordreuil–Pardee matter; for KTU 1.1–1.4 also consult Smith and Smith–Pitard.
  * Alternative parsing can be added after `#` when needed, but you can’t preserve every possible option.

### General process

* **Special characters inside DULAT lemmas (reconstructions like brackets, ?, etc.)**

  * These are reconstruction markers, not parsing operators.
  * Provisional handling: remove them if reconstruction is clear; Martijn to confirm the standard policy.

* **Ground-truth images**

  * Still unclear what “which pictures” means; needs clarification/decision (see action points).

* **Translations to consult**

  * For Baal Cycle: primarily Smith–Pitard; also Tropper and DULAT; optionally other not-too-outdated resources.

* **Reference grammar**

  * Tania offered to share the reference grammar file.

### Specific KTU 1.3 follow-ups

* **Broken-context homographs (e.g., `al`)**

  * In broken/obscure contexts: ambiguity acknowledged; defaulting to `al(I)` is suggested as a practical default.

* **Split/merged tokens (p + rdmn vs prdmn)**

  * DULAT: one word (hapax divine name); KTU: split reading possible.
  * Current recommendation: keep as-is (don’t force merge) given obscurity.

* **Sequence mlḥt / qṣ / mri / ndd**

  * `mlḥt`: noun exists, but in-context commonly parsed as passive participle used adjectivally (attribute to “knife/sword”); question remains whether to keep both analyses.
  * `qṣ`: prefer noun here (supported by following genitive logic).
  * `mri`: treated as passive participle of m-r-ʔ in grammars; can be adjectival or substantivized.
  * `ndd`: Tania’s reasoning supports active participle in circumstantial use (parallelism with other lines).

* **Text corrections / erased letters**

  * `&p` may already serve as the notation for an erased letter; question is whether additional editorial marks should be included in the input files given to parsers.

* **Hypothetical stems**

  * Don’t tag as D-stem unless clearly supported; in the cited case, D-stem doesn’t fit expected II-weak morphology.

* **Feminine divine names**

  * Parser behavior (treat as divine names with feminine endings) is acceptable.

* **Plural endings / assimilation (bt etc.)**

  * Not encoding assimilated `n` is acceptable in the examples discussed.
  * Plural of `bt` (bnt) will require a dedicated encoding like `b(n(t/t=` (tentative).

* **Conjugation table “stars”**

  * Meaning unknown.

---

## Action points (who does what)

### Alex

* Update the **automatic parser rules** / normalization to enforce:

  * `l(I)+y` (not `l(I)/y` in those cases).
  * `hw(t(I)/t` (not `hwt(I)/` when that’s intended).
  * Feminine divine names and bt-plural handling consistent with Tania’s guidance.
* Add a **default rule** for broken-context `al`: prefer `al(I)` unless stronger evidence.
* Implement the **aleph/case-ending correction**:

  * Fix `rp(u&/m` → `rp(u&u/m`.
  * Choose and apply one consistent internal representation for the `&/` vs `/&` ordering (even if the output format stays stable).
* Draft a short **“when to add alternative parsing after #”** guideline (1–2 paragraphs) based on the “can’t preserve everything” principle.

### Tania

* Share the promised **reference grammar file**.
* Provide a brief **policy note on stems**:

  * Which stems/pattern tags are in scope (e.g., `:pass`, `:d`, N-stem assimilation mark), and what minimum evidence is required.
* Decide on `mlḥt` in-context policy:

  * single preferred analysis vs allowing an alternate after `#` for participle vs noun.

### Martijn

* Confirm the standard handling of **DULAT reconstruction characters** (`[]`, `?`, etc.): strip vs keep vs normalize.
* Clarify what should count as **ground-truth images**:

  * which edition/scan set is canonical, and whether parsers should see editorial marks (erasures/corrections) by default.
* Give a ruling on whether the project wants to **actively disambiguate suffix homographs now** (strict rules) or explicitly defer (minimal tagging until later).

### Open questions to park (needs answers later)

* Meaning of the **asterisks** in the conjugation table.
* A stable, documented policy for **merge/split tokens** across datasets (when to preserve KTU segmentation, when to follow DULAT, and how to represent uncertainty if needed).

If you want, I can turn this into a one-page “Parsing conventions delta” note suitable to paste into your documentation (only the decided items + the open items, without the email narrative).


## Overall

Clarifying the boundary between transcription and reconstruction

The document opens with a clear policy: "we decided not to reconstruct consonants… vowels and other grammatical markings that do not appear on the surface." However, subsequent rules appear to mandate significant reconstruction, creating a tension between the stated policy and the required practice. For example, the instructions require adding the "assimilated letter n" via (, explicitly marking the "ʔ" in verbs like š(ʔ&ib[/t= even when not visible, and adding :w to plural verbs where the vowel letter is "never written."

This creates a "gray zone" where annotators may be unsure whether to prioritize the surface-only rule or the reconstruction requirements. If the goal is a strict surface transcription, tags like :pass (for internal passives) or :w (for invisible plurals) seem out of place. If the goal is morpho-lexical analysis, the opening restriction on reconstruction requires revision. Explicitly defining which "non-surface" elements are mandatory will prevent annotator divergence.

Establishing a distinct token grammar for validation

The specification introduces a robust set of operators and markers (including (, &, !!, ]], +, ~, /, [, and various colon-tags like :w). Currently, however, the text serves more as a list of examples than a formal definition of the token grammar. It is not entirely clear which orders are allowed, how wrappers nest, or what the precedence rules are.

This ambiguity is already influencing the document's own consistency. For instance, verbal preformatives are described as being "between !!" (e.g., !t!qtl[), yet the "Prosthetic aleph" section notes a conflict where !! might need to change because it is already used for verbal prefixes. Without a strict, validator-ready syntax definition (e.g., stating exactly where [[ or !! can appear relative to root letters), different annotators may encode the same analysis in syntactically different ways, complicating the development of ingestion tools.

Resolving contradictory instructions for feminine endings

There appears to be a direct conflict regarding how to handle feminine noun endings. The section on Suffixes and enclitics states: "If feminine ending -t … is part of the lexeme, we leave it unmarked at this stage." However, the NOUNS section mandates a split encoding where t appears twice (e.g., am(t/t), describing it as both "a nominal ending" and "part of the lexeme."

Since these instructions are mutually exclusive, annotators following one section will be non-compliant with the other. This issue propagates through the system, interacting with plural markings (t=) and part-of-speech terminations (/). Because this affects such a large portion of the nominal system, it is critical to select one canonical pattern and deprecate the conflicting instruction to ensure the dataset remains deterministic.

Distinct semantic roles for aleph and vocalization markers

The current use of aleph markers (( and &) alongside the vowels u, i, and a seems to overload the notation, conflating graphemes with vocalic realizations. The document notes that ( and & can be used for aleph letters, but also employs u/i/a as case endings in III-ˀ nouns (e.g., ks(u/&u) and as vocalic inserts in verbs.

The III-ˀ noun rule is particularly difficult to parse conceptually. It requires encoding a final element as both "not present in the realized form" (indicated by () and "not present in the paradigmatic form" (indicated by &), despite the letter appearing on the surface. Clarifying the distinct semantic roles of these markers—separating the presence of a letter from its phonetic value or inflectional status—would reduce the risk of misapplication.

Handling ambiguity and variants systematically

The document acknowledges the difficulty of disambiguation but currently relies on ad hoc or informal methods to capture it. The conjugation tables frequently use an asterisk (e.g., 3m qtl[*), yet the text does not define whether * is a literal symbol for the annotator to type or a placeholder for a decision they must make.

Similarly, the VARIANTS section suggests using free-text comments following a # (e.g., "with Smith Pitard, or..."). While useful for human readers, this approach renders the ambiguity invisible to machine queries. Developing a formal syntax for alternatives (e.g., a specific delimiter for "Option A OR Option B") would allow the database to capture uncertainty in a way that remains searchable and actionable.

## Unresolved draft notes and citation mismatch

```
A very special case of aleph that is added in the plural of a noun, namely a prostetic aleph: dmʿ "tear". In the plural, it has a prefixed “u”. The same aleph occurs as well in imperative forms (see below), and its function is to break the initial cluster of consonants. In the encoding, we treat it as a prefix, e.g.:

udmʿth !(ʔ&u!dmʿ(t/t+h ”his tears” (TODO: maybe think about other marker than !! for the prefix, because this is used for verbal prefixes.:
```

The prosthetic aleph subsection still contains an inline “TODO” about whether the prefix should be marked with the same delimiter used for verbal preformatives (“!!”). For a tagging manual this leaves the convention explicitly unsettled and can lead to inconsistent annotation. Separately, the example “udmʿth !(ʔ&u!dmʿ(t/t+h” is difficult to square with the document’s own general nominal conventions: (i) the lemma is introduced as “dmʿ” but the split “(t/t” notation normally presupposes a lexeme-final -t, and (ii) the noun POS marker “/” and the segmentation of the pronominal suffix with “+” are not clearly represented here. Clarifying the intended lemma form and segmentation in this example would reduce confusion.


## Example contradicts the stated rule for I-aleph verbs

```
If the verb is of I or II-aleph root, firstly aleph is added by (, and then the vocalization is added by &:
!yrš[ "he desires"; !t!(]n](ʔ&adm[ "she blushed" (in the N-stem) š(ʔ&ib[/t= "(they, fem) water-drawers" (active participle). 
```

In the paragraph describing I/II-aleph root encoding (“firstly aleph is added by (, and then the vocalization is added by &”), the example block begins with “!yrš[”. As printed, this example neither shows the stated (… then &… sequence nor follows the manual’s own delimiter convention for prefix-conjugation preformatives (elsewhere consistently given as “!y!”/“!t!”). If “!yrš[” is intended as an I/II-aleph illustration, its encoding needs to reflect the rule; if it is not an aleph-root example, its placement in this block is likely to mislead.

## Ambiguity of surface forms in III-aleph paradigm


```
Case endings of nouns with aleph as final consonant... ksu "seat"... have 3 forms in singualar, processed as follows:
ks(u/&u nominative ks(u/&i genitive ks(u/&a accusative 
```

In the III-ˀ noun paradigm, the text introduces ksu and then lists three encodings with &u/&i/&a without explicitly pairing them with the corresponding surface spellings (e.g., ksu, ksi, ksa). The intended mapping is inferable for specialists, but making the surface↔tag correspondence explicit here would better match the manual’s “visible elements” emphasis. Also, the prose says these endings are placed after /, but the displayed examples appear to omit /; it would help to ensure that the examples reflect the intended placement consistently.

## Irregular plural paradigm for 'amt'

```
The plural of feminine words ending on -t is am(t/t=. -t= is the feminine plural marker.
```

The example “am(t/t=” is introduced right after “am(t/t … for the lexeme amt”, so it reads as a concrete plural example for that lexeme. If plural spellings of this noun (or comparable -t feminines) can include an additional consonant not present in the lemma, it would help to clarify whether “am(t/t=” is intended as a purely schematic illustration of the plural marker, and (if not) how such extra consonantal material should be encoded under the project’s “& = surface-only” convention.


## Typo in Prefix Conjugation table

```
2f !t==!qtl[		2f !t!qtl[n=	2f !t!qtl[*
1c !(ʔ$a!qtl[		1c !n!qtl[

Infinitive
!!qtl[/
```

In the PREFIX CONJUGATION table, the 1c singular entry contains an undefined symbol: “1c !(ʔ” is not part of the encoding inventory described elsewhere (where “&” is the relevant marker in this environment, cf. “!(ʔ&a!šlw[”), this looks like a typo that will cause avoidable inconsistencies if the table is used as a template.

## Syntactic fragmentation in 'gg' example

```
A noun that appears without the feminine -t in singular, but has it in plural gg, gg/t= "roof".
```

The line introducing the gg example reads as an English fragment (the general description is not explicitly linked to the example by a predicate such as “is tagged as” / “e.g.”). The intended analysis is clear, but a small connective would make the presentation smoother and easier to skim.