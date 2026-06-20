"""Executive plot library for myBytes Research publications.

Standardised, self-explanatory plots that satisfy the Executive
Accessibility Hard Rule: a non-technical decision-maker must understand
the plot in under 15 seconds without surrounding text.

Every plot returns a (Figure, Axes) tuple so the caller can
post-process if needed. Saving and showing are the caller's
responsibility.

Design rules baked in:
* Title is an *assertion*, not a variable label.
* Axes have units in the label.
* Caption is mandatory and rendered as italic footer text.
* Source attribution is mandatory and rendered as small grey footer.
* Colour semantics are constant across the library
  (red = crisis/fail, green = pass/safe, blue = model/forecast,
  grey = baseline/historical).
* No LaTeX in titles or captions.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Iterable, Sequence

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Brand palette — kept deliberately small and meaningful.
# ---------------------------------------------------------------------------

COLOR_CRISIS = "#C0392B"
COLOR_PASS = "#27AE60"
COLOR_MODEL = "#1F77B4"
COLOR_BASELINE = "#7F8C8D"
COLOR_NEUTRAL = "#34495E"
COLOR_HIGHLIGHT = "#E67E22"

STATUS_PALETTE = [COLOR_CRISIS, COLOR_HIGHLIGHT, COLOR_PASS]  # 0=fail, 1=partial, 2=pass

DEFAULT_FOOTER_FONTSIZE = 8
DEFAULT_CAPTION_FONTSIZE = 9
DEFAULT_TITLE_FONTSIZE = 12

# ---------------------------------------------------------------------------
# Footer helper — every executive plot needs the same anatomy.
# ---------------------------------------------------------------------------


_SOURCE_PREFIX = "Quelle: "


def set_source_prefix(prefix: str) -> None:
    """Override the footer source-line prefix for localized renders (EN/PL).

    Module-level switch so every ``executive_*`` renderer picks up the locale
    without threading a parameter through each signature. Reset to the German
    default ``"Quelle: "`` after a localized batch.
    """
    global _SOURCE_PREFIX
    _SOURCE_PREFIX = prefix


def _attach_footer(fig: plt.Figure, caption: str, source: str) -> None:
    """Place the 15-second-message caption and the source attribution.

    Caption and source are stacked on two separate horizontal lines to
    avoid overlap. The caption is the primary 15-second message; the
    source is a smaller, secondary attribution. Both are left-aligned.
    """
    if caption:
        fig.text(
            0.02,
            0.045,
            caption,
            fontsize=DEFAULT_CAPTION_FONTSIZE,
            style="italic",
            color=COLOR_NEUTRAL,
        )
    if source:
        fig.text(
            0.02,
            0.012,
            f"{_SOURCE_PREFIX}{source}",
            fontsize=DEFAULT_FOOTER_FONTSIZE,
            color=COLOR_BASELINE,
        )


def _set_executive_title(ax: plt.Axes, title: str) -> None:
    """Title is left-aligned and bold by convention."""
    ax.set_title(title, loc="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")


# ---------------------------------------------------------------------------
# Plot 1 — Truth-check Funnel
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FunnelStep:
    """A single filter step in the truth-check funnel.

    Attributes:
        label: Short label shown inside the bar.
        retain_pct: Retention rate at this step, 0–1.
    """

    label: str
    retain_pct: float


def executive_truth_funnel(
    steps: Sequence[FunnelStep],
    *,
    title: str = "Sieben Filter zwischen einer KI-Behauptung und ihrer Veröffentlichung",
    caption: str = (
        "Die meisten Claims überleben den Prozess nicht. Genau deshalb steht er hier."
    ),
    header_annotation: str | None = None,
    source: str = "myBytes Research, Schema in Anlehnung an Gelman & Loken 2014",
    figsize: tuple[float, float] = (9.5, 5.6),
) -> tuple[plt.Figure, plt.Axes]:
    """Render a top-of-article truth-check funnel.

    A vertical funnel where each step's bar width is proportional to the
    cumulative retention. The final step is highlighted in green to mark
    the publishable residue.
    """
    fig, ax = plt.subplots(figsize=figsize)
    n = len(steps)
    y = np.arange(n)
    widths = np.array([s.retain_pct for s in steps])

    centers = 0.5 - widths / 2
    colors = [COLOR_BASELINE] * (n - 1) + [COLOR_PASS]
    bars = ax.barh(y, widths, left=centers, color=colors, edgecolor="white", linewidth=2)

    # Label-on-Element Hard Rule: every label stays INSIDE its bar. When a
    # bar is too narrow for the default rendering, we degrade in this fixed
    # priority order: (1) wrap to two lines at same font; (2) shrink font;
    # (3) wrap + shrink. We never push the label outside the bar.
    #
    # Empirical calibration at fig width = 9.5 inch:
    #   ~100 characters of bold fontsize-10 text fit into width=1.0
    #   → chars-per-width-unit ≈ 100
    fig_width_in = fig.get_size_inches()[0]
    CHARS_PER_WIDTH_UNIT = 100 * (fig_width_in / 9.5)

    def _fit_label(text: str, bar_width: float) -> tuple[str, int]:
        """Return (rendered_text, fontsize) so the label fits inside the bar."""
        # Safety margin so text never touches the bar edge.
        usable = max(0.04, bar_width - 0.02)
        for fontsize in (10, 9, 8, 7):
            chars_per_line = max(8, int(usable * CHARS_PER_WIDTH_UNIT * (10 / fontsize)))
            if len(text) <= chars_per_line:
                return text, fontsize
            wrapped = textwrap.wrap(text, width=chars_per_line)
            if wrapped and max(len(line) for line in wrapped) <= chars_per_line:
                return "\n".join(wrapped), fontsize
        # Last resort — keep label on bar with smallest font and wrap aggressively.
        chars_per_line = max(8, int(usable * CHARS_PER_WIDTH_UNIT))
        return "\n".join(textwrap.wrap(text, width=chars_per_line)), 7

    # Bars get a minimum height so wrapped two-line labels still fit
    # vertically inside the bar.
    bar_height = bars[0].get_height()
    needs_taller_bars = any(
        len(_fit_label(f"{s.label}  ({s.retain_pct * 100:.0f} %)", s.retain_pct)[0].split("\n")) >= 2
        for s in steps
    )
    if needs_taller_bars:
        # Increase row spacing by stretching the y-axis.
        ax.set_ylim(n - 0.3, -0.7)

    for bar, step in zip(bars, steps):
        label_text = f"{step.label}  ({step.retain_pct * 100:.0f} %)"
        y_centre = bar.get_y() + bar.get_height() / 2
        rendered, fontsize = _fit_label(label_text, step.retain_pct)
        ax.text(
            0.5,
            y_centre,
            rendered,
            ha="center",
            va="center",
            fontsize=fontsize,
            color="white",
            fontweight="bold",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(n - 0.5, -0.5)  # invert so step 1 is at the top
    ax.set_yticks([])
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Title via fig.suptitle so we control vertical placement precisely and
    # can stack a subtitle annotation below it without colliding with the axes.
    fig.suptitle(title, x=0.02, y=0.965, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    if header_annotation:
        fig.text(
            0.02,
            0.915,
            header_annotation,
            fontsize=9,
            color=COLOR_NEUTRAL,
            style="italic",
        )

    # Generous top margin so the title + annotation strip is clear of the bars.
    fig.subplots_adjust(top=0.86 if not header_annotation else 0.82, bottom=0.18)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 2 — Tier pyramid of evidence anchors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TierRow:
    """A row of the tier pyramid.

    Attributes:
        tier: Tier identifier, e.g. "Tier 1".
        description: One-line description of what counts as this tier.
        examples: Example sources.
    """

    tier: str
    description: str
    examples: str


def executive_tier_pyramid(
    tiers: Sequence[TierRow],
    *,
    title: str = "Welche Quelle reicht für welche Behauptung. Eine Hierarchie",
    caption: str = (
        "Tier 3 reicht nie alleinstehend. Tier 4 reicht nur mit öffentlichem "
        "Code, Seed und Daten-Version."
    ),
    source: str = "myBytes Research, basierend auf ASA Statement 2016 und Ioannidis 2005",
    figsize: tuple[float, float] = (10, 6),
) -> tuple[plt.Figure, plt.Axes]:
    """Render the tier pyramid of evidence anchors.

    The narrowest band at the top is the most authoritative tier.
    """
    fig, ax = plt.subplots(figsize=figsize)
    n = len(tiers)
    band_height = 1.0 / n
    palette = [COLOR_PASS, COLOR_MODEL, COLOR_HIGHLIGHT, COLOR_BASELINE]

    # Minimum band width for the top tier so labels always fit.
    # Linear interpolation from MIN at the top to 1.0 at the base.
    MIN_TOP_WIDTH = 0.62

    # Approximate characters per band-width-unit at fontsize 9.5 in a 10-inch
    # figure. Calibrated empirically; conservative.
    CHARS_PER_UNIT_WIDTH = 80

    for i, tier in enumerate(tiers):
        y_bottom = 1.0 - (i + 1) * band_height
        width_factor = MIN_TOP_WIDTH + (1.0 - MIN_TOP_WIDTH) * (i / max(1, n - 1))
        x_left = (1 - width_factor) / 2

        rect = mpatches.Rectangle(
            (x_left, y_bottom),
            width_factor,
            band_height * 0.94,
            facecolor=palette[i % len(palette)],
            edgecolor="white",
            linewidth=2,
            alpha=0.92,
        )
        ax.add_patch(rect)

        # Wrap each line of the band label to fit the band's effective width.
        max_chars = max(20, int(width_factor * CHARS_PER_UNIT_WIDTH))
        line1 = f"{tier.tier}: {tier.description}"
        line2 = tier.examples
        wrapped_lines = textwrap.wrap(line1, width=max_chars) + textwrap.wrap(line2, width=max_chars)
        wrapped = "\n".join(wrapped_lines)

        ax.text(
            0.5,
            y_bottom + band_height * 0.5,
            wrapped,
            ha="center",
            va="center",
            fontsize=9.5,
            color="white",
            fontweight="bold",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Use fig.suptitle for consistent placement and to avoid axes-bbox crowding.
    fig.suptitle(title, x=0.02, y=0.96, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.90, bottom=0.16)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 3 — Claim-map heatmap
# ---------------------------------------------------------------------------


def executive_claim_heatmap(
    matrix: pd.DataFrame,
    *,
    claim_texts: Iterable[str] | None = None,
    title: str = "Wie dieser Artikel auf seine eigenen Behauptungen geprüft wurde",
    caption: str = "Das Protokoll wird angewendet, nicht behauptet.",
    source: str = "myBytes Research, eigene Anwendung des Truth-Check-Protokolls",
    figsize: tuple[float, float] = (11, None),  # type: ignore[arg-type]
) -> tuple[plt.Figure, plt.Axes]:
    """Render the per-claim status heatmap used as Plot 3 of the protocol article.

    Args:
        matrix: DataFrame indexed by claim_id, with one column per protocol
            check. Values must be in {0, 1, 2, NaN} encoding fail/partial/pass.
        claim_texts: Optional list of human-readable claim texts; if provided,
            they are shown in a side annotation column.
    """
    n_rows = len(matrix)
    height = figsize[1] if figsize[1] else max(3.5, 0.55 * n_rows + 1.5)
    fig, ax = plt.subplots(figsize=(figsize[0], height))

    data = matrix.values.astype(float)
    n_cols = data.shape[1]

    # Draw cells manually so NaN cells are clearly distinct.
    for i in range(n_rows):
        for j in range(n_cols):
            val = data[i, j]
            if np.isnan(val):
                color = "#ECEFF1"
                txt = "n/a"
                tcol = COLOR_BASELINE
            else:
                color = STATUS_PALETTE[int(round(val))]
                txt = {0: "fail", 1: "partial", 2: "pass"}[int(round(val))]
                tcol = "white"
            rect = mpatches.Rectangle((j, i), 1, 1, facecolor=color, edgecolor="white", linewidth=2)
            ax.add_patch(rect)
            ax.text(j + 0.5, i + 0.5, txt, ha="center", va="center", fontsize=9, color=tcol, fontweight="bold")

    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_xticklabels(matrix.columns, fontsize=10)
    ax.set_yticks(np.arange(n_rows) + 0.5)

    if claim_texts is not None:
        labels = [f"#{cid} · {ct[:70]}{'…' if len(ct) > 70 else ''}" for cid, ct in zip(matrix.index, claim_texts)]
    else:
        labels = [f"Claim #{cid}" for cid in matrix.index]
    ax.set_yticklabels(labels, fontsize=9)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", which="both", length=0)

    _set_executive_title(ax, title)

    # Legend strip
    legend_handles = [
        mpatches.Patch(color=COLOR_PASS, label="pass"),
        mpatches.Patch(color=COLOR_HIGHLIGHT, label="partial / pending"),
        mpatches.Patch(color=COLOR_CRISIS, label="fail / absent"),
        mpatches.Patch(color="#ECEFF1", label="n/a"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=4,
        frameon=False,
        fontsize=9,
    )

    fig.subplots_adjust(top=0.90, bottom=0.20)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 4 — Executive forecast chart (for future commodity-intelligence articles)
# ---------------------------------------------------------------------------


def executive_forecast_chart(
    timestamps: pd.DatetimeIndex,
    actual: np.ndarray,
    forecast: np.ndarray,
    lower_band: np.ndarray | None = None,
    upper_band: np.ndarray | None = None,
    *,
    title: str,
    caption: str,
    source: str,
    annotations: dict[pd.Timestamp, str] | None = None,
    ylabel: str = "Wert",
    figsize: tuple[float, float] = (10.5, 5.2),
) -> tuple[plt.Figure, plt.Axes]:
    """Render a self-explanatory forecast chart with optional uncertainty band.

    Annotations dictionary maps timestamp → free-text label that will be
    rendered as a vertical line + caption (e.g. crisis events).
    """
    fig, ax = plt.subplots(figsize=figsize)

    if lower_band is not None and upper_band is not None:
        ax.fill_between(timestamps, lower_band, upper_band, color=COLOR_MODEL, alpha=0.18, label="Modell-Konfidenzband")
    ax.plot(timestamps, actual, color=COLOR_BASELINE, lw=1.6, label="Realisiert")
    ax.plot(timestamps, forecast, color=COLOR_MODEL, lw=2.0, label="Modell-Vorhersage")

    if annotations:
        for ts, txt in annotations.items():
            ax.axvline(ts, color=COLOR_CRISIS, lw=1.0, ls="--", alpha=0.75)
            ax.text(
                ts,
                ax.get_ylim()[1] * 0.97,
                f" {txt}",
                color=COLOR_CRISIS,
                fontsize=9,
                rotation=90,
                ha="left",
                va="top",
            )

    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    _set_executive_title(ax, title)
    fig.subplots_adjust(top=0.88, bottom=0.18)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 5 — Executive risk heatmap (for EUDR + Compliance articles)
# ---------------------------------------------------------------------------


def executive_risk_heatmap(
    matrix: pd.DataFrame,
    *,
    title: str,
    caption: str,
    source: str,
    cbar_label: str = "Risiko-Anteil (%)",
    figsize: tuple[float, float] = (10, 5.6),
) -> tuple[plt.Figure, plt.Axes]:
    """Render a region × period risk heatmap with diverging red scale.

    Args:
        matrix: DataFrame with regions as rows, periods as columns,
            values are percentages 0–100.
    """
    fig, ax = plt.subplots(figsize=figsize)
    vmax = float(np.nanmax(matrix.values))
    im = ax.imshow(matrix.values, cmap="OrRd", vmin=0, vmax=vmax, aspect="auto")

    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_xticklabels(matrix.columns, fontsize=9, rotation=45, ha="right")
    ax.set_yticklabels(matrix.index, fontsize=9)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix.values[i, j]
            if np.isnan(val):
                continue
            ax.text(
                j,
                i,
                f"{val:.1f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if val > vmax * 0.55 else COLOR_NEUTRAL,
            )

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(cbar_label, fontsize=9)

    _set_executive_title(ax, title)
    fig.subplots_adjust(top=0.86, bottom=0.20)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Convenience constructors for the truth-check article's three plots
# ---------------------------------------------------------------------------


def build_default_funnel() -> list[FunnelStep]:
    """Default seven-step funnel as used in the X2-01 article."""
    return [
        FunnelStep("1 · Claim Extraction", 1.00),
        FunnelStep("2 · Classification", 0.92),
        FunnelStep("3 · Anchor Mapping", 0.74),
        FunnelStep("4 · Reproducibility", 0.58),
        FunnelStep("5 · Steel-Man", 0.42),
        FunnelStep("6 · Limitations", 0.28),
        FunnelStep("7 · Independent Review", 0.18),
    ]


def build_default_tiers() -> list[TierRow]:
    """Default four-tier pyramid as used in the X2-01 article."""
    return [
        TierRow(
            "Tier 1",
            "peer-reviewed scientific literature",
            "JoF, Econometrica, Nature, Science, RSE",
        ),
        TierRow(
            "Tier 2",
            "institutional, authoritative",
            "IMF, FAO, ICCO, USDA, EU-Kommission, ESA, MIT NANDA, Gartner",
        ),
        TierRow(
            "Tier 3",
            "industry-respected, nie alleinstehend",
            "Mintec, Reuters, FT, Bloomberg, Risk.net",
        ),
        TierRow(
            "Tier 4",
            "eigene Forschung mit voller Reproduzierbarkeit",
            "öffentliches Repo · fixer Seed · dokumentierte Daten-Version",
        ),
    ]


# ---------------------------------------------------------------------------
# Plot 6 — Two-mask schema (EUDR AND operation)
# ---------------------------------------------------------------------------


def executive_two_mask_schema(
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    *,
    title: str = "Was eine EUDR-konforme Risk-Definition pro Pixel tatsächlich tut",
    caption: str = (
        "Eine zwei-Masken-AND-Operation. Mehr und weniger gleichzeitig — die meisten "
        "Vendoren liefern nur Maske A."
    ),
    source: str = (
        "Schema. Datengrundlagen: Hansen GFC v2025 (UMD), FDP Cocoa Probability 2025a, "
        "Kalischek et al. 2023"
    ),
    figsize: tuple[float, float] = (13, 5.2),
) -> tuple[plt.Figure, np.ndarray]:
    """Render the three-panel schema for the EUDR two-mask AND operation.

    The three panels show, left to right:
      1. Mask A (Hansen lossyear >= 21) as red-on-grey pixels.
      2. Mask B (Plantation probability >= tau) as blue-shaded probability.
      3. AND result as red-on-grey, but only pixels where both A and B fire.

    Args:
        mask_a: Boolean array — Hansen loss mask sample. 2D.
        mask_b: Float array of plantation probability in [0,1]. Same shape.

    Returns:
        (Figure, Axes-array) — the three panels.
    """
    if mask_a.shape != mask_b.shape:
        raise ValueError("mask_a and mask_b must have the same shape")

    # Bigger default size for mobile/social-media legibility (Hard Rule 3).
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    risk = mask_a.astype(bool) & (mask_b >= 0.5)

    PANEL_TITLE_FONTSIZE = 12
    SUB_CAPTION_FONTSIZE = 11

    # Panel 1 — Mask A
    panel_a_rgb = np.zeros((*mask_a.shape, 3))
    panel_a_rgb[..., 0] = 0.92
    panel_a_rgb[..., 1] = 0.95
    panel_a_rgb[..., 2] = 0.92  # base: pale forest green for "untouched"
    panel_a_rgb[mask_a > 0] = [0.75, 0.27, 0.17]  # COLOR_CRISIS-ish for "lost"
    axes[0].imshow(panel_a_rgb, interpolation="nearest")
    axes[0].set_title("Maske A · Hansen lossyear ≥ 2021", fontsize=PANEL_TITLE_FONTSIZE, fontweight="bold")
    axes[0].text(
        0.5, -0.14,
        '"war Wald, ist weg"',
        transform=axes[0].transAxes, ha="center", va="top",
        fontsize=SUB_CAPTION_FONTSIZE, style="italic", color=COLOR_NEUTRAL,
    )

    # Panel 2 — Mask B (probability heatmap)
    im = axes[1].imshow(mask_b, cmap="Blues", vmin=0, vmax=1, interpolation="nearest")
    axes[1].set_title("Maske B · Plantation-Probability ≥ τ", fontsize=PANEL_TITLE_FONTSIZE, fontweight="bold")
    axes[1].text(
        0.5, -0.14,
        '"ist heute Plantage"',
        transform=axes[1].transAxes, ha="center", va="top",
        fontsize=SUB_CAPTION_FONTSIZE, style="italic", color=COLOR_NEUTRAL,
    )

    # Panel 3 — AND result
    panel_c_rgb = np.zeros((*risk.shape, 3))
    panel_c_rgb[..., 0] = 0.96
    panel_c_rgb[..., 1] = 0.96
    panel_c_rgb[..., 2] = 0.96  # background: light grey
    panel_c_rgb[risk] = [0.75, 0.15, 0.15]  # pure crisis red for the AND
    axes[2].imshow(panel_c_rgb, interpolation="nearest")
    axes[2].set_title("A ∧ B · EUDR-Risk-Pixel", fontsize=PANEL_TITLE_FONTSIZE, fontweight="bold")
    axes[2].text(
        0.5, -0.14,
        '"war Wald, ist weg, ist heute Plantage"',
        transform=axes[2].transAxes, ha="center", va="top",
        fontsize=SUB_CAPTION_FONTSIZE, style="italic", color=COLOR_NEUTRAL,
    )

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    # AND-operator labels between panels
    fig.text(0.345, 0.52, "∧", fontsize=24, ha="center", va="center", color=COLOR_NEUTRAL, fontweight="bold")
    fig.text(0.668, 0.52, "=", fontsize=24, ha="center", va="center", color=COLOR_NEUTRAL, fontweight="bold")

    fig.suptitle(title, x=0.02, y=0.97, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.83, bottom=0.20, wspace=0.18)
    _attach_footer(fig, caption, source)
    return fig, axes


# ---------------------------------------------------------------------------
# Plot 7 — Region comparison bars (EUDR risk share per AOI)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegionRiskRow:
    """One row for the region-comparison-bars plot.

    Attributes:
        region_name: Display name of the region (e.g. ``"Soubré, CIV"``).
        plantation_ha: Total plantation area in hectares.
        risk_ha: EUDR-risk area in hectares.
        topology: Short topology annotation (e.g. ``"Smallholder-Mosaik"``).
    """

    region_name: str
    plantation_ha: float
    risk_ha: float
    topology: str

    @property
    def risk_share_pct(self) -> float:
        return (self.risk_ha / self.plantation_ha * 100.0) if self.plantation_ha > 0 else 0.0


def executive_region_comparison_bars(
    rows: Sequence[RegionRiskRow],
    *,
    title: str = "Welcher Anteil der heutigen Plantage gilt nach EUDR-Definition als Risiko-Fläche",
    caption: str = (
        "Sefwi-Wiawso hat fast dreimal so viel EUDR-Risiko-Fläche pro Plantagen-Hektar wie Soubré, "
        "sichtbar pro Pixel, nicht pro Marketing-Claim."
    ),
    source: str = "myBytes Pipeline-Lauf 2026-05-30 auf GFC v2025 × FDP 2025a",
    legend_labels: tuple[str, str] = (
        "EUDR-konform (Plantage ohne Loss-Cut-off-Hit)",
        "EUDR-Risiko-Fläche (A ∧ B)",
    ),
    x_axis_label: str = "Plantagen-Fläche · Hektar",
    of_word: str = "von",
    figsize: tuple[float, float] = (11, None),  # type: ignore[arg-type]
) -> tuple[plt.Figure, plt.Axes]:
    """Render horizontal stacked bars: one per region, plantation vs. risk."""
    n = len(rows)
    height = figsize[1] if figsize[1] else max(2.8, 1.05 * n + 1.6)
    fig, ax = plt.subplots(figsize=(figsize[0], height))

    y = np.arange(n)
    plantation_only = np.array([r.plantation_ha - r.risk_ha for r in rows])
    risk = np.array([r.risk_ha for r in rows])

    bar_height = 0.55
    ax.barh(y, plantation_only, height=bar_height, color=COLOR_PASS, label=legend_labels[0], alpha=0.85)
    ax.barh(y, risk, height=bar_height, left=plantation_only, color=COLOR_CRISIS, label=legend_labels[1])

    # Per-row annotations
    for i, r in enumerate(rows):
        total = r.plantation_ha
        ax.text(
            total + total * 0.015,
            i,
            f"{r.risk_share_pct:.1f} %  ·  {r.risk_ha:,.0f} ha {of_word} {r.plantation_ha:,.0f} ha",
            va="center", fontsize=9.5, color=COLOR_NEUTRAL, fontweight="bold",
        )
        ax.text(
            -total * 0.02,
            i - 0.32,
            r.topology,
            va="center", ha="right", fontsize=8.5, color=COLOR_BASELINE, style="italic",
        )

    ax.set_yticks(y)
    ax.set_yticklabels([r.region_name for r in rows], fontsize=10, fontweight="bold")
    ax.set_xlabel(x_axis_label)
    ax.set_xlim(0, max(r.plantation_ha for r in rows) * 1.32)
    ax.set_ylim(n - 0.5, -0.7)
    ax.tick_params(axis="y", length=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=9.5,
    )

    fig.suptitle(title, x=0.02, y=0.965, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.86, bottom=0.30, left=0.18)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 8 — Audit-trail table render
# ---------------------------------------------------------------------------


def executive_audit_trail_table(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    column_widths: Sequence[float] | None = None,
    title: str = "Was ein Auditor pro Risiko-Pixel rekonstruieren können muss",
    caption: str = (
        "Jede Zeile rückverfolgbar auf einen öffentlichen Quell-Datensatz. "
        "Das ist der Unterschied zur schönen Karte."
    ),
    source: str = "eigene Pipeline-Ausgabe; Quell-Daten: UMD GFC, ETH Kalischek-Map, Wageningen RADD",
    figsize: tuple[float, float] = (15, None),  # type: ignore[arg-type]
) -> tuple[plt.Figure, plt.Axes]:
    """Render an audit-trail DataFrame as a clean executive-style table figure.

    Args:
        df: DataFrame with one row per audit pixel.
        columns: Optional explicit column order; default uses df.columns.
    """
    if columns is None:
        columns = list(df.columns)
    sub = df[columns].copy()

    n_rows, n_cols = sub.shape
    height = figsize[1] if figsize[1] else max(2.2, 0.42 * n_rows + 1.4)
    fig, ax = plt.subplots(figsize=(figsize[0], height))
    ax.set_axis_off()

    # Build cell text with type-aware formatting.
    def _fmt(value: object) -> str:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return "-"
        if isinstance(value, float):
            return f"{value:.4f}" if abs(value) < 1 else f"{value:.3f}"
        return str(value)

    cell_text = [[_fmt(v) for v in row] for row in sub.itertuples(index=False, name=None)]

    table_kwargs = dict(
        cellText=cell_text,
        colLabels=list(columns),
        loc="upper center",
        cellLoc="left",
        colLoc="left",
    )
    if column_widths is not None:
        if len(column_widths) != n_cols:
            raise ValueError(
                f"column_widths length {len(column_widths)} must equal number of "
                f"columns {n_cols}"
            )
        table_kwargs["colWidths"] = list(column_widths)
    table = ax.table(**table_kwargs)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.55)

    # Style header row
    for j, _ in enumerate(columns):
        cell = table[(0, j)]
        cell.set_facecolor(COLOR_NEUTRAL)
        cell.set_text_props(color="white", fontweight="bold")
        cell.set_edgecolor("white")
    # Style body rows — zebra stripes for executive readability
    for i in range(1, n_rows + 1):
        for j in range(n_cols):
            cell = table[(i, j)]
            cell.set_facecolor("#F5F7FA" if i % 2 == 0 else "white")
            cell.set_edgecolor("#E5E9EE")

    fig.suptitle(title, x=0.02, y=0.96, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.88, bottom=0.02, left=0.02, right=0.98)

    # Caption and source are anchored to the table's measured bottom edge,
    # not to the figure bottom: a figure-bottom anchor leaves a whitespace
    # band between table end and footer that bbox_inches='tight' cannot
    # crop (visual-QA finding 2026-06-12).
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    table_bottom = (
        table.get_window_extent(renderer).transformed(fig.transFigure.inverted()).y0
    )
    line_gap = 0.18 / height  # 0.18 inch below the last row, in figure fraction
    if caption:
        fig.text(
            0.02,
            table_bottom - line_gap,
            caption,
            fontsize=DEFAULT_CAPTION_FONTSIZE,
            style="italic",
            color=COLOR_NEUTRAL,
            va="top",
        )
    if source:
        fig.text(
            0.02,
            table_bottom - 3.1 * line_gap,
            f"{_SOURCE_PREFIX}{source}",
            fontsize=DEFAULT_FOOTER_FONTSIZE,
            color=COLOR_BASELINE,
            va="top",
        )

    # matplotlib >= 3.6 reports the full axes position as tight bbox even
    # with the axis switched off, so the dead band between footer and axes
    # bottom survives bbox_inches='tight'. Pull the axes bottom up to the
    # lowest footer text and rescale the cells so their physical height is
    # unchanged (cell heights are stored as axes fractions).
    lowest_text = min(
        (
            t.get_window_extent(renderer).transformed(fig.transFigure.inverted()).y0
            for t in fig.texts
        ),
        default=table_bottom,
    )
    old_pos = ax.get_position()
    new_y0 = max(lowest_text - 0.5 * line_gap, 0.0)
    if new_y0 > old_pos.y0:
        ax.set_position([old_pos.x0, new_y0, old_pos.width, old_pos.y1 - new_y0])
        table.scale(1.0, old_pos.height / (old_pos.y1 - new_y0))
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 9 — Regulatory timeline (parallel-track date comparisons)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TimelineEvent:
    """One event on a regulatory timeline.

    Attributes:
        date: ISO date string (YYYY-MM-DD).
        label: Short event label rendered next to the marker.
        track: Which horizontal track to render on (e.g. ``"original"``
            or ``"revised"``).
    """

    date: str
    label: str
    track: str


def executive_regulatory_timeline(
    events: Sequence[TimelineEvent],
    tracks: Sequence[str],
    *,
    track_labels: dict[str, str] | None = None,
    track_colors: dict[str, str] | None = None,
    title: str,
    caption: str,
    source: str,
    x_axis_label: str = "Kalenderjahr",
    figsize: tuple[float, float] = (13, 6.0),
) -> tuple[plt.Figure, plt.Axes]:
    """Render a multi-track horizontal regulatory timeline.

    Designed for the EUDR-update article where two parallel timelines
    (original vs revised effective dates) need to be compared on one
    axis.
    """
    fig, ax = plt.subplots(figsize=figsize)
    dates = pd.to_datetime([e.date for e in events])
    date_min, date_max = dates.min(), dates.max()
    # Visual margin on left so track labels have their own space.
    data_span = date_max - date_min
    label_x_pos = date_min - data_span * 0.04
    xlim_left = date_min - data_span * 0.20
    xlim_right = date_max + data_span * 0.04

    track_labels = track_labels or {t: t for t in tracks}
    default_palette = [COLOR_BASELINE, COLOR_CRISIS, COLOR_MODEL, COLOR_HIGHLIGHT]
    track_colors = track_colors or {t: default_palette[i % len(default_palette)] for i, t in enumerate(tracks)}

    track_y = {t: i for i, t in enumerate(tracks)}

    # Horizontal track lines
    for t in tracks:
        y = track_y[t]
        ax.hlines(y, date_min, date_max, color=track_colors[t], linewidth=2.2, alpha=0.75)
        # Track label in dedicated left area, vertically centred on the track,
        # right-aligned so it never reaches into the event-marker zone.
        ax.text(
            label_x_pos,
            y,
            track_labels[t],
            color=track_colors[t],
            fontweight="bold",
            fontsize=10,
            ha="right",
            va="center",
        )

    # Markers — per-track event ordering produces alternating y-offsets so
    # closely-spaced labels on the same track do not collide horizontally.
    events_by_track: dict[str, list[TimelineEvent]] = {t: [] for t in tracks}
    for ev in events:
        events_by_track.setdefault(ev.track, []).append(ev)
    for t in events_by_track:
        events_by_track[t].sort(key=lambda e: pd.to_datetime(e.date))

    # All labels on the same track sit at the SAME vertical offset from the
    # track line, so the eye can compare event positions consistently.
    label_offset = 38  # in points

    for t, ev_list in events_by_track.items():
        y = track_y[t]
        for ev in ev_list:
            d = pd.to_datetime(ev.date)
            ax.scatter([d], [y], s=120, color=track_colors[t], edgecolor="white", linewidth=2, zorder=3)
            offset = -label_offset if y == 0 else label_offset
            ax.annotate(
                ev.label,
                xy=(d, y),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va="top" if y == 0 else "bottom",
                fontsize=8,
                color=COLOR_NEUTRAL,
            )

    ax.set_xlim(xlim_left, xlim_right)
    # Generous vertical headroom so the lower track's annotations never reach
    # into the x-axis label, and the upper track's annotations never collide
    # with the suptitle.
    ax.set_ylim(-1.4, len(tracks) - 0.4)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelsize=10)
    if x_axis_label:
        ax.set_xlabel(x_axis_label, fontsize=10, color=COLOR_NEUTRAL, labelpad=14)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.grid(True, axis="x", alpha=0.2)

    fig.suptitle(title, x=0.02, y=0.965, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.84, bottom=0.22)
    _attach_footer(fig, caption, source)
    return fig, ax


# ---------------------------------------------------------------------------
# Plot 10 — Roadmap quarters (4-column action board)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoadmapAction:
    """One action in a quarter column.

    Attributes:
        text: The action description.
        priority: One of ``"mandatory"``, ``"recommended"``, ``"strategic"``.
    """

    text: str
    priority: str


def executive_roadmap_quarters(
    quarters: Sequence[str],
    actions: Sequence[Sequence[RoadmapAction]],
    *,
    title: str,
    caption: str,
    source: str,
    priority_labels: dict[str, str] | None = None,
    figsize: tuple[float, float] = (13, 6.5),
) -> tuple[plt.Figure, plt.Axes]:
    """Render an N-column quarter roadmap with priority-coded actions.

    Args:
        quarters: Column headers (e.g. ``["Q3 2026", "Q4 2026", "Q1 2027", "Q2 2027"]``).
        actions: For each quarter, a sequence of ``RoadmapAction`` items
            in the order they should appear top-to-bottom.
    """
    if len(quarters) != len(actions):
        raise ValueError(f"quarters ({len(quarters)}) must match actions ({len(actions)})")

    priority_palette = {
        "mandatory": COLOR_CRISIS,
        "recommended": COLOR_HIGHLIGHT,
        "strategic": COLOR_MODEL,
    }
    priority_label = priority_labels or {
        "mandatory": "Verpflichtend",
        "recommended": "Empfohlen",
        "strategic": "Strategisch",
    }

    fig, ax = plt.subplots(figsize=figsize)
    n_cols = len(quarters)
    col_width = 1.0 / n_cols

    # Column headers
    for j, q in enumerate(quarters):
        x_center = (j + 0.5) * col_width
        rect = mpatches.Rectangle(
            (j * col_width, 0.88),
            col_width,
            0.10,
            facecolor=COLOR_NEUTRAL,
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(x_center, 0.93, q, ha="center", va="center", color="white", fontweight="bold", fontsize=12)

    # Action cards per column
    max_actions = max(len(col) for col in actions) if actions else 1
    card_height = 0.78 / max_actions
    inner_pad = 0.012

    for j, col_actions in enumerate(actions):
        for i, action in enumerate(col_actions):
            y_top = 0.86 - i * card_height
            y_bottom = y_top - card_height + 0.015
            color = priority_palette.get(action.priority, COLOR_BASELINE)
            rect = mpatches.Rectangle(
                (j * col_width + inner_pad, y_bottom),
                col_width - 2 * inner_pad,
                y_top - y_bottom,
                facecolor=color,
                edgecolor="white",
                linewidth=2,
                alpha=0.92,
            )
            ax.add_patch(rect)
            wrapped = textwrap.fill(action.text, width=24)
            ax.text(
                j * col_width + col_width / 2,
                (y_top + y_bottom) / 2,
                wrapped,
                ha="center",
                va="center",
                color="white",
                fontsize=9,
                fontweight="bold",
            )

    # Legend
    legend_handles = [
        mpatches.Patch(color=priority_palette[k], label=priority_label[k])
        for k in ("mandatory", "recommended", "strategic")
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=3,
        frameon=False,
        fontsize=10,
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.suptitle(title, x=0.02, y=0.97, ha="left", fontsize=DEFAULT_TITLE_FONTSIZE, fontweight="bold")
    fig.subplots_adjust(top=0.91, bottom=0.16)
    _attach_footer(fig, caption, source)
    return fig, ax


__all__ = [
    "FunnelStep",
    "TierRow",
    "RegionRiskRow",
    "TimelineEvent",
    "RoadmapAction",
    "executive_truth_funnel",
    "executive_tier_pyramid",
    "executive_claim_heatmap",
    "executive_forecast_chart",
    "executive_risk_heatmap",
    "executive_two_mask_schema",
    "executive_region_comparison_bars",
    "executive_audit_trail_table",
    "executive_regulatory_timeline",
    "executive_roadmap_quarters",
    "build_default_funnel",
    "build_default_tiers",
    "COLOR_CRISIS",
    "COLOR_PASS",
    "COLOR_MODEL",
    "COLOR_BASELINE",
    "COLOR_NEUTRAL",
    "COLOR_HIGHLIGHT",
]
