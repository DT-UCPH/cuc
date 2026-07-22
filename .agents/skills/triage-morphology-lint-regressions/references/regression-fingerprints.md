# Lint Regression Fingerprints

## Stable Identity

The repository comparator identifies an issue by:

- severity;
- normalized logical file path;
- surface form;
- normalized full diagnostic message.

It deliberately excludes mutable TSV row numbers and token IDs. Inside messages it normalizes references such as `first seen on line ...`, `ids: ...`, and `lines: ...`.

The comparison is a multiset subtraction. If a baseline contains one occurrence and the candidate contains two identical occurrences, one occurrence is new.

## What Remains Significant

- TF/output version in the logical path;
- surface form;
- diagnostic wording and encoded analysis mentioned in it;
- number of occurrences;
- severity.

Do not compare `auto_parsing/0.2.6/FILE` against `auto_parsing/0.2.7/FILE` as if they were the same baseline. Tokenization versions are logically distinct even when tablet names match.

## Correct Baselines

- staged file: `HEAD:path` versus the staged blob;
- unstaged file: `HEAD:path` versus working tree;
- regeneration experiment: saved pre-run output versus regenerated output at the same version path;
- new file: empty baseline, making every ERROR new;
- migration preview: original target-version reviewed state if it exists, otherwise document that no equivalent baseline exists.

## Failure Classes

### Environmental

Missing interpreter, database, source file, or override table; import failure; linter crash. These invalidate the comparison.

### Data regression

The candidate row violates an established encoding, schema, lexical, or reconstruction rule.

### Parser regression

Regeneration introduces the invalid row consistently from a pipeline step or configuration change.

### Linter regression

A linter change newly flags valid established data or changes issue identity accidentally. Verify with focused positive and negative tests before weakening the check.

### Tokenization-dependent change

The TF split/join changes the correct unit of reconstruction or comparison. Use merged-token validation or version-specific expectations rather than matching IDs.

