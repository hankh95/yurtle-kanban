---
id: EXP-002
title: "Auto-close kanban items on PR merge"
type: expedition
status: backlog
priority: medium
created: 2026-02-27
depends_on: []
---

# EXP-002: Auto-close kanban items on PR merge

## Context

When a PR is merged on GitHub, any linked issues close automatically via
`Closes #XX` keywords. But yurtle-kanban items (EXP-XXX, CHORE-XXX, etc.)
still require a manual `yurtle-kanban move XXX done` afterward. This is easy
to forget and leaves the board out of sync with reality.

## Goal

Ship a GitHub Action that automatically moves linked kanban items to `done`
when a PR merges — mirroring GitHub's own `Closes` convention.

## Design

### Detection: two complementary strategies

1. **Branch name convention** — Parse the merged branch name for item ID
   prefixes (e.g., `exp-1023-hdd-knowledge-blocks` → `EXP-1023`). Already
   follows our naming convention, zero extra effort for developers.

2. **PR body keyword** — Scan for `Closes EXP-1023` / `Closes CHORE-055`
   patterns in the PR body. More explicit, supports multiple items, mirrors
   GitHub's own pattern.

Both run together: keywords take priority, branch name is the fallback.

### Action implementation

- **Trigger:** `pull_request` event with `closed` + `merged` condition
- **Inputs:** configurable item ID pattern (default: common prefixes like
  EXP, CHORE, FEAT, VOY, EPIC, BUG, etc.)
- **Steps:**
  1. Extract item IDs from PR body keywords and/or branch name
  2. For each ID, run `yurtle-kanban move <ID> done`
  3. Commit and push the updated frontmatter
- **Ships as:** A reusable workflow or composite action in `.github/workflows/`
  that any repo using yurtle-kanban can reference

### Supported patterns

```
# PR body keywords (case-insensitive)
Closes EXP-1023
Fixes CHORE-055
Resolves FEAT-042

# Branch name (first matching prefix)
exp-1023-hdd-knowledge-blocks → EXP-1023
chore-055-document-dual-repr  → CHORE-055
```

## Existing Workflows

- **`ci.yml`** — Tests + linting + type-check on PRs/pushes
- **`kanban-board.yml`** — Regenerates static HTML board on push to main
  when work item files change

The auto-close action feeds naturally into `kanban-board.yml`: PR merge →
auto-close moves item to `done` → that push triggers board regeneration.

## Scope

1. GitHub Action workflow file (`.github/workflows/kanban-auto-close.yml`)
2. Helper script or inline logic to parse item IDs from branch + body
3. Documentation in README for adoption by other repos

## Non-Goals

- GitLab / Bitbucket support (GitHub Actions only for now)
- Moving to statuses other than `done` (e.g., `review`)
- Reopening items if a PR is reverted

## Acceptance Criteria

- [ ] Merging a PR with `Closes EXP-XXX` in the body moves that item to done
- [ ] Merging a PR on branch `exp-xxx-*` moves that item to done (fallback)
- [ ] Multiple `Closes` keywords in one PR move multiple items
- [ ] No-op if item is already done or ID not found (no error)
- [ ] Action is documented for adoption by consuming repos
