#!/usr/bin/env python3
"""
Analyze a completed LAMMPS sticker-spacer simulation.

Metrics (v4 - with S(q) and g_12(r)):
  1. Cv (heat capacity) from energy fluctuations - phase transition indicator
  2. Sticker-spacer (1-2) inter-chain contact fraction at rc=1.0 nm - structural order parameter
  3. Sub-box density variance (Δρ/ρ) - spatial heterogeneity order parameter
  4. Cluster analysis via 1-2 cross-type contacts - network connectivity
  5. E_pair per bead from thermo - cohesive energy
  6. Static structure factor S(q) at low q - density fluctuation order parameter
  7. Radial distribution function g_12(r) - sticker-spacer structural correlations

CRITICAL PHYSICS:
- The ONLY attractive interaction is the soft potential between type 1 (sticker) 
  and type 2 (spacer) beads: pair_coeff 1 2 soft A 1 with A = -3.45 * eps, rc = 1.0 nm
- Type 1-1 (sticker-sticker) and 2-2 (spacer-spacer) are WCA (purely repulsive)
- Phase separation is driven by sticker-spacer cross contacts, NOT sticker-sticker contacts
- Contact cutoff MUST be 1.0 nm (soft potential range), NOT 5.0 nm

Previous versions (v1, v2) incorrectly measured sticker-sticker contacts at 5 nm cutoff.
This measured noise, not signal, because there is no 1-1 attraction.

Reference: Hoffmann et al., J. Mol. Biol. 2025 (sticker-spacer grammar);
           Milovanovic et al., Science 2018 (synapsin LLPS).
"""
import argparse
import json
import os
import re
import sys
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict


# Boltzmann constant in LAMMPS units nano: attogram*nm^2/(ns^2*K)
kB = 0.01380649


# ---------------------------------------------------------------------------
# Thermo parsing
# ---------------------------------------------------------------------------

def parse_thermo_from_log(log_path: str) -> dict:
    """Parse LAMMPS thermo output from production log.
    Returns dict with column names -> list of values over time.
    """
    thermo = {}
    headers = []
    in_thermo = False

    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("Step "):
                headers = line.split()
                for h in headers:
                    if h not in thermo:
                        thermo[h] = []
                in_thermo = True
                continue
            if in_thermo:
                # Skip WARNING lines that LAMMPS injects mid-thermo block
                # (e.g. "WARNING: Communication cutoff ..." between data rows)
                if line.startswith("WARNING"):
                    continue
                # End thermo block on loop summary, blank lines, or non-numeric
                if (line.startswith("Loop time") or
                    line == "" or
                    (not line[0].isdigit() and line[0] != '-')):
                    in_thermo = False
                    continue
            if in_thermo and headers:
                parts = line.split()
                if len(parts) == len(headers):
                    try:
                        for h, val in zip(headers, parts):
                            thermo[h].append(float(val))
                    except ValueError:
                        in_thermo = False
    return thermo


def compute_thermo_averages(thermo: dict, discard_frac: float = 0.2) -> dict:
    """Compute time-averaged thermo properties, discarding early fraction."""
    averages = {}
    for key, vals in thermo.items():
        if key == "Step" or not vals:
            continue
        arr = np.array(vals)
        n_discard = int(len(arr) * discard_frac)
        equil = arr[n_discard:]
        if len(equil) > 0:
            averages[key] = {
                "mean": float(np.mean(equil)),
                "std": float(np.std(equil)),
                "n_samples": len(equil)
            }
    return averages


def compute_Cv(thermo: dict, T: float, n_atoms: int, discard_frac: float = 0.2) -> dict:
    """Compute heat capacity from energy fluctuations.
    
    Cv = var(E_total) / (kB * T^2)
    Cv_per_bead = Cv / n_atoms
    
    Returns dict with Cv, Cv_per_bead, and metadata.
    """
    # Find E_total column (may be named "TotEng", "E_total", "Etot", etc.)
    e_keys = [k for k in thermo.keys() if k.lower() in 
              ("toteng", "e_total", "etot", "total_energy", "energy")]
    if not e_keys:
        return {"Cv": None, "Cv_per_bead": None, "error": "E_total not found in thermo"}
    
    e_key = e_keys[0]
    E_total = np.array(thermo[e_key])
    n_discard = int(len(E_total) * discard_frac)
    E_equil = E_total[n_discard:]
    
    if len(E_equil) < 10:
        return {"Cv": None, "Cv_per_bead": None, "error": "insufficient equilibrated samples"}
    
    var_E = np.var(E_equil)
    Cv = var_E / (kB * T**2)
    Cv_per_bead = Cv / n_atoms
    
    return {
        "Cv": float(Cv),
        "Cv_per_bead": float(Cv_per_bead),
        "var_E_total": float(var_E),
        "mean_E_total": float(np.mean(E_equil)),
        "std_E_total": float(np.std(E_equil)),
        "n_samples": len(E_equil),
        "T": T,
        "kB": kB,
        "source_column": e_key
    }


# ---------------------------------------------------------------------------
# Trajectory reading (last N frames, memory-efficient)
# ---------------------------------------------------------------------------

def parse_last_frames(traj_path: str, max_frames: int = 5):
    """Read the last N frames from a LAMMPS trajectory.

    Returns list of dicts with keys: timestep, box, atoms (Nx8 array:
    id, type, x, y, z, ix, iy, iz).
    """
    # Index frame offsets
    offsets = []
    with open(traj_path) as f:
        pos = 0
        for line in f:
            if line.startswith("ITEM: TIMESTEP"):
                offsets.append(pos)
            pos += len(line)

    if not offsets:
        return []

    use = offsets[-max_frames:]
    frames = []

    with open(traj_path) as f:
        f.seek(use[0])
        content = f.read()

    # Split into per-frame blocks
    blocks = content.split("ITEM: TIMESTEP\n")
    blocks = [b for b in blocks if b.strip()]

    for block in blocks[-max_frames:]:
        lines = block.strip().split("\n")
        if len(lines) < 10:
            continue

        timestep = int(lines[0])
        n_atoms = int(lines[2])  # line after NUMBER OF ATOMS

        # Box bounds (3 lines after BOX BOUNDS header)
        box = []
        for i in range(4, 7):
            lo, hi = map(float, lines[i].split()[:2])
            box.append([lo, hi])

        # Atom header and data
        atom_header = lines[7]
        cols = atom_header.replace("ITEM: ATOMS ", "").split()

        # Build column index map
        col_map = {c: i for i, c in enumerate(cols)}

        atoms = []
        for i in range(8, min(8 + n_atoms, len(lines))):
            parts = lines[i].split()
            if len(parts) >= len(cols):
                try:
                    atoms.append([float(x) for x in parts])
                except ValueError:
                    continue

        if atoms:
            frames.append({
                "timestep": timestep,
                "box": box,
                "col_map": col_map,
                "atoms": np.array(atoms),
                "n_atoms": n_atoms
            })

    return frames


# ---------------------------------------------------------------------------
# Metric 1: Sub-box density variance
# ---------------------------------------------------------------------------

def compute_density_variance(frame, n_sub=7):
    """Divide box into n_sub^3 sub-volumes. Compute density in each.
    Return normalized variance: std(rho_local) / mean(rho_local).

    High values indicate spatial heterogeneity (phase separation).
    Low values (~1/sqrt(N_per_subbox)) indicate homogeneity.
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]

    # Get wrapped coordinates
    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))

    x = atoms[:, xi]
    y = atoms[:, yi]
    z = atoms[:, zi]

    box_lo = np.array([b[0] for b in box])
    box_hi = np.array([b[1] for b in box])
    box_L = box_hi - box_lo

    # Wrap coordinates into box (in case of unwrapped)
    x_wrap = box_lo[0] + (x - box_lo[0]) % box_L[0]
    y_wrap = box_lo[1] + (y - box_lo[1]) % box_L[1]
    z_wrap = box_lo[2] + (z - box_lo[2]) % box_L[2]

    # Assign to sub-boxes
    ix = np.clip(((x_wrap - box_lo[0]) / box_L[0] * n_sub).astype(int), 0, n_sub - 1)
    iy = np.clip(((y_wrap - box_lo[1]) / box_L[1] * n_sub).astype(int), 0, n_sub - 1)
    iz = np.clip(((z_wrap - box_lo[2]) / box_L[2] * n_sub).astype(int), 0, n_sub - 1)

    # Count beads in each sub-box
    counts = np.zeros((n_sub, n_sub, n_sub), dtype=float)
    for a, b, c in zip(ix, iy, iz):
        counts[a, b, c] += 1

    sub_vol = (box_L[0] / n_sub) * (box_L[1] / n_sub) * (box_L[2] / n_sub)
    densities = counts / sub_vol

    mean_rho = np.mean(densities)
    if mean_rho == 0:
        return 0.0

    # Normalized density fluctuation (coefficient of variation)
    return float(np.std(densities) / mean_rho)


def compute_density_variance_stickers_only(frame, n_sub=7):
    """Same as above but only for sticker beads (type 1).
    Sticker spatial distribution is the direct indicator of condensate formation.
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]

    type_col = col_map.get("type", 1)
    stickers = atoms[atoms[:, type_col] == 1.0]
    if len(stickers) == 0:
        return 0.0

    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))

    x = stickers[:, xi]
    y = stickers[:, yi]
    z = stickers[:, zi]

    box_lo = np.array([b[0] for b in box])
    box_hi = np.array([b[1] for b in box])
    box_L = box_hi - box_lo

    x_wrap = box_lo[0] + (x - box_lo[0]) % box_L[0]
    y_wrap = box_lo[1] + (y - box_lo[1]) % box_L[1]
    z_wrap = box_lo[2] + (z - box_lo[2]) % box_L[2]

    ix = np.clip(((x_wrap - box_lo[0]) / box_L[0] * n_sub).astype(int), 0, n_sub - 1)
    iy = np.clip(((y_wrap - box_lo[1]) / box_L[1] * n_sub).astype(int), 0, n_sub - 1)
    iz = np.clip(((z_wrap - box_lo[2]) / box_L[2] * n_sub).astype(int), 0, n_sub - 1)

    counts = np.zeros((n_sub, n_sub, n_sub), dtype=float)
    for a, b, c in zip(ix, iy, iz):
        counts[a, b, c] += 1

    sub_vol = (box_L[0] / n_sub) * (box_L[1] / n_sub) * (box_L[2] / n_sub)
    densities = counts / sub_vol
    mean_rho = np.mean(densities)
    if mean_rho == 0:
        return 0.0
    return float(np.std(densities) / mean_rho)


# ---------------------------------------------------------------------------
# Metric 2: Sticker-spacer (1-2) inter-chain contact fraction
# ---------------------------------------------------------------------------

def compute_cross_contacts(frame, chain_length, contact_cutoff=1.0):
    """Compute the fraction of sticker beads (type 1) that have at least one
    inter-chain contact with a spacer bead (type 2) within contact_cutoff.

    Also computes the average number of inter-chain 1-2 contacts per sticker
    (coordination number).

    This is the CORRECT order parameter: the soft potential between 1-2 pairs
    is the ONLY attractive interaction in the model.

    contact_cutoff = 1.0 nm matches the soft potential range (rc = 1.0 nm).
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]

    type_col = col_map.get("type", 1)
    id_col = col_map.get("id", 0)
    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))

    # Separate stickers (type 1) and spacers (type 2)
    stickers = atoms[atoms[:, type_col] == 1.0]
    spacers = atoms[atoms[:, type_col] == 2.0]
    
    if len(stickers) == 0 or len(spacers) == 0:
        return {"contact_fraction": None, "coordination_mean": None, "coordination_std": None, "n_stickers": 0}

    sticker_coords = stickers[:, [xi, yi, zi]]
    spacer_coords = spacers[:, [xi, yi, zi]]
    
    sticker_ids = stickers[:, id_col].astype(int)
    spacer_ids = spacers[:, id_col].astype(int)
    
    sticker_chain_ids = (sticker_ids - 1) // chain_length
    spacer_chain_ids = (spacer_ids - 1) // chain_length

    box_L = np.array([b[1] - b[0] for b in box])
    n_stickers = len(sticker_coords)
    cutoff_sq = contact_cutoff ** 2

    # Track contacts: has_contact[i] = True if sticker i has at least one inter-chain 1-2 contact
    has_contact = np.zeros(n_stickers, dtype=bool)
    contact_counts = np.zeros(n_stickers, dtype=int)

    # Use cell list for efficiency
    cell_size = contact_cutoff
    n_cells = np.maximum((box_L / cell_size).astype(int), 1)

    # Wrap coordinates
    sticker_wrapped = sticker_coords.copy()
    spacer_wrapped = spacer_coords.copy()
    for d in range(3):
        sticker_wrapped[:, d] = (sticker_coords[:, d] - box[d][0]) % box_L[d]
        spacer_wrapped[:, d] = (spacer_coords[:, d] - box[d][0]) % box_L[d]

    # Build cell lists for stickers and spacers
    def get_cell_idx(coords, n_cells):
        cell_idx = np.zeros(len(coords), dtype=int)
        for d in range(3):
            ci = np.clip((coords[:, d] / cell_size).astype(int), 0, n_cells[d] - 1)
            if d == 0:
                cell_idx = ci
            elif d == 1:
                cell_idx = cell_idx * n_cells[1] + ci
            else:
                cell_idx = cell_idx * n_cells[2] + ci
        return cell_idx

    sticker_cell_idx = get_cell_idx(sticker_wrapped, n_cells)
    spacer_cell_idx = get_cell_idx(spacer_wrapped, n_cells)

    sticker_cells = defaultdict(list)
    spacer_cells = defaultdict(list)
    for i, c in enumerate(sticker_cell_idx):
        sticker_cells[c].append(i)
    for i, c in enumerate(spacer_cell_idx):
        spacer_cells[c].append(i)

    # Iterate over cell pairs
    for cx in range(n_cells[0]):
        for cy in range(n_cells[1]):
            for cz in range(n_cells[2]):
                c0 = cx * n_cells[1] * n_cells[2] + cy * n_cells[2] + cz
                if c0 not in sticker_cells:
                    continue

                # Check 27 neighbors (including self) for spacers
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        for dz in [-1, 0, 1]:
                            nx = (cx + dx) % n_cells[0]
                            ny = (cy + dy) % n_cells[1]
                            nz = (cz + dz) % n_cells[2]
                            c1 = nx * n_cells[1] * n_cells[2] + ny * n_cells[2] + nz
                            if c1 not in spacer_cells:
                                continue

                            # Check all sticker-spacer pairs in these cells
                            for i in sticker_cells[c0]:
                                sticker_chain = sticker_chain_ids[i]
                                for j in spacer_cells[c1]:
                                    spacer_chain = spacer_chain_ids[j]
                                    # Only count inter-chain contacts
                                    if sticker_chain == spacer_chain:
                                        continue

                                    delta = sticker_coords[i] - spacer_coords[j]
                                    delta -= box_L * np.round(delta / box_L)
                                    dsq = np.sum(delta ** 2)

                                    if dsq < cutoff_sq:
                                        has_contact[i] = True
                                        contact_counts[i] += 1

    frac = float(np.mean(has_contact))
    coord_mean = float(np.mean(contact_counts))
    coord_std = float(np.std(contact_counts))

    return {
        "contact_fraction": frac,
        "coordination_mean": coord_mean,
        "coordination_std": coord_std,
        "n_stickers": int(n_stickers)
    }


# ---------------------------------------------------------------------------
# Metric 3: Cluster analysis (contact-based via 1-2 cross-type contacts)
# ---------------------------------------------------------------------------

def compute_cluster_fraction_cross_contact(frame, chain_length, contact_cutoff=1.0):
    """Build clusters via sticker-spacer (1-2) inter-chain contacts.
    Two chains are in the same cluster if they share at least one
    inter-chain 1-2 contact. Returns largest cluster / total chains.

    This measures associative network connectivity through the actual
    attractive interaction (1-2 soft potential), which is the defining
    feature of sticker-spacer LLPS.
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]

    type_col = col_map.get("type", 1)
    id_col = col_map.get("id", 0)
    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))

    # Get all atoms and their chain assignments
    all_coords = atoms[:, [xi, yi, zi]]
    all_ids = atoms[:, id_col].astype(int)
    all_chain_ids = (all_ids - 1) // chain_length
    all_types = atoms[:, type_col]

    unique_chains = np.unique(all_chain_ids)
    n_chains = len(unique_chains)
    chain_to_idx = {c: i for i, c in enumerate(unique_chains)}

    box_L = np.array([b[1] - b[0] for b in box])
    cutoff_sq = contact_cutoff ** 2

    # Find inter-chain 1-2 contacts
    connected_pairs = set()

    # Cell list
    cell_size = contact_cutoff
    n_cells = np.maximum((box_L / cell_size).astype(int), 1)

    wrapped = all_coords.copy()
    for d in range(3):
        wrapped[:, d] = (all_coords[:, d] - box[d][0]) % box_L[d]

    cell_idx = np.zeros(len(all_coords), dtype=int)
    for d in range(3):
        ci = np.clip((wrapped[:, d] / cell_size).astype(int), 0, n_cells[d] - 1)
        if d == 0:
            cell_idx = ci
        elif d == 1:
            cell_idx = cell_idx * n_cells[1] + ci
        else:
            cell_idx = cell_idx * n_cells[2] + ci

    cells = defaultdict(list)
    for i, c in enumerate(cell_idx):
        cells[c].append(i)

    for cx in range(n_cells[0]):
        for cy in range(n_cells[1]):
            for cz in range(n_cells[2]):
                c0 = cx * n_cells[1] * n_cells[2] + cy * n_cells[2] + cz
                if c0 not in cells:
                    continue
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        for dz in [-1, 0, 1]:
                            nx = (cx + dx) % n_cells[0]
                            ny = (cy + dy) % n_cells[1]
                            nz = (cz + dz) % n_cells[2]
                            c1 = nx * n_cells[1] * n_cells[2] + ny * n_cells[2] + nz
                            if c1 not in cells:
                                continue
                            for i in cells[c0]:
                                for j in cells[c1]:
                                    if j <= i:
                                        continue
                                    # Only count 1-2 cross-type contacts
                                    if not ((all_types[i] == 1.0 and all_types[j] == 2.0) or
                                            (all_types[i] == 2.0 and all_types[j] == 1.0)):
                                        continue
                                    ci_chain = all_chain_ids[i]
                                    cj_chain = all_chain_ids[j]
                                    if ci_chain == cj_chain:
                                        continue
                                    delta = all_coords[i] - all_coords[j]
                                    delta -= box_L * np.round(delta / box_L)
                                    if np.sum(delta ** 2) < cutoff_sq:
                                        a = chain_to_idx[ci_chain]
                                        b = chain_to_idx[cj_chain]
                                        connected_pairs.add((min(a, b), max(a, b)))

    # Union-find on chains
    parent = list(range(n_chains))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b

    for a, b in connected_pairs:
        union(a, b)

    roots = [find(i) for i in range(n_chains)]
    cluster_sizes = Counter(roots)
    largest = max(cluster_sizes.values()) if cluster_sizes else 0
    n_clusters = len(cluster_sizes)

    return {
        "largest_cluster_frac": float(largest / n_chains) if n_chains > 0 else 0.0,
        "n_clusters": n_clusters,
        "n_chains": n_chains
    }


# ---------------------------------------------------------------------------
# Metric 4: Static structure factor S(q)
# ---------------------------------------------------------------------------

def compute_Sq(frame, max_n=20):
    """Compute static structure factor S(q) at low q.
    
    S(q) = (1/N) * |sum_j exp(-i q.r_j)|^2
    
    Uses isotropic q vectors: q = 2*pi*n/L for n = 1, 2, ..., max_n
    where L is the box length (assumed cubic).
    
    A rising S(q->0) signals growing density fluctuations near LLPS.
    For subcritical systems (A4B20), S(q) should be flat.
    For transitioning systems (A8B16), S(q) should show enhancement at low q.
    
    Returns dict with q_magnitudes (nm^-1) and S_q values.
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]
    
    # Get coordinates (all beads)
    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))
    
    coords = atoms[:, [xi, yi, zi]]
    n_atoms = len(coords)
    
    if n_atoms == 0:
        return {"q_magnitudes": [], "S_q": [], "error": "no atoms"}
    
    # Box dimensions (assume cubic)
    box_L = np.array([b[1] - b[0] for b in box])
    L = np.mean(box_L)  # Use average for isotropic approximation
    
    # Wrap coordinates into box
    box_lo = np.array([b[0] for b in box])
    coords_wrapped = coords.copy()
    for d in range(3):
        coords_wrapped[:, d] = (coords[:, d] - box_lo[d]) % box_L[d]
    
    # Generate q vectors: q = 2*pi*n/L for n = 1, 2, ..., max_n
    # Use isotropic approximation: average over all directions
    q_magnitudes = []
    S_q_values = []
    
    for n in range(1, max_n + 1):
        q_mag = 2 * np.pi * n / L  # magnitude in nm^-1
        
        # Average over multiple q directions for better statistics
        # Use principal directions: (1,0,0), (0,1,0), (0,0,1), and diagonal
        q_dirs = [
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([1, 1, 0]) / np.sqrt(2),
            np.array([1, 0, 1]) / np.sqrt(2),
            np.array([0, 1, 1]) / np.sqrt(2),
            np.array([1, 1, 1]) / np.sqrt(3),
        ]
        
        S_q_dir = []
        for q_dir in q_dirs:
            q_vec = q_mag * q_dir
            
            # Compute sum_j exp(-i q.r_j) = sum_j [cos(q.r_j) - i*sin(q.r_j)]
            q_dot_r = np.dot(coords_wrapped, q_vec)
            sum_cos = np.sum(np.cos(q_dot_r))
            sum_sin = np.sum(np.sin(q_dot_r))
            
            # |sum|^2 = (sum_cos)^2 + (sum_sin)^2
            S_q_val = (sum_cos**2 + sum_sin**2) / n_atoms
            S_q_dir.append(S_q_val)
        
        # Average over directions
        S_q_mean = np.mean(S_q_dir)
        q_magnitudes.append(q_mag)
        S_q_values.append(S_q_mean)
    
    return {
        "q_magnitudes": [float(q) for q in q_magnitudes],
        "S_q": [float(s) for s in S_q_values],
        "n_directions": len(q_dirs),
        "L_box_nm": float(L)
    }


# ---------------------------------------------------------------------------
# Metric 5: Radial distribution function g_12(r)
# ---------------------------------------------------------------------------

def compute_g12r(frame, r_max=5.0, dr=0.05):
    """Compute radial distribution function g_12(r) between type 1 (sticker) 
    and type 2 (spacer) beads.
    
    g(r) measures the probability of finding a spacer bead at distance r 
    from a sticker bead, normalized by ideal gas density.
    
    Growth/sharpening of the first peak at contact (r ~ 1.0 nm) indicates 
    structural ordering and enhanced sticker-spacer correlations.
    
    Parameters:
        r_max: maximum distance in nm (default: 5.0)
        dr: bin width in nm (default: 0.05)
    
    Returns dict with r_bins (nm) and g_r values.
    """
    atoms = frame["atoms"]
    col_map = frame["col_map"]
    box = frame["box"]
    
    type_col = col_map.get("type", 1)
    xi = col_map.get("x", col_map.get("xu", col_map.get("xs", 2)))
    yi = col_map.get("y", col_map.get("yu", col_map.get("ys", 3)))
    zi = col_map.get("z", col_map.get("zu", col_map.get("zs", 4)))
    
    # Separate stickers (type 1) and spacers (type 2)
    stickers = atoms[atoms[:, type_col] == 1.0]
    spacers = atoms[atoms[:, type_col] == 2.0]
    
    if len(stickers) == 0 or len(spacers) == 0:
        return {"r_bins": [], "g_r": [], "error": "missing atom types"}
    
    sticker_coords = stickers[:, [xi, yi, zi]]
    spacer_coords = spacers[:, [xi, yi, zi]]
    
    n_stickers = len(sticker_coords)
    n_spacers = len(spacer_coords)
    
    # Box dimensions
    box_L = np.array([b[1] - b[0] for b in box])
    box_lo = np.array([b[0] for b in box])
    V = np.prod(box_L)  # box volume
    
    # Wrap coordinates
    sticker_wrapped = sticker_coords.copy()
    spacer_wrapped = spacer_coords.copy()
    for d in range(3):
        sticker_wrapped[:, d] = (sticker_coords[:, d] - box_lo[d]) % box_L[d]
        spacer_wrapped[:, d] = (spacer_coords[:, d] - box_lo[d]) % box_L[d]
    
    # Set up bins
    n_bins = int(r_max / dr)
    r_bins = np.arange(0, r_max, dr) + 0.5 * dr  # bin centers
    histogram = np.zeros(n_bins, dtype=float)
    
    # Compute distances between all sticker-spacer pairs
    # Use cell list for efficiency
    cell_size = min(r_max, np.min(box_L) / 2)
    n_cells = np.maximum((box_L / cell_size).astype(int), 1)
    
    def get_cell_idx(coords, n_cells):
        cell_idx = np.zeros(len(coords), dtype=int)
        for d in range(3):
            ci = np.clip((coords[:, d] / cell_size).astype(int), 0, n_cells[d] - 1)
            if d == 0:
                cell_idx = ci
            elif d == 1:
                cell_idx = cell_idx * n_cells[1] + ci
            else:
                cell_idx = cell_idx * n_cells[2] + ci
        return cell_idx
    
    sticker_cell_idx = get_cell_idx(sticker_wrapped, n_cells)
    spacer_cell_idx = get_cell_idx(spacer_wrapped, n_cells)
    
    sticker_cells = defaultdict(list)
    spacer_cells = defaultdict(list)
    for i, c in enumerate(sticker_cell_idx):
        sticker_cells[c].append(i)
    for i, c in enumerate(spacer_cell_idx):
        spacer_cells[c].append(i)
    
    # Iterate over cell pairs
    for cx in range(n_cells[0]):
        for cy in range(n_cells[1]):
            for cz in range(n_cells[2]):
                c0 = cx * n_cells[1] * n_cells[2] + cy * n_cells[2] + cz
                if c0 not in sticker_cells:
                    continue
                
                # Check 27 neighbors (including self) for spacers
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        for dz in [-1, 0, 1]:
                            nx = (cx + dx) % n_cells[0]
                            ny = (cy + dy) % n_cells[1]
                            nz = (cz + dz) % n_cells[2]
                            c1 = nx * n_cells[1] * n_cells[2] + ny * n_cells[2] + nz
                            if c1 not in spacer_cells:
                                continue
                            
                            # Check all sticker-spacer pairs in these cells
                            for i in sticker_cells[c0]:
                                for j in spacer_cells[c1]:
                                    delta = sticker_wrapped[i] - spacer_wrapped[j]
                                    # Minimum image convention
                                    delta -= box_L * np.round(delta / box_L)
                                    r = np.linalg.norm(delta)
                                    
                                    if r < r_max:
                                        bin_idx = int(r / dr)
                                        if bin_idx < n_bins:
                                            histogram[bin_idx] += 1
    
    # Normalize by ideal gas density
    # g(r) = (V / (N1 * N2)) * (histogram(r) / (4*pi*r^2*dr))
    g_r = np.zeros(n_bins)
    for i in range(n_bins):
        r = r_bins[i]
        if r > 0:
            shell_vol = 4 * np.pi * r**2 * dr
            ideal_density = n_spacers / V
            n_observed = histogram[i]
            # Normalize: g(r) = (observed density) / (ideal density)
            # observed density = n_observed / (N1 * shell_vol)
            # ideal density = N2 / V
            # g(r) = (n_observed * V) / (N1 * N2 * shell_vol)
            g_r[i] = (n_observed * V) / (n_stickers * n_spacers * shell_vol)
        else:
            g_r[i] = 0.0
    
    return {
        "r_bins": [float(r) for r in r_bins],
        "g_r": [float(g) for g in g_r],
        "n_stickers": n_stickers,
        "n_spacers": n_spacers,
        "r_max_nm": r_max,
        "dr_nm": dr
    }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_sim_params(sim_dir_name: str) -> dict:
    """Extract parameters from directory name like sim_038_E5_T325_A4B20."""
    m = re.match(r'sim_(\d+)_E(\d+)_T(\d+)_A(\d+)B(\d+)', sim_dir_name)
    if m:
        return {
            "sim_id": m.group(1),
            "eps": int(m.group(2)),
            "temp": int(m.group(3)),
            "arch_a": int(m.group(4)),
            "arch_b": int(m.group(5)),
            "chain_length": int(m.group(4)) + int(m.group(5))
        }
    return {}


def extract_rg(thermo: dict) -> dict:
    """Extract radius of gyration if present in thermo output."""
    rg_keys = [k for k in thermo if "gyrat" in k.lower() or k.lower() in
               ("c_rg", "c_gyration", "v_rg")]
    if rg_keys:
        key = rg_keys[0]
        vals = np.array(thermo[key])
        n_discard = int(len(vals) * 0.2)
        equil = vals[n_discard:]
        return {
            "rg_mean": float(np.mean(equil)),
            "rg_std": float(np.std(equil)),
            "rg_source": key
        }
    return {"rg_mean": None, "rg_source": "not in thermo"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Analyze LAMMPS sim (v4 - with S(q) and g_12(r))")
    parser.add_argument("--sim-dir", required=True,
                        help="Path to collected sim directory")
    parser.add_argument("--prd-log", required=True,
                        help="Path to production log")
    parser.add_argument("--trajectory", required=True,
                        help="Path to production trajectory (.lammpstrj)")
    parser.add_argument("--output", required=True,
                        help="Output JSON path")
    parser.add_argument("--n-frames", type=int, default=5,
                        help="Number of final frames to analyze")
    parser.add_argument("--n-sub", type=int, default=7,
                        help="Number of sub-boxes per dimension for density variance")
    parser.add_argument("--contact-cutoff", type=float, default=1.0,
                        help="Sticker-spacer (1-2) contact cutoff in nm (default: 1.0 = soft potential range)")
    args = parser.parse_args()

    sim_name = os.path.basename(args.sim_dir.rstrip("/"))
    params = parse_sim_params(sim_name)
    chain_length = params.get("chain_length", 24)
    T = params.get("temp", 250)
    n_atoms = 12000  # standard for all sims

    print(f"Analyzing {sim_name} (chain_length={chain_length}, T={T}K)...")
    print(f"  Prd log: {args.prd_log}")
    print(f"  Trajectory: {args.trajectory}")
    print(f"  Contact cutoff: {args.contact_cutoff} nm (1-2 cross-type)")

    # 1. Parse thermo
    print("  Parsing thermo data...")
    thermo = parse_thermo_from_log(args.prd_log)
    n_steps = len(thermo.get("Step", []))
    print(f"  Found {n_steps} thermo samples")

    averages = compute_thermo_averages(thermo)

    # Cv from energy fluctuations
    print("  Computing Cv from energy fluctuations...")
    cv_result = compute_Cv(thermo, T, n_atoms)
    if cv_result.get("Cv") is not None:
        print(f"    Cv = {cv_result['Cv']:.2e}, Cv_per_bead = {cv_result['Cv_per_bead']:.2e}")

    # E_pair per bead
    e_pair = averages.get("E_pair", {})
    e_pair_per_bead = None
    if e_pair and "mean" in e_pair:
        e_pair_per_bead = e_pair["mean"] / n_atoms

    # 2. Rg
    rg = extract_rg(thermo)

    # 3. Trajectory-based metrics
    traj_size_mb = os.path.getsize(args.trajectory) / (1024 * 1024)
    print(f"  Trajectory: {traj_size_mb:.0f} MB")

    n_frames_to_use = args.n_frames
    if traj_size_mb > 200:
        n_frames_to_use = min(3, args.n_frames)
        print(f"  Large trajectory, using {n_frames_to_use} frames")

    print(f"  Reading last {n_frames_to_use} frames...")
    frames = parse_last_frames(args.trajectory, max_frames=n_frames_to_use)
    print(f"  Got {len(frames)} frames")

    # Compute metrics over frames and average
    density_var_all = []
    density_var_sticker = []
    contact_results = []
    cluster_results = []
    sq_results = []
    g12r_results = []

    for i, frame in enumerate(frames):
        print(f"  Frame {i+1}/{len(frames)} (timestep {frame['timestep']})...")

        # Sub-box density variance (all beads)
        dv_all = compute_density_variance(frame, n_sub=args.n_sub)
        density_var_all.append(dv_all)

        # Sub-box density variance (stickers only)
        dv_stk = compute_density_variance_stickers_only(frame, n_sub=args.n_sub)
        density_var_sticker.append(dv_stk)

        # Sticker-spacer cross contacts
        contacts = compute_cross_contacts(
            frame, chain_length, contact_cutoff=args.contact_cutoff)
        contact_results.append(contacts)

        # Cluster analysis via 1-2 contacts
        clusters = compute_cluster_fraction_cross_contact(
            frame, chain_length, contact_cutoff=args.contact_cutoff)
        cluster_results.append(clusters)

        # Static structure factor S(q)
        sq = compute_Sq(frame, max_n=20)
        sq_results.append(sq)

        # Radial distribution function g_12(r)
        g12r = compute_g12r(frame, r_max=5.0, dr=0.05)
        g12r_results.append(g12r)

    # Average metrics
    def safe_mean(vals):
        clean = [v for v in vals if v is not None]
        return float(np.mean(clean)) if clean else None

    def safe_std(vals):
        clean = [v for v in vals if v is not None]
        return float(np.std(clean)) if clean else None

    density_var_all_mean = safe_mean(density_var_all)
    density_var_sticker_mean = safe_mean(density_var_sticker)

    contact_frac_vals = [c.get("contact_fraction") for c in contact_results]
    coord_vals = [c.get("coordination_mean") for c in contact_results]
    cluster_frac_vals = [c.get("largest_cluster_frac") for c in cluster_results]
    n_cluster_vals = [c.get("n_clusters") for c in cluster_results]

    # Average S(q) over frames (element-wise average of arrays)
    sq_q_mags = sq_results[0].get("q_magnitudes", []) if sq_results else []
    sq_avg = None
    if sq_q_mags and all("S_q" in sq for sq in sq_results if sq.get("S_q")):
        sq_arrays = [np.array(sq.get("S_q", [])) for sq in sq_results if sq.get("S_q")]
        if sq_arrays and len(sq_arrays[0]) > 0:
            sq_avg = np.mean(sq_arrays, axis=0).tolist()
            sq_avg = [float(s) for s in sq_avg]

    # Average g_12(r) over frames (element-wise average of arrays)
    g12r_r_bins = g12r_results[0].get("r_bins", []) if g12r_results else []
    g12r_avg = None
    if g12r_r_bins and all("g_r" in g for g in g12r_results if g.get("g_r")):
        g12r_arrays = [np.array(g.get("g_r", [])) for g in g12r_results if g.get("g_r")]
        if g12r_arrays and len(g12r_arrays[0]) > 0:
            g12r_avg = np.mean(g12r_arrays, axis=0).tolist()
            g12r_avg = [float(g) for g in g12r_avg]

    # Assemble output
    metrics = {
        "sim_id": params.get("sim_id"),
        "eps": params.get("eps"),
        "temp": params.get("temp"),
        "arch_a": params.get("arch_a"),
        "arch_b": params.get("arch_b"),
        "chain_length": chain_length,

        # Thermo
        "thermo_averages": averages,
        "e_pair_per_bead": e_pair_per_bead,
        "Cv": cv_result,
        "rg": rg,

        # Density variance (spatial heterogeneity)
        "density_variance_all": {
            "mean": density_var_all_mean,
            "std": safe_std(density_var_all),
            "description": "CV of sub-box bead density (all types), n_sub={}".format(args.n_sub)
        },
        "density_variance_stickers": {
            "mean": density_var_sticker_mean,
            "std": safe_std(density_var_sticker),
            "description": "CV of sub-box sticker density, n_sub={}".format(args.n_sub)
        },

        # Sticker-spacer cross contacts (CORRECT order parameter)
        "cross_contacts": {
            "contact_fraction_mean": safe_mean(contact_frac_vals),
            "contact_fraction_std": safe_std(contact_frac_vals),
            "coordination_mean": safe_mean(coord_vals),
            "coordination_std": safe_std(coord_vals),
            "n_stickers": contact_results[0].get("n_stickers") if contact_results else None,
            "cutoff_nm": args.contact_cutoff,
            "description": "Fraction of stickers with inter-chain 1-2 contacts within cutoff (soft potential range)"
        },

        # Cluster analysis via 1-2 contacts
        "cluster": {
            "largest_cluster_frac_mean": safe_mean(cluster_frac_vals),
            "largest_cluster_frac_std": safe_std(cluster_frac_vals),
            "n_clusters_mean": safe_mean(n_cluster_vals),
            "n_clusters_std": safe_std(n_cluster_vals),
            "description": "Contact-based chain clustering via sticker-spacer (1-2) cross-type contacts"
        },

        # Static structure factor S(q)
        "Sq": {
            "q_magnitudes_nm_inv": sq_q_mags,
            "S_q_mean": sq_avg,
            "n_frames": len(sq_results),
            "description": "Static structure factor S(q) at low q. Rising S(q->0) signals density fluctuations near LLPS."
        },

        # Radial distribution function g_12(r)
        "g12r": {
            "r_bins_nm": g12r_r_bins,
            "g_r_mean": g12r_avg,
            "n_frames": len(g12r_results),
            "r_max_nm": 5.0,
            "dr_nm": 0.05,
            "description": "Radial distribution function between type 1 (sticker) and type 2 (spacer) beads. Growth/sharpening of first peak indicates structural ordering."
        },

        "n_thermo_samples": n_steps,
        "n_frames_analyzed": len(frames),
        "analysis_version": "pipeline_v4"
    }

    # Write output
    with open(args.output, "w") as f:
        json.dump(metrics, f, indent=2)

    # Summary
    print(f"\n  === Results for {sim_name} ===")
    print(f"  eps={params.get('eps')}  T={params.get('temp')}  arch=A{params.get('arch_a')}B{params.get('arch_b')}")
    if cv_result.get("Cv_per_bead") is not None:
        print(f"  Cv_per_bead       = {cv_result['Cv_per_bead']:.2e}")
    print(f"  E_pair/bead         = {e_pair_per_bead:.3f}" if e_pair_per_bead else "  E_pair/bead = N/A")
    print(f"  density_var (all)   = {density_var_all_mean:.4f}" if density_var_all_mean else "  density_var (all) = N/A")
    print(f"  density_var (stick) = {density_var_sticker_mean:.4f}" if density_var_sticker_mean else "  density_var (stick) = N/A")
    cf = safe_mean(contact_frac_vals)
    print(f"  cross_contact_frac  = {cf:.4f}" if cf else "  cross_contact_frac = N/A")
    coord = safe_mean(coord_vals)
    print(f"  coordination        = {coord:.2f}" if coord else "  coordination = N/A")
    lcf = safe_mean(cluster_frac_vals)
    print(f"  largest_cluster     = {lcf:.4f}" if lcf else "  largest_cluster = N/A")
    nc = safe_mean(n_cluster_vals)
    print(f"  n_clusters          = {nc:.1f}" if nc else "  n_clusters = N/A")
    if sq_avg and len(sq_avg) > 0:
        sq0 = sq_avg[0] if sq_q_mags else None
        print(f"  S(q->0)            = {sq0:.4f}" if sq0 else "  S(q->0) = N/A")
    if g12r_avg and len(g12r_avg) > 0:
        # Find peak in first 2 nm (contact region)
        peak_idx = None
        peak_val = None
        if g12r_r_bins:
            for i, r in enumerate(g12r_r_bins):
                if r <= 2.0 and g12r_avg[i] > (peak_val or 0):
                    peak_val = g12r_avg[i]
                    peak_idx = i
        if peak_val is not None:
            peak_r = g12r_r_bins[peak_idx]
            print(f"  g_12(r) peak       = {peak_val:.3f} at r={peak_r:.2f} nm")
    print(f"  Written to {args.output}")


if __name__ == "__main__":
    main()
