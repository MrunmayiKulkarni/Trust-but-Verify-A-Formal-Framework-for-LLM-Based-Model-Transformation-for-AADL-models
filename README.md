# Artifact: Trust but Verify — Reproduction Guide

**Paper:** *Trust but Verify: A Formal Framework for LLM-Based Model Transformation for AADL Models*

This document provides a complete, step-by-step guide to reproduce the results of the paper. The workflow proceeds through five main stages:

```
AADL Source Model
      │
      ▼
[Step 1] LLM Refinement (Gemini)
      │
      ▼
[Step 2] OSATE Compilation Check
      │  ← errors fed back → [Step 3] Repair Loop (repeat until zero errors)
      ▼
[Step 4] Acceleo M2T: AADL → PNML
      │
      ▼
[Step 5] TINA: PNML → AUT (Labelled Transition System)
      │
      ▼
[Step 6] CADP: AUT → BCG → Bisimulation Check
```

---

## Prerequisites

Install and configure the following tools before starting.

### 1. OSATE (AADL Compiler and IDE) with Acceleo Plugin (Model-to-Text Transformation)
- Download from: https://osate.org/download.html
- OSATE is an Eclipse-based IDE for AADL. It is used to validate and compile AADL models.
- Install the Acceleo plugin via: `Help → Install New Software → Acceleo`
- Acceleo is used to run the `generate.mtl` template that converts AADL instances to PNML.


### 2. TINA (Petri Net Analyzer — PNML to AUT)
- Download from: https://projects.laas.fr/tina/download.html
- Install the appropriate binary for your OS (Windows, Linux, or macOS).
- Note the path to the `tina` executable (e.g., `C:\tina\bin\tina.exe` on Windows).
- TINA takes a `.pnml` file and produces a `.aut` Labelled Transition System file.

### 3. CADP (Bisimulation Checker — AUT to BCG and equivalence)
- Request a free academic licence at: https://cadp.inria.fr/registration/
- After installation, set the environment variable:
  ```bash
  export CADP=/path/to/cadp
  export PATH=$CADP/com:$CADP/bin.x64:$PATH
  ```
- On Windows, CADP must be run inside **WSL (Windows Subsystem for Linux)**. The commands in Step 6 assume a Linux/WSL environment.
- Verify the installation:
  ```bash
  bcg_io --version
  bcg_cmp --version
  ```

### 4. Gemini Access
- The paper uses **Gemini 3**.

---

## Step 1: LLM Refinement — Generate the Refined AADL Model

This step uses the LLM to transform the source AADL model according to a set of refinement rules.

### 1a. Open the Initial Refinement Prompt

Open `InitialPrompt.txt`. The prompt has three sections you must fill in:

```
[SECTION 1 — SOURCE MODEL]
Paste the full content of your source .aadl file here.

[SECTION 2 — REFINEMENT RULES]
Write your refinement requirements in natural language here.
Example:
  - Set Dispatch_Protocol => Periodic on all threads.
  - Add Queue_Size => 5 to all event data ports.
  - Apply Data_Model::Data_Representation => Float to all data types.

[SECTION 3 — CONSTRAINTS]
(Already filled in the template — do not change)
You are an expert AADL 2.2 engineer. Output only the refined AADL code
between the markers <<REFINED_AADL_START>> and <<REFINED_AADL_END>>.
Preserve all existing interfaces and component names exactly.
```

### 1b. Send the Prompt to Gemini

- Go to https://aistudio.google.com.
- Paste the completed prompt and run it.
- The model will return a refined AADL file between the markers `<<REFINED_AADL_START>>` and `<<REFINED_AADL_END>>`.

### 1c. Extract the Refined Model

Copy everything between the markers and save it as a new `.aadl` file, e.g., `refined.aadl`.

---

## Step 2: OSATE Compilation Check

This step validates that the refined model is syntactically correct AADL.

### 2a. Open OSATE

Launch OSATE and create a new AADL project:
- `File → New → AADL Project`
- Add both `source.aadl` and `refined.aadl` to the project.

### 2b. Save the Model

Try to save the model by pressing Ctrl+S.

OSATE will attempt to compile and instantiate the model. Errors will appear in the **Problems** panel at the bottom.

### 2c. Check for Errors

- **Zero errors:** Proceed to Step 4.
- **Errors present:** Proceed to Step 3 (Repair Loop).

---

## Step 3: Repair Loop — Fix Syntax Errors Iteratively

This step feeds the OSATE errors back to the LLM for correction. Repeat until OSATE reports zero errors.

### 3a. Copy the Error Log

In OSATE, right-click the Problems panel and select **Copy**. This gives you the full error list.

### 3b. Open the Repair Loop Prompt

Open `RepairLoopPrompt.txt`. Fill in the two sections:

```
[SECTION 1 — CURRENT REFINED MODEL]
Paste the full content of your current refined.aadl here.

[SECTION 2 — OSATE ERRORS]
Paste the copied OSATE error log here.
```

The prompt instructs the LLM to:
- Fix **only** the identified errors.
- Preserve all structural and architectural changes from the previous iteration.
- Output the corrected model between `<<REFINED_AADL_START>>` and `<<REFINED_AADL_END>>`.

### 3c. Send to Gemini and Extract

Send the repair prompt to Gemini, extract the corrected model, save it as the new `refined.aadl`, and return to Step 2.

> **Typical iteration counts from the paper:**
> - Producer-Consumer: 1 repair iteration
> - Car System: 1 repair iteration
> - Round-Robin Scheduler: 2 repair iterations
> - Flight Control System: 3 repair iterations

---

## Step 4: Acceleo M2T Transformation — AADL to PNML

Once OSATE reports zero errors, this step converts both the source and refined AADL models into Petri Net Markup Language (PNML) using the `generate.mtl` Acceleo template.

### 4a. Set Up the Acceleo Project in OSATE

1. Open OSATE (with the Acceleo plugin installed).
2. Create a new **Acceleo Project**: `File → New → Acceleo Project`.
3. Copy `acceleo/generate.mtl` from this repository into the `src` folder of your Acceleo project.

### 4b. Instantiate the AADL Model

Before running Acceleo, you must create an AADL **instance model** in OSATE:

1. In OSATE, right-click your top-level system implementation.
2. Select `Instantiate`.
3. OSATE generates a `.aaxl2` instance file in the `instances/` folder of your project.
4. This `.aaxl2` file is the input to Acceleo.

### 4c. Run the Acceleo Transformation

1. In Eclipse, right-click the `.aaxl2` instance file.
2. Select `Run As → Launch Acceleo Application`.
3. In the dialog, set:
   - **Module:** point to your `generate.mtl`
   - **Output folder:** choose a folder where the PNML will be written
4. Click **Run**.

Two PNML files will be generated:
- `original.pnml` — from `source.aaxl2`
- `refined.pnml` — from `refined.aaxl2`

Repeat this process for both the source and refined models.

---

## Step 5: Run the Bisimulation Pipeline (`bisim_check.py`)

---

### 5a. Prerequisites — Where Each Tool Must Be Installed

Before running the script, confirm the following installation layout. The script requires
**Windows as the host OS**, with WSL providing the Linux environment for CADP.

| Tool | Where it must be installed | Notes |
|------|---------------------------|-------|
| **Python 3** | Windows (host) | Run `python --version` in PowerShell to verify |
| **TINA** (`tina.exe`) | Windows (host) | Any folder on Windows, e.g. `C:\tina\bin\tina.exe` |
| **WSL** | Windows feature | Enable via `wsl --install` in an admin PowerShell |
| **CADP** | Inside WSL (Linux) | e.g. `/home/username/cadp` — this is the path you pass to `--cadp-home` |

> **Important:** CADP must be installed **inside WSL**, not on the Windows side.
> The script invokes all CADP tools (`bcg_io`, `bcg_labels`, `bcg_cmp`) through WSL
> automatically — you do not need to open WSL manually or set any environment variables
> yourself.

---

### 5b. How to Specify Paths

The script accepts two types of paths. It is important to use the right format for each argument.

**`--tina` → Windows path to `tina.exe` **

```
--tina "C:\tina\bin\tina.exe"
```

**`--cadp-home` → WSL/Linux path (forward slashes, starts with `/`)**

This is the path to the CADP installation directory **as seen from inside WSL**.
Open your WSL terminal and run `echo $CADP` or `ls ~/cadp` to confirm the path.

```
--cadp-home "/home/username/cadp"
```

**`--orig` and `--ref` → Windows paths to your PNML files**

These are the two PNML files generated by Acceleo in Step 4. 

```
--orig "C:\original.pnml"
--ref  "C:\refined.pnml"
```

**`--hide` → Windows path to your `hide.spec` file** *(optional)*

Required for structural refinements. See section 5e for how to create this file.

```
--hide "C:\hide.spec"
```

**`--outdir` → Windows path for intermediate output files** *(optional)*

The script saves intermediate `.aut` and `.bcg` files here. If omitted, a temporary
folder is created automatically.

```
--outdir "C:\output"
```

---

### 5c. Run the Script

Open a **Windows PowerShell or Command Prompt** (not a WSL terminal) in the folder
containing `bisim_check.py`, then run:

**Minimal command (no hiding):**

```cmd
python bisim_check.py ^
  --orig  "C:\original.pnml" ^
  --ref   "C:\refined.pnml" ^
  --tina  "C:\tina\bin\tina.exe" ^
  --cadp-home "/home/username/cadp"
```

**Full command (with hiding):**

```cmd
python bisim_check.py ^
  --orig     "C:\work\ProducerConsumer\original.pnml" ^
  --ref      "C:\work\ProducerConsumer\refined.pnml" ^
  --tina     "C:\tina\bin\tina.exe" ^
  --cadp-home "/home/mrunmayi/cadp" ^
  --hide     "C:\work\ProducerConsumer\hide.spec" ^
  --outdir   "C:\work\ProducerConsumer\output" ^
```

> **Note:** The `^` character is the Windows line-continuation symbol. You can also write
> the entire command on a single line without `^`.

**What the script does internally (in order):**

```
[Stage 1] TINA:       original.pnml  →  orig.aut
[Stage 2] TINA:       refined.pnml   →  ref.aut
[Stage 3] bcg_io:     orig.aut       →  orig.bcg
[Stage 4] bcg_io:     ref.aut        →  ref.bcg
[Stage 5] bcg_labels: orig.bcg       →  o_h.bcg   (only if --hide is given)
[Stage 6] bcg_labels: ref.bcg        →  r_h.bcg   (only if --hide is given)
[Stage 7] bcg_cmp:    branching bisimulation check  →  RESULT
```

---

### 5d. Interpret the Result

The final output printed by the script will be one of the following:

| Output | Meaning |
|--------|---------|
| `TRUE` | The refined model is branching bisimilar to the original. The LLM-generated refinement is **formally verified correct**. No deadlocks, race conditions, or unintended non-determinism were introduced. |
| `FALSE` | The models are **not** bisimilar. The refinement introduced a behavioral discrepancy. |

---

### 5e. Creating the `hide.spec` File

List out the transitions you want to hide in hide.spec file.


**`hide.spec` format** (one label per line, labels in double quotes):

```
hide
"t_exec_Producer1"
"t_comp_Producer1"
"t_exec_Consumer1"
"t_comp_Consumer1"
"t_exec_Init1"
"t_comp_Init1"
```

Save this file on the Windows side (e.g. `C:\hide.spec`)
and pass it to `--hide`.

## Reproducing the Paper's Case Studies

### Producer-Consumer System

| Parameter | Value |
|-----------|-------|
| Source model | `ProducerConsumer/producer_consumer.aadl` |
| Refinement goal | Copy the refinement rules in `ProducerConsumer/producer_consumer_refinement_rules.txt` |
| Repair iterations | 1 |
| Hiding set size | 4 transitions |
| Bisimulation result | TRUE |


### Soundness Check: Round-Robin Scheduler (Detecting Hallucination)

To reproduce the hallucination detection experiment described in Section 5:

1. Use the Round-Robin source model with an **ambiguous** refinement rule:
   > *"Refine the time-slot assignment for T1 and T2. A third slot for a diagnostic thread may be defined if required."*
2. The LLM will likely add a concrete `T_Diag` thread subcomponent.
3. Run the full pipeline without hiding the `T_Diag` lifecycle transitions.
4. The bisimulation check will return `FALSE` — the correct result, as `T_Diag` is absent from the source model.

This demonstrates that the pipeline is sound: a `FALSE` result is a genuine witness of behavioral divergence introduced by the LLM, not a tool artifact.

---

