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

## Prior Art: nusy-product-team `kanban-ci.yml`

`nusy-product-team/.github/workflows/kanban-ci.yml` (EXP-930) already has a
4-phase kanban CI pipeline including an `auto-move` job. What it does:

- Triggers on `pull_request.closed` + `merged == true`
- Extracts expedition ID from `exp-*` branch names only
- Moves to `review` (not `done`) — agent does final verification
- Commits and pushes via `github-actions[bot]`

**Limitations to generalize:**
- Hardcoded to `exp-*` prefix only — no CHORE, FEAT, VOY, HYP, etc.
- No PR body keyword support (`Closes EXP-XXX`)
- Moves to `review` only — should be configurable (`done` or `review`)
- Lives in nusy-product-team — not reusable by other yurtle-kanban consumers

This expedition ships the generalized version **in yurtle-kanban itself**,
so any repo (including nusy with Bosun/HDD workflows) can adopt it.

## Existing yurtle-kanban Workflows

- **`ci.yml`** — Tests + linting + type-check on PRs/pushes
- **`kanban-board.yml`** — Regenerates static HTML board on push to main

The auto-close action feeds naturally into `kanban-board.yml`: PR merge →
auto-close moves item to `done` → that push triggers board regeneration.

## Scope

1. **Reusable workflow** (`.github/workflows/kanban-auto-close.yml`) shipped
   with yurtle-kanban — consuming repos reference it via
   `uses: hankh95/yurtle-kanban/.github/workflows/kanban-auto-close.yml@main`
2. ID extraction logic supporting all item prefixes (EXP, CHORE, FEAT, VOY,
   EPIC, BUG, HYP, LIT, PAPER, IDEA, MEASURE) from both branch names and
   PR body keywords
3. Configurable target status (`done` or `review`) via workflow input
4. Documentation in README for adoption
5. After shipping: update nusy-product-team `kanban-ci.yml` to replace its
   `auto-move` job with the reusable workflow from yurtle-kanban

## Non-Goals

- GitLab / Bitbucket support (GitHub Actions only for now)
- Reopening items if a PR is reverted
- Replacing the other 3 phases of nusy's `kanban-ci.yml` (validate,
  annotate, label) — those are nusy-specific

## Acceptance Criteria

- [ ] Merging a PR with `Closes EXP-XXX` in the body moves that item to done
- [ ] Merging a PR on branch `exp-xxx-*` moves that item to done (fallback)
- [ ] Works with all item prefixes (EXP, CHORE, FEAT, VOY, HYP, etc.)
- [ ] Multiple `Closes` keywords in one PR move multiple items
- [ ] Target status is configurable (`done` or `review`)
- [ ] No-op if item is already done or ID not found (no error)
- [ ] Ships as reusable workflow in yurtle-kanban repo
- [ ] Documented for adoption by consuming repos
