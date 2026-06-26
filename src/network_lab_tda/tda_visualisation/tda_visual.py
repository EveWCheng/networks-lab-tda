from .simplicial_pyvis import simplicial_pyvis
import json
import os

def born_before_threshold(birth,threshold):
    return birth <= threshold + 1e-5

class tda_visual_from_jason:
    def __init__(self, jason_path, thresholds=None, which_cycle="harmonic_cycles", log_path=None, index_to_name=None):
        self.jason_path = jason_path
        self.thresholds = thresholds
        self.which_cycle = which_cycle
        self.log_path = log_path
        self.index_to_name = index_to_name

        with open(self.jason_path) as f:
            data = json.load(f)
        self.data = data

        self.log_path = log_path or os.path.join(os.getcwd(), "outputs")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        self.simplicies = {}
        for simplex, birth in zip(self.data["simplicies"], self.data["appears_at"]):
            dim = str(len(simplex) - 1)
            self.simplicies.setdefault(dim, {})[tuple(sorted(simplex))] = birth

        if self.index_to_name is None:
            vertices = [k[0] for k in self.simplicies.get("0", {}).keys()]
            self.index_to_name = {v: -v for v in vertices}

        if self.thresholds is None:
            if data["harmonic_cycles"]:
                self.thresholds = [c["birth"] for c in data["harmonic_cycles"]]
            else:
                edge_births = list(self.simplicies.get("1", {}).values())
                self.thresholds = [max(edge_births)] if edge_births else []
            print(f"no cycles was detected, using {self.thresholds} instead")

    def cycle_plot(self):
        for threshold in self.thresholds:
            self.cycle_plot_per_threshold(threshold)

    def cycle_plot_per_threshold(self,threshold):
        cycles = self.read_cycles_from_jason(threshold)
        simplicies = self.filter_simplicies_threshold(threshold)
        vis = simplicial_pyvis(
                simplicies=simplicies,
                max_dim=1,
                cycles=cycles,
                cycle_dim=1,
                index_to_name = self.index_to_name,
                log_path=os.path.join(self.log_path,f"threshold_{threshold}_network.html")
                )
        vis.add_graph_to_net()
        vis.make_net()
        print(f"Graph HTML saved to {vis.log_path}")
        self.add_polygon(vis.net,threshold)

    def read_cycles_from_jason(self,threshold):
        cycles = []
        for cycle in self.data[self.which_cycle]:
            if born_before_threshold(cycle["birth"],threshold) and float(cycle["death"]) > threshold:
                cycles.append([(edge["simplex"], edge["weight"]) for edge in cycle["edges"] if edge["weight"]!=0])
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

    def add_polygon(self,net,threshold):
        html = net.generate_html(notebook=False)
        simplicies = self.filter_simplicies_threshold(threshold)
        vertices  = simplicies.get("0", {})
        edges     = simplicies.get("1", {})
        triangles = simplicies.get("2", {})
        tetras    = simplicies.get("3", {})
        simplex_tuple = (vertices,edges,triangles,tetras)
        html = self.inject_overlay(html,simplex_tuple)
        out_path = f"{self.log_path}/rips_complex.html"
        with open(out_path, "w") as f:
            f.write(html)
       
        print(f"Saved → {out_path}")
        print(f"Open it in a browser. Drag nodes to re-layout; polygons follow in real time.")
