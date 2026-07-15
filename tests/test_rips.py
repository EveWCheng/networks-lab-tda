import json
import numpy as np
import pytest

from network_lab_tda.tda_analysis import Rips


@pytest.fixture
def triangle_D():
    # unit right triangle: (0,0), (1,0), (0,1)
    return np.array([
        [0.0, 1.0, 1.0],
        [1.0, 0.0, np.sqrt(2)],
        [1.0, np.sqrt(2), 0.0],
    ])


def test_vertices_born_at_zero(triangle_D, tmp_path):
    rips = Rips(triangle_D, max_dimension=2, log_path=str(tmp_path / "log.json"))
    simplices, births = rips.rips_filtration()

    vertex_births = {tuple(s): b for s, b in zip(simplices, births) if len(s) == 1}
    assert vertex_births == {(0,): 0.0, (1,): 0.0, (2,): 0.0}


def test_edges_born_at_pairwise_distance(triangle_D, tmp_path):
    rips = Rips(triangle_D, max_dimension=2, log_path=str(tmp_path / "log.json"))
    simplices, births = rips.rips_filtration()

    edge_births = {tuple(s): b for s, b in zip(simplices, births) if len(s) == 2}
    assert edge_births[(0, 1)] == pytest.approx(1.0)
    assert edge_births[(0, 2)] == pytest.approx(1.0)
    assert edge_births[(1, 2)] == pytest.approx(np.sqrt(2))


def test_filtration_sorted_by_birth(triangle_D, tmp_path):
    rips = Rips(triangle_D, max_dimension=2, log_path=str(tmp_path / "log.json"))
    _, births = rips.rips_filtration()

    assert births == sorted(births)


def test_threshold_excludes_long_edges(triangle_D, tmp_path):
    rips = Rips(triangle_D, max_dimension=2, log_path=str(tmp_path / "log.json"))
    simplices, _ = rips.rips_filtration(threshold=1.0)

    edges = [tuple(s) for s in simplices if len(s) == 2]
    assert (1, 2) not in edges
    assert (0, 1) in edges
    assert (0, 2) in edges


def test_log_populated_only_when_requested(triangle_D, tmp_path):
    rips = Rips(triangle_D, max_dimension=2, log_path=str(tmp_path / "log.json"))
    rips.rips_filtration(log=False)
    assert rips.log == {}

    rips.rips_filtration(log=True)
    assert "simplicies" in rips.log
    assert "appears_at" in rips.log


def test_save_log_writes_valid_json(triangle_D, tmp_path):
    log_path = tmp_path / "log.json"
    rips = Rips(triangle_D, max_dimension=2, log_path=str(log_path))
    rips.rips_filtration(log=True)
    rips.save_log()

    with open(log_path) as f:
        data = json.load(f)
    assert "simplicies" in data
    assert "appears_at" in data


def test_default_log_path_creates_outputs_dir(triangle_D, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rips = Rips(triangle_D, max_dimension=2)

    assert rips.log_path == str(tmp_path / "outputs" / "rips_log.json")
    assert (tmp_path / "outputs").is_dir()
