"""Pure helpers to turn dry-run byte counts into a cost report (no GCP imports)."""

from __future__ import annotations

from dataclasses import dataclass

BYTES_PER_TIB = 1024**4
BYTES_PER_GIB = 1024**3
# On-demand list price per TiB scanned. Check https://cloud.google.com/bigquery/pricing for your region.
DEFAULT_USD_PER_TIB = 6.25
# BigQuery bills at least 10 MiB per table referenced by a query.
MIN_BILLED_BYTES = 10 * 1024**2


@dataclass(frozen=True)
class Comparison:
    query: str
    baseline_bytes: int
    optimized_bytes: int

    @property
    def reduction_pct(self) -> float:
        return reduction_pct(self.baseline_bytes, self.optimized_bytes)


def billed_bytes(processed_bytes: int) -> int:
    if processed_bytes < 0:
        raise ValueError("processed_bytes cannot be negative")
    return 0 if processed_bytes == 0 else max(processed_bytes, MIN_BILLED_BYTES)


def to_gib(n_bytes: int) -> float:
    return n_bytes / BYTES_PER_GIB


def estimated_cost_usd(processed_bytes: int, usd_per_tib: float = DEFAULT_USD_PER_TIB) -> float:
    return billed_bytes(processed_bytes) / BYTES_PER_TIB * usd_per_tib


def reduction_pct(baseline: int, optimized: int) -> float:
    if baseline <= 0:
        return 0.0
    return round((1 - optimized / baseline) * 100, 1)


def render_table(rows: list[Comparison], usd_per_tib: float = DEFAULT_USD_PER_TIB) -> str:
    header = f"{'query':<26}{'baseline_GiB':>14}{'optimized_GiB':>15}{'reduction':>11}{'cost_base_USD':>15}{'cost_opt_USD':>14}"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r.query:<26}{to_gib(r.baseline_bytes):>14.3f}{to_gib(r.optimized_bytes):>15.3f}"
            f"{r.reduction_pct:>10.1f}%{estimated_cost_usd(r.baseline_bytes, usd_per_tib):>15.4f}"
            f"{estimated_cost_usd(r.optimized_bytes, usd_per_tib):>14.4f}"
        )
    return "\n".join(lines)
