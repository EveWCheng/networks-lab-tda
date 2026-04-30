import sys
from pathlib import Path

import numpy as np

from tqdm.auto import tqdm

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

import matilda
import matilda.prototyping
import matilda.harmonic

def define_simplices():
    simplices = [[0], [1], [2], [0, 1], [0, 2], [1, 2], [3], [0, 1, 2], [0, 3], [2, 3]]
    coord_vertices = [[1, 0], [1 / 2, 1], [0, 0], [1 / 2, -1]]
    simplices = [np.array(s) for s in simplices]
    return coord_vertices,simplices

def main():
    coord_vertices,simplices = define_simplices()
    K = matilda.prototyping.FilteredSimplicialComplex(
    dimension=2,
    simplices=simplices,
    simplices_indices=[i for i in range(len(simplices))],
    appears_at=[0, 1, 2, 3, 3, 3, 4, 5, 6, 6],
)
    homology_computer = matilda.PersistentHomologyComputer()
    homology_computer.compute_persistent_homology(K, with_representatives=True, modulus=0)
    harmonic_computer = matilda.harmonic.HarmonicRepresentativesComputer(K, homology_computer)
    harmonic_computer.compute_harmonic_cycles(dim=1, verbose=3)
    print(harmonic_computer.harmonic_cycles)
    for i, id in enumerate(harmonic_computer.harmonic_cycles[1].keys()):
        print("i",i)
        print("id", id)
        for i, (key,sign) in enumerate(harmonic_computer.harmonic_cycles[1][id].items()):
            print("key",key)
            #sign is the weight
            print("sign",sign)

main()
