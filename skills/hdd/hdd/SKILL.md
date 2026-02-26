---
name: hdd
description: Hypothesis-Driven Development overview and workflow
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "[phase]"
---

# Hypothesis-Driven Development (HDD)

**Goal:** Improved software. Papers are documentation of validated improvements.

HDD is a feedback loop where experiments validate enhancements before merging:

```
IDEA -> HYPOTHESIS -> EXPERIMENT (on branch) -> RESULTS
                                                   |
                        VALIDATED -> MERGE branch -> improved software -> PAPER
                        REFUTED -> learn -> NEW IDEA -> iterate
```

## The Critical Feedback Loop

**Every experiment runs on a feature branch.** Based on results:

| Outcome | Action | Branch | What We Learn |
|---------|--------|--------|---------------|
| **VALIDATED** | Merge to main | `git merge` | Enhancement works |
| **REFUTED** | Don't merge | Archive | Why it failed |
| **NEEDS-MORE-DATA** | Keep branch | Continue | Need larger N |

## The HDD Cycle

### Phase 0: Discovery

1. **Capture Idea**: `/idea "Research question"`
2. **Literature Review**: `/literature IDEA-R-XXX "topic"`
3. **Formalize Hypothesis**: `/hypothesis PAPER-XXX "claim" --target ">=85%"`

### Phase 1-4: Build-Measure-Learn

4. **Create Branch + Implement**: `git checkout -b exp-XXX-description`
5. **Design Experiment**: `/experiment H{paper}.{n} "design"`
6. **Run Experiment**: Collect data
7. **Decide**: Merge (validated) or Learn (refuted)
8. **Document**: Update files, optionally write paper

## yurtle-kanban HDD Board

```bash
# Add HDD board
yurtle-kanban board-add research --preset hdd --path research/

# Create items
yurtle-kanban create --board research idea "Research question"
yurtle-kanban create --board research hypothesis "Testable claim"

# View board
yurtle-kanban board research
```

## Key Principles

1. **Software First**: Working code, not papers, is the goal
2. **Branch Per Experiment**: Isolate until proven
3. **Merge Only Validated**: No unproven changes
4. **Learn from Failures**: Refuted hypotheses inform new ideas

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/idea` | Capture research idea |
| `/literature` | LLM-assisted review |
| `/hypothesis` | Formalize testable claim |
| `/experiment` | Design and run experiment |
