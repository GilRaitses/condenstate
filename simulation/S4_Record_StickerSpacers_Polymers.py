import argparse
import os
import numpy as np
import random
import time

random.seed(int(time.time()))


def Parse_bool(s):
    s = s.strip().lower()
    return s in ("1", "true", "t", "yes", "y")


def Read_parameters(file_path):
    with open(file_path, "r") as parameter_file:
        params = {}
        lines = parameter_file.readlines()
        params["BeadSize"] = float(lines[0].split(": ")[1])
        params["BeadCsi"] = float(lines[1].split(": ")[1])
        params["Temp"] = float(lines[2].split(": ")[1])
        params["kBT"] = float(lines[3].split(": ")[1])
        params["outputfilename"] = lines[4].split(": ")[1].strip()
        params["N"] = int(lines[5].split(": ")[1])
        params["consecutive_A"] = int(lines[6].split(": ")[1])
        params["consecutive_B"] = int(lines[7].split(": ")[1])
        params["mass_A"] = float(lines[8].split(": ")[1])
        params["mass_B"] = float(lines[9].split(": ")[1])
        params["num_copies"] = int(lines[10].split(": ")[1])
        params["Box_half_X"] = float(lines[11].split(": ")[1])
        params["Box_half_Y"] = float(lines[12].split(": ")[1])
        params["Box_half_Z"] = float(lines[13].split(": ")[1])
        params["Poly_Rand_Complete"] = Parse_bool(lines[14].split(":", 1)[1])
        params["FracA_Rand"] = float(lines[15].split(":", 1)[1])

    return params


def Generate_input_record_file(
    folder,
    params,
    epsilon_ab=4,
    thermo=40000,
    run_steps=3000000,
    record_interval=None,
    stage5=False,
):
    BeadCsi = params["BeadCsi"]
    BeadSize = params["BeadSize"]
    Temp = int(params["Temp"])
    kBT = params["kBT"]

    Damp = 10
    BeadMass = Damp * BeadCsi

    Ai = 0 * kBT
    Epsilon_AB = float(epsilon_ab)
    Af = round(-Epsilon_AB * kBT, 4)
    eps = round(1 * kBT, 4)
    Rc = 1
    # FENE bond parameters: Kremer-Grest converted to nano units
    # k = 30 * eps_LJ / sigma^2 ≈ 26, R0 = 1.5 * sigma = 3.0 nm
    # WCA core: eps = eps_LJ = 3.45, sigma = BeadSize = 2.0 nm
    # See: Kremer & Grest (1990); LAMMPS bond_fene docs; followup8.md Q4/Q8
    FENE_k = 26.0
    FENE_R0 = 1.5 * BeadSize  # 3.0 nm
    FENE_eps = round(kBT, 4)   # use LJ epsilon from pair potential
    FENE_sigma = BeadSize      # 2.0 nm
    Rb = 90
    # Reduced timestep for stability
    TimeStep = Damp / 80000
    RunSteps = int(run_steps)
    Thermo = int(thermo)
    if record_interval and int(record_interval) > 0:
        RecordInterval = int(record_interval)
    else:
        RecordInterval = int(RunSteps / 50)
    sigma_11 = (BeadSize + BeadSize) / 2
    sigma_22 = (BeadSize + BeadSize) / 2
    wca = 1.122
    # fene_E removed: now using FENE_k, FENE_R0, FENE_eps, FENE_sigma above

    # Stage 5: 1-1 soft (attractive), 1-2 soft 0; default: 1-1 WCA, 1-2 soft (attractive)
    pair_11_attract = stage5

    consecutive_A = params["consecutive_A"]
    consecutive_B = params["consecutive_B"]
    os.makedirs(os.path.join(folder, "Out_Record"), exist_ok=True)
    eps_tag = f"{Epsilon_AB:g}"
    input_file = os.path.join(
        folder,
        f"Poly_Record_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{Temp}_E{eps_tag}.in",
    )

    with open(input_file, "w") as f:
        f.write(
            f"read_restart Out_Relax/PolyStickers_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{int(params['Temp'])}_E{eps_tag}_Relax.restart\n\n"
        )
        f.write(f"pair_style hybrid lj/cut {wca * sigma_11} soft {Rc}\n")
        if pair_11_attract:
            f.write(f"pair_coeff 1 1 soft {Af} {Rc}\n")
            f.write(f"pair_coeff 2 2 lj/cut {eps} {sigma_22} {sigma_22 * wca}\n")
            f.write(f"pair_coeff 1 2 soft 0 {Rc}\n")
        else:
            f.write(f"pair_coeff 1 1 lj/cut {eps} {sigma_11} {sigma_11 * wca}\n")
            f.write(f"pair_coeff 2 2 lj/cut {eps} {sigma_22} {sigma_22 * wca}\n")
            f.write(f"pair_coeff 1 2 soft {Af} {Rc}\n")
        f.write("pair_modify shift yes\n")
        f.write("special_bonds lj/coul 0 1 1\n\n")
        f.write("angle_style none\n\n")
        f.write("bond_style fene\n")
        f.write(f"bond_coeff 1 {FENE_k} {FENE_R0} {FENE_eps} {FENE_sigma}\n\n")
        f.write("neighbor 7.7551 bin\n")
        f.write("neigh_modify every 1 delay 0\n")
        # Extend communication cutoff beyond LAMMPS' conservative bond-length
        # estimate (10.665 nm) to suppress the comm.cpp:723 warning.
        # See S3 script and matsci.org/t/47062/4 for full explanation.
        f.write("comm_modify cutoff 11.0\n\n")
        f.write("fix 1 all nve\n")
        f.write(f"fix 2 all langevin {Temp} {Temp} {Damp} {np.random.randint(10**7)} zero yes\n")
        f.write("fix 3 all balance 100000 1.05 shift x 10 1.05\n\n")
        f.write(f"thermo {Thermo}\n")
        f.write("thermo_modify flush yes\n")
        f.write(f"timestep {TimeStep}\n\n")
        f.write(
            "restart 1000000 "
            f"Out_Relax/SimPD_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{int(params['Temp'])}_E{eps_tag}.restart\n\n"
        )
        f.write(
            f"dump D1 all custom {RecordInterval} "
            f"Out_Record/traj_PolyStickers_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{int(params['Temp'])}_E{eps_tag}_Record.lammpstrj id type x y z ix iy iz\n\n"
        )
        f.write(
            f"dump D2 all xyz {RecordInterval} "
            f"Out_Record/PolyStickers_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{int(params['Temp'])}_E{eps_tag}.xyz\n\n"
        )
        f.write("dump_modify D2 sort id\n\n")
        f.write(f"run {RunSteps}\n\n")
        f.write(
            f"write_restart Out_Record/PolyStickers_A{consecutive_A}B{consecutive_B}_Chain{params['N']}_Copies{params['num_copies']}_T{int(params['Temp'])}_E{eps_tag}_Record.restart\n"
        )


def main():
    parser = argparse.ArgumentParser(description="Generate record input file")
    parser.add_argument("-p", dest="parameter_file", default="Parameter/Initial_Parameter_0.dat", help="Parameter file")
    parser.add_argument("-e", dest="epsilon_ab", type=float, default=4, help="Epsilon AB")
    parser.add_argument("--thermo", dest="thermo", type=int, default=40000, help="Thermo output interval")
    parser.add_argument("--run-steps", dest="run_steps", type=int, default=3000000, help="Record stage steps")
    parser.add_argument("--record-interval", dest="record_interval", type=int, default=0, help="Dump interval")
    parser.add_argument("--stage5", dest="stage5", action="store_true", help="Stage 5: 1-1 sticker-sticker attraction (instead of 1-2)")
    args = parser.parse_args()

    params = Read_parameters(args.parameter_file)
    Temp = params["Temp"]

    InFolder = f"Simulations_T{int(Temp)}/"
    os.makedirs(InFolder, exist_ok=True)
    Output_Folder = InFolder
    os.makedirs(Output_Folder, exist_ok=True)

    Record_Folder = "Out_Record/"
    NewFolder = os.path.join(InFolder, Record_Folder)
    os.makedirs(NewFolder, exist_ok=True)

    Generate_input_record_file(
        Output_Folder,
        params,
        epsilon_ab=args.epsilon_ab,
        thermo=args.thermo,
        run_steps=args.run_steps,
        record_interval=args.record_interval,
        stage5=args.stage5,
    )


if __name__ == "__main__":
    main()
