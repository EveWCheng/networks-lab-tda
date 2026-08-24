import networkx as nx
import pytest

from network_lab_tda.data_prep.Populate_Edge import Populate_Edge


def build_graph(edges):
    G = nx.Graph()
    for u, v, length in edges:
        G.add_edge(u, v, length=length)
    return G


def make_pe(edges, tmp_path, epsilon=1.0, max_node_per_edge=5):
    G = build_graph(edges)
    return Populate_Edge(
        G=G,
        log_path=str(tmp_path),
        epsilon=epsilon,
        max_node_per_edge=max_node_per_edge,
    )


def test_add_nodes_to_one_edge_exact_multiple(tmp_path):
    pe = make_pe([(0, 1, 3.0)], tmp_path, epsilon=1.0)
    pe.add_nodes_to_one_edge(0, 1, 3.0)

    assert not pe.G.has_edge(0, 1)
    chain = [0, "added_node_2", "added_node_3", 1]
    weights = [pe.G[a][b]["length"] for a, b in zip(chain, chain[1:])]
    assert weights == pytest.approx([1.0, 1.0, 1.0])
    assert pe.num_added == 2
    assert pe.max_index == 4


def test_add_nodes_to_one_edge_with_remainder(tmp_path):
    pe = make_pe([(0, 1, 2.5)], tmp_path, epsilon=1.0)
    pe.add_nodes_to_one_edge(0, 1, 2.5)

    chain = [0, "added_node_2", "added_node_3", 1]
    weights = [pe.G[a][b]["length"] for a, b in zip(chain, chain[1:])]
    assert weights == pytest.approx([1.0, 1.0, 0.5])
    assert pe.num_added == 2


def test_add_nodes_to_one_edge_short_edge_is_noop(tmp_path):
    pe = make_pe([(0, 1, 0.5)], tmp_path, epsilon=1.0)
    pe.add_nodes_to_one_edge(0, 1, 0.5)

    assert pe.G.has_edge(0, 1)
    assert pe.G[0][1]["length"] == pytest.approx(0.5)
    assert pe.num_added == 0
    assert pe.G.number_of_nodes() == 2


def test_add_nodes_to_one_edge_respects_max_node_per_edge_cap(tmp_path):
    pe = make_pe([(0, 1, 10.0)], tmp_path, epsilon=1.0, max_node_per_edge=3)
    pe.add_nodes_to_one_edge(0, 1, 10.0)

    assert pe.num_added == 3
    chain = [0, "added_node_2", "added_node_3", "added_node_4", 1]
    weights = [pe.G[a][b]["length"] for a, b in zip(chain, chain[1:])]
    # capped branch splits into equal segments, unlike the uncapped branch
    # where only the trailing segment absorbs the remainder
    assert weights == pytest.approx([2.5, 2.5, 2.5, 2.5])


def test_bookkeeping_accumulates_across_edges(tmp_path):
    pe = make_pe([(0, 1, 3.0), (1, 2, 3.0)], tmp_path, epsilon=1.0)
    pe.add_nodes_to_one_edge(0, 1, 3.0)
    pe.add_nodes_to_one_edge(1, 2, 3.0)

    assert pe.num_added == 4
    assert pe.max_index == 7
    assert set(pe.G.nodes) == {0, 1, 2, "added_node_3", "added_node_4", "added_node_5", "added_node_6"}
    # second call's new node ids must not collide with the first call's
    assert pe.G.has_edge(1, "added_node_5")
    assert pe.G.has_edge("added_node_5", "added_node_6")
    assert pe.G.has_edge("added_node_6", 2)


def test_populate_edges_raises_on_second_call(tmp_path):
    pe = make_pe([(0, 1, 3.0)], tmp_path, epsilon=1.0)
    pe.populate_edges()

    with pytest.raises(RuntimeError):
        pe.populate_edges()


def test_isclose_remainder_check_misses_float_noise(tmp_path):
    # 0.1 + 0.1 + 0.1 is conceptually an exact multiple of epsilon=0.1, but
    # float addition leaves ~2.8e-17 of noise. math.isclose(remainder, 0)
    # defaults to abs_tol=0.0, so it never treats near-zero remainders as
    # zero -- only exact equality counts. That means this "exact multiple"
    # case takes the generic-remainder path instead of the -1 correction,
    # producing one extra node and a zero-length trailing segment instead of
    # the clean 2-node/3-equal-segment split seen with clean floats (see
    # test_add_nodes_to_one_edge_exact_multiple).
    length = 0.1 + 0.1 + 0.1
    epsilon = 0.1
    pe = make_pe([(0, 1, length)], tmp_path, epsilon=epsilon)
    pe.add_nodes_to_one_edge(0, 1, length)

    assert pe.num_added == 3
    chain = [0, "added_node_2", "added_node_3", "added_node_4", 1]
    weights = [pe.G[a][b]["length"] for a, b in zip(chain, chain[1:])]
    assert weights == pytest.approx([0.1, 0.1, 0.1, 0.0], abs=1e-12)
