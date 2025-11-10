#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The SEMFE Heat Transfer Solver
Computational Mechanics

Pre-processing Script
"""

import numpy as np
import xml.etree.ElementTree as ET


def read_input_file(filepath):
    """
    Read FEBio XML (.feb) file and extract nodes, elements, materials, and boundary conditions.
    Returns:
      nodes: (Nnodes,3) array
      elems: (Nelements,Nnodes_per_elem) array of node indices (0-based)
      materials: dict with material properties
      bcs: dict with boundary conditions, e.g., {'temperature': [(node_id, value), ...]}
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Nodes
    nodes_el = root.find('.//Nodes')
    nodes_list = []
    for node in nodes_el.findall('node'):
        nid = int(node.attrib['id']) -1  # FEBio node IDs start at 1
        x = float(node.attrib['x'])
        y = float(node.attrib['y'])
        z = float(node.attrib.get('z', 0.0))
        nodes_list.append([x, y, z])
    nodes = np.array(nodes_list)

    # Elements
    elems_el = root.find('.//Elements')
    elems_list = []
    for elem in elems_el.findall('elem'):
        conn = [int(nid)-1 for nid in elem.text.strip().split()]  # 0-based indexing
        elems_list.append(conn)
    elems = np.array(elems_list, dtype=int)

    # Materials
    materials = {}
    for mat in root.findall('.//Material'):
        mat_id = mat.attrib.get('id', None)
        mat_name = mat.attrib.get('name', None)
        properties = {child.tag: child.text for child in mat}
        materials[mat_name or mat_id] = properties

    # Extract thermal conductivity 'k' from the first material (assuming single material)
    material_keys = list(materials.keys())
    if material_keys:
        first_mat = materials[material_keys[0]]
        k = float(first_mat.get('conductivity', 1.0)) # default 1.0 if not specified
    else:
        k = 1.0 # default
        
    # Boundary conditions (simplified: temperature, displacement)
    bcs = {'temperature': [], 'displacement': []}
    for bcset in root.findall('.//Boundary'):
        for bc in bcset:
            bc_type = bc.tag.lower()
            node = int(bc.attrib['node']) - 1
            value = float(bc.attrib['value'])
            if bc_type == 'temperature':
                bcs['temperature'].append((node, value))
            elif bc_type == 'fix':
                bcs['displacement'].append((node, value))
                
                
    bcs['heat_flux'] = []
    bcs['convection'] = []

    for hf in root.findall('.//HeatFlux/flux'):
        elem_id = int(hf.attrib['elem']) - 1
        edge_id = int(hf.attrib['edge'])
        value = float(hf.attrib['value'])
        bcs['heat_flux'].append((elem_id, edge_id, value))

    for cv in root.findall('.//Convection/conv'):
        elem_id = int(cv.attrib['elem']) - 1
        edge_id = int(cv.attrib['edge'])
        h = float(cv.attrib['h'])
        Tinf = float(cv.attrib['Tinf'])
        bcs['convection'].append((elem_id, edge_id, h, Tinf))


    return nodes, elems, materials, k, bcs

# --------------------------
# Usage example in main.py
# --------------------------
# nodes, elems, materials, bcs = read_febio_file('model.feb')
