# CUC-Origin — Agent Instructions

## Never hand-edit generated data — fix the generator instead

Auto-parsing output (`auto_parsing/**`) and every other intermediate or
generated artifact is produced by the pipeline. It may change **only** by
regenerating it. Do **not** apply "surgical" manual edits — row deletions,
substitutions, patches, or find-and-replace — to generated data, not even to
make it match a result you know is correct.

If generated output is wrong, the **generator** is wrong. Debug and fix the
parser/pipeline (and add a test), then regenerate. Surgery hides the defect
instead of fixing it and silently diverges the committed data from what the
pipeline actually produces, so the next regeneration undoes or contradicts the
edit.

If regeneration is blocked — non-determinism, drift versus the committed
baseline, a tripped step-change safeguard — **that blocker is the bug**. Stop
and fix it; do not route around it by editing the output.

Reviewed data (`reviewed/**`) is the opposite case: it is curated by hand and
is never overwritten by regeneration.
