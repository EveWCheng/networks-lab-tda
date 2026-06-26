import os
import numpy as np
from network_lab_tda.data_prep.Data_Prep import Data_Prep
from network_lab_tda.data_prep.Populate_Edge import Populate_Edge

HERE = os.path.dirname(os.path.abspath(__file__))

# 5 nodes placed at: (0,0), (1,0), (5,0), (3,4), (0,7)
# epsilon = 1.0 (shortest edge), so long edges get intermediate nodes inserted


def main(headers=False, header_fn="header.txt", populated_header_fn="populated_headers.txt"):
    input_path = os.path.join(HERE, "inputs", "example_distance_matrix.txt")
    output_path = os.path.join(HERE, "outputs")

    dp = Data_Prep(filepath=input_path, log_path=output_path, headers=headers, header_fn=header_fn)

    pe = Populate_Edge(G=dp.G, log_path=output_path, headers=headers, header_fn=header_fn, populated_header_fn=populated_header_fn)
    print(f"\nEpsilon (shortest edge): {pe.epsilon:.3f}")
    print(f"Original node count:     {pe.original_node_count}")

    dist_matrix = pe.populate_edges()

    print(f"Populated node count:    {pe.max_index}")
    print(f"Populated distance matrix shape: {dist_matrix.shape}")


main()
