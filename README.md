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
matilda = { path = "../networks-lab-tda/external_packages/matilda" }
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
