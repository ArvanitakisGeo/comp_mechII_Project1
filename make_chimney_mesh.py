

import math
from collections import defaultdict

# ---------------------------------------------------------
# Ρύθμιση πυκνότητας πλέγματος
# ---------------------------------------------------------
NX = 2     # οριζόντιος πολλαπλασιαστής
NY = 2     # κατακόρυφος πολλαπλασιαστής

OUTER_W = 0.8
OUTER_H = 0.6

#Center of chimney
HOLE_X1, HOLE_X2 = 0.2, 0.6
HOLE_Y1, HOLE_Y2 = 0.2, 0.4

K_BRICK = 1.0      # αγωγιμότητα  δεν το χρησιμοποιουμε
H_CONV  = 25       # συναγωγή
T_INF   = 25.0     # Τ∞ για συναγωγή
T_INNER = 100.0    # Τ στο εσωτερικό τοίχωμα
T_TOP   = 30.0     # Τ στην επάνω εξωτερική πλευρά


def generate_chimney_mesh(nx=1, ny=1):
    """Structured grid σε όλο το ορθογώνιο και πετάμε το κέντρο (οπλή)."""
    n_el_x = 4 * nx
    n_el_y = 3 * ny

    dx = OUTER_W / n_el_x
    dy = OUTER_H / n_el_y

    n_nodes_x = n_el_x + 1
    n_nodes_y = n_el_y + 1

    # κόμβοι
    nodes = []
    for j in range(n_nodes_y):
        for i in range(n_nodes_x):
            nodes.append((i * dx, j * dy))

    def nid(i, j):
        return j * n_nodes_x + i

    # στοιχεία (τετράγωνα -> 2 τρίγωνα)
    elems = []
    for j in range(n_el_y):
        for i in range(n_el_x):
            xc = (i + 0.5) * dx
            yc = (j + 0.5) * dy

            # κόβω τα κελιά που πέφτουν μέσα στο άνοιγμα
            if HOLE_X1 < xc < HOLE_X2 and HOLE_Y1 < yc < HOLE_Y2:
                continue

            n1 = nid(i,     j)
            n2 = nid(i + 1, j)
            n3 = nid(i + 1, j + 1)
            n4 = nid(i,     j + 1)

            # 2 τρίγωνα
            elems.append((n1, n2, n4))
            elems.append((n2, n3, n4))

    return nodes, elems


def find_boundary_edges(nodes, elems):
    """Βρίσκει ακμές που ανήκουν μόνο σε 1 στοιχείο (σύνορα)."""
    edge_map = defaultdict(list)

    for e_idx, (n1, n2, n3) in enumerate(elems):
        tri_edges = [(n1, n2, 1),
                     (n2, n3, 2),
                     (n3, n1, 3)]
        for a, b, local_id in tri_edges:
            key = (min(a, b), max(a, b))
            edge_map[key].append((e_idx, local_id))

    boundary = []
    for (a, b), owners in edge_map.items():
        if len(owners) == 1:
            e_idx, local_id = owners[0]
            boundary.append((a, b, e_idx, local_id))

    return boundary


def classify_edges(nodes, boundary_edges):
    """
    Χωρίζει σύνορα σε:
    - bottom: y = 0        -> q = 0
    - right_ext: x = W     -> συναγωγή
    - top_ext: y = H       -> T = 30 (Dirichlet)
    - inner: εσωτερικό τοίχωμα -> T = 100 (Dirichlet)
    """
    tol = 1e-9
    bottom = []
    right_ext = []
    top_ext = []
    left_ext = []
    inner = []

    for a, b, e_idx, local in boundary_edges:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]

        if abs(y1) < tol and abs(y2) < tol:
            bottom.append((a, b, e_idx, local))
        elif abs(x1 - OUTER_W) < tol and abs(x2 - OUTER_W) < tol:
            right_ext.append((a, b, e_idx, local))
        elif abs(y1 - OUTER_H) < tol and abs(y2 - OUTER_H) < tol:
            top_ext.append((a, b, e_idx, local))
        elif abs(x1) < tol and abs(x2) < tol:
            left_ext.append((a, b, e_idx, local))
        else:
            inner.append((a, b, e_idx, local))

    return bottom, right_ext, top_ext, left_ext, inner


def cleanup_nodes(nodes, elems, bottom, right_ext, top_ext, left_ext, inner):
    """
    Πετάει κόμβους που δεν εμφανίζονται σε κανένα στοιχείο
    και ξανακάνει reindex nodes & edges.
    """
    used = set()
    for n1, n2, n3 in elems:
        used.update([n1, n2, n3])

    used_sorted = sorted(used)
    mapping = {old: new for new, old in enumerate(used_sorted)}

    new_nodes = [nodes[old] for old in used_sorted]

    def remap_edges(edge_list):
        return [(mapping[a], mapping[b], e_idx, local)
                for (a, b, e_idx, local) in edge_list]

    new_elems = [(mapping[n1], mapping[n2], mapping[n3]) for (n1, n2, n3) in elems]

    bottom = remap_edges(bottom)
    right_ext = remap_edges(right_ext)
    top_ext = remap_edges(top_ext)
    left_ext = remap_edges(left_ext)
    inner = remap_edges(inner)

    return new_nodes, new_elems, bottom, right_ext, top_ext, left_ext, inner


# ---------------------------------------------------------
# ΓΡΑΦΩ ΤΟ XML
# ---------------------------------------------------------
def write_chimney_semfe(filename, nx=1, ny=1):
    nodes, elems = generate_chimney_mesh(nx, ny)
    bnd = find_boundary_edges(nodes, elems)
    bottom, right_ext, top_ext, left_ext, inner = classify_edges(nodes, bnd)

    # καθάρισμα άχρηστων κόμβων
    nodes, elems, bottom, right_ext, top_ext, left_ext, inner = cleanup_nodes(
        nodes, elems, bottom, right_ext, top_ext, left_ext, inner
    )

    # κόμβοι εσωτερικού τοιχώματος (T = 100)
    inner_nodes = set()
    for a, b, _, _ in inner:
        inner_nodes.add(a)
        inner_nodes.add(b)

    # κόμβοι πάνω εξωτερικής πλευράς (T = 30)
    top_nodes = set()
    for a, b, _, _ in top_ext:
        top_nodes.add(a)
        top_nodes.add(b)

    with open(filename, "w", encoding="ISO-8859-1") as f:
        f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
        f.write('<SEMFE_spec>\n')
        f.write('  <Module type="heat conduction"/>\n')
        f.write('  <Globals>\n')
        f.write('    <Constants>\n')
        f.write('      <heat_capacity>2.5</heat_capacity>\n')
        f.write('    </Constants>\n')
        f.write('  </Globals>\n\n')

        # Υλικό
        f.write('  <Materials>\n')
        f.write('    <Material id="1" name="Brick">\n')
        f.write(f'      <conductivity>{K_BRICK}</conductivity>\n')
        f.write('    </Material>\n')
        f.write('  </Materials>\n\n')

        # Γεωμετρία
        f.write('  <Geometry>\n')
        f.write('    <Nodes>\n')
        for i, (x, y) in enumerate(nodes, start=1):
            f.write(f'      <node id="{i}" x="{x:.6f}" y="{y:.6f}" z="0.0"/>\n')
        f.write('    </Nodes>\n\n')

        f.write('    <Elements type="tri3" name="mesh">\n')
        for e_id, (n1, n2, n3) in enumerate(elems, start=1):
            f.write(f'      <elem id="{e_id}">{n1+1} {n2+1} {n3+1}</elem>\n')
        f.write('    </Elements>\n')
        f.write('  </Geometry>\n\n')

        # Συνοριακές συνθήκες
        f.write('  <BoundaryConditions>\n')

        # Dirichlet: εσωτερικό & πάνω
        f.write('    <Boundary>\n')
        for n in sorted(inner_nodes):
            f.write(f'      <temperature node="{n+1}" value="{T_INNER}"/>\n')
        for n in sorted(top_nodes):
            f.write(f'      <temperature node="{n+1}" value="{T_TOP}"/>\n')
        f.write('    </Boundary>\n\n')

        # Neumann: ΜΟΝΟ κάτω (q = 0)
        f.write('    <HeatFlux>\n')
        for a, b, e_idx, local in bottom:
            f.write(f'      <flux elem="{e_idx+1}" edge="{local}" value="0.0"/>\n')
        f.write('    </HeatFlux>\n\n')

        # Convection: ΜΟΝΟ δεξιά
        f.write('    <Convection>\n')
        for a, b, e_idx, local in right_ext:
            f.write(
                f'      <conv elem="{e_idx+1}" edge="{local}" '
                f'h="{H_CONV}" Tinf="{T_INF}"/>\n'
            )
        f.write('    </Convection>\n')

        f.write('  </BoundaryConditions>\n\n')

        f.write('  <Step name="step1" type="steady-state">\n')
        f.write('    <HeatSource>\n')
        f.write('    </HeatSource>\n')
        f.write('  </Step>\n')
        f.write('</SEMFE_spec>\n')

    print(f"Έφτιαξα {len(nodes)} κόμβους και {len(elems)} τριγωνικά στοιχεία.")


if __name__ == "__main__":
    write_chimney_semfe("chimney.semfe", NX, NY)
