from pathlib import Path
from .simplicial_pyvis import simplicial_pyvis
import json
import numpy as np

class tda_visual_from_jason:
    def __init__(self, jason_path, threshold, which_cycle="harmonic_cycles", distance_mat=None, neighbour_layers=0, log_path=None):
        self.jason_path = jason_path
        self.threshold = threshold
        self.D = distance_mat
        self.neighbour_layers = neighbour_layers
        self.which_cycle = which_cycle
        self.log_path = log_path

        with open(self.jason_path) as f:
            data = json.load(f)
        self.data = data

        if self.threshold is None and data["harmonic_cycles"]:
            self.threshold = min(c["birth"] for c in data["harmonic_cycles"]) + 1

        if self.log_path is None:
            self.log_path = Path.cwd()

        self.simplicies = {}
        for simplex, birth in zip(self.data["simplicies"], self.data["appears_at"]):
            dim = str(len(simplex) - 1)
            self.simplicies.setdefault(dim, []).append([simplex, birth])


    def tda_plot(self):
        cycles = self.read_cycles_from_jason()
        if self.D is not None:
            D_neighbour = self.neighbourhood_D(cycles)
            D_neighbour[D_neighbour > self.threshold] = 0.0
        else:
            D_neighbour = self.D
        simplicies = self.filter_simplicies_threshold()
        vis = simplicial_pyvis(
                distance_mat=D_neighbour,
                simplicies=simplicies,
                max_dim=1,
                cycles=cycles,
                cycle_dim=1
                )
        vis.add_graph_to_net()
        vis.make_net()
        print(f"Graph HTML saved to {self.log_path}")
        self.add_polygon(vis.net)

    def read_cycles_from_jason(self):
        cycles = []
        for cycle in self.data[self.which_cycle]:
            if cycle["birth"] <= self.threshold:
                cycles.append([edge["simplex"] for edge in cycle["edges"]])
        return cycles

    def filter_D_threshold(self):
        D_ = self.D.copy()
        D_[D_ > self.threshold] = 0.0
        return D_

    def filter_simplicies_threshold(self):
        filtered = {}
        for dim, simplices in self.simplicies.items():
            for simplex, birth in simplices:
                if birth <= self.threshold:
                    filtered.setdefault(dim, []).append([simplex, birth])
        return filtered

    def neighbourhood_D(self, cycles):
        def find_all_verts(D, cycles, num_layer):
            cycle_verts = set()
            for cycle in cycles:
                for edge in cycle:
                    cycle_verts.update(edge)

            if num_layer == 0:
                return cycle_verts

            all_verts = cycle_verts.copy()
            frontier = cycle_verts.copy()
            for _ in range(num_layer):
                next_frontier = set()
                for v in frontier:
                    neighbours = set(np.where(D[v] > 0)[0].tolist())
                    next_frontier.update(neighbours - all_verts)
                all_verts.update(next_frontier)
                frontier = next_frontier
            return all_verts
        all_verts = find_all_verts(self.D, cycles, self.neighbour_layers)
        D_new = np.zeros_like(self.D)
        verts = list(all_verts)
        ix = np.ix_(verts, verts)
        D_new[ix] = self.D[ix]
        return D_new

    # ── Polygon overlay ──────────────────────────────────────────────────────────

    def overlay_js(self, simplex_tuple):
        _, _, triangles, tetras = simplex_tuple

        tri_json = json.dumps([s[0] for s in triangles])
        tet_json = json.dumps([s[0] for s in tetras])
        return f"""
    <script>
    var TRI_FILL   = "rgba(100, 160, 255, 0.22)";
    var TRI_STROKE = "rgba(100, 160, 255, 0.55)";
    var TET_FILL   = "rgba(255, 140, 80,  0.18)";
    var TET_STROKE = "rgba(255, 140, 80,  0.50)";

    var triangles = {tri_json};
    var tetras    = {tet_json};

    function attachOverlay() {{
      if (typeof network === "undefined") {{ setTimeout(attachOverlay, 100); return; }}

      var container = document.getElementById("mynetwork");
      var visCanvas = container.querySelector("canvas");
      if (!visCanvas) {{ setTimeout(attachOverlay, 100); return; }}

      var oc = document.createElement("canvas");
      oc.style.position      = "absolute";
      oc.style.top           = "0"; oc.style.left = "0";
      oc.style.pointerEvents = "none";
      oc.style.zIndex        = "5";
      container.style.position = "relative";
      container.appendChild(oc);

      var ctx = oc.getContext("2d");

      function syncSize() {{
        oc.width  = visCanvas.width;
        oc.height = visCanvas.height;
      }}
      syncSize();

      function getNodePos(id) {{
        var pos = network.getPositions([id]);
        if (!pos[id]) return null;
        return network.canvasToDOM({{ x: pos[id].x, y: pos[id].y }});
      }}

      function drawPolygon(ids, fill, stroke) {{
        var pts = ids.map(getNodePos);
        if (pts.some(p => p === null)) return;
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.closePath();
        ctx.fillStyle   = fill;   ctx.fill();
        ctx.strokeStyle = stroke; ctx.lineWidth = 1.2; ctx.stroke();
      }}

      function tetFaces(ids) {{
        return [
          [ids[0], ids[1], ids[2]],
          [ids[0], ids[1], ids[3]],
          [ids[0], ids[2], ids[3]],
          [ids[1], ids[2], ids[3]],
        ];
      }}

      function redraw() {{
        syncSize();
        ctx.clearRect(0, 0, oc.width, oc.height);
        tetras.forEach(function(ids) {{
          tetFaces(ids).forEach(function(face) {{ drawPolygon(face, TET_FILL, TET_STROKE); }});
        }});
        triangles.forEach(function(ids) {{ drawPolygon(ids, TRI_FILL, TRI_STROKE); }});
      }}

      network.on("afterDrawing", function() {{ redraw(); }});
      window.addEventListener("resize", function() {{ syncSize(); redraw(); }});
      redraw();
    }}

    setTimeout(attachOverlay, 50);
    </script>
    """

    def inject_overlay(self, html, simplex_tuple):
        return html.replace("</body>", self.overlay_js(simplex_tuple) + "\n</body>")

    def legend_info_panel(self,simplex_tuple):
        vertices, edges,triangles,tetras = simplex_tuple
        return f"""
    <div style="position:fixed; bottom:18px; left:18px; background:rgba(20,20,40,0.88);
                border:1px solid #444; border-radius:8px; padding:12px 16px;
                font-family:sans-serif; font-size:13px; color:#ccc; z-index:100;">
      <div style="font-weight:600; margin-bottom:8px; color:#fff;">Rips complex  ε={self.threshold}</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <span style="width:14px;height:14px;border-radius:50%;background:#e0e0ff;display:inline-block;"></span>
        <span>0-simplex &nbsp;({len(vertices)} vertices)</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <span style="width:18px;height:3px;background:#7070cc;display:inline-block;"></span>
        <span>1-simplex &nbsp;({len(edges)} edges)</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <span style="width:14px;height:14px;background:rgba(100,160,255,0.5);
                     border:1.5px solid rgba(100,160,255,0.9);display:inline-block;"></span>
        <span>2-simplex &nbsp;({len(triangles)} triangles)</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="width:14px;height:14px;background:rgba(255,140,80,0.45);
                     border:1.5px solid rgba(255,140,80,0.9);display:inline-block;"></span>
        <span>3-simplex &nbsp;({len(tetras)} tetrahedra)</span>
      </div>
      <div style="margin-top:10px; font-size:11px; color:#888; border-top:1px solid #444; padding-top:8px;">
        Drag nodes · Scroll to zoom · Hover for info
      </div>
    </div>
    """

    def add_polygon(self,net):
        html = net.generate_html(notebook=False)
        simplicies = self.filter_simplicies_threshold()
        vertices  = simplicies.get("0", [])
        edges     = simplicies.get("1", [])
        triangles = simplicies.get("2", [])
        tetras    = simplicies.get("3", [])
        simplex_tuple = (vertices,edges,triangles,tetras)
        html = self.inject_overlay(html,simplex_tuple)
        html = html.replace("</body>", self.legend_info_panel(simplex_tuple) + "\n</body>")
        out_path = f"{self.log_path}/rips_complex.html"
        with open(out_path, "w") as f:
            f.write(html)
       
        print(f"Saved → {out_path}")
        print(f"Open it in a browser. Drag nodes to re-layout; polygons follow in real time.")
