from .simplicial_pyvis import simplicial_pyvis
import json
import os
import warnings

def born_before_threshold(birth,threshold):
    return birth <= threshold + 1e-5

class tda_visual_from_jason:
    def __init__(self, jason_path=None, plt_together=True, plt_sep = False,data=None, thresholds=None, which_cycle="harmonic_cycles", log_path=None, index_to_name=None, cycle_qualify=None, verbose=False):
        self.jason_path = jason_path
        self.plt_together = plt_together
        self.plt_sep = plt_sep
        self.thresholds = thresholds

        self.which_cycle = which_cycle
        self.index_to_name = index_to_name
        self.cycle_qualify = cycle_qualify or (lambda cycle: any(edge["weight"] != 0 for edge in cycle["edges"]))
        self.verbose = verbose

        if data is None:
            if jason_path is None:
                raise ValueError("either jason_path or data must be provided")
            with open(self.jason_path) as f:
                data = json.load(f)
        self.data = data

        self.log_path = log_path or os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.log_path, exist_ok=True)

        self.simplicies = {}
        for simplex, birth in zip(self.data["simplicies"], self.data["appears_at"]):
            dim = str(len(simplex) - 1)
            self.simplicies.setdefault(dim, {})[tuple(sorted(simplex))] = birth

        if self.index_to_name is None:
            vertices = [k[0] for k in self.simplicies.get("0", {}).keys()]
            self.index_to_name = {v: -v for v in vertices}

        if self.thresholds is None:
            if data[self.which_cycle]:
                self.thresholds = [c["birth"] for c in data[self.which_cycle]]
            else:
                edge_births = list(self.simplicies.get("1", {}).values())
                self.thresholds = [max(edge_births)] if edge_births else []
                if self.verbose:
                    print(f"no cycles was detected, using {self.thresholds} instead")

    def cycle_plot(self):
        if not self.plt_sep and not self.plt_together:
            if self.verbose:
                warnings.warn("Nothing is plotted")
            return
        for threshold in self.thresholds:
            self.cycle_plot_per_threshold(threshold)

    def cycle_plot_per_threshold(self,threshold):
        if self.verbose:
            warnings.warn("cycle_plot only supports visualisation of 1-dimensional cycles. Higher-dimensional cycles are not rendered.",UserWarning,stacklevel=2)
        cycles = self.read_cycles_from_jason(threshold)
        simplicies = self.filter_simplicies_threshold(threshold)

        if self.plt_together:
            vis = simplicial_pyvis(
                    simplicies=simplicies,
                    max_dim=1,
                    cycles=[c["edges"] for c in cycles],
                    cycle_dim=1,
                    index_to_name = self.index_to_name,
                    log_path=os.path.join(self.log_path,f"threshold_{threshold}_network.html")
                    )
            vis.net.heading = " | ".join(f"cycle {i}: {self.cycle_life_text(c['birth'], c['death'])}" for i, c in enumerate(cycles))
            vis.add_graph_to_net()
            vis.make_net()
            self.add_polygon(vis.net,simplicies,suffix=f"_threshold_{threshold}")

        if self.plt_sep:
            for i, cycle in enumerate(cycles):
                vis = simplicial_pyvis(
                        simplicies=simplicies,
                        max_dim=1,
                        cycles=[cycle["edges"]],
                        cycle_dim=1,
                        index_to_name = self.index_to_name,
                        log_path=os.path.join(self.log_path,f"threshold_{threshold}_cycle_{i}_network.html")
                        )
                vis.net.heading = f"cycle {i}: {self.cycle_life_text(cycle['birth'], cycle['death'])}"
                vis.add_graph_to_net()
                vis.make_net()
                self.add_polygon(vis.net,simplicies,suffix=f"_threshold_{threshold}_cycle_{i}")

    @staticmethod
    def cycle_life_text(birth, death):
        if death is None:
            return f"birth={birth:.3g}, death=inf, life=inf"
        life = float(death) - birth
        return f"birth={birth:.3g}, death={float(death):.3g}, life={life:.3g}"

    def read_cycles_from_jason(self,threshold):
        cycles = []
        for cycle in self.data[self.which_cycle]:
            drawn_edges = [(edge["simplex"], edge["weight"]) for edge in cycle["edges"] if edge["weight"]!=0]
            if not self.cycle_qualify(cycle):
                continue
            if born_before_threshold(cycle["birth"],threshold) and (cycle["death"] is None or float(cycle["death"]) > threshold):
                cycles.append({"edges": drawn_edges, "birth": cycle["birth"], "death": cycle["death"]})
        return cycles

    def filter_simplicies_threshold(self, threshold):
        filtered = {}
        for dim, simplices in self.simplicies.items():
            for simplex, birth in simplices.items():
                if born_before_threshold(birth,threshold):
                    filtered.setdefault(dim, {})[simplex] = birth
#        print(f"{filtered=}")
        return filtered

    # ── Polygon overlay ──────────────────────────────────────────────────────────

    def overlay_js(self, simplex_tuple):
        _, _, triangles, tetras = simplex_tuple

        tri_json = json.dumps([list(k) for k in triangles.keys()])
        tet_json = json.dumps([list(k) for k in tetras.keys()])

        js_path = os.path.join(os.path.dirname(__file__), "overlay.js")
        with open(js_path) as f:
            js = f.read()
        js = js.replace("__TRI_JSON__", tri_json).replace("__TET_JSON__", tet_json)
        return f"<script>\n{js}\n</script>"

    def inject_overlay(self, html, simplex_tuple):
        return html.replace("</body>", self.overlay_js(simplex_tuple) + "\n</body>")

    def add_polygon(self,net,simplicies,suffix=""):
        html = net.generate_html(notebook=False)
        vertices  = simplicies.get("0", {})
        edges     = simplicies.get("1", {})
        triangles = simplicies.get("2", {})
        tetras    = simplicies.get("3", {})
        simplex_tuple = (vertices,edges,triangles,tetras)
        html = self.inject_overlay(html,simplex_tuple)
        out_path = f"{self.log_path}/rips_complex{suffix}.html"
        with open(out_path, "w") as f:
            f.write(html)
       
