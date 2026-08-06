"""Portable location of the external sources these scripts read.

No script in this skill may contain a machine-specific path. Every source is
resolved in the same order:

  1. an explicit ``--`` argument, where the script offers one;
  2. an environment variable (``CUC_*``, matching ``agent/project_paths.py``);
  3. whatever ``agent/project_paths.py`` resolves, so the repo's own layout and
     env vars keep working unchanged;
  4. a sibling checkout discovered by walking up from the repo root.

Step 4 is what makes a co-located working copy just work without configuration,
on any machine, without naming anyone's home directory. Set the environment
variable when your layout differs:

    CUC_DULAT_DB           structured DULAT (entries, senses, forms, attestations)
    CUC_DULAT_SEARCH_DB    DULAT full-text + dulat_reverse_refs
    CUC_UDB_DB             UDB concordance
    CUC_MODULES_DB         translations, commentaries, EUPT layers
    CUC_TROPPER_OCR        Tropper OCR directory or .ocr.txt
    CUC_BURNS_WORKBOOKS    Burns cultic-vocabulary workbooks

If these external databases become standard for the pipeline rather than for
this skill, promote their resolution into ``agent/project_paths.py``, which is
where the ``CUC_*`` convention lives.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

# Sibling-checkout layouts, relative to an ancestor of the repo root.
SIBLING_CANDIDATES = {
    "dulat_search": ("dulat/app/data/dulat_search.sqlite",),
    "modules": ("dulat/app/data/modules_cache.sqlite",),
    "dulat": ("dulat/app/data/dulat_cache.sqlite",),
    "tropper": ("ugaritic_ocr/artifacts/ocr/tropper-full",),
    "burns": ("context_labeling",),
}

ENV_VARS = {
    "dulat": "CUC_DULAT_DB",
    "dulat_search": "CUC_DULAT_SEARCH_DB",
    "udb": "CUC_UDB_DB",
    "modules": "CUC_MODULES_DB",
    "tropper": "CUC_TROPPER_OCR",
    "burns": "CUC_BURNS_WORKBOOKS",
}


def repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for cand in [start, *start.parents]:
        if (cand / "reviewed").is_dir() and (cand / "agent").is_dir():
            return cand
    raise SystemExit("run this from inside the corpus repository")


ROOT = repo_root()


def _from_project_paths(kind: str):
    """Whatever the repo's own resolver says, if it is importable and knows."""
    agent = ROOT / "agent"
    if not (agent / "project_paths.py").exists():
        return None
    if str(agent) not in sys.path:
        sys.path.insert(0, str(agent))
    try:
        from project_paths import get_project_paths  # noqa: E402
    except Exception:
        return None
    getter = {
        "dulat": "default_dulat_db",
        "udb": "default_udb_db",
        "modules": "default_modules_db",
    }.get(kind)
    if not getter:
        return None
    try:
        p = getattr(get_project_paths(), getter)()
    except Exception:
        return None
    return p if p and Path(p).exists() else None


def _from_siblings(kind: str):
    for rel in SIBLING_CANDIDATES.get(kind, ()):
        for anc in [ROOT, *ROOT.parents]:
            cand = anc / rel
            if cand.exists():
                return cand
    return None


def _has_eupt_layer(path: Path) -> bool:
    """The repo-local modules cache predates the EUPT layer; prefer one that has it."""
    try:
        con = connect_ro(path)
        n = con.execute(
            "select count(*) from module_records where module_id='EUPT_vocalisation'"
            " and data_json is not null and data_json != ''").fetchone()[0]
        con.close()
        return bool(n)
    except Exception:
        return False


# A candidate must satisfy this to be preferred; otherwise the search continues
# and only falls back to it if nothing better exists.
PREFER = {"modules": _has_eupt_layer}


def locate(kind: str, explicit: str | None = None, required: bool = True, quiet: bool = False):
    """Resolve one source. Returns a Path, or None when optional and absent.

    An explicit argument or environment variable is always honoured as given.
    Otherwise candidates are tried in order and the first that satisfies the
    content check for that kind wins, so a stale local cache does not shadow a
    complete sibling copy.
    """
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            raise SystemExit("%s not found: %s" % (kind, p))
        return p
    env = os.environ.get(ENV_VARS.get(kind, ""), "").strip()
    if env:
        p = Path(env).expanduser()
        if not p.exists():
            raise SystemExit("%s=%s does not exist" % (ENV_VARS[kind], env))
        return p

    prefer = PREFER.get(kind)
    fallback = None
    for finder in (_from_project_paths, _from_siblings):
        p = finder(kind)
        if not p:
            continue
        p = Path(p)
        if prefer is None or prefer(p):
            return p
        if fallback is None:
            fallback = p
    if fallback is not None:
        if not quiet:
            sys.stderr.write(
                "NOTE: using %s for '%s'; it failed the content check, so it may be an\n"
                "      older snapshot. Set %s to a complete copy.\n"
                % (fallback, kind, ENV_VARS.get(kind, "the CUC_* variable")))
        return fallback
    if not required:
        return None
    raise SystemExit(
        "Could not locate the %s source.\n"
        "Set %s, or place the checkout beside %s.\n"
        "Looked for: %s"
        % (kind, ENV_VARS.get(kind, "the relevant CUC_* variable"), ROOT,
           ", ".join(SIBLING_CANDIDATES.get(kind, ("(no default)",))))
    )


def connect_ro(path: Path):
    """Read-only connect, falling back where URI mode is unavailable.

    The probe must actually read the database file. `select 1` is answered
    without opening it, so it passes even for a WAL database that `mode=ro`
    cannot read (opening WAL needs write access to the -shm file), leaving a
    connection that fails on the first real query. Several of these sources are
    live application databases in WAL mode.
    """
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
        con.execute("select count(*) from sqlite_master")
        return con
    except sqlite3.Error:
        return sqlite3.connect(str(path))
