# šlyṭ: reported alternatives and proposed registry integration

Discussion draft, 2026-09-07. No new morphology notation, registry entries or
parser acceptance rules are introduced by this document.

## Correction to the first review

DULAT p. 810, entry 4055, classifies the headword as a masculine noun but reports
several other interpretations in its full note:

- Margalit, MLD p. 90: an encircling interpretation derived from lw/yṭ.
- De Moor, UF 11 (1979), p. 641 n. 12: ly/uṭ, explicitly Š, associated with
  the tyrant interpretation and Akkadian lâṭu.
- Caquot–Sznycer, TOu/1 p. 168: a personal-name interpretation.
- Fronzaroli, MARI 8 p. 289 n. 56, and Watson, Historiae 4 (2007), p. 102:
  further etymological interpretations involving piercing/biting.

These are **authors’ proposals reported by DULAT**, not necessarily DULAT’s
preferred analysis. Specifically, “diff. from ltn” in this entry concerns the
monster's identification; the subsequent “Other etym.” passage contains the
alternative derivations. The distinction matters when extracting claims.

The initial lookup helper printed structured POS, translations and forms but
omitted the full notes. Those fields do not encode all the alternatives just
listed. The helper now prints the notes and page as well. Consequently, neither
“Not in DULAT” nor “invented roots” adequately describes these proposals.
The earlier helper's own assertion of invented roots is not independent evidence.

The old rows also make more specific claims than the note alone establishes:
they distinguish /l-w-ṭ/ and /l-y-ṭ/, active versus passive participles, and
encircling versus cursing glosses. Attribution cannot be transferred from one
combination to another. Verify the cited original passages before certifying
those exact parses. Tania's rejection and the source-backed competing proposals
must both remain visible. The working TSV now records this reopening in comments;
no unverified full participial rows have been reinstated as accepted scoring gold.

## Registry inspected

Read the local `issue-43-reference-authority` branch in `../dulat`, HEAD
`2a3c1100`, including `data/lexeme_registry/README.md`, the TSVs, record model,
and minting script. The checkout has unrelated uncommitted changes and was not
modified. Relevant existing design:

- Opaque ULR IDs, independent of DULAT entry IDs; source-owned homonym numbering.
- Separate senses, including stem-specific verbal senses.
- Explicit source mappings and reviewed mapping decisions.
- `NEW:<tag>` in mapping inputs to request minting from known source records.
- A `provisional` lexeme-status constant in the model. This alone does not
  implement a complete proposal/review workflow.

The current registry contains `ULR-03916` for šlyṭ, with DULAT 4055, LUPT,
GlOS, Ukrainian and CUC-lexicon links. It has no explicit sense row in the
inspected `lexeme_senses.tsv`. The De Moor/Margalit proposals are not separately
represented by those source links. `NEW:<tag>` requires an existing source
entry recognized by the minting readers; an arbitrary citation to a paragraph
cannot presently be supplied as though it were such an entry.

## Recommended representation — proposed, not implemented

Keep three distinct decisions:

| Decision | What to record |
|---|---|
| Is there a lexical proposal worth representing? | Proposed lemma/root or sense; exact author and citation; whether consulted directly or reported through DULAT; proposal status. |
| Is it the same lexeme/sense as an existing registry entry? | Mapping proposal to a ULR ID or request for a new identity; reviewer and rationale. A new etymology does not automatically require a new lexeme. |
| Does this token instantiate that proposal? | Token/reference, candidate morphology, supporting source, expert objections and local review status. Lexeme registration does not accept every token analysis. |

For human-readable corpus comments, a possible temporary reference would be
`LEX-PROPOSAL: CUC-SHLYT-001`. This is an **illustrative syntax**, not a reserved
ID or a recognized linter directive. It would point to a separate curated
proposal record. Keep uncertainty and workflow status out of the morphology
string: adding a prefix there would change reconstruction semantics, while
adding a fake DULAT homonym would misstate the source.

The proposal record should contain: ID, proposed lemma/root or sense, related
ULR ID if any, attributed claim, bibliographic locator, reporting source,
directly-checked flag, affected token IDs, alternative analyses, expert responses,
status (proposed / accepted / rejected / superseded), reviewer, and eventual
registry target. Preserve the proposal ID as a redirect after acceptance.
These fields are a design recommendation, not existing registry capabilities.

For šlyṭ, start with separate attributed claims, not three automatically minted
verbs. Decide whether each is (a) an alternative derivation of the existing name,
(b) a stem-specific sense of a root already registered, or (c) a proposed new
root/lexeme. A personal-name interpretation can likewise require a sense/category
decision without creating a new spelling identity.

Once the proposal workflow is agreed, the corpus can link accepted analyses to
ULR/sense IDs and unresolved candidates to proposal IDs in a sidecar keyed by
reference, token and alternative. Then the linter can distinguish an unresolved
lexical reference from an invalid morphological encoding. A proposal must never
exempt reconstruction or silently count as an accepted analysis in scoring.
The present DULAT column need not be overloaded before this migration is designed.

## GitHub discussion retrieval

Read the three locally identified Tania commits' comment endpoints, repository
commit comments, pull-request review comments, and commit comments on alexsosn/cuc.
The specific šlyṭ / “diff.” comment was not located. The repository-wide comments
instead exposed discussion on an earlier commit, `1413e103`, so the first review's
three-commit inventory does not cover the entire historical conversation.
The user's account of the missing comment is retained; its wording is not
reconstructed. A direct permalink would let us add it to the evidence record.

## Next decisions

1. Verify the original cited interpretations and map them to the historical
   analyses without transferring root/stem/voice/gloss claims between authors.
2. Agree whether proposals live in the ULR repository (preferred for shared
   editorial ownership) with a corpus sidecar pointing to them, or temporarily
   in CUC with stable IDs that survive migration.
3. Add the proposal workflow and source-claim addressing before teaching parser,
   linter and scorer to consume it. Reuse ULR identities and sense distinctions;
   avoid introducing a competing permanent lexeme numbering system in CUC.
