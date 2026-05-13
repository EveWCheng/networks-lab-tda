# networks-lab-tda

A toolkit for TDA (topological data analysis) on networks.

## Installation

Clone the repository:

```bash
git clone https://github.com/EveWCheng/networks-lab-tda.git
cd networks-lab-tda
```

You then have two ways to work with this project.

### Option 1: Add it as a workspace member in your own uv project (recommended)

This project is structured as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/), which means it can be plugged into a larger uv project alongside your own code and other packages. This is the right choice if you want to develop against `network_lab_tda` while keeping your own scripts, notebooks, or experiments in a separate directory — edits to the library are picked up immediately because it is installed in editable mode.

In the `pyproject.toml` of your *outer* uv project, declare this repo as a workspace member and pin the dependency to it:

```toml
[tool.uv.workspace]
members = [
    "path/to/networks-lab-tda",
]

[project]
dependencies = [
    "network_lab_tda",
]

[tool.uv.sources]
network_lab_tda = { workspace = true, editable = true }
```

Replace `path/to/networks-lab-tda` with the relative path from your outer project to the cloned repo. Then run:

```bash
uv sync
```

uv will resolve everything (including the bundled `matilda` workspace package) into a single shared virtual environment at the outer project's root. You can then `import network_lab_tda` from any script in your outer project.

### Option 2: Work directly inside the `examples/` directory (quick and dirty)

If you just want to try things out without setting up an outer project, you can run scripts directly from within this repo:

```bash
cd networks-lab-tda
uv sync
uv run examples/example_plot.py
```

`uv sync` from the repo root will install all dependencies into `.venv/`, and `uv run` executes scripts inside that environment. Add your own scripts to `examples/` and run them the same way.
