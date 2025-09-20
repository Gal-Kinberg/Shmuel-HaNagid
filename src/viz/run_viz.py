from GPT_graph_viz import draw_manuscript_graph, save_graph_figure

# Suppose `items` is your list of Apparatus (dataclass instances) or dicts
fig, ax = draw_manuscript_graph(
    correction_list,
    layout="sfdp",          # "spring", "kamada_kawai", or "circular"
    iterations=200,         # more iterations → nicer layout for large graphs
    min_edge_weight=1,      # only draw edges that appear at least this many times
    max_edges_per_type=None,# set e.g. 2000 to cap very dense types
    node_size=80,
    edge_alpha=0.15,
    edge_arrowsize=8,
    show_legend=True,
    figsize=(14, 12),
    seed=7,
    title="Manuscript Graph (directed; colored by apparatus type)"
)

# save_graph_figure(fig, "/path/to/manuscript_graph.png")
