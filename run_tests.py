import os
import subprocess
import sys

# Define the directory containing the SAS files
DATA_DIR = "data"

# Define the scripts to test
SCRIPTS = {
    "hmax": "hmax.py",
    "lmcut": "lmcut.py",
    "planner_hmax": "planner.py",
    "planner_lmcut": "planner.py",
}

# --- Helper function to run a command ---
def run_command(command_parts):
    command_str = ' '.join(command_parts)
    print(f"--- Running: {command_str} ---", flush=True)
    try:
        result = subprocess.run(
            [sys.executable] + command_parts, # Use sys.executable for portability
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,  # older equivalent to text=True
            check=False, # Don't throw exception on non-zero exit code
            timeout=120 # Add a timeout (e.g., 2 minutes)
        )
        print("--- Output ---")
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("--- Errors ---", file=sys.stderr)
            print(result.stderr.strip(), file=sys.stderr)
        if result.returncode != 0:
             print(f"--- Command failed with exit code: {result.returncode} ---", file=sys.stderr)
        print("---------------\\n", flush=True)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("--- Command Timed Out --- ", file=sys.stderr)
        print("---------------\\n", flush=True)
        return -1 # Indicate timeout
    except Exception as e:
        print(f"--- Error running command: {e} ---", file=sys.stderr)
        print("---------------\\n", flush=True)
        return -2 # Indicate other exception

# --- Main test execution logic ---
def main():
    if not os.path.isdir(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found.", file=sys.stderr)
        sys.exit(1)

    sas_files = sorted([
        f for f in os.listdir(DATA_DIR) 
        if os.path.isfile(os.path.join(DATA_DIR, f)) and f.endswith(".sas")
    ])

    if not sas_files:
        print(f"No .sas files found in '{DATA_DIR}'.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(sas_files)} SAS files in '{DATA_DIR}': {sas_files}\n")

    all_passed = True
    for filename in sas_files:
        filepath = os.path.join(DATA_DIR, filename)
        print(f"===== Testing {filename} =====")

        # Run hmax
        if run_command([SCRIPTS["hmax"], filepath]) != 0:
             all_passed = False

        # Run lmcut
        if run_command([SCRIPTS["lmcut"], filepath]) != 0:
            all_passed = False

        # Run planner with hmax
        if run_command([SCRIPTS["planner_hmax"], filepath, "hmax"]) != 0:
            all_passed = False

        # Run planner with lmcut
        # Note: Make sure lmcut is enabled in planner.py
        print("Note: Running planner with lmcut. Ensure lmcut heuristic is enabled in planner.py.")
        if run_command([SCRIPTS["planner_lmcut"], filepath, "lmcut"]) != 0:
            all_passed = False

        print(f"===== Finished {filename} =====\n")

    print("=========================")
    if all_passed:
        print("All tests completed (check output for correctness).")
    else:
        print("Some commands failed or timed out. Check errors above.", file=sys.stderr)
    print("=========================")

if __name__ == "__main__":
    main() 