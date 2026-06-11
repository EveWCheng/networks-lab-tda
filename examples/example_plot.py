import os
import random
import string
import numpy as np
import networkx as nx
from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_visualisation.tda_visual import tda_visual_from_jason
from network_lab_tda.data_prep.Populate_Edge import Populate_Edge

HERE = os.path.dirname(os.path.abspath(__file__))


def make_circle_pts():
    n_per_circle = 30
    radius = 1.0
    rng = np.random.default_rng(0)
    theta = np.linspace(0.0, 2.0 * np.pi, n_per_circle, endpoint=False)
    left  = np.column_stack([radius * np.cos(theta) - 1.1, radius * np.sin(theta)])
    right = np.column_stack([radius * np.cos(theta) + 1.1, radius * np.sin(theta)])
    pts = np.vstack([left, right])
    pts += rng.normal(scale=0.05, size=pts.shape)
    return pts


def make_tree_pts():
    rng = np.random.default_rng(42)
    T = nx.random_labeled_tree(20, seed=42)
    for u, v in T.edges():
        T[u][v]['length'] = rng.uniform(0.5, 3.0)
    return T


def dist_matrix(pts):
    n = pts.shape[0]
    return np.array([[np.linalg.norm(pts[i] - pts[j]) for j in range(n)] for i in range(n)])


def run_analysis(label,D=None, G=None):
    out_dir = os.path.join(HERE, "outputs", label)
    os.makedirs(out_dir, exist_ok=True)
    
    "Tree is run"
    if D is None:
        pe = Populate_Edge(G, log_path=out_dir)
        D = pe.populate_edges()
#        print(D)

    n = D.shape[0]
    log_path = os.path.join(out_dir, "rips_log.json")
    hc = harmonic_cycle(D.tolist(), cycle_dim=1, sim_log=True, log_path=log_path)
    simplices, appears_at = hc.rips_filtration()
    hc.compute_harmonics(simplices, appears_at)
    hc.run_harmonics()
    hc.save_log()

    index_to_name = {i: "".join(random.choices(string.ascii_letters, k=5)) for i in range(n)}
    plotter = tda_visual_from_jason(
        jason_path=hc.log_path,
        index_to_name=index_to_name,
        log_path=out_dir,
    )
    plotter.cycle_plot()


#run_analysis(dist_matrix(make_circle_pts()), "circle", populate_edge=False)
run_analysis("tree",G=make_tree_pts())
