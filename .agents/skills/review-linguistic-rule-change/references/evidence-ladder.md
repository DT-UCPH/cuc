# Linguistic Rule Evidence Ladder

Use higher evidence to constrain lower evidence; do not treat the list as a voting system.

## Evidence Order

1. Explicitly accepted project tagging conventions.
2. Direct expert clarification tied to the disputed analysis.
3. DULAT lexeme, homonym, inflected-form morphology, and cited KTU attestation.
4. Stable parallel reviewed analyses with explanatory comments.
5. Other editions or grammars already admitted by the project.
6. Automatic parser output and surface analogy.

Automatic output is a hypothesis, not authority. Surface analogy can discover candidates but cannot establish lexeme identity, number, suffix, enclitic, or homonym by itself.

Surface reconstruction is a validation invariant, not lexical evidence. An analysis can reconstruct perfectly while assigning a written consonant to the wrong root, stem formative, or ending.

## Turn Feedback Into a Rule

Record:

- lexical scope: one headword, a closed class, or productive morphology;
- morphological scope: gender, number, state, case, suffix, enclitic, or stem;
- required encoding markers;
- explicit counterexamples and exceptions;
- whether the claim applies to reviewed data, automatic parsing, lint validity, or all three.

If any scope dimension is unknown, keep the claim provisional and audit before editing broadly.

## Corpus Matrix

Count and inspect separately:

| Corpus | Why it matters |
|---|---|
| Reviewed TSVs | Human decisions that may need correction or preservation |
| Current automatic output | Present parser behavior |
| Historical automatic versions | Whether behavior is parser- or TF-version-dependent |
| Parser tests/config | Existing intended rule and exception boundaries |
| DULAT/UDB evidence | Lexical and attestation constraints |

## Implementation Boundary

- A single exceptional lexeme belongs in reviewed data or a narrow override.
- A finite named set belongs in configuration with tests.
- A productive form belongs in a parser step with change-ratio safeguards.
- A universally malformed encoding belongs in the linter.
- A convention clarification belongs in the tagging conventions plus tests that encode it.

Do not add a broad parser heuristic to make one reviewed row agree. Do not duplicate the same rule independently in several steps when one authoritative transformation can feed downstream consumers.

## Review Outcome

End with one of:

- accepted as a general rule;
- accepted for a closed lexical set;
- accepted only for the cited token;
- already encoded correctly;
- unresolved pending stronger evidence;
- rejected because a documented exception applies.
