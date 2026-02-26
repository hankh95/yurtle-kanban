---
name: experiment
description: Create an experiment protocol for HDD - tests enhancement on branch
disable-model-invocation: true
allowed-tools: Bash, Write, Read, Grep, Glob
argument-hint: "<hypothesis-id> \"experiment design description\""
---

# Create Experiment

Create an experiment protocol to test a hypothesis in HDD.

**Goal:** Validate an enhancement BEFORE merging to main. Only proven improvements ship.

## Overview

An experiment is a **pre-registered protocol** for testing a hypothesis:
- Methods (what you'll do)
- Measures (what you'll measure)
- Data location (where results stored)
- Analysis plan (how to interpret)
- **Branch**: The feature branch with the implementation

**Pre-registration** = commit protocol BEFORE running. Prevents HARKing.

## The Feedback Loop

**Every experiment runs on a feature branch.** Based on results:

| Outcome | Action | Software Impact |
|---------|--------|-----------------|
| **VALIDATED** | Merge branch | Enhancement ships |
| **REFUTED** | Don't merge | We learned why |
| **NEEDS-MORE-DATA** | Extend | Keep branch open |

## Steps

### 1. Create Feature Branch

```bash
git checkout -b exp-{expedition}-{description}
# Example: git checkout -b exp-042-redis-caching
```

### 2. Implement the Enhancement

Build the feature you want to test.

### 3. Create Experiment File

Create `research/experiments/EXPR-{paper}.md`:

```markdown
---
id: EXPR-{paper}
type: experiment
paper: Paper {paper}
hypothesis: H{paper}.{n}
status: draft
created: YYYY-MM-DD
---

# EXPR-{paper}: $TITLE

## Purpose

[What hypothesis this tests and why it matters]

## Pre-Registration

**Locked before experiment runs:**

| Element | Value | Git Hash |
|---------|-------|----------|
| Hypothesis | H{paper}.{n} | TBD |
| Primary Outcome | [measure] | TBD |
| Target | [threshold] | TBD |
| Analysis Plan | [how to interpret] | TBD |
| Pre-registered | YYYY-MM-DD | TBD |

## Hypotheses Tested

| ID | Statement | Target | Status |
|----|-----------|--------|--------|
| H{paper}.{n} | [statement] | [target] | PENDING |

## Method

[Detailed description of what you'll do]

### Procedure

1. [Step 1]
2. [Step 2]
3. [Step 3]

### Measures

| Measure | ID | Unit | How Collected |
|---------|----|------|---------------|
| [Name] | M-XXX | [unit] | [method] |

## Run Command

```bash
# Example run command
./run_experiment.sh --experiment EXPR-{paper}
```

## Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| [measure] | [target] | TBD | PENDING |

## Data Location

`research/experiments/EXPR-{paper}/data/`
```

### 4. Pre-Register (Critical!)

Before running:
```bash
git add research/experiments/EXPR-{paper}.md
git commit -m "exp(HDD): pre-register EXPR-{paper}"
git rev-parse HEAD  # Record this hash
```

### 5. Run Experiment

Execute the protocol on the branch. Collect data.

### 6. Handle Results

**If VALIDATED:**
```bash
# Update experiment file
# Create PR from feature branch
gh pr create --title "feat(EXPR-{paper}): Validated H{paper}.{n}"

# After review, merge to main
git checkout main && git merge exp-{description}
```

**If REFUTED:**
```bash
# Document learnings in experiment file
# DO NOT merge

# Create new idea based on learnings
/idea "Based on EXPR-{paper}: [new approach]"

# Archive branch
git checkout main && git branch -D exp-{description}
```

## Experiment States

| State | Meaning |
|-------|---------|
| `draft` | Protocol defined, not run |
| `active` | Running |
| `complete` | Finalized (validated or refuted) |
| `abandoned` | Cancelled |

## Anti-Patterns

| Don't | Instead |
|-------|---------|
| Run before pre-registration | Commit protocol first |
| Modify target after results | Create new hypothesis |
| Merge unvalidated branch | Document learnings only |
| Skip documenting refuted | Capture why it failed |

## Output

Confirm creation:
1. Experiment ID (EXPR-{paper})
2. Feature branch name
3. Pre-registration status
4. Link to hypothesis being tested
5. Reminder: **Merge only if validated**
