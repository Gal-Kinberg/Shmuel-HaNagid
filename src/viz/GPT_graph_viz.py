# We'll create a reusable Python module that takes your Apparatus objects (or dicts)
# and renders a directed, colored-by-type manuscript graph with matplotlib + networkx.
# We'll also generate a small demo plot (with some Hebrew strings) so you can see it render.
from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from collections import Counter, defaultdict
from typing import Iterable, Mapping, Sequence, Tuple, Dict, Any, Optional, List, Union

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.lines import Line2D
import networkx as nx
import random
import json
import os

# Ensure a font that supports Hebrew (DejaVu Sans usually does)
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial Unicode MS", "Noto Sans Hebrew", "Noto Sans", "Arial",
                                          "Liberation Sans"]
matplotlib.rcParams["font.family"] = "sans-serif"


def _as_records(
        items: Iterable[Union[Mapping[str, Any], Any]]
) -> List[Dict[str, Any]]:
    """
    Normalize input to list of dicts. Accepts:
    - dataclass instances (like your Apparatus variants)
    - plain dicts with keys (song_name, line, lemma, source, target, type, ...)
    """
    out = []
    for it in items:
        if is_dataclass(it):
            out.append(asdict(it))
        elif isinstance(it, dict):
            out.append(dict(it))
        else:
            # Try a generic fallback
            try:
                out.append(dict(it))
            except Exception as e:
                raise TypeError(f"Unsupported item type: {type(it)}") from e
    return out


def build_manuscript_graph(
        items: Iterable[Union[Mapping[str, Any], Any]],
        treat_missing_target_as_isolated: bool = False,
) -> nx.MultiDiGraph:
    """
    Nodes are unique manuscript identifiers from the union of `source` and `target` fields.
    Directed edges go from 'source' -> 'target' and are labeled by apparatus 'type'.
    """
    records = _as_records(items)
    G = nx.MultiDiGraph()

    # Collect nodes (manuscripts)
    manuscripts = set()
    for r in records:
        src = r.get("source")
        tgt = r.get("target")
        if src is not None:
            manuscripts.add(src)
        if (tgt is not None) or not treat_missing_target_as_isolated:
            manuscripts.add(tgt)
    if None in manuscripts:
        manuscripts.remove(None)

    for m in manuscripts:
        G.add_node(m)

    # Add edges
    for r in records:
        src = r.get("source")
        tgt = r.get("target")
        typ = r.get("type", "unknown")
        # Require both ends to make a directed edge; otherwise skip or add isolated nodes
        if src is not None and tgt is not None:
            G.add_edge(src, tgt, type=typ)
    return G


def aggregate_edges_by_type(G: nx.MultiDiGraph) -> Dict[Tuple[Any, Any, str], int]:
    """
    Collapse multiedges into counts per (u, v, type).
    Returns a dict mapping (u, v, type) -> weight
    """
    counts: Dict[Tuple[Any, Any, str], int] = defaultdict(int)
    for u, v, data in G.edges(data=True):
        typ = data.get("type", "unknown")
        counts[(u, v, typ)] += 1
    return counts


def _categorical_color_map(categories: Sequence[str]) -> Dict[str, Any]:
    """
    Deterministic color mapping for categories using tab20 colormap.
    """
    # Use a qualitative palette with enough distinct colors. If overflow, cycle.
    unique = list(dict.fromkeys(categories))  # preserve order
    base_cmap = cm.get_cmap("tab20")
    colors = {}
    for i, cat in enumerate(unique):
        colors[cat] = base_cmap(i % base_cmap.N)
    return colors


def draw_manuscript_graph(
        items: Iterable[Union[Mapping[str, Any], Any]],
        layout: str = "sfdp",
        k: Optional[float] = None,
        iterations: int = 100,
        min_edge_weight: int = 1,
        max_edges_per_type: Optional[int] = None,
        node_size: int = 60,
        edge_alpha: float = 0.2,
        edge_arrowstyle: str = "-|>",
        edge_arrowsize: int = 8,
        show_legend: bool = True,
        figsize: Tuple[int, int] = (12, 10),
        seed: int = 42,
        title: Optional[str] = "Manuscript Graph (source → target; edge color = apparatus type)",
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Render a large directed graph with edges colored by apparatus type.

    - items: iterable of Apparatus-like dict/dataclass objects.
    - layout: "spring" (default F-R), "kamada_kawai", "sfdp" (via networkx's spring but tuned),
              or "circular" for baseline. "sfdp" here is a tuned spring layout for large graphs.
    - min_edge_weight: collapse multiedges; draw only edges with weight >= this threshold.
    - max_edges_per_type: if set, randomly subsample edges per type to avoid overplotting.
    - node_size: size of nodes.
    - edge_alpha: transparency for edges (lower helps with thousands of edges).
    - edge_arrowstyle, edge_arrowsize: styles for directed edges.
    - show_legend: include a legend mapping colors to edge types.
    - seed: for layout reproducibility.
    """
    random.seed(seed)
    G = build_manuscript_graph(items)
    counts = aggregate_edges_by_type(G)  # (u, v, type) -> weight

    # Filter by weight
    filtered = {k: w for k, w in counts.items() if w >= min_edge_weight}

    # Optionally cap per-type edges for readability/performance
    if max_edges_per_type is not None:
        by_type = defaultdict(list)
        for (u, v, t), w in filtered.items():
            by_type[t].append(((u, v, t), w))
        filtered2 = {}
        for t, lst in by_type.items():
            if len(lst) > max_edges_per_type:
                # randomly sample
                sample = random.sample(lst, max_edges_per_type)
                filtered2.update(sample)
            else:
                filtered2.update(lst)
        filtered = filtered2

    # Build a simple DiGraph to draw (weights stored on edges)
    H = nx.DiGraph()
    for (u, v, t), w in filtered.items():
        H.add_node(u)
        H.add_node(v)
        # For drawing, keep type and weight; if multiple types between same pair after filtering,
        # keep the max weight per (u,v,t) which we already ensured.
        H.add_edge(u, v, type=t, weight=w)

    # Choose layout
    if layout == "spring" or layout == "sfdp":
        # tuned spring layout for larger graphs
        # k controls spacing; lower k = more compact
        k_val = k if k is not None else 1 / math.sqrt(max(1, H.number_of_nodes()))
        pos = nx.spring_layout(H, k=k_val, iterations=iterations, seed=seed)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(H)
    elif layout == "circular":
        pos = nx.circular_layout(H)
    else:
        pos = nx.spring_layout(H, seed=seed)

    # Prepare color mapping
    edge_types = [data["type"] for _, _, data in H.edges(data=True)]
    color_map = _categorical_color_map(edge_types)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title if title else "")
    ax.axis("off")

    # Draw nodes
    nx.draw_networkx_nodes(
        H, pos, ax=ax, node_size=node_size, node_color="#cccccc", linewidths=0.0
    )

    # Draw edges grouped by type for color/legend control
    legend_handles: List[Line2D] = []
    for t in sorted(set(edge_types)):
        edges_of_type = [(u, v) for u, v, d in H.edges(data=True) if d["type"] == t]
        weights = [H[u][v]["weight"] for (u, v) in edges_of_type]
        # Map weight -> linewidth with a mild scaling
        if weights:
            w_min, w_max = min(weights), max(weights)
            if w_min == w_max:
                linewidths = [1.0 for _ in weights]
            else:
                linewidths = [1.0 + 2.5 * (w - w_min) / (w_max - w_min) for w in weights]
        else:
            linewidths = []

        nx.draw_networkx_edges(
            H,
            pos,
            ax=ax,
            edgelist=edges_of_type,
            arrows=True,
            arrowstyle=edge_arrowstyle,
            arrowsize=edge_arrowsize,
            width=linewidths,
            edge_color=[color_map[t]] * len(edges_of_type),
            alpha=edge_alpha,
            connectionstyle="arc3,rad=0.06",  # slight curvature to reduce overlap
            min_source_margin=2,
            min_target_margin=2,
        )

        # legend entry for this type
        legend_handles.append(
            Line2D([0], [0], color=color_map[t], lw=2, label=t)
        )

    # Optionally draw a subset of labels (too many labels clutter)
    # Here: label only high-degree nodes (top 10% by degree) and a cap.
    deg = H.degree()
    if H.number_of_nodes() > 0:
        deg_values = sorted(deg, key=lambda kv: kv[1], reverse=True)
        top_n = max(5, H.number_of_nodes() // 10)
        labeled_nodes = set([n for n, _ in deg_values[:top_n]])
        nx.draw_networkx_labels(
            H, pos, labels={n: str(n) for n in labeled_nodes}, font_size=9
        )

    if show_legend and legend_handles:
        ax.legend(
            handles=legend_handles,
            title="Apparatus Type",
            loc="lower right",
            frameon=False,
            ncols=1,
        )

    fig.tight_layout()
    return fig, ax


def save_graph_figure(fig: plt.Figure, path: str = "/mnt/data/manuscript_graph.png") -> str:
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


# --- Demo with synthetic data (including Hebrew strings) ---
def _demo_data(n_edges: int = 800, seed: int = 123):
    random.seed(seed)
    # Synthetic manuscript ids (including Hebrew)
    manuscripts = [
        "MS_A", "MS_B", "MS_C", "MS_D",
        "כתב־יד א", "כתב־יד ב", "כתב־יד ג", "כתב־יד ד",
        "Codex I", "Codex II", "Codex III",
    ]
    # Apparatus types from your dataclasses
    types = [
        "apparatus", "missing", "full_spelling",
        "letter_swap", "word_swap", "order_swap", "deletion"
    ]
    items = []
    for _ in range(n_edges):
        src, tgt = random.sample(manuscripts, 2)
        typ = random.choice(types)
        # minimal fields used by the visualizer
        items.append({
            "song_name": "DemoSong",
            "line": random.randint(1, 120),
            "lemma": "דוגמה",
            "source": src,
            "target": tgt,
            "type": typ
        })
    return items


if __name__ == "__main__":
    fig, ax = draw_manuscript_graph(
        correction_list,
        layout="sfdp",  # "spring", "kamada_kawai", or "circular"
        iterations=100,  # more iterations → nicer layout for large graphs
        min_edge_weight=1,  # only draw edges that appear at least this many times
        max_edges_per_type=None,  # set e.g. 2000 to cap very dense types
        node_size=2000,
        edge_alpha=0.25,
        edge_arrowsize=50,
        show_legend=True,
        figsize=(int(28/4), int(24/4)),
        seed=7,
        title="Manuscript Graph (directed; colored by apparatus type)"
    )
    plt.show()
    # out_path = save_graph_figure(fig, "/mnt/data/manuscript_graph_demo.png")
    # out_path
