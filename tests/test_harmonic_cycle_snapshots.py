import numpy as np
import pytest

import matilda
import matilda.prototyping
import matilda.harmonic

from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_analysis.harmonic_cycle_snapshots import harmonic_cycle_snapshots
from network_lab_tda.tda_analysis.rips import Rips


def _distance_matrix(points):
    n = len(points)
    D = np.zeros((n, n))
    for i, (x1, y1) in enumerate(points):
        for j, (x2, y2) in enumerate(points):
            D[i, j] = np.hypot(x1 - x2, y1 - y2)
    return D


def _edge_vector(cycle, edge_keys):
    weights = {tuple(e["simplex"]): e["weight"] for e in cycle["edges"]}
    return np.array([weights.get(k, 0.0) for k in edge_keys])


def _matilda_harmonic_at_threshold(D, cycle_dim, threshold, log_path):
    # harmonic_cycle.run_harmonics() projects each persistent cycle onto the boundary
    # space present at *that cycle's own birth*, not at `threshold` -- so its output
    # isn't comparable to harmonic_cycle_snapshots, which always projects onto the
    # boundary space of the full complex at `threshold`. This calls matilda's own
    # projection machinery (project_cycle/OrthonormalBasis) directly against the
    # boundary space at `threshold`, for a true same-threshold comparison.
    rips = Rips(D, max_dimension=cycle_dim + 1, log_path=log_path)
    simplices, appears_at = rips.rips_filtration(threshold=threshold)
    simplices_np = [np.array(s) for s in simplices]

    K = matilda.prototyping.FilteredSimplicialComplex(
        dimension=cycle_dim + 1,
        simplices=simplices_np,
        simplices_indices=list(range(len(simplices_np))),
        appears_at=appears_at,
    )
    homology = matilda.PersistentHomologyComputer()
    homology.compute_persistent_homology(K, with_representatives=True, modulus=0)

    M, faces_idx, _ = K.get_boundary_matrix_at_filtration(
        boundary_dict=homology.reduced_boundary_matrix, value=threshold, dim=cycle_dim + 1, mode="economic",
    )
    boundary_basis = matilda.harmonic.OrthonormalBasis(M).basis if M.shape[1] > 0 else np.zeros((M.shape[0], 0))

    cycles = []
    for cid, (birth, death) in homology.bars[cycle_dim].items():
        if not (birth <= threshold and (not np.isfinite(death) or death > threshold)):
            continue
        cycle_arr = matilda.harmonic.cycle_array_from_dict(homology.persistent_cycles[cycle_dim][cid], faces_idx).astype(float)
        harmonic_vec = matilda.harmonic.project_cycle(cycle_arr, boundary_basis) if boundary_basis.shape[1] > 0 else cycle_arr
        edges = [
            {"simplex": sorted(K.simplices[K.simplices_indices[i]].tolist()), "weight": float(w)}
            for i, w in zip(faces_idx, harmonic_vec) if abs(w) > 1e-8
        ]
        cycles.append({"edges": edges})
    return cycles


@pytest.fixture
def square_D():
    # 4 points on a unit square: side = 1.0, diagonal = sqrt(2), so a threshold
    # between them leaves the loop open (no triangles) in both computations
    return _distance_matrix([(0, 0), (1, 0), (1, 1), (0, 1)])


@pytest.fixture
def line_D():
    # 4 collinear points: no possible 1-cycle at any threshold
    return _distance_matrix([(0, 0), (1, 0), (2, 0), (3, 0)])


@pytest.fixture
def two_squares_D():
    # two unit squares far enough apart that they never share an edge,
    # so exactly two independent 1-cycles coexist at the same threshold
    return _distance_matrix([(0, 0), (1, 0), (1, 1), (0, 1), (10, 10), (11, 10), (11, 11), (10, 11)])


@pytest.fixture
def shared_edge_squares_D():
    # a 2x1 rectangle split by a shared middle wall: two unit squares (loops) that
    # share exactly one edge, (1, 4), unlike two_squares_D's fully disjoint loops
    return _distance_matrix([(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)])


@pytest.fixture
def two_squares_different_sizes_D():
    # a unit square (side 1, loop born at threshold 1.0) and a far-away, larger
    # square (side 1.3, loop born at threshold 1.3), so the two independent cycles
    # have distinct births instead of appearing together
    square_a = [(0, 0), (1, 0), (1, 1), (0, 1)]
    square_b = [(100, 100), (101.3, 100), (101.3, 101.3), (100, 101.3)]
    return _distance_matrix(square_a + square_b)


@pytest.fixture
def point_cloud_D():
    # 14 points scattered noisily around a circle: one persistent 1-cycle, born at
    # ~7.746, with triangles continuing to form well past its birth (the very next
    # triangle in the whole filtration appears at ~7.768) -- unlike the hand-picked
    # polygon fixtures above, this exercises the case where the boundary space keeps
    # growing between the cycle's birth and the threshold we snapshot it at
    rng = np.random.default_rng(0)
    n = 14
    theta = np.sort(rng.uniform(0, 2 * np.pi, n))
    radius = 5.0
    noise = rng.normal(0, 0.15, n)
    points = np.column_stack([(radius + noise) * np.cos(theta), (radius + noise) * np.sin(theta)])
    return _distance_matrix(points.tolist())


def test_square_single_cycle_matches_persistent_harmonic(square_D, tmp_path):
    threshold = 1.2  # between side length 1.0 and diagonal length sqrt(2)

    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "hc.json"))
    hc.run_harmonics(threshold=threshold, save=False)
    persistent_cycles = hc.log["harmonic_cycles"]

    snap = harmonic_cycle_snapshots(square_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snapshot_cycles = snap.run_snapshots(save=False)[threshold]

    assert len(persistent_cycles) == len(snapshot_cycles) == 1

    edge_keys = sorted({tuple(e["simplex"]) for e in persistent_cycles[0]["edges"]})
    persistent_vec = _edge_vector(persistent_cycles[0], edge_keys)
    persistent_vec /= np.linalg.norm(persistent_vec)
    snapshot_vec = _edge_vector(snapshot_cycles[0], edge_keys)
    snapshot_vec /= np.linalg.norm(snapshot_vec)

    # multiplicity is 1, so the harmonic representative is unique up to scale and sign
    # (matilda's representative isn't unit-normalized like the SVD-derived snapshot one)
    sign = np.sign(np.dot(persistent_vec, snapshot_vec))
    assert snapshot_vec == pytest.approx(sign * persistent_vec, abs=1e-6)


def test_line_produces_no_cycles_in_both(line_D, tmp_path):
    threshold = 3.0

    hc = harmonic_cycle(line_D, cycle_dim=1, log_path=str(tmp_path / "hc.json"))
    hc.run_harmonics(threshold=threshold, save=False)

    snap = harmonic_cycle_snapshots(line_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snapshot_cycles = snap.run_snapshots(save=False)[threshold]

    assert hc.log["harmonic_cycles"] == []
    assert snapshot_cycles == []


def test_two_disjoint_squares_harmonic_subspace_matches(two_squares_D, tmp_path):
    threshold = 1.2  # each square's loop is open, the two components never connect

    hc = harmonic_cycle(two_squares_D, cycle_dim=1, log_path=str(tmp_path / "hc.json"))
    hc.run_harmonics(threshold=threshold, save=False)
    persistent_cycles = hc.log["harmonic_cycles"]

    snap = harmonic_cycle_snapshots(two_squares_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snapshot_cycles = snap.run_snapshots(save=False)[threshold]

    assert len(persistent_cycles) == len(snapshot_cycles) == 2

    edge_keys = sorted({tuple(e["simplex"]) for cycle in persistent_cycles for e in cycle["edges"]})
    persistent_matrix = np.column_stack([_edge_vector(c, edge_keys) for c in persistent_cycles])
    snapshot_matrix = np.column_stack([_edge_vector(c, edge_keys) for c in snapshot_cycles])

    # with multiplicity 2, individual basis vectors need not match -- only the
    # subspace they span does, so check snapshot's basis is fully reconstructible
    # as a linear combination of the persistent basis (and vice versa)
    coeffs, *_ = np.linalg.lstsq(persistent_matrix, snapshot_matrix, rcond=None)
    residual = snapshot_matrix - persistent_matrix @ coeffs
    assert residual == pytest.approx(np.zeros_like(residual), abs=1e-6)

    coeffs_back, *_ = np.linalg.lstsq(snapshot_matrix, persistent_matrix, rcond=None)
    residual_back = persistent_matrix - snapshot_matrix @ coeffs_back
    assert residual_back == pytest.approx(np.zeros_like(residual_back), abs=1e-6)


def test_two_squares_sharing_edge_harmonic_subspace_matches(shared_edge_squares_D, tmp_path):
    threshold = 1.2  # below diagonal length sqrt(2), so no triangles form either side

    hc = harmonic_cycle(shared_edge_squares_D, cycle_dim=1, log_path=str(tmp_path / "hc.json"))
    hc.run_harmonics(threshold=threshold, save=False)
    persistent_cycles = hc.log["harmonic_cycles"]

    snap = harmonic_cycle_snapshots(shared_edge_squares_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snapshot_cycles = snap.run_snapshots(save=False)[threshold]

    assert len(persistent_cycles) == len(snapshot_cycles) == 2

    edge_keys = sorted({tuple(e["simplex"]) for cycle in persistent_cycles for e in cycle["edges"]})
    assert (1, 4) in edge_keys  # the shared wall

    persistent_matrix = np.column_stack([_edge_vector(c, edge_keys) for c in persistent_cycles])
    snapshot_matrix = np.column_stack([_edge_vector(c, edge_keys) for c in snapshot_cycles])

    # sharing an edge couples the two loops' bases even more than the disjoint case,
    # so again compare the spanned subspace rather than individual basis vectors
    coeffs, *_ = np.linalg.lstsq(persistent_matrix, snapshot_matrix, rcond=None)
    residual = snapshot_matrix - persistent_matrix @ coeffs
    assert residual == pytest.approx(np.zeros_like(residual), abs=1e-6)

    coeffs_back, *_ = np.linalg.lstsq(snapshot_matrix, persistent_matrix, rcond=None)
    residual_back = persistent_matrix - snapshot_matrix @ coeffs_back
    assert residual_back == pytest.approx(np.zeros_like(residual_back), abs=1e-6)


def test_point_cloud_matches_matilda_harmonic_at_same_threshold(point_cloud_D, tmp_path):
    threshold = 8.2  # past birth (~7.746), well after new triangles have formed

    matilda_cycles = _matilda_harmonic_at_threshold(
        point_cloud_D, cycle_dim=1, threshold=threshold, log_path=str(tmp_path / "matilda.json")
    )
    snap = harmonic_cycle_snapshots(point_cloud_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snapshot_cycles = snap.run_snapshots(save=False)[threshold]

    assert len(matilda_cycles) == len(snapshot_cycles) == 1

    edge_keys = sorted({tuple(e["simplex"]) for e in matilda_cycles[0]["edges"]})
    matilda_vec = _edge_vector(matilda_cycles[0], edge_keys)
    matilda_vec /= np.linalg.norm(matilda_vec)
    snapshot_vec = _edge_vector(snapshot_cycles[0], edge_keys)
    snapshot_vec /= np.linalg.norm(snapshot_vec)

    sign = np.sign(np.dot(matilda_vec, snapshot_vec))
    assert snapshot_vec == pytest.approx(sign * matilda_vec, abs=1e-6)


def test_log_format_matches_harmonic_cycle_shape(square_D, tmp_path):
    threshold = 1.2

    hc = harmonic_cycle(square_D, cycle_dim=1, log_path=str(tmp_path / "hc.json"))
    hc.run_harmonics(threshold=threshold, save=False)
    hc_cycle = hc.log["harmonic_cycles"][0]

    snap = harmonic_cycle_snapshots(square_D, thresholds=[threshold], log_path=str(tmp_path / "snap.json"))
    snap.run_snapshots(save=False)
    snap_cycle = snap.log["harmonic_cycles"][0]

    assert set(snap_cycle.keys()) == set(hc_cycle.keys())
    assert set(snap_cycle["edges"][0].keys()) == set(hc_cycle["edges"][0].keys())


def test_log_flattens_persistent_cycle_to_single_birth(square_D, tmp_path):
    # the same loop is alive at all three thresholds (all below the diagonal, so it
    # never dies); the log should record it once, at the lowest threshold, not three times
    snap = harmonic_cycle_snapshots(square_D, thresholds=[1.05, 1.2, 1.35], log_path=str(tmp_path / "snap.json"))
    snap.run_snapshots(save=False)

    flat_cycles = snap.log["harmonic_cycles"]
    assert len(flat_cycles) == 1
    assert flat_cycles[0]["birth"] == pytest.approx(1.05)
    assert flat_cycles[0]["death"] is None
    assert len(flat_cycles[0]["edges"]) == 4


def test_log_records_distinct_births_for_distinct_cycles(two_squares_different_sizes_D, tmp_path):
    snap = harmonic_cycle_snapshots(
        two_squares_different_sizes_D, thresholds=[1.1, 1.35], log_path=str(tmp_path / "snap.json")
    )
    snap.run_snapshots(save=False)

    flat_cycles = snap.log["harmonic_cycles"]
    assert sorted(c["birth"] for c in flat_cycles) == [pytest.approx(1.1), pytest.approx(1.35)]
