import os
from network_lab_tda.tree_edit.tree_addition import merge_trees

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    input_dir = os.path.join(HERE, "inputs", "mock_trees")
    output_dir = os.path.join(HERE, "outputs", "tree_addition")

    merge_trees(input_dir=input_dir, output_dir=output_dir, vis=True)


main()
