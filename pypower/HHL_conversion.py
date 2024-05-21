# QAEGO (Quantum Algorithms for Electrical Grid Optimization) Research
# University of Lethbridge
# David Neufeld 
# May 2023

import numpy as np
from numpy.linalg import norm
from math import ceil, log
# linear_solvers can be installed from
# https://github.com/anedumla/quantum_linear_solvers
from linear_solvers import NumPyLinearSolver, HHL
from qiskit import Aer
from qiskit.quantum_info import Statevector

class hhl_helper:
    
    def _make_2nx2n(self, matrix, vector):
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("The matrix must be square")

        original_size = matrix.shape[0]
        if not log(original_size, 2).is_integer():
            n = 2 ** ceil(log(original_size, 2))
            #print(f"Original matrix size: {original_size}, Resized matrix size: {n}")

            # Calculate padding dimensions
            pad_height = n - matrix.shape[0]
            pad_width = n - matrix.shape[1]

            #print(f"Padding matrix: pad_height = {pad_height}, pad_width = {pad_width}")

            try:
                # Padding the matrix
                matrix = np.pad(matrix, ((0, pad_height), (0, pad_width)), mode='constant', constant_values=0)
                #print(f"Matrix after padding:\n{matrix}")
            except ValueError as e:
                print(f"Error padding matrix: {e}")
                print(f"Matrix shape: {matrix.shape}")
                print(f"Padding dimensions: ((0, {pad_height}), (0, {pad_width}))")
                raise

            # Padding the vector
            vector_pad_size = n - vector.size
            try:
                if vector.ndim == 1:
                    #print(f"Padding vector: vector_pad_size = {vector_pad_size}")
                    vector = np.pad(vector, (0, vector_pad_size), mode='constant', constant_values=0)
                elif vector.ndim == 2 and vector.shape[0] == 1:
                    #print(f"Padding 2D vector: vector_pad_size = {vector_pad_size}")
                    vector = np.pad(vector, ((0, 0), (0, vector_pad_size)), mode='constant', constant_values=0)
                else:
                    raise ValueError(f"Unexpected vector shape: {vector.shape}")
                #print(f"Vector after padding:\n{vector}")
            except ValueError as e:
                print(f"Error padding vector: {e}")
                print(f"Vector shape: {vector.shape}")
                print(
                    f"Padding dimensions: {(0, vector_pad_size) if vector.ndim == 1 else ((0, 0), (0, vector_pad_size))}")
                raise

            # Ensuring the diagonal elements are not zero
            for i in range(n):
                if matrix[i][i] == 0:
                    matrix[i][i] = 1

        return matrix, vector


    
    def _make_hermitian(self, matrix, vector):
        # this function assumes that the matrix is square
        # if the matrix is not hermitian, make it hermitian and alter the vector accordingly
        matrix_H = np.matrix(matrix).H
        if not np.array_equal(matrix, matrix_H):
            zeros = np.zeros((matrix.shape[0], matrix.shape[0]))
            matrix = np.block([[zeros, matrix_H],
                        [matrix, zeros]])
            vector_conj = np.conj(vector)
            vector = np.append(vector_conj, vector)
        return matrix, vector

    def _hhl_compatible(self, matrix, vector):
        mat = matrix.copy()
        vec = vector.copy()
        mat, vec = self._make_2nx2n(mat, vec)
        mat, vec = self._make_hermitian(mat, vec)
        return mat, vec
    
    def _new_HHL(self, ep):
        backend = Aer.get_backend('aer_simulator')
        self.hhl = HHL(ep, quantum_instance=backend)

    def run_HHL(self, matrix, vector, ep):
        self._new_HHL(ep)
        mat, vec = self._hhl_compatible(matrix, vector)
        solution = self.hhl.solve(mat, vec)
        sv = Statevector(solution.state)
        data_start = sv.data.size // 2
        data_end = data_start + vec.size
        sv_data = sv.data[data_start:data_end].real
        solution_norm = solution.euclidean_norm
        data = solution_norm * sv_data / norm(sv_data)
        vec_norm = norm(vec)
        final_data = (vec_norm * data)[0:vector.size]
        return final_data