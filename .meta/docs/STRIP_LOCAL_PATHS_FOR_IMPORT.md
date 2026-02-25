# How to fix local paths before importing into condenstate

When a file (e.g. `AGENT_HANDOFF.md`) contains **absolute paths** or **machine-specific paths**, use one of these approaches so the same doc works in any clone.

---

## Option A: Use a single “repo root” variable

Replace every absolute path with `$REPO_ROOT` (or `REPO_ROOT/`) and add a one-line note at the top:

```markdown
<!-- In this doc, REPO_ROOT = directory containing .sst (repo root). Set: export REPO_ROOT=$(git rev-parse --show-toplevel) -->
```

Then in the body:

- `/Users/gilraitses/PHY600/Presentations/main.tex` → `$REPO_ROOT/paper1/main.tex` (or whatever path you use in condenstate for the manuscript)
- `cd /Users/gilraitses/PHY600/Presentations/modeling` → `cd $REPO_ROOT/modeling`
- `/Users/gilraitses/PHY600/Presentations/figures/` → `$REPO_ROOT/figures/` or `$REPO_ROOT/paper1/figures/`

**Pros:** One convention, easy to search/replace. **Cons:** Readers must set the variable or know what REPO_ROOT is.

---

## Option B: Relative paths from repo root

Assume the reader is at repo root (or document “all paths relative to repo root”). No variable.

- `/Users/gilraitses/PHY600/Presentations/main.tex` → `paper1/main.tex` or `manuscript/paper1/main.tex`
- `cd /Users/gilraitses/PHY600/Presentations/modeling` → `cd modeling`
- `/Users/gilraitses/PHY600/Presentations/figures/` → `figures/` or `paper1/figures/`
- `/Users/gilraitses/PHY600/assets/Class_simulation/` → `simulation/` or drop if not present in condenstate

Add at top: **“All paths below are relative to the repository root (the directory that contains `.sst`).”**

**Pros:** Works in any clone, no env setup. **Cons:** You must pick a condenstate layout and stick to it.

---

## Option C: Placeholder + “see repo layout”

For docs that might live in different repos (PHY600 vs condenstate), avoid hard paths:

- Replace with: “Manuscript source: `main.tex` (see repo; may be under `paper1/` or `manuscript/`).”
- “Run from the modeling directory: `cd <modeling_dir>` then run the phase scripts.”
- “Figures: directory named `figures/` or `paper1/figures/` at repo root or under manuscript.”

Then add a short “In condenstate, layout is: …” section that lists the actual paths once.

**Pros:** Portable across repos. **Cons:** Less copy-paste friendly.

---

## What to do with AGENT_HANDOFF.md specifically

1. **Replace absolute paths** using Option B (recommended for condenstate):
   - `main.tex` → `paper1/main.tex` (or your chosen path)
   - `main.pdf` → `paper1/main.pdf`
   - `assets/Class_simulation/` → `simulation/` or remove line if you don’t have that in condenstate
   - “5 figures in …” → `figures/` or `paper1/figures/`
   - “How to Start” block: `cd modeling` (and ensure the phase scripts are under `modeling/` in condenstate)

2. **Remove or generalize the Cursor-specific path:**
   - “The plan file at `.cursor/plans/material_eligibility_modeling_pipeline_*.plan.md`”  
   → “See `modeling/PLAN.md` in this repo for the phase specification.”

3. **Save the result** as something like `modeling/AGENT_HANDOFF.md` or `.meta/docs/MODELING_HANDOFF.md` in condenstate so it’s the repo-relative version.

---

## One-line rule

**Before import:** Replace every path that starts with `/Users/...` or contains a specific username/machine with either `$REPO_ROOT/...`, a repo-relative path, or a short “see repo layout” note.
