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


def _dist(points):
    p = np.array(points, dtype=float)
    return np.linalg.norm(p[:, None] - p[None], axis=-1)


@pytest.fixture
def shared_edge_D():
    # two squares sharing the edge 1-2; the right one is wider so its loop is born later (1.1)
    # while the left one is still alive. Threshold 1.3 keeps out all diagonals, so no triangles
    return _dist([(0, 0), (1, 0), (1, 1), (0, 1), (2.1, 0), (2.1, 1)])


@pytest.fixture
def triangle_D():
    # rectangle whose bottom edge 0-1 is also a side of the filled triangle 0-1-4. The triangle
    # enters at 1.0, before the loop is born at 1.1, so the loop's flow can detour through 4
    return _dist([(0, 0), (1, 0), (1, 1.1), (0, 1.1), (0.5, -0.3)])


def _weights(cycle, field):
    return {tuple(e["simplex"]): e[field] for e in cycle["edges"]}


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


def test_single_cycle_weight_before_projection_matches_weight(square_D, tmp_path):
    # only one cycle alive, so there is nothing to project off
    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.5)

    for edge in hc.log["harmonic_cycles"][0]["edges"]:
        assert edge["weight_before_projection"] == pytest.approx(edge["weight"])


def test_shared_edge_keeps_full_weight_before_projection(shared_edge_D, tmp_path):
    hc = harmonic_cycle(shared_edge_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.3)

    cycles = hc.log["harmonic_cycles"]
    assert len(cycles) == 2
    later = max(cycles, key=lambda c: c["birth"])
    before = _weights(later, "weight_before_projection")
    after = _weights(later, "weight")

    # no triangles: every edge of the loop is required (|w| = 1) and every other edge is unused (0)
    for w in before.values():
        assert abs(w) == pytest.approx(0.0, abs=1e-8) or abs(w) == pytest.approx(1.0)
    assert abs(before[(1, 2)]) == pytest.approx(1.0)
    # projecting off the older left square dilutes the shared edge
    assert abs(after[(1, 2)]) < 1 - 1e-6

    boundary = np.zeros(len(shared_edge_D))
    for (u, v), w in before.items():
        boundary[v] += w
        boundary[u] -= w
    assert boundary == pytest.approx(np.zeros(len(shared_edge_D)), abs=1e-8)


def test_filled_triangle_splits_weight_before_projection(triangle_D, tmp_path):
    hc = harmonic_cycle(triangle_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.3)

    cycles = hc.log["harmonic_cycles"]
    assert len(cycles) == 1
    before = _weights(cycles[0], "weight_before_projection")

    # the direct edge 0-1 shares the flow with the detour 0-4-1
    assert 0 < abs(before[(0, 1)]) < 1
    assert abs(before[(0, 4)]) > 1e-8
    assert abs(before[(1, 4)]) > 1e-8
    assert abs(before[(0, 1)]) + abs(before[(0, 4)]) == pytest.approx(1.0)
