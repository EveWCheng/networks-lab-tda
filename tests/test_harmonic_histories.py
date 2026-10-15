import numpy as np
import pytest

from matilda.harmonic import OrthonormalBasis, cycle_array_from_dict, project_cycle
from network_lab_tda.tda_analysis import harmonic_cycle


def _dist(points):
    p = np.array(points, dtype=float)
    return np.linalg.norm(p[:, None] - p[None], axis=-1)


@pytest.fixture
def late_triangle_D():
    """Rectangle loop born at 1.1; triangle 0-1-4 enters later, at about 1.118."""
    return _dist([(0, 0), (1, 0), (1, 1.1), (0, 1.1), (0.5, -1.0)])


@pytest.fixture
def four_triangles_D():
    """Rectangle loop born at 1.1; one outside point per side, triangles enter at 1.118, 1.141, 1.163, 1.185."""
    return _dist([(0, 0), (1, 0), (1, 1.1), (0, 1.1), (0.5, -1.0), (-1.0, 0.55), (0.5, 2.15), (2.05, 0.55)])


@pytest.fixture
def tied_triangles_D():
    """Unit square loop born at 1; triangles 0-1-4 and 2-3-5 both enter at exactly sqrt(1.25)."""
    return _dist([(0, 0), (1, 0), (1, 1), (0, 1), (0.5, -1.0), (0.5, 2.0)])


@pytest.fixture
def shared_edge_D():
    """Two squares sharing edge 1-2, born at 1.0 and 1.1."""
    return _dist([(0, 0), (1, 0), (1, 1), (0, 1), (2.1, 0), (2.1, 1)])


def _computer(D, tmp_path, threshold=float("inf")):
    """Run the rips filtration and harmonics; return (computer, simplices, appears_at)."""
    hc = harmonic_cycle(D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    simplices, appears_at = hc.rips_filtration(threshold=threshold, log=False)
    return hc.compute_harmonics(simplices, appears_at), simplices, [float(t) for t in appears_at]


def _simplex_id(simplices, *vertices):
    """Filtration id of the simplex with these vertices."""
    return next(i for i, s in enumerate(simplices) if sorted(s) == sorted(vertices))


def _times(history):
    """Distinct filtration values recorded anywhere in a class's history."""
    return sorted({t for pts in history.values() for t, _ in pts})


def _state_at(history, t):
    """Each face's weight at filtration value t, forward-filled from its history."""
    return {f: [w for s, w in pts if s <= t][-1] for f, pts in history.items() if pts[0][0] <= t}


def _death_value(H, appears_at, cid):
    """Filtration value of the simplex that kills class cid; inf if it never dies."""
    killer = int(H.homology.proto_bars[1][cid][1])
    return appears_at[killer] if killer >= 0 else np.inf


def brute_force_histories(H, appears_at, dim=1):
    """Per class, at each distinct value from birth to before death, project off all boundary columns so far."""
    hom, K = H.homology, H.K
    result = {}
    for cid, z_dict in hom.persistent_cycles[dim].items():
        death = _death_value(H, appears_at, cid)
        result[cid] = {}
        for t in sorted({v for v in appears_at if appears_at[cid] <= v < death}):
            last = max(i for i, v in enumerate(appears_at) if v <= t)
            M, fidx, cidx = K.get_boundary_matrix_at_filtration(
                simplex_id=last, dim=dim + 1, boundary_dict=hom.boundary_matrix, mode="economic")
            z = cycle_array_from_dict(z_dict, fidx).astype(float)
            h = project_cycle(z, OrthonormalBasis(M).basis) if len(fidx) and len(cidx) else z
            result[cid][t] = dict(zip(fidx, h))
    return result


@pytest.mark.parametrize("fixture, threshold", [
    ("late_triangle_D", 1.3), ("late_triangle_D", float("inf")),
    ("shared_edge_D", 1.3), ("shared_edge_D", float("inf")),
    ("four_triangles_D", 1.3), ("four_triangles_D", float("inf")),
    ("tied_triangles_D", 1.3), ("tied_triangles_D", float("inf")),
])
def test_incremental_histories_match_brute_force(fixture, threshold, request, tmp_path):
    H, _, appears_at = _computer(request.getfixturevalue(fixture), tmp_path, threshold)
    histories = H.compute_harmonic_histories(1)
    for cid, by_value in brute_force_histories(H, appears_at).items():
        for t, expected in by_value.items():
            state = _state_at(histories[cid], t)
            for face, w in expected.items():
                assert state.get(face, 0.0) == pytest.approx(w, abs=1e-8)


def test_tied_triangles_give_one_snapshot(tied_triangles_D, tmp_path):
    H, simplices, appears_at = _computer(tied_triangles_D, tmp_path, threshold=1.3)
    (cid, history), = H.compute_harmonic_histories(1).items()
    low, high = _simplex_id(simplices, 0, 1, 4), _simplex_id(simplices, 2, 3, 5)
    assert low != high and appears_at[low] == appears_at[high]
    t = appears_at[low]
    for pts in history.values():
        times = [s for s, _ in pts]
        assert times == sorted(set(times))
    assert t in _times(history)
    before, after = _state_at(history, max(s for s in _times(history) if s < t)), _state_at(history, t)
    for detour in (_simplex_id(simplices, 0, 4), _simplex_id(simplices, 3, 5)):
        assert before.get(detour, 0.0) == pytest.approx(0.0)
        assert abs(after[detour]) > 0


@pytest.mark.parametrize("fixture, threshold", [("late_triangle_D", 1.3), ("late_triangle_D", float("inf")), ("shared_edge_D", 1.3)])
def test_histories_start_at_weight_before_projection(fixture, threshold, request, tmp_path):
    H, _, appears_at = _computer(request.getfixturevalue(fixture), tmp_path, threshold)
    histories = H.compute_harmonic_histories(1)
    assert histories
    for cid, history in histories.items():
        before = H.harmonic_cycles_before_projection[1][cid]
        start = _state_at(history, appears_at[cid])
        for face, w in before.items():
            assert start.get(face, 0.0) == pytest.approx(w, abs=1e-8)


def test_histories_end_at_projection_before_death(late_triangle_D, tmp_path):
    H, _, appears_at = _computer(late_triangle_D, tmp_path)
    hom, K = H.homology, H.K
    for cid, history in H.compute_harmonic_histories(1).items():
        death = _death_value(H, appears_at, cid)
        assert np.isfinite(death)
        last = max(i for i, v in enumerate(appears_at) if v < death)
        M, fidx, cidx = K.get_boundary_matrix_at_filtration(
            simplex_id=last, dim=2, boundary_dict=hom.reduced_boundary_matrix, mode="economic")
        z = cycle_array_from_dict(hom.persistent_cycles[1][cid], fidx).astype(float)
        expected = dict(zip(fidx, project_cycle(z, OrthonormalBasis(M).basis)))
        end = {f: pts[-1][1] for f, pts in history.items()}
        for face, w in expected.items():
            assert end.get(face, 0.0) == pytest.approx(w, abs=1e-8)


def test_triangle_entering_mid_lifetime_moves_flow(late_triangle_D, tmp_path):
    H, simplices, appears_at = _computer(late_triangle_D, tmp_path, threshold=1.3)
    (cid, history), = H.compute_harmonic_histories(1).items()
    bottom, left, right = (_simplex_id(simplices, *e) for e in [(0, 1), (0, 4), (1, 4)])
    start, end = _state_at(history, appears_at[cid]), {f: pts[-1][1] for f, pts in history.items()}
    assert abs(start[bottom]) == pytest.approx(1.0)
    assert start.get(left, 0.0) == pytest.approx(0.0) and start.get(right, 0.0) == pytest.approx(0.0)
    assert 0 < abs(end[bottom]) < 1
    assert abs(end[left]) > 0 and abs(end[right]) > 0
    assert abs(end[bottom]) + abs(end[left]) == pytest.approx(1.0)


def test_each_late_triangle_moves_flow_when_it_enters(four_triangles_D, tmp_path):
    H, simplices, appears_at = _computer(four_triangles_D, tmp_path, threshold=1.3)
    (cid, history), = H.compute_harmonic_histories(1).items()
    sides = {4: (0, 1), 5: (0, 3), 6: (2, 3), 7: (1, 2)}
    entered = []
    for point, (a, b) in sides.items():
        side, detour = _simplex_id(simplices, a, b), _simplex_id(simplices, a, point)
        t = appears_at[_simplex_id(simplices, a, b, point)]
        assert appears_at[cid] < t
        before = _state_at(history, max(s for s in _times(history) if s < t))
        after = _state_at(history, t)
        assert before.get(detour, 0.0) == pytest.approx(0.0)
        assert abs(after[detour]) > 0
        assert abs(after[side]) < abs(before[side])
        entered.append(t)
    assert len(set(entered)) == 4


def test_history_snapshots_stay_closed(late_triangle_D, tmp_path):
    H, simplices, _ = _computer(late_triangle_D, tmp_path)
    for cid, history in H.compute_harmonic_histories(1).items():
        for t in _times(history):
            boundary = np.zeros(5)
            for face, w in _state_at(history, t).items():
                u, v = sorted(simplices[face])
                boundary[v] += w
                boundary[u] -= w
            assert boundary == pytest.approx(np.zeros(5), abs=1e-8)


@pytest.mark.parametrize("fixture", ["late_triangle_D", "four_triangles_D", "tied_triangles_D", "shared_edge_D"])
def test_every_seen_face_recorded_at_every_snapshot(fixture, request, tmp_path):
    H, _, _ = _computer(request.getfixturevalue(fixture), tmp_path, threshold=1.3)
    for history in H.compute_harmonic_histories(1).values():
        times = _times(history)
        for pts in history.values():
            assert [s for s, _ in pts] == times


def test_edge_ids_restricts_recorded_faces(late_triangle_D, tmp_path):
    H, simplices, _ = _computer(late_triangle_D, tmp_path, threshold=1.3)
    keep = {_simplex_id(simplices, 0, 1), _simplex_id(simplices, 0, 4)}
    for history in H.compute_harmonic_histories(1, edge_ids=keep).values():
        assert set(history) <= keep
        assert set(history)


def test_harmonic_cycle_logs_weight_history_when_enabled(four_triangles_D, tmp_path):
    hc = harmonic_cycle(four_triangles_D, cycle_dim=1, log_path=str(tmp_path / "log.json"), histories=True)
    hc.run_harmonics(threshold=1.3)
    (cycle,) = hc.log["harmonic_cycles"]
    history = {tuple(e["simplex"]): e["history"] for e in cycle["weight_history"]}
    start = {s: pts[0][1] for s, pts in history.items() if pts[0][0] == pytest.approx(cycle["birth"])}
    for edge in cycle["edges"]:
        assert start.get(tuple(edge["simplex"]), 0.0) == pytest.approx(edge["weight_before_projection"], abs=1e-8)
    assert any(len(pts) > 1 for pts in history.values())
    assert all(a[0] < b[0] for pts in history.values() for a, b in zip(pts, pts[1:]))
    assert (tmp_path / "log.json").exists()


def test_harmonic_cycle_omits_weight_history_by_default(four_triangles_D, tmp_path):
    hc = harmonic_cycle(four_triangles_D, cycle_dim=1, log_path=str(tmp_path / "log.json"))
    hc.run_harmonics(threshold=1.3)
    assert all("weight_history" not in cycle for cycle in hc.log["harmonic_cycles"])
