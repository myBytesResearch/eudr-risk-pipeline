"""Load published pipeline-run snapshots from ``data/runs/{date}/``.

Snapshots are CSV exports of the upstream myBytes EUDR pipeline runs on
the two publicly documented Côte d'Ivoire / Ghana cocoa sub-regions
referenced in the companion article. Files:

  * ``area_summary.csv`` — one row per AOI
  * ``audit_trail_sample.csv`` — five example pixels with full provenance

The CSVs are the **source of truth** for every quantitative claim in the
companion article. If you cannot reproduce a number from one of these
files, the article must not publish.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_RUN_DATE = "2026-06-08"


def _runs_dir(repo_root: Path | None = None) -> Path:
    here = Path(__file__).resolve()
    root = repo_root if repo_root is not None else here.parents[2]
    return root / "data" / "runs"


def load_area_summary(
    run_date: str = DEFAULT_RUN_DATE,
    *,
    repo_root: Path | None = None,
) -> pd.DataFrame:
    """Load the per-AOI area summary for a given run date.

    Args:
        run_date: ISO date directory name under ``data/runs/`` (e.g.
            ``"2026-06-08"``).
        repo_root: Override the repository root for tests.

    Returns:
        DataFrame with one row per AOI and the columns documented in
        ``data/runs/{run_date}/README.md``.

    Raises:
        FileNotFoundError: if the snapshot for the given run date is
            absent.
    """
    path = _runs_dir(repo_root) / run_date / "area_summary.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"No area_summary snapshot at {path}. "
            f"Known runs: {sorted(p.name for p in _runs_dir(repo_root).glob('*') if p.is_dir())}"
        )
    df = pd.read_csv(path, parse_dates=["run_timestamp"])
    return df


def load_audit_trail_sample(
    run_date: str = DEFAULT_RUN_DATE,
    *,
    aoi_id: str | None = None,
    repo_root: Path | None = None,
) -> pd.DataFrame:
    """Load a sample audit trail with per-pixel provenance.

    Args:
        run_date: ISO date directory name.
        aoi_id: Optional AOI filter (e.g. ``"civ_soubre_33km"``).
        repo_root: Override the repository root for tests.

    Returns:
        DataFrame with one row per audited pixel.
    """
    path = _runs_dir(repo_root) / run_date / "audit_trail_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"No audit_trail snapshot at {path}.")
    df = pd.read_csv(path, parse_dates=["run_timestamp", "radd_alert_date"])
    if aoi_id is not None:
        df = df[df["aoi_id"] == aoi_id].reset_index(drop=True)
    return df
