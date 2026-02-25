import argparse
import os
import numpy as np


def write_parameter_file(
    temp=250,
    chain_length=12,
    consecutive_a=6,
    consecutive_b=6,
    copies=200,
    poly_rand_chain=False,
    frac_ab=0.5,
    box_half_x=100,
    box_half_y=20,
    box_half_z=20,
    bead_size=2,
    mass_a=0.001176,
    mass_b=0.001176,
    water_eta=1,
    output_dir="Parameter",
):
    kB = 1.38 * 10**-2
    bead_csi = 6 * np.pi * water_eta * bead_size / 2
    kBT = kB * temp

    os.makedirs(output_dir, exist_ok=True)

    outputfilename = f"Polymer_Stickers_A{consecutive_a}B{consecutive_b}_Chain{chain_length}_Copies{copies}.dat"
    output_path = os.path.join(output_dir, "Initial_Parameter_0.dat")

    with open(output_path, "w") as f:
        f.write(f"BeadSize: {bead_size}\n")
        f.write(f"BeadCsi: {bead_csi}\n")
        f.write(f"Temp: {temp}\n")
        f.write(f"kBT: {kBT}\n")
        f.write(f"OutputDataFile: {outputfilename}\n")
        f.write(f"Chain Length: {chain_length}\n")
        f.write(f"Segement A: {consecutive_a}\n")
        f.write(f"Segemtn B: {consecutive_b}\n")
        f.write(f"Mass-A: {mass_a}\n")
        f.write(f"Mass-B: {mass_b}\n")
        f.write(f"Number of Polymer Chains: {copies}\n")
        f.write(f"Box_half_X: {box_half_x}\n")
        f.write(f"Box_half_Y: {box_half_y}\n")
        f.write(f"Box_half_Z: {box_half_z}\n")
        f.write(f"Poly_Random_Chain: {poly_rand_chain}\n")
        f.write(f"Fracton_Type: {frac_ab}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Write parameter file for polymer run")
    parser.add_argument("-t", dest="temp", type=float, default=250, help="Temperature")
    parser.add_argument("-n", dest="chain_length", type=int, default=12, help="Chain length")
    parser.add_argument("-a", dest="consecutive_a", type=int, default=6, help="Consecutive A length")
    parser.add_argument("-b", dest="consecutive_b", type=int, default=6, help="Consecutive B length")
    parser.add_argument("-c", dest="copies", type=int, default=200, help="Number of copies")
    parser.add_argument("-x", dest="box_half_x", type=float, default=100, help="Half box size X")
    parser.add_argument("-y", dest="box_half_y", type=float, default=20, help="Half box size Y")
    parser.add_argument("-z", dest="box_half_z", type=float, default=20, help="Half box size Z")
    parser.add_argument("-o", dest="output_dir", default="Parameter", help="Output directory")
    parser.add_argument("-r", dest="poly_rand_chain", action="store_true", help="Random chain")
    parser.add_argument("-f", dest="frac_ab", type=float, default=0.5, help="Frac A")
    args = parser.parse_args()

    write_parameter_file(
        temp=args.temp,
        chain_length=args.chain_length,
        consecutive_a=args.consecutive_a,
        consecutive_b=args.consecutive_b,
        copies=args.copies,
        poly_rand_chain=args.poly_rand_chain,
        frac_ab=args.frac_ab,
        box_half_x=args.box_half_x,
        box_half_y=args.box_half_y,
        box_half_z=args.box_half_z,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
