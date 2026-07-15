import pytest

from network_lab_tda.tda_visualisation.tda_visual import tda_visual_from_jason
from network_lab_tda.tda_visualisation.simplicial_pyvis import simplicial_pyvis


def make_data(vertices):
    simplicies = [[v] for v in vertices]
    appears_at = [0.0 for _ in vertices]
    for i, a in enumerate(vertices):
        for b in vertices[i + 1:]:
            simplicies.append([a, b])
            appears_at.append(1.0)
    return {"simplicies": simplicies, "appears_at": appears_at, "harmonic_cycles": []}


def test_default_index_to_name_built_from_present_vertices(tmp_path):
    data = make_data([0, 1, 2])
    viz = tda_visual_from_jason(data=data, log_path=str(tmp_path))

    assert viz.index_to_name == {0: 0, 1: -1, 2: -2}


def test_default_index_to_name_handles_noncontiguous_vertices(tmp_path):
    data = make_data([2, 5, 9])
    viz = tda_visual_from_jason(data=data, log_path=str(tmp_path))

    assert viz.index_to_name == {2: -2, 5: -5, 9: -9}
    assert 0 not in viz.index_to_name
    assert 1 not in viz.index_to_name


def test_custom_index_to_name_is_preserved(tmp_path):
    data = make_data([0, 1, 2])
    custom = {0: "Alice", 1: "Bob", 2: "Carol"}
    viz = tda_visual_from_jason(data=data, log_path=str(tmp_path), index_to_name=custom)

    assert viz.index_to_name == custom


def test_add_graph_to_net_uses_index_to_name_as_label(tmp_path):
    simplicies = {
        "0": {(0,): 0.0, (1,): 0.0, (2,): 0.0},
        "1": {(0, 1): 1.0, (0, 2): 1.0, (1, 2): 1.4142},
    }
    index_to_name = {0: "Alice", 1: "Bob", 2: "Carol"}
    vis = simplicial_pyvis(
        max_dim=1,
        simplicies=simplicies,
        index_to_name=index_to_name,
        log_path=str(tmp_path / "network.html"),
    )
    vis.add_graph_to_net()

    labels = {node["id"]: node["label"] for node in vis.net.nodes}
    assert labels == {0: "Alice", 1: "Bob", 2: "Carol"}


def test_missing_vertex_in_custom_index_to_name_raises_keyerror(tmp_path):
    simplicies = {
        "0": {(0,): 0.0, (1,): 0.0, (3,): 0.0},
        "1": {(0, 1): 1.0, (0, 3): 1.0, (1, 3): 1.4142},
    }
    incomplete_index_to_name = {0: "Alice", 1: "Bob"}  # vertex 3 missing
    vis = simplicial_pyvis(
        max_dim=1,
        simplicies=simplicies,
        index_to_name=incomplete_index_to_name,
        log_path=str(tmp_path / "network.html"),
    )

    with pytest.raises(KeyError):
        vis.add_graph_to_net()
