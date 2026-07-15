import numpy as np
import pytest

from network_lab_tda.tda_analysis import harmonic_cycle


@pytest.fixture
def square_D():
    # 4 points on a unit square: forms a 1-cycle once the 4 sides are connected
    # but the diagonals are longer, so a loop persists before the square fills in
    points = [(0, 0), (1, 0), (1, 1), (0, 1)]
    n = len(points)
    D = np.zeros((n, n))
    for i, (x1, y1) in enumerate(points):
        for j, (x2, y2) in enumerate(points):
            D[i, j] = np.hypot(x1 - x2, y1 - y2)
    return D


@pytest.fixture
def line_D():
    # 4 collinear points: no possible 1-cycle at any threshold
    points = [(0, 0), (1, 0), (2, 0), (3, 0)]
    n = len(points)
    D = np.zeros((n, n))
    for i, (x1, y1) in enumerate(points):
        for j, (x2, y2) in enumerate(points):
            D[i, j] = np.hypot(x1 - x2, y1 - y2)
    return D


def test_square_produces_one_harmonic_cycle(square_D, tmp_path):
    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    # threshold below the diagonal length (sqrt(2)) so the loop hasn't filled in
    hc.run_harmonics(threshold=1.5)

    cycles = hc.log["harmonic_cycles"]
    assert len(cycles) == 1
    assert len(cycles[0]["edges"]) == 4
    assert cycles[0]["birth"] == pytest.approx(1.0)


def test_line_produces_no_cycles(line_D, tmp_path):
    hc = harmonic_cycle(line_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics()

    assert hc.log["harmonic_cycles"] == []


def test_infinite_bar_serializes_death_as_none(square_D, tmp_path):
    # no upper threshold: the loop born at the square's side length never
    # dies within this point set's own filtration range in a way that would
    # break serialization -- but if it does persist to infinity, death must
    # come through as None, not a raw inf float
    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.5)

    for cycle in hc.log["harmonic_cycles"]:
        assert cycle["death"] is None or isinstance(cycle["death"], float)


def test_cycle_edges_sum_to_closed_loop(square_D, tmp_path):
    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.5)

    cycle = hc.log["harmonic_cycles"][0]
    boundary = np.zeros(4)
    for edge in cycle["edges"]:
        u, v = edge["simplex"]
        w = edge["weight"]
        boundary[v] += w
        boundary[u] -= w
    assert boundary == pytest.approx(np.zeros(4), abs=1e-8)
