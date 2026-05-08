
# """
# bisim_check.py — Standalone Bisimulation Pipeline
# ====================================================
# This script automates the verification of AADL refinements by:
#   1. Converting PNML models to AUT (via TINA)
#   2. Converting AUT to BCG and checking bisimulation (via CADP/WSL)

# Requirements:
#   - Windows with WSL installed
#   - TINA binaries (Windows)
#   - CADP installed within the WSL distribution
# """

# import argparse
# import os
# import subprocess
# import sys
# import tempfile
# import platform
# import shutil

# # ----------------------------------------------
# # Helpers
# # ----------------------------------------------

# def banner(msg: str):
#     width = 60
#     print("\n" + "─" * width)
#     print(f"  {msg}")
#     print("─" * width)

# def run(cmd: list, label: str, cwd=None) -> subprocess.CompletedProcess:
#     print(f"\n[RUN] {label}")
#     print("  $", " ".join(str(c) for c in cmd))
#     result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
#     if result.stdout:
#         print(result.stdout.strip())
#     if result.stderr:
#         print(result.stderr.strip(), file=sys.stderr)
#     if result.returncode != 0:
#         print(f"\n[ERROR] '{label}' failed with exit code {result.returncode}", file=sys.stderr)
#         sys.exit(result.returncode)
#     return result

# def to_wsl_path(win_path: str) -> str:
#     """Convert Windows path to WSL /mnt/... format."""
#     win_path = os.path.abspath(win_path).replace("\\", "/")
#     if len(win_path) >= 2 and win_path[1] == ":":
#         drive = win_path[0].lower()
#         rest = win_path[2:]
#         return f"/mnt/{drive}{rest}"
#     return win_path

# def fix_line_endings(path: str):
#     """Ensure .aut files have Unix line endings for CADP compatibility."""
#     with open(path, "rb") as f:
#         content = f.read()
#     fixed = content.replace(b"\r\n", b"\n")
#     with open(path, "wb") as f:
#         f.write(fixed)

# def wsl_bash(cadp_home: str, workspace: str, command: str) -> list:
#     """Execute a command in WSL with CADP environment variables set."""
#     cadp_com = f"{cadp_home}/com"
#     cadp_bin = f"{cadp_home}/bin.x64"
#     wsl_ws   = to_wsl_path(workspace)
#     return [
#         "wsl", "bash", "-c",
#         f'export CADP="{cadp_home}" && '
#         f'export PATH="{cadp_com}:{cadp_bin}:$PATH" && '
#         f'cd "{wsl_ws}" && '
#         f'{command}'
#     ]

# # ----------------------------------------------
# # Core Logic
# # ----------------------------------------------

# def run_tina(tina_exe: str, pnml_path: str, aut_path: str):
#     banner("STEP 1 — TINA: PNML → AUT")
#     if not os.path.isfile(tina_exe):
#         print(f"[ERROR] TINA not found at: {tina_exe}", file=sys.stderr)
#         sys.exit(1)
#     run([tina_exe, pnml_path, aut_path], label=f"tina {os.path.basename(pnml_path)}")
#     fix_line_endings(aut_path)

# def run_bcg_io(cadp_home: str, aut_path: str, bcg_path: str, workspace: str):
#     banner("STEP 2 — CADP bcg_io: AUT → BCG")
#     wsl_aut = to_wsl_path(aut_path)
#     wsl_bcg = to_wsl_path(bcg_path)
#     cmd = wsl_bash(cadp_home, workspace, f'bcg_io "{wsl_aut}" "{wsl_bcg}"')
#     run(cmd, label=f"WSL bcg_io {os.path.basename(aut_path)}", cwd=workspace)

# def run_hiding(cadp_home: str, hide_spec: str, orig_bcg: str, ref_bcg: str, 
#                orig_out: str, ref_out: str, workspace: str):
#     banner("STEP 3 — CADP bcg_labels: Hiding")
#     w_hide = to_wsl_path(hide_spec)
#     for b_in, b_out in [(orig_bcg, orig_out), (ref_bcg, ref_out)]:
#         cmd = wsl_bash(cadp_home, workspace, f'bcg_labels -hide "{w_hide}" "{to_wsl_path(b_in)}" "{to_wsl_path(b_out)}"')
#         run(cmd, label=f"Hiding labels in {os.path.basename(b_in)}")

# def run_bisimulation(cadp_home: str, orig: str, ref: str, workspace: str, diag: bool):
#     banner("STEP 4 — CADP bcg_cmp: Bisimulation Check")
#     diag_flag = "-diag" if diag else ""
#     cmd = wsl_bash(cadp_home, workspace, f'bcg_cmp -branching {diag_flag} "{to_wsl_path(orig)}" "{to_wsl_path(ref)}" || true')
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     return (result.stdout + result.stderr).strip()

# def main():
#     parser = argparse.ArgumentParser(description="Bisimulation Pipeline (Local Script Version)")
#     parser.add_argument("--orig", required=True, help="Original PNML file")
#     parser.add_argument("--ref", required=True, help="Refined PNML file")
#     parser.add_argument("--tina", required=True, help="Path to tina.exe (Windows path)")
#     parser.add_argument("--cadp-home", required=True, help="CADP home in WSL (e.g., /home/user/cadp)")
#     parser.add_argument("--hide", help="Path to hide.spec")
#     parser.add_argument("--diag", action="store_true", help="Show diagnostic trace")
#     parser.add_argument("--outdir", help="Output directory for intermediate files")

#     args = parser.parse_args()
#     workspace = os.path.abspath(args.outdir) if args.outdir else tempfile.mkdtemp()
#     os.makedirs(workspace, exist_ok=True)

#     # Path setup
#     orig_aut, ref_aut = os.path.join(workspace, "orig.aut"), os.path.join(workspace, "ref.aut")
#     orig_bcg, ref_bcg = os.path.join(workspace, "orig.bcg"), os.path.join(workspace, "ref.bcg")
    
#     # Execution
#     run_tina(args.tina, args.orig, orig_aut)
#     run_tina(args.tina, args.ref, ref_aut)
#     run_bcg_io(args.cadp_home, orig_aut, orig_bcg, workspace)
#     run_bcg_io(args.cadp_home, ref_aut, ref_bcg, workspace)

#     if args.hide:
#         o_hid, r_hid = os.path.join(workspace, "o_h.bcg"), os.path.join(workspace, "r_h.bcg")
#         run_hiding(args.cadp_home, args.hide, orig_bcg, ref_bcg, o_hid, r_hid, workspace)
#         output = run_bisimulation(args.cadp_home, o_hid, r_hid, workspace, args.diag)
#     else:
#         output = run_bisimulation(args.cadp_home, orig_bcg, ref_bcg, workspace, args.diag)

#     banner("RESULT")
#     print(output)

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import tempfile
import platform

def banner(msg: str):
    width = 60
    print("\n" + "─" * width + f"\n  {msg}\n" + "─" * width)

def run(cmd: list, label: str, cwd=None) -> subprocess.CompletedProcess:
    print(f"\n[RUN] {label}\n  $ " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.stdout: print(result.stdout.strip())
    if result.stderr: print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        print(f"\n[ERROR] '{label}' failed (Exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
    return result

def to_wsl_path(win_path: str) -> str:
    """Converts Windows paths to WSL format if on Windows; else returns path as-is."""
    if platform.system() != "Windows": return os.path.abspath(win_path)
    win_path = os.path.abspath(win_path).replace("\\", "/")
    if len(win_path) >= 2 and win_path[1] == ":":
        return f"/mnt/{win_path[0].lower()}{win_path[2:]}"
    return win_path

def wsl_bash(cadp_home: str, workspace: str, command: str) -> list:
    """Builds the command string. Uses 'wsl bash' on Windows, or just 'bash' on Linux/Mac."""
    cadp_env = f'export CADP="{cadp_home}" && export PATH="{cadp_home}/com:{cadp_home}/bin.x64:$PATH"'
    full_cmd = f'{cadp_env} && cd "{to_wsl_path(workspace)}" && {command}'
    return ["wsl", "bash", "-c", full_cmd] if platform.system() == "Windows" else ["bash", "-c", full_cmd]

def run_tina(tina_exe: str, pnml_path: str, aut_path: str):
    banner("STEP 1 — TINA: PNML → AUT")
    # Resolve to absolute paths so TINA.exe doesn't get lost
    abs_pnml = os.path.abspath(pnml_path)
    abs_aut = os.path.abspath(aut_path)
    run([tina_exe, abs_pnml, abs_aut], label=f"tina {os.path.basename(pnml_path)}")

def run_bcg_io(cadp_home: str, aut_path: str, bcg_path: str, workspace: str):
    banner("STEP 2 — CADP bcg_io: AUT → BCG")
    cmd = wsl_bash(cadp_home, workspace, f'bcg_io "{to_wsl_path(aut_path)}" "{to_wsl_path(bcg_path)}"')
    run(cmd, label="bcg_io conversion")

def main():
    parser = argparse.ArgumentParser(description="Cross-Platform Bisimulation Pipeline")
    parser.add_argument("--orig", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--tina", required=True, help="Path to tina executable")
    parser.add_argument("--cadp-home", required=True, help="CADP installation directory")
    parser.add_argument("--hide", help="Path to hide.spec")
    parser.add_argument("--diag", action="store_true")
    parser.add_argument("--outdir")

    args = parser.parse_args()
    workspace = os.path.abspath(args.outdir) if args.outdir else tempfile.mkdtemp()
    os.makedirs(workspace, exist_ok=True)

    # Resolve inputs to absolute paths immediately
    orig_pnml, ref_pnml = os.path.abspath(args.orig), os.path.abspath(args.ref)
    orig_aut, ref_aut = os.path.join(workspace, "orig.aut"), os.path.join(workspace, "ref.aut")
    orig_bcg, ref_bcg = os.path.join(workspace, "orig.bcg"), os.path.join(workspace, "ref.bcg")

    run_tina(args.tina, orig_pnml, orig_aut)
    run_tina(args.tina, ref_pnml, ref_aut)
    run_bcg_io(args.cadp_home, orig_aut, orig_bcg, workspace)
    run_bcg_io(args.cadp_home, ref_aut, ref_bcg, workspace)

    target_orig, target_ref = orig_bcg, ref_bcg
    if args.hide:
        banner("STEP 3 — Hiding & Bisimulation")
        o_h, r_h = os.path.join(workspace, "o_h.bcg"), os.path.join(workspace, "r_h.bcg")
        h_cmd = f'bcg_labels -hide "{to_wsl_path(args.hide)}" '
        run(wsl_bash(args.cadp_home, workspace, h_cmd + f'"{to_wsl_path(orig_bcg)}" "{to_wsl_path(o_h)}"'), "Hide Original")
        run(wsl_bash(args.cadp_home, workspace, h_cmd + f'"{to_wsl_path(ref_bcg)}" "{to_wsl_path(r_h)}"'), "Hide Refined")
        target_orig, target_ref = o_h, r_h

    diag = "-diag" if args.diag else ""
    res = subprocess.run(wsl_bash(args.cadp_home, workspace, f'bcg_cmp -branching {diag} "{to_wsl_path(target_orig)}" "{to_wsl_path(target_ref)}" || true'), capture_output=True, text=True)
    banner("RESULT")
    print(res.stdout + res.stderr)

if __name__ == "__main__":
    main()