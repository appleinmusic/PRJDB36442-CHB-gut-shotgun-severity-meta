#!/usr/bin/env python3
"""
Scan ENA Portal API for HBV-related gut microbiome studies and classify which
look like shotgun metagenomics (vs amplicon).

Outputs:
  - results/feasibility/ena_hbv_gut_studies.tsv
  - results/feasibility/ena_hbv_gut_runs.tsv
"""

from __future__ import annotations

import csv
import datetime as dt
import time
import sys
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path


RESULTS_DIR = Path("results/feasibility")
STUDIES_OUT = RESULTS_DIR / "ena_hbv_gut_studies.tsv"
RUNS_OUT = RESULTS_DIR / "ena_hbv_gut_runs.tsv"


def _urlopen_text(url: str, timeout: int = 60, max_attempts: int = 5) -> list[str]:
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "codex-meta/ena-scan (research feasibility)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            return data.decode("utf-8", errors="replace").splitlines()
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            if attempt == max_attempts:
                break
            time.sleep(min(2**attempt, 20))
    raise urllib.error.URLError(last_err) if last_err else urllib.error.URLError("unknown error")


def _ena_search(
    *,
    result: str,
    query: str,
    fields: list[str],
    limit: int,
) -> list[dict[str, str]]:
    params = {
        "result": result,
        "query": query,
        "fields": ",".join(fields),
        "format": "tsv",
        "limit": str(limit),
    }
    url = "https://www.ebi.ac.uk/ena/portal/api/search?" + urllib.parse.urlencode(params)
    lines = _urlopen_text(url)
    if len(lines) <= 1:
        return []
    reader = csv.DictReader(lines, delimiter="\t")
    return list(reader)


@dataclass(frozen=True)
class Study:
    study_accession: str
    study_title: str
    center_name: str
    first_public: str


def _study_queries() -> list[str]:
    # Query grammar: field predicates. Wildcards use *...* inside quoted string.
    return [
        'study_title="*HBV*" AND study_title="*gut*"',
        'study_title="*HBV*" AND study_title="*microbiot*"',
        'study_title="*HBV*" AND study_title="*microbiome*"',
        'study_title="*hepatitis B*" AND study_title="*gut*"',
        'study_title="*hepatitis B*" AND study_title="*microbiot*"',
        # Fibrosis/cirrhosis variants (may miss if title uses abbreviations)
        'study_title="*HBV*" AND study_title="*fibrosis*" AND study_title="*gut*"',
        'study_title="*HBV*" AND study_title="*cirrhosis*" AND study_title="*gut*"',
        # From earlier observations: “metagenome-based characterization … chronic hepatitis B …”
        'study_title="*chronic hepatitis B*" AND study_title="*metagenome*"',
    ]


def _load_studies(limit_per_query: int = 200) -> dict[str, Study]:
    studies: dict[str, Study] = {}
    for q in _study_queries():
        rows = _ena_search(
            result="study",
            query=q,
            fields=["study_accession", "study_title", "center_name", "first_public"],
            limit=limit_per_query,
        )
        for r in rows:
            acc = (r.get("study_accession") or "").strip()
            if not acc:
                continue
            studies.setdefault(
                acc,
                Study(
                    study_accession=acc,
                    study_title=(r.get("study_title") or "").strip(),
                    center_name=(r.get("center_name") or "").strip(),
                    first_public=(r.get("first_public") or "").strip(),
                ),
            )
    return studies


def _fetch_runs(study_accession: str, limit: int = 100000) -> list[dict[str, str]]:
    return _ena_search(
        result="read_run",
        query=f"study_accession={study_accession}",
        fields=[
            "study_accession",
            "study_title",
            "run_accession",
            "sample_accession",
            "sample_title",
            "library_strategy",
            "library_source",
            "library_selection",
            "instrument_platform",
            "instrument_model",
            "read_count",
            "base_count",
            "fastq_ftp",
            "fastq_bytes",
            "fastq_md5",
            "first_public",
        ],
        limit=limit,
    )


def _is_shotgun_candidate(run_rows: list[dict[str, str]]) -> bool:
    """
    Heuristic:
      - accept metagenomic source + RANDOM selection
      - exclude AMPLICON strategy (likely 16S)
    """
    for r in run_rows:
        src = (r.get("library_source") or "").upper()
        sel = (r.get("library_selection") or "").upper()
        strat = (r.get("library_strategy") or "").upper()
        if src == "METAGENOMIC" and sel == "RANDOM" and strat != "AMPLICON":
            return True
    return False


def _write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def main() -> int:
    studies = _load_studies()
    if not studies:
        print("No studies found. Check ENA availability / query grammar.", file=sys.stderr)
        return 2

    today = dt.date.today().isoformat()
    study_rows: list[dict[str, str]] = []
    run_rows_all: list[dict[str, str]] = []

    for acc, st in sorted(studies.items(), key=lambda kv: kv[0]):
        runs: list[dict[str, str]] = []
        fetch_error: str = ""
        try:
            runs = _fetch_runs(acc)
        except Exception as exc:  # network/ENA instability
            fetch_error = f"{type(exc).__name__}: {exc}"
        shotgun = _is_shotgun_candidate(runs) if runs else False

        # Summarize strategy combos
        combos = {}
        for r in runs:
            key = (
                (r.get("library_strategy") or "").strip(),
                (r.get("library_source") or "").strip(),
                (r.get("library_selection") or "").strip(),
                (r.get("instrument_platform") or "").strip(),
            )
            combos[key] = combos.get(key, 0) + 1
        combos_str = "; ".join(
            f"{n}×{ls}/{src}/{sel}/{plat}"
            for (ls, src, sel, plat), n in sorted(combos.items(), key=lambda kv: (-kv[1], kv[0]))
        )

        study_rows.append(
            {
                "study_accession": st.study_accession,
                "study_title": st.study_title,
                "center_name": st.center_name,
                "first_public": st.first_public,
                "n_runs": str(len(runs)),
                "shotgun_candidate": "yes" if shotgun else "no",
                "strategy_summary": combos_str,
                "fetch_error": fetch_error,
                "checked_date": today,
            }
        )

        for r in runs:
            r2 = dict(r)
            r2["checked_date"] = today
            run_rows_all.append(r2)

    _write_tsv(
        STUDIES_OUT,
        study_rows,
        [
            "study_accession",
            "study_title",
            "center_name",
            "first_public",
            "n_runs",
            "shotgun_candidate",
            "strategy_summary",
            "fetch_error",
            "checked_date",
        ],
    )
    _write_tsv(
        RUNS_OUT,
        run_rows_all,
        [
            "study_accession",
            "study_title",
            "run_accession",
            "sample_accession",
            "sample_title",
            "library_strategy",
            "library_source",
            "library_selection",
            "instrument_platform",
            "instrument_model",
            "read_count",
            "base_count",
            "fastq_ftp",
            "fastq_bytes",
            "fastq_md5",
            "first_public",
            "checked_date",
        ],
    )

    print(f"Wrote {STUDIES_OUT}")
    print(f"Wrote {RUNS_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
