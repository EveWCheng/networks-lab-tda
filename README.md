# networks-lab-tda

A toolkit for TDA (topological data analysis) on networks.

## Prerequisites: install uv

This project uses [uv](https://docs.astral.sh/uv/) to manage Python versions, dependencies, and virtual environments. If you don't already have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installing, restart your shell (or `source ~/.bashrc` / `source ~/.zshrc`) so the `uv` command is on your `PATH`. Verify with:

```bash
uv --version
```

This project requires Python 3.14+. You don't need to install it yourself — uv will download a matching interpreter automatically the first time you run `uv sync`.

## Installation

Clone the repository. `matilda` is included as a git submodule under `external_packages/`, so make sure to pull it down at the same time with `--recurse-submodules`:

```bash
git clone --recurse-submodules https://github.com/EveWCheng/networks-lab-tda.git
cd networks-lab-tda
```

If you already cloned without `--recurse-submodules`, you can pull the submodule afterwards with:

```bash
git submodule update --init --recursive
```

You then have three ways to work with this project. Pick based on whether you want to edit the library code:

- **Option 1** — Use it as a plain path dependency. You won't edit `network_lab_tda` itself, just consume it from your own project.
- **Option 2** — Add it as a workspace member. You want to edit the library and have changes picked up live.
- **Option 3** — Work directly inside this repo's `examples/` directory for a quick start.

### Option 1: Use it as a path dependency in your own uv project (read-only)

Use this if you just want to *use* `network_lab_tda` — import it, call its functions, and otherwise treat it as a black box. The repo is consumed as a normal package built from your local clone, not as a workspace.

If you don't already have an outer uv project, create one next to the cloned repo:

```bash
cd ..                          # step out of networks-lab-tda
uv init my-research-project    # pick whatever name you like
cd my-research-project
```

Open `my-research-project/pyproject.toml` and add:

```toml
[project]
dependencies = [
    "network_lab_tda",
    "matilda",
]

[tool.uv.sources]
network_lab_tda = { path = "../networks-lab-tda" }
matilda = { path = "../networks-lab-tda/external_packages/matilda", editable=true }
```

You have to list `matilda` explicitly because it isn't on PyPI — it lives as a git submodule inside this repo at `external_packages/matilda/`. `[tool.uv.sources]` is only respected at the workspace/project root, so the *consuming* project has to redeclare it.

Then:

```bash
uv sync
uv run python your_script.py
```

To pull in upstream updates later, `git pull --recurse-submodules` inside the `networks-lab-tda/` clone and re-run `uv sync` in your outer project. Note that changes you make inside `networks-lab-tda/src/` will **not** be picked up automatically with this setup — if you want live edits, use Option 2 instead.

### Option 2: Add it as a workspace member in your own uv project (for editing)

If you want to develop against `network_lab_tda` while keeping your own scripts, notebooks, or experiments in a separate directory, the cleanest setup is to make your outer uv project a [workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) and add this repo as a member. Edits to the library are picked up immediately because it is installed in editable mode.

If you don't already have an outer uv project, create one next to the cloned repo:

```bash
cd ..                          # step out of networks-lab-tda
uv init my-research-project    # pick whatever name you like
cd my-research-project
```

Your directory layout should now look something like:

```
.
├── networks-lab-tda/              # the cloned repo
│   └── external_packages/matilda/ # bundled submodule
└── my-research-project/   # your outer uv project
    └── pyproject.toml
```

Open `my-research-project/pyproject.toml` and add the following blocks (merge them with whatever `uv init` generated):

```toml
[project]
dependencies = [
    "network_lab_tda",
]

[tool.uv.workspace]
members = [
    "../networks-lab-tda",
]

[tool.uv.sources]
network_lab_tda = { workspace = true, editable = true }
matilda = { path = "../networks-lab-tda/external_packages/matilda", editable = true }
```

The `matilda` source is required because `network_lab_tda` depends on `matilda`, and `matilda` is not published to PyPI — it lives as a git submodule inside this repo at `external_packages/matilda/`. `[tool.uv.sources]` only takes effect at the workspace root, so you need to declare the path here in the outer project. Adjust the relative paths if your layout is different. Then, from inside `my-research-project/`:

```bash
uv sync
```

uv will create a `.venv/` at the outer project's root, download Python 3.14 if needed, and install both `network_lab_tda` and `matilda` in editable mode along with all dependencies. You can now `import network_lab_tda` from any script in your outer project and run it with:

```bash
uv run python your_script.py
```

### Option 3: Work directly inside the `examples/` directory (quick and dirty)

If you just want to try things out without setting up an outer project, you can run scripts directly from within this repo:

```bash
cd networks-lab-tda
uv sync
uv run examples/example_plot.py
```

`uv sync` from the repo root will install all dependencies into `.venv/`, and `uv run` executes scripts inside that environment. Add your own scripts to `examples/` and run them the same way:

```bash
uv run examples/your_script.py
```

If you'd rather drop into an interactive session with the environment activated:

```bash
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
python                         # or jupyter, ipython, etc.
```

### Using the example scripts from your own project

The scripts under `networks-lab-tda/examples/` (e.g. `example_plot.py`, `harmonic_example.py`) don't rely on living inside the repo. With either Option 1 or Option 2 set up, you can copy any of them into your own project directory and run them with `uv run python your_copy.py`, and they'll work the same way.

## Data preparation

Before running TDA, you typically need to load your distance data into a NetworkX graph and (optionally) subdivide long edges so the filtration sees a finer-grained metric space. Two classes handle this: `Data_Prep` for loading, and `Populate_Edge` for subdivision.

### `Data_Prep`

`Data_Prep` accepts a distance matrix in three forms — a CSV file, a NumPy array, or an existing NetworkX graph — and builds a weighted `networkx.Graph` from it.

```python
from network_lab_tda.data_prep.Data_Prep import Data_Prep

# From a CSV file (no headers)
dp = Data_Prep(filepath="distances.csv")

# From a CSV file with column headers (saves headers to log_path/header.txt)
dp = Data_Prep(filepath="distances.csv", headers=True)

# From a NumPy distance matrix
import numpy as np
dp = Data_Prep(matrix=np.array([[0, 1.2, 3.4], [1.2, 0, 2.1], [3.4, 2.1, 0]]))

# From an existing NetworkX graph
dp = Data_Prep(G=my_graph)
```

After construction, `dp.G` is a `networkx.Graph` with an edge attribute `length` equal to the non-zero entries of the distance matrix. If you passed `headers=True`, the column names are also saved to a text file so downstream steps can label nodes.

**Constructor arguments:**

| Argument | Default | Description |
|---|---|---|
| `filepath` | `None` | Path to a CSV distance matrix |
| `matrix` | `None` | NumPy distance matrix (2-D array) |
| `G` | `None` | Pre-built NetworkX graph |
| `log_path` | `./outputs` | Directory where output files are written |
| `headers` | `False` | If `True`, read column headers from the CSV and save them to `header_fn` |
| `header_fn` | `"header.txt"` | Filename for the saved header list inside `log_path` |

Exactly one of `filepath`, `matrix`, or `G` must be provided.

---

### `Populate_Edge`

Long edges in a sparse network can cause the Rips filtration to add simplices at unrealistically large radii. `Populate_Edge` solves this by subdividing every edge whose length exceeds a threshold `epsilon` into segments of length ≤ `epsilon`, inserting synthetic intermediate nodes. The result is a denser graph whose all-pairs shortest-path matrix more faithfully reflects the geodesic distances in the original network.

```python
from network_lab_tda.data_prep.Populate_Edge import Populate_Edge

pe = Populate_Edge(G=dp.G, headers=True)
dist_matrix = pe.populate_edges()
```

`populate_edges()` returns the new all-pairs distance matrix (computed via Floyd–Warshall) and writes two files to `log_path`:

- `populated_distance_matrix.txt` — the distance matrix after subdivision, ready to pass to `Data_Prep` or directly to `Rips`.
- `populated_headers.txt` — labels for all nodes (original + synthetic). Synthetic nodes are labelled by their index.

**Constructor arguments:**

| Argument | Default | Description |
|---|---|---|
| `G` | *(required)* | NetworkX graph to subdivide (e.g. `dp.G`) |
| `epsilon` | 40th percentile of edge lengths | Subdivision threshold; edges longer than this are split |
| `vis` | `False` | If `True`, writes `unpopulated_network.html` and `populated_network.html` to `log_path` for visual inspection |
| `populated_header_fn` | `"populated_headers.txt"` | Filename for the populated node label list |
| `headers`, `header_fn`, `log_path` | *(inherited)* | Same as `Data_Prep` |

**Typical pipeline:**

```python
from network_lab_tda.data_prep.Data_Prep import Data_Prep
from network_lab_tda.data_prep.Populate_Edge import Populate_Edge

dp = Data_Prep(filepath="distances.csv", headers=True)
pe = Populate_Edge(G=dp.G, headers=True, vis=True)
dist_matrix = pe.populate_edges()

# dist_matrix can now be passed to the TDA pipeline
```

---

## Output log format (`log.json`)

When you call `save_log()` on a `Rips` (or any subclass like `harmonic_cycle`), the results of the filtration and cycle computation are written to a JSON file. By default this goes to `./outputs/rips_log.json`, but you can override the path via the `log_path` argument to the constructor.

The log is a single JSON object with the following top-level keys:

### `simplicies` and `appears_at` (the filtration)

These two arrays are written when you run `rips_filtration(..., log=True)` (which `harmonic_cycle` does automatically when constructed with `sim_log=True`). They describe the full Rips filtration as a flat, sorted list:

- `simplicies` — every simplex in the complex, listed as an array of vertex indices. A `[0]` is a vertex, `[0, 2]` is an edge, `[0, 1, 3]` is a triangle, and so on.
- `appears_at` — the filtration value (birth time) at which the simplex on the corresponding row of `simplicies` enters the complex.

The two arrays are aligned by index: `simplicies[i]` first appears at `appears_at[i]`. The list is sorted by `appears_at` so you can read it top-to-bottom as the order in which simplices are added as the filtration radius grows.

```json
{
  "simplicies": [[0], [1], [2], [0, 1], [1, 2], [0, 1, 2]],
  "appears_at": [0.0, 0.0, 0.0, 1.0, 1.2, 1.4]
}
```

### Cycle results

In addition to the filtration, the log includes the cycles produced by whichever cycle method you ran. The key depends on the option you chose — currently `harmonic_cycle` writes to `"harmonic_cycles"`. Each entry is one cycle, described as:

- `cycle_index` — position of this cycle in the output list.
- `birth` — filtration value at which the cycle is born.
- `death` — filtration value at which the cycle dies, or `null` if it never dies (an essential cycle).
- `edges` — the simplices that make up the cycle, each with its weight in the representative. An edge with `weight: 0.0` is not part of the cycle's support; nonzero weights indicate which simplices carry the cycle and how strongly.

```json
{
  "harmonic_cycles": [
    {
      "cycle_index": 0,
      "birth": 1.4,
      "death": 2.1,
      "edges": [
        {"simplex": [0, 1], "weight": 0.577},
        {"simplex": [1, 2], "weight": 0.577},
        {"simplex": [0, 2], "weight": -0.577}
      ]
    }
  ]
}
```

The visualisation module (`tda_visualisation.tda_visual`) reads this same file back and uses the `which_cycle` argument to pick which set of cycles to draw — so if other cycle methods are added later, they will appear as additional top-level keys (e.g. `"persistent_cycles"`) alongside `harmonic_cycles`.

### Working with the log directly

Because the log is just JSON, you can load it with the standard library and pull out whatever you need. For example, to grab the first cycle and find its heaviest edge:

```python
import json

with open("outputs/rips_log.json") as f:
    log = json.load(f)

cycle = log["harmonic_cycles"][0]
heaviest = max(cycle["edges"], key=lambda e: abs(e["weight"]))
print(f"cycle {cycle['cycle_index']}: heaviest edge {heaviest['simplex']} with weight {heaviest['weight']}")
```

Once the log is loaded as a Python dict, every field described above is plain lists, numbers, and strings — so the same pattern works for any other question you want to ask about the filtration or the cycles.

## Visualisation inputs

The interactive plot is produced by `tda_visual_from_jason` in `network_lab_tda.tda_visualisation.tda_visual`. It reads the log file written by `save_log()` and renders one HTML page per threshold using [pyvis](https://pyvis.readthedocs.io/). All arguments except `jason_path` are optional.

```python
from network_lab_tda.tda_visualisation.tda_visual import tda_visual_from_jason

plotter = tda_visual_from_jason(
    jason_path=hc.log_path,         # required
    thresholds=None,                # default: each cycle's birth value
    which_cycle="harmonic_cycles",  # which log key to read cycles from
    log_path=None,                  # default: ./outputs
    index_to_name=None,             # default: index → index (no renaming)
)
plotter.cycle_plot()
```

- **`jason_path`** *(str, required)* — path to the `log.json` produced by `Rips.save_log()` / `harmonic_cycle.save_log()`.
- **`thresholds`** *(list of float, optional)* — filtration radii at which to draw the complex. One HTML file is produced per threshold. If left as `None`, the plotter falls back to the `birth` value of every cycle in the log, so you get one snapshot per cycle birth.
- **`which_cycle`** *(str, optional)* — top-level key in the log to read cycles from. Defaults to `"harmonic_cycles"`. Switch this if you logged cycles under a different name.
- **`log_path`** *(str, optional)* — output directory for the generated HTML files. Defaults to `./outputs`. One file `threshold_<value>_network.html` and one `rips_complex.html` are written per threshold.
- **`index_to_name`** *(dict[int, str], optional)* — maps a vertex index (the integer used in `simplicies`) to a display label shown on the node in the visualisation. If omitted, vertices are labelled by their numerical index.

### Example: labelling nodes

In `examples/example_plot.py` the points are anonymous but the script attaches a random 5-letter name to each one so the visualisation is easier to read:

```python
import random, string

index_to_name = {i: "".join(random.choices(string.ascii_letters, k=5)) for i in range(n)}

plotter = tda_visual_from_jason(
    jason_path=hc.log_path,
    index_to_name=index_to_name,
)
plotter.cycle_plot()
```

For real data, build `index_to_name` from whatever identifies your nodes — for example, if your distance matrix was computed from a list of gene names, country codes, or user IDs, pass `{i: my_names[i] for i in range(n)}` and those labels will appear on the rendered graph instead of bare integers.
