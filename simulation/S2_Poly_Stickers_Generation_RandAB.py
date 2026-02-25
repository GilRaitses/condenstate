#!/usr/bin/env python3
import argparse
import os
import numpy as np


def Parse_bool(s: str) -> bool:
    s = s.strip().lower()
    return s in ("1", "true", "t", "yes", "y")


def Random_AB_sequence_ID(N: int, pA: float = 0.5, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    draws = rng.random(N) < pA
    return [1 if a else 2 for a in draws]


def Generate_polymer_data(parameter_file):
    with open(parameter_file, "r") as parameter_file:
        lines = parameter_file.readlines()
        BeadSize = float(lines[0].split(": ")[1])
        BeadCsi = float(lines[1].split(": ")[1])
        Temp = float(lines[2].split(": ")[1])
        kBT = float(lines[3].split(": ")[1])
        outputfilename = lines[4].split(": ")[1].strip()
        N = int(lines[5].split(": ")[1])
        consecutive_A = int(lines[6].split(": ")[1])
        consecutive_B = int(lines[7].split(": ")[1])
        mass_A = float(lines[8].split(": ")[1])
        mass_B = float(lines[9].split(": ")[1])
        num_copies = int(lines[10].split(": ")[1])

        Box_half_X = Box_half_Y = Box_half_Z = None
        try:
            Box_half_X = float(lines[11].split(": ")[1])
            Box_half_Y = float(lines[12].split(": ")[1])
            Box_half_Z = float(lines[13].split(": ")[1])
        except Exception:
            pass

        try:
            Poly_Rand_Complete = Parse_bool(lines[14].split(":", 1)[1])
        except Exception:
            Poly_Rand_Complete = False
        try:
            FracA_Rand = float(lines[15].split(":", 1)[1])
        except Exception:
            FracA_Rand = 0.5

        Rand_Seed = None

        for _line in lines:
            if ":" not in _line:
                continue
            key, val = _line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
            if key == "box_edge":
                try:
                    Box_Edge = float(val)
                except Exception:
                    Box_Edge = None
            elif key == "poly_rand_complete":
                Poly_Rand_Complete = Parse_bool(val)
            elif key == "fraca_rand":
                try:
                    FracA_Rand = float(val)
                except Exception:
                    pass
            elif key == "rand_seed":
                try:
                    Rand_Seed = int(val)
                except Exception:
                    Rand_Seed = None

    InFolder = f"Simulations_T{int(Temp)}/"
    os.makedirs(InFolder, exist_ok=True)
    Output_Folder = InFolder
    os.makedirs(Output_Folder, exist_ok=True)

    d = 2.0
    if Box_half_X is not None:
        b_xlo, b_xhi = -Box_half_X, Box_half_X
        b_ylo, b_yhi = -Box_half_Y, Box_half_Y
        b_zlo, b_zhi = -Box_half_Z, Box_half_Z
    else:
        b_xlo, b_xhi = -30.0, 30.0
        b_ylo, b_yhi = -20.0, 20.0
        b_zlo, b_zhi = -20.0, 20.0

    x_min, x_max = b_xlo + d, b_xhi - d
    y_min, y_max = b_ylo + d, b_yhi - d
    z_min, z_max = b_zlo + d, b_zhi - d

    chain_span = (N - 1) * d
    if chain_span > (x_max - x_min):
        raise ValueError(
            f"Chain of N={N} at d={d} (span {chain_span}) does not fit inside "
            f"x usable range {(x_min, x_max)}. Increase Box_Edge or reduce N."
        )

    if Rand_Seed is None:
        Rand_Seed = np.random.randint(10**9)
    rng_main = np.random.default_rng(Rand_Seed)

    outpath = os.path.join(Output_Folder, outputfilename)
    with open(outpath, "w") as write:
        write.write("LAMMPS data file for Polymer Chain (lattice, centered)\n\n")
        write.write(f"{N * num_copies} atoms\n")
        write.write(f"{(N - 1) * num_copies} bonds\n")
        write.write(f"{(N - 2) * num_copies} angles\n\n")
        write.write("2 atom types\n")
        write.write("1 bond types\n")
        write.write("1 angle types\n\n")
        write.write(f"{b_xlo} {b_xhi} xlo xhi\n")
        write.write(f"{b_ylo} {b_yhi} ylo yhi\n")
        write.write(f"{b_zlo} {b_zhi} zlo zhi\n\n")

        write.write("Masses\n\n")
        write.write(f"1 {mass_A}\n")
        write.write(f"2 {mass_B}\n\n")

        write.write("Atoms\n\n")

        atom_count = 1
        polymers_placed = 0

        def make_ab_seq(poly_idx: int):
            if Poly_Rand_Complete:
                local_seed = Rand_Seed + poly_idx if Rand_Seed is not None else None
                local_rng = np.random.default_rng(local_seed)
                return Random_AB_sequence_ID(N, pA=FracA_Rand, rng=local_rng)

            ab = []
            counter = 0
            period = max(1, consecutive_A + consecutive_B)
            for _ in range(N):
                ab.append(1 if counter < consecutive_A else 2)
                counter = (counter + 1) % period
            return ab

        x_center = 0.0
        x_start_centered = x_center - 0.5 * chain_span
        x_start = max(x_min, min(x_start_centered, x_max - chain_span))

        y_coords = np.arange(y_min, y_max + 1e-9, d)
        z_coords = np.arange(z_min, z_max + 1e-9, d)
        y_coords = list(sorted(y_coords, key=lambda yy: abs(yy - 0.0)))
        z_coords = list(sorted(z_coords, key=lambda zz: abs(zz - 0.0)))

        for y_val in y_coords:
            if polymers_placed >= num_copies:
                break
            for z_val in z_coords:
                if polymers_placed >= num_copies:
                    break
                ab_seq = make_ab_seq(polymers_placed)
                mol_id = polymers_placed + 1

                for i in range(N):
                    bead_type = ab_seq[i]
                    x = x_start + i * d
                    y = y_val
                    z = z_val
                    write.write(f"{atom_count} {mol_id} {bead_type} {x} {y} {z}\n")
                    atom_count += 1
                polymers_placed += 1

        write.write("\nBonds\n\n")
        bond_count = 1
        for copy in range(num_copies):
            atom_offset = copy * N
            for n in range(N - 1):
                write.write(f"{bond_count} 1 {n + atom_offset + 1} {n + atom_offset + 2}\n")
                bond_count += 1

        write.write("\nAngles\n\n")
        angle_count = 1
        for copy in range(num_copies):
            atom_offset = copy * N
            for n in range(N - 2):
                write.write(f"{angle_count} 1 {n + atom_offset + 1} {n + atom_offset + 2} {n + atom_offset + 3}\n")
                angle_count += 1

    expected_atoms = N * num_copies
    if polymers_placed < num_copies:
        print(
            f"WARNING: placed only {polymers_placed} / {num_copies} polymers. "
            "Increase the Box Dimensions."
        )
    else:
        print(f"SUCCESS: placed {polymers_placed} polymers. Wrote {expected_atoms} atoms to {outpath}")


def main():
    parser = argparse.ArgumentParser(description="Generate polymer data file")
    parser.add_argument(
        "-p",
        dest="parameter_file",
        default="Parameter/Initial_Parameter_0.dat",
        help="Parameter file path",
    )
    args = parser.parse_args()
    Generate_polymer_data(args.parameter_file)


if __name__ == "__main__":
    main()
