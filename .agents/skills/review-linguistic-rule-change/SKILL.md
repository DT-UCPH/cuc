---
name: review-linguistic-rule-change
description: Evaluate expert or upstream feedback about Ugaritic morphological parsing, determine whether it expresses a general rule or a local reading, measure all affected reviewed and automatic rows, and implement the justified data, parser, documentation, and test changes. Use for review comments, disputed encodings, or requests to find similar cases. Do not generalize from one surface form without lexical and grammatical evidence.
---

# Review a Linguistic Rule Change

Convert expert feedback into a testable claim before editing data or parser code. Keep the reviewer’s evidence and comments visible throughout the investigation.

## Build the Evidence Record

1. Read `references/evidence-ladder.md` completely.
2. Inspect the exact upstream commit, inline comment, surrounding rows, and relevant history. Separate what the reviewer asserted from what the patch actually changed.
3. Restate the claim as a rule with explicit positive cases, negative cases, and ambiguity boundaries.
4. Check the repository’s current tagging conventions, DULAT lexeme and forms, homonym, KTU attestation, POS, comments, and parallel reviewed examples.
5. For a changed marker encoding, use `$audit-ugaritic-analysis-reconstruction` to verify the surface invariant. Treat reconstruction as necessary but not as linguistic proof. For N-stem disputes, also use `$parse-ugaritic-n-stems`.

Do not erase the original comment when it contains evidence or migration provenance. Correct factual wording by appending or narrowly editing with justification.

## Measure Corpus Impact

Search reviewed and automatic parsing independently. Report counts by file, lexeme, morphology, and existing encoding rather than one undifferentiated total.

Classify every hit as:

- confirmed positive: the proposed rule applies;
- confirmed negative: a guardrail or exception applies;
- ambiguous: evidence does not select one analysis;
- unrelated surface match.

Inspect automatic parser code and tests separately from reviewed TSVs. Correct reviewed data only when asked; correct automatic parsing at the rule source when the behavior should generalize.

## Choose the Smallest Durable Change

- Use a reviewed-row edit for an isolated adjudicated reading.
- Use configuration for a closed, explicit lexical set.
- Use a parser step for a productive structural rule.
- Use linter logic when an encoding is invalid regardless of parser provenance.
- Update tagging conventions when the accepted convention itself changed.

For parser or linter changes, add at least one positive, one negative, and one ambiguous or boundary test. Place a parser step according to the data it requires and the transformations that must precede or follow it.

## Validate the Rule

1. Run focused unit tests for the changed rule.
2. Regenerate a small representative tablet set with the step-change safeguard enabled.
3. Count intended and unintended changed rows.
4. Run lint-regression comparison and reviewed-agreement scoring where relevant.
5. Re-run the original reviewer example and every discovered positive case.
6. Inspect the scoped diff for lost comments, over-normalized alternatives, and unrelated cleanup.

Report the accepted rule, evidence, affected-row count, exceptions, automatic-parser status, reviewed-data status, and remaining ambiguities. Do not commit unless requested.
