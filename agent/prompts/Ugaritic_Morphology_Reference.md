# Ugaritic Morphology Reference (Project Use)

Primary source: `linter/morphology.py`.
This file is a compact, agent-oriented reference for feature names and stem inventory used in labeling decisions.

## 1. Verbal Stem Inventory

From `stems` in `linter/morphology.py`:

- `G`: basic/ground stem.
- `Gt`: G with infixed `-t-` (often reflexive-like).
- `Gpass.`: passive of G.
- `N`: n-prefixed reflexive/passive-like stem.
- `D`: factitive/causative/intensive (geminated second radical).
- `Dpass.`: passive of D.
- `tD`: t-prefixed D.
- `Dt`: D with infixed `-t-`.
- `L`: lengthened stem (often hollow-root analog of D).
- `Lt`: L with infixed `-t-`.
- `tL`: t-prefixed L.
- `Lpass.`: passive of L.
- `R`: reduplicated biconsonantal stem.
- `Š`: š-prefixed causative stem.
- `Špass.`: passive of Š.
- `Št`: š-prefixed + infixed `-t-` stem.

Project marker mapping in analyses:

- `]š]` -> Š-family behavior (`Š`, `Št`, `Špass`).
- `]t]` -> Xt-family behavior (`Gt`, `Št`, `Dt`, `Lt`, `Nt` when attested).
- `:d` -> D-family (`D`, `Dt`).
- `:l` -> L-family (`L`, `Lt`).
- `:pass` -> passive marking (checked against `Špass` in current linter logic).

## 2. Core Grammatical Features

### 2.1 Case

- `nom.` nominative
- `gen.` genitive
- `acc.` accusative
- `gen., acc.` oblique

### 2.2 Person

- `1`, `2`, `3`

### 2.3 Gender

- `m.` masculine
- `f.` feminine
- `c. n.` common

### 2.4 Number

- `s` singular
- `d` dual
- `p` plural

### 2.5 State

- `emph.` emphatic
- `cstr.` construct
- `suff.` suffix construct

### 2.6 Pronominal Type

- `p.` personal
- `dem.` demonstrative
- `interr.` interrogative
- `rel.` relative
- `indef.` indefinite

### 2.7 Adjective Degree

- `P` positive
- `R` comparative
- `S` superlative

## 3. Verbal Category Labels

### 3.1 Conjugation / Tense Labels

- `suffc.` suffix conjugation
- `pref.` prefix conjugation
- `inf.` infinitive
- `impv.` imperative
- `ptcpl.` participle

### 3.2 Prefix-Conjugation Mood

- `indic.` indicative
- `juss.-pret.` jussive-preterite
- `vol.` volitive

### 3.3 Participle Voice

- `act. ptcpl.` active participle
- `pass. ptcpl.` passive participle

## 4. G-Stem Pattern Vowel Labels

From `Stem` in `linter/morphology.py`:

- `u` -> qatal
- `i` -> qatil
- `a` -> qatul

Project note: this label set is reference-only; in surface labeling, avoid over-reconstruction beyond visible evidence.

## 5. POS Inventory (Project-Relevant)

From `morphology["pos"]` and `POS` enum:

- `pn`: pronoun
- `PSS`: pronominal suffix
- `NN`: noun
- `PN`: proper noun
- `adj.`: adjective
- `adv.`: adverb
- `vb. n.`: verbal noun / infinitive
- `vb.`: verb

## 6. G-Stem Strong Templates (Reference)

These are model paradigms included in `linter/morphology.py`:

- G suffix conjugation:
  - qatal pattern `/1a2a3a/`,
  - qatil pattern `/1a2i3a/`,
  - qatul pattern `/1a2u3a/`.
- G prefix conjugation:
  - indicative pattern with `...u` endings,
  - jussive pattern with shortened endings,
  - volitive pattern with `...a` style endings.

Use these patterns as comparative reference only; project annotation policy is surface-first and symbol-based, not full vocalic reconstruction.

## 7. Practical Integration with Labeling

When annotating with project conventions:

1. Use morphology categories as lookup constraints, not mandatory full feature output.
2. Prefer explicit project symbols (`[`, `/`, `[/`, `]š]`, `]t]`, `:d`, `:l`, `:pass`, `+`, `~`).
3. Resolve lexical identity and stem family through DULAT (`entries` + `forms.morphology`).
4. Query verb entries as roots (`/q-t-l/` format) when validating verbal analyses.
5. Keep unresolved alternatives explicit instead of forcing one unsupported analysis.
