import gudhi
import numpy as np
import json

def rips_filtration(D, threshold=float('inf')):
    rips = gudhi.RipsComplex(distance_matrix=D, max_edge_length=threshold)
    st = rips.create_simplex_tree(max_dimension=2)  # vertices, edges, triangles

    filtration = sorted(st.get_filtration(), key=lambda x: x[1])
    simplices = [list(s) for s, _ in filtration]
    births    = [b       for _, b in filtration]
    return simplices, births

def show_filtration(simplices, births):
    print("Simplex filtration (0-indexed vertices):")
    for s, b in zip(simplices, births):
        print(f"  {s} -> {round(b, 6)}")

def write_filtration_json(simplices, births, path):
    with open(path, "w") as f:
        json.dump({"simplices": simplices, "appears_at": births}, f)

pts = [(1,0),(2,0),(1,1),(2,1)]
D = [[np.sqrt((x1-x2)**2+(y1-y2)**2) for x2,y2 in pts] for x1,y1 in pts]

simplices, births = rips_filtration(D, threshold=1.5)
show_filtration(simplices, births)
write_filtration_json(simplices, births, "filtration.json")
