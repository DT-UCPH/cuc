# Reconstruction Semantics

Reconstruction answers one question: which letters of the edited linguistic word does this analysis encode? It does not establish the correct lexeme, homonym, stem, POS, or interpretation.

## Core Atoms

- Plain letters contribute to the surface.
- `(x` records lexical `x` as reconstructed and contributes nothing to the surface.
- `(x&y` substitutes edited-reading `y` for reconstructed lexical `x` and contributes `y`.
- `&y` contributes an attested `y` that remains in the edited word but is absent from the lexical representation.
- `(]n]` is one reconstructed N-stem marker atom and contributes no `n`.
- `]n]` contributes a written N-stem `n` because brackets are delimiters.
- `!`, `]`, `[`, `/`, `=`, `+`, `~`, comma, and closing parenthesis are structural delimiters and contribute no letters themselves.
- Roman-numeral homonym tags such as `(III)` contribute nothing.
- Stem and unwritten-ending labels such as `:d`, `:l`, `:r`, `:pass`, `:w`, and legacy `:n` contribute no surface letters.

The opening `(` binds exactly one letter or supported marker atom. In `]n](nšy[t`, `(n` hides `n`, but `y` remains plain and therefore visible.

## Three Independent Validations

Require all three:

1. **Edited-reading validity:** the analysis reconstructs the word after ancient and modern editorial operations have been applied, or an explicitly merged edited word when migration split one lexical word.
2. **Structural validity:** letters belong to the correct root, stem formative, ending, suffix, enclitic, or allographic substitution.
3. **Linguistic validity:** DULAT, POS, textual context, expert comments, and parallels support the analysis.

For example, both `(]n]nš(y[t` and `]n](nš(y[t` reconstruct `nšt`. Only the second follows this project's suffix-conjugation convention when the N formative coincides with root-initial `/n/`.

## Accepted Surface Equivalences

Use the repository helper because it normalizes project allographs such as `ʕ`/`ˤ` and handles designated unwritten endings such as `:w`. Do not duplicate only part of those rules in a one-off audit.

## Split-Token Exceptions

Rows marked `MERGE WITH THE NEXT` or `MERGE WITH THE PREVIOUS` can carry a whole-word analysis on each component row. Such an analysis may intentionally fail against either component surface alone.

Do not silence the exception globally. Report or skip only rows with explicit paired migration comments, then validate:

- adjacency and paired comments;
- concatenated surface;
- identical intended whole-word analysis where appropriate;
- preservation of the legacy comment and lexical decision.

Use `$audit-split-token-migrations` for the full paired-row audit.

## Common Failure Patterns

- one `(` assumed to hide a sequence rather than one atom;
- weak `y`, `w`, or `ʔ` left plain despite being unwritten;
- edited-reading stem formative encoded with a reconstructed marker;
- root letter and stem formative collapsed without recording both roles;
- suffix or enclitic delimiter placed before the wrong segment;
- analysis validated against a split component instead of the merged edited reading;
- decoder changed to accept an encoding that remains morphologically wrong.
