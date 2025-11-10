#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The SEMFE Heat Transfer Solver
Computational Mechanics

Post-processing Script
"""

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import plotly.graph_objects as go
import numpy as np
import matplotlib.tri as tri

# Assuming you already did:
# nodes, elems, materials, bcs = read_febio_file('tri_mesh_example.feb')
import sys
print(sys.executable)

def plot_mesh(nodes, elems, show=True, filename=None):
    """
    Simple plot of triangular mesh
    """
    x = nodes[:, 0]
    y = nodes[:, 1]
    triang = mtri.Triangulation(x, y, triangles=elems)
    
    plt.figure(figsize=(5,5))
    plt.triplot(triang, color='black', lw=0.8)
    plt.plot(x, y, 'ro', markersize=4)
    plt.gca().set_aspect('equal')
    plt.title('Triangular Mesh')
    if filename:
        plt.savefig(filename, dpi=200, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()
        
        


def plot_mesh_interactive(nodes, elems, show=True, filename=None):
    """
    Interactive triangular mesh plot with node indices.
    """
    x = nodes[:, 0]
    y = nodes[:, 1]

    fig = go.Figure()

    # Draw each triangle
    for tri_nodes in elems:
        tri_x = x[tri_nodes].tolist() + [x[tri_nodes[0]]]  # close loop
        tri_y = y[tri_nodes].tolist() + [y[tri_nodes[0]]]
        fig.add_trace(go.Scatter(
            x=tri_x, y=tri_y,
            mode='lines',
            line=dict(color='black'),
            showlegend=False
        ))

    # Draw nodes
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers+text',
        marker=dict(color='red', size=6),
        text=[str(i) for i in range(len(nodes))],  # node indices
        textposition='top center',
        showlegend=False
    ))

    fig.update_layout(
        title='Interactive Triangular Mesh',
        xaxis=dict(scaleanchor='y'),  # equal aspect
        yaxis=dict(scaleanchor='x'),
        width=600,
        height=600
    )

    if filename:
        fig.write_html(filename)
    if show:
        fig.show()
        

def plot_temperature_field(nodes, elems, u, cmap='plasma', filename=None, show=True):
    """
    Plot the temperature field as a filled contour (color map) on the mesh.
    nodes: Nx2 or Nx3 array of node coordinates
    elems: Mx3 array of element connectivity
    u: temperature solution vector (length N)
    """
    x = nodes[:, 0]
    y = nodes[:, 1]

    triang = tri.Triangulation(x, y, triangles=elems)

    plt.figure(figsize=(6, 5))
    contour = plt.tricontourf(triang, u, levels=50, cmap=cmap)
    plt.triplot(triang, color='k', linewidth=0.5, alpha=0.7)
    plt.gca().set_aspect('equal')
    plt.colorbar(contour, label='Temperature (°C)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Temperature Distribution')

    if filename:
        plt.savefig(filename, dpi=200, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def export_temperature_csv(nodes, u, filename='temperature_field.csv'):
    """
    Export nodal temperature results to CSV file.
    Columns: x, y, temperature
    """
    data = np.column_stack([nodes[:, 0], nodes[:, 1], u])
    np.savetxt(filename, data, delimiter=',', header='x,y,Temperature', comments='')
    return filename





