#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The SEMFE Heat Transfer Solver
Computational Mechanics

Main Script
"""
import numpy as np
from PreProcessor import read_input_file
from Solver import assemble_global, apply_convection, apply_dirichlet
from Solver import apply_heat_flux, solve_system
from PostProcessor import plot_mesh, plot_mesh_interactive, plot_temperature_field
from PostProcessor import export_temperature_csv


# Import model info
nodes, elems, materials, k, bcs = read_input_file('chimney.semfe')

# Check Mesh Quality
plot_mesh_interactive(nodes, elems, show=True, filename='interactive_chimney.html')

# Assemble global
K = assemble_global(nodes, elems, k=k)

# Apply BCs

# Dirichlet
bc_nodes  = [node for (node, val) in bcs.get('temperature', [])]
bc_values = [val  for (node, val) in bcs.get('temperature', [])]

# Convection (Robin): (elem_id, edge_id, h, Tinf)
bc_conv = [(elem_id, edge_id, h, Tinf)
            for (elem_id, edge_id, h, Tinf) in bcs.get('convection', [])]

# Heat flux (Neumann): (elem_id, edge_id, q)
bc_heat_flux = [(elem_id, edge_id, q)
                 for (elem_id, edge_id, q) in bcs.get('heat_flux', [])]

f0 = np.zeros(nodes.shape[0])

# 1) Convection
K1, f1 = apply_convection(K, f0, nodes, elems, bc_conv)

# 2) Heat flux
f2 = apply_heat_flux(f1, nodes, elems, bc_heat_flux)

# 3) Dirichlet στο τέλος
Kmod, fmod = apply_dirichlet(K1, f2, bc_nodes, bc_values)

# Kmod, fmod = apply_dirichlet(K, np.zeros(nodes.shape[0]), bc_nodes, bc_values)
# Kmod, fmod = apply_convection(K, fmod, nodes, elems, bc_values)

#
u = solve_system(Kmod, fmod)

# Call it in main
plot_temperature_field(nodes, elems, u, filename='chimney_temperature_field.png')
export_temperature_csv(nodes, u)
