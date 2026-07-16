from network_lab_tda.tree_edit.tree_addition import TreeBuilder


def build(tree_groups, flag="t"):
    tb = TreeBuilder()
    tb.load_tree(tree_groups)
    tb.add_tree(flag)
    return tb.G


def test_cherry_with_direct_root_attachment():
    # A and B form a cherry; C attaches straight to the root with no
    # intermediate group -- exercises the one-level skip fallback
    tree_groups = {
        1: [["A"], ["B"], ["C"]],
        2: [["A", "B"]],
        3: [["A", "B", "C"]],
    }

    G = build(tree_groups)

    assert set(G.nodes()) == {
        ("A",), ("B",), ("C",),
        ("A", "B"), ("A", "B", "C"),
    }
    assert set(G.edges()) == {
        (("A",), ("A", "B")),
        (("B",), ("A", "B")),
        (("A", "B"), ("A", "B", "C")),
        (("C",), ("A", "B", "C")),
    }


def test_second_tree_merges_onto_same_builder():
    # a second, independent tree_groups sharing leaf C with the first tree
    # is loaded onto the same TreeBuilder -- this is exactly how
    # merge_trees() combines multiple gene trees. The shared leaf node
    # should end up with edges from both trees rather than being
    # duplicated or overwritten.
    tree_groups_1 = {
        1: [["A"], ["B"], ["C"]],
        2: [["A", "B"]],
        3: [["A", "B", "C"]],
    }
    tree_groups_2 = {
        1: [["C"], ["D"], ["E"]],
        2: [["C", "D"]],
        3: [["C", "D", "E"]],
    }

    tb = TreeBuilder()
    tb.load_tree(tree_groups_1)
    tb.add_tree("tree_1")
    tb.load_tree(tree_groups_2)
    tb.add_tree("tree_2")
    G = tb.G

    assert set(G.nodes()) == {
        ("A",), ("B",), ("C",), ("D",), ("E",),
        ("A", "B"), ("A", "B", "C"),
        ("C", "D"), ("C", "D", "E"),
    }
    assert set(G.edges()) == {
        (("A",), ("A", "B")),
        (("B",), ("A", "B")),
        (("A", "B"), ("A", "B", "C")),
        (("C",), ("A", "B", "C")),
        (("C",), ("C", "D")),
        (("D",), ("C", "D")),
        (("C", "D"), ("C", "D", "E")),
        (("E",), ("C", "D", "E")),
    }
    # the shared leaf is one node participating in both trees, not duplicated
    assert G.degree(("C",)) == 2


def test_multiple_skip_levels_and_multiple_matches_per_level():
    # two cherries (A,B) and (D,E) at level 2, nothing at levels 3/4, and a
    # lone leaf C that only attaches at the root -- exercises: empty
    # intermediate levels being skipped cleanly, two groups matched in the
    # same previous-level scan, and a leaf resolved four levels back
    tree_groups = {
        1: [["A"], ["B"], ["C"], ["D"], ["E"]],
        2: [["A", "B"], ["D", "E"]],
        5: [["A", "B", "C", "D", "E"]],
    }

    G = build(tree_groups)

    assert set(G.nodes()) == {
        ("A",), ("B",), ("C",), ("D",), ("E",),
        ("A", "B"), ("D", "E"), ("A", "B", "C", "D", "E"),
    }
    assert set(G.edges()) == {
        (("A",), ("A", "B")),
        (("B",), ("A", "B")),
        (("D",), ("D", "E")),
        (("E",), ("D", "E")),
        (("A", "B"), ("A", "B", "C", "D", "E")),
        (("D", "E"), ("A", "B", "C", "D", "E")),
        (("C",), ("A", "B", "C", "D", "E")),
    }
