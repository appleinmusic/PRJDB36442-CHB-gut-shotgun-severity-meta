#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def _http_get_json(url: str, timeout_s: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _chars_to_flat(characteristics: dict) -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, items in (characteristics or {}).items():
        values: list[str] = []
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict) and "text" in it:
                    values.append(str(it["text"]))
                else:
                    values.append(str(it))
        elif items is not None:
            values.append(str(items))
        flat[key] = "; ".join(values)
    return flat


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch EBI BioSamples JSON and write a flat TSV for audit.")
    ap.add_argument("runs_tsv", type=Path, help="ENA runs TSV (with sample_accession column).")
    ap.add_argument("study_accession", help="Study accession to filter (e.g. PRJDB36442).")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: results/feasibility/<study>_biosamples.tsv).",
    )
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep between requests (seconds).")
    args = ap.parse_args()

    rows = _read_tsv(args.runs_tsv)
    samples: list[str] = []
    for r in rows:
        if r.get("study_accession") != args.study_accession:
            continue
        s = (r.get("sample_accession") or "").strip()
        if s:
            samples.append(s)
    uniq_samples = sorted(set(samples))

    out_path = args.out or Path("results/feasibility") / f"{args.study_accession}_biosamples.tsv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Columns we care about for audit/reproducibility.
    pick_keys = [
        "title",
        "sample_name",
        "host",
        "host status",
        "disease",
        "age",
        "host_sex",
        "collection_date",
        "geo_loc_name",
        "env_medium",
        "env_local_scale",
        "env_broad_scale",
        "ngdc_project_id",
        "ngdc_sample_id",
        "ngdc_release_date",
        "INSDC center name",
        "INSDC first public",
        "INSDC secondary accession",
        "SRA accession",
    ]

    fieldnames = ["sample_accession", "n_characteristics", "has_histology_like", *pick_keys]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        for s in uniq_samples:
            url = f"https://www.ebi.ac.uk/biosamples/samples/{s}"
            for attempt in range(5):
                try:
                    obj = _http_get_json(url)
                    break
                except urllib.error.HTTPError as e:
                    if attempt == 4:
                        raise
                    if e.code in (429, 500, 502, 503, 504):
                        time.sleep(1.0 + attempt)
                        continue
                    raise
                except Exception:
                    if attempt == 4:
                        raise
                    time.sleep(1.0 + attempt)
            chars = obj.get("characteristics") or {}
            flat = _chars_to_flat(chars)
            keys_lower = " ".join(k.lower() for k in flat.keys())
            has_hist = any(k in keys_lower for k in ["fibros", "stage", "grade", "histolog", "scheuer", "ishak", "metavir"])

            out: dict[str, str] = {
                "sample_accession": s,
                "n_characteristics": str(len(chars)),
                "has_histology_like": "1" if has_hist else "0",
            }
            for k in pick_keys:
                out[k] = flat.get(k, "")
            w.writerow(out)
            time.sleep(max(0.0, float(args.sleep)))

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

