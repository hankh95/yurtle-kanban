---
name: hypothesis
description: Create a formal hypothesis for HDD workflow
disable-model-invocation: true
allowed-tools: Bash, Write, Read, Grep, Glob
argument-hint: "<paper-number> \"hypothesis statement\" --target \"threshold\""
---

# Create Hypothesis

Create a formal, testable hypothesis as part of HDD.

## Overview

A hypothesis is a testable claim with a measurable target. It must be:
- **Falsifiable**: Can be proven wrong
- **Measurable**: Has a specific metric and threshold
- **Linked**: Connected to a paper and (later) an experiment

## Hypothesis Format

```
H{paper}.{n}: [Statement of testable claim] - Target: [threshold]
```

**Examples:**
- `H42.1: Redis caching reduces p99 latency by >=50%` - Target: >=50%
- `H15.2: Static analysis catches >=30% more bugs` - Target: >=30%

## Steps

### 1. Check Paper Exists

```bash
# Verify paper exists and get current hypothesis count
grep "Paper $PAPER_NUMBER" research/papers/
grep "^| H$PAPER_NUMBER\." research/hypotheses/
```

### 2. Determine Hypothesis Number

Check existing hypotheses for this paper and use next number.

### 3. Create via yurtle-kanban

```bash
yurtle-kanban create --board research hypothesis "H{paper}.{n}: $STATEMENT" --push
```

Or manually create `research/hypotheses/H{paper}.{n}.md`:

```markdown
---
id: H{paper}.{n}
type: hypothesis
paper: Paper {paper}
statement: "$STATEMENT"
target: "$TARGET"
status: draft
created: YYYY-MM-DD
---

# H{paper}.{n}: $STATEMENT

## Hypothesis

**Statement:** $STATEMENT

**Target:** $TARGET

**Null Hypothesis:** [What we'd conclude if target NOT met]

## Rationale

[Why we expect this to be true]

## Measurement

| Measure | ID | Unit | How Collected |
|---------|-----|------|---------------|
| [Primary] | M-XXX | [unit] | [method] |

## Related

- Paper: Paper {paper}
- Literature: LIT-XXX
- Experiment: TBD (created after hypothesis)
```

### 4. Commit

```bash
git add research/hypotheses/H{paper}.{n}.md
git commit -m "hyp(HDD): create H{paper}.{n}"
```

## Hypothesis States

| State | Meaning |
|-------|---------|
| `draft` | Not yet tested |
| `active` | Experiment in progress |
| `complete` | Validated or Refuted |
| `abandoned` | Superseded |

## Good vs Bad Hypotheses

**Good (testable with clear threshold):**
- "Caching reduces p99 latency to <=100ms"
- "Batch processing improves throughput by >=40%"

**Bad (vague, not measurable):**
- "The system will be faster"
- "Users will prefer our approach"
- "It will work better"

## Output

Confirm creation:
1. Show hypothesis ID (H{paper}.{n})
2. Suggest next step: `/experiment H{paper}.{n} "design"`
