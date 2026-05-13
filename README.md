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

Clone the repository:

```bash
git clone https://github.com/EveWCheng/networks-lab-tda.git
cd networks-lab-tda
```

You then have two ways to work with this project.

### Option 1: Add it as a workspace member in your own uv project (recommended)

This project is structured as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/), which means it can be plugged into a larger uv project alongside your own code and other packages. This is the right choice if you want to develop against `network_lab_tda` while keeping your own scripts, notebooks, or experiments in a separate directory — edits to the library are picked up immediately because it is installed in editable mode.

If you don't already have an outer uv project, create one next to the cloned repo:

```bash
cd ..                          # step out of networks-lab-tda
uv init my-research-project    # pick whatever name you like
cd my-research-project
```

Your directory layout should now look something like:

```
.
├── networks-lab-tda/      # the cloned repo
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
```

Adjust `"../networks-lab-tda"` if your relative path is different. Then, from inside `my-research-project/`:

```bash
uv sync
```

uv will create a `.venv/` at the outer project's root, download Python 3.14 if needed, and install `network_lab_tda` (plus its bundled `matilda` workspace package and all dependencies) in editable mode. You can now `import network_lab_tda` from any script in your outer project and run it with:

```bash
uv run python your_script.py
```

### Option 2: Work directly inside the `examples/` directory (quick and dirty)

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
