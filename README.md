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

## Step 5: TINA — Convert PNML to AUT

TINA performs reachability analysis on the 1-safe Petri net and produces a Labelled Transition System in `.aut` format.

### 5a. Run TINA on Both PNML Files

```bash
# Convert original model
tina original.pnml original.aut

# Convert refined model
tina refined.pnml refined.aut
```

On Windows, use the full path to the TINA executable:
```cmd
C:\tina\bin\tina.exe original.pnml original.aut
C:\tina\bin\tina.exe refined.pnml refined.aut
```

### 5b. Verify Output

Check that `original.aut` and `refined.aut` are non-empty. The `.aut` files should look like:

```
des (0, 12, 8)
(0,"t_dispatch_Init1",1)
(1,"t_exec_Init1",2)
...
```

The header `des (initial_state, num_transitions, num_states)` should be present.

> **Note:** If TINA produces empty output or errors, check that your PNML is well-formed. Common issue: the `generate.mtl` transformation must be run on an **instantiated** AADL model (`.aaxl2`), not the raw `.aadl` file.

---

## Step 6: CADP — Convert to BCG and Run Bisimulation

CADP converts the `.aut` files to Binary Coded Graphs (BCG) and performs branching bisimulation checking.

> All CADP commands must be run in a **Linux or WSL terminal** with CADP properly configured.

### 6a. Set Up the CADP Environment

```bash
export CADP=/path/to/cadp
export PATH=$CADP/com:$CADP/bin.x64:$PATH
```

### 6b. Convert AUT to BCG

```bash
bcg_io original.aut original.bcg
bcg_io refined.aut refined.bcg
```

Verify that both `.bcg` files are created and non-empty:
```bash
ls -lh original.bcg refined.bcg
```

### 6c. Identify Internal Transitions to Hide

Before running bisimulation, you must determine which transitions in the refined model represent internal implementation details absent from the source model, and list them in a `hide.spec` file.

**How to find these transitions:**

List all transition labels in each BCG:
```bash
bcg_labels original.bcg
bcg_labels refined.bcg
```

Compare the two label sets. Transitions present in `refined.bcg` but absent from `original.bcg` are candidates for hiding. For **structural refinements** (new components added), hide all lifecycle transitions of the new component. For **property-level refinements** (capacity/marking changes), hide transitions whose enabling conditions changed, plus the full lifecycle chain they belong to.

**Create `hide.spec`:**

> **Producer-Consumer example:** Hide the 4 transitions for shared buffer acquire/release:

```
hide
"t_exec_Producer1"
"t_comp_Producer1"
"t_exec_Consumer1"
"t_comp_Consumer1"
"t_exec_Init1"
"t_comp_Init1"
```

### 6d. Apply Hiding and Run Bisimulation Check

```bash
# Apply hiding to both models
bcg_labels -hide hide.spec original.bcg original_hidden.bcg
bcg_labels -hide hide.spec refined.bcg refined_hidden.bcg

# Run branching bisimulation check
bcg_cmp -branching original_hidden.bcg refined_hidden.bcg
```

### 6e. Interpret the Result

| Output | Meaning |
|--------|---------|
| `TRUE` | The refined model is branching bisimilar to the original after hiding. The LLM-generated refinement is **formally verified correct**. No deadlocks, race conditions, or unintended non-determinism were introduced. |
| `FALSE` | The models are **not** bisimilar. The refinement introduced a behavioral discrepancy. Inspect the diagnostic trace and revise the refined model or the hiding set. |

To get a diagnostic trace on a `FALSE` result:
```bash
bcg_cmp -branching -diag original_hidden.bcg refined_hidden.bcg
```

This outputs a witness trace showing exactly where the models diverge.

---

## Reproducing the Paper's Case Studies

### Producer-Consumer System

| Parameter | Value |
|-----------|-------|
| Source model | `ProducerConsumer/producer_consumer.aadl` |
| Refinement goal | Copy the refinement rules in `ProducerConsumer/producer_consumer_refinement_rules.txt` |
| Repair iterations | 1 |
| Hiding set size | 4 transitions |
| Bisimulation result | TRUE |

### Case Study 2: Flight Control System (End-to-End)


### Soundness Check: Round-Robin Scheduler (Detecting Hallucination)

To reproduce the hallucination detection experiment described in Section 5:

1. Use the Round-Robin source model with an **ambiguous** refinement rule:
   > *"Refine the time-slot assignment for T1 and T2. A third slot for a diagnostic thread may be defined if required."*
2. The LLM will likely add a concrete `T_Diag` thread subcomponent.
3. Run the full pipeline without hiding the `T_Diag` lifecycle transitions.
4. The bisimulation check will return `FALSE` — the correct result, as `T_Diag` is absent from the source model.

This demonstrates that the pipeline is sound: a `FALSE` result is a genuine witness of behavioral divergence introduced by the LLM, not a tool artifact.

---

## Troubleshooting

**TINA produces an empty `.aut` file**
- Ensure the PNML input was generated from an **instantiated** AADL model (`.aaxl2`), not from the raw `.aadl` source.
- Check that all places in the PNML have valid initial markings.

**CADP `bcg_io` fails**
- Ensure CADP environment variables are set correctly before running any `bcg_*` command.
- On WSL, verify the path translation is correct: Windows path `C:\work\original.aut` becomes `/mnt/c/work/original.aut` in WSL.

**Bisimulation returns FALSE unexpectedly**
- First check: are all new transitions from the refinement included in `hide.spec`? Run `bcg_labels original.bcg` and `bcg_labels refined.bcg` and diff the outputs.
- Second check: if a transition is mid-chain, the entire lifecycle chain it belongs to must be hidden (not just the single transition). See Section 4 of the paper for the closure rule.

**OSATE cannot instantiate the refined model**
- This usually means there is a classifier name mismatch (e.g., a component references a type that was renamed by the LLM). Check the Problems panel carefully and use the Repair Loop prompt with the full error text.

---
