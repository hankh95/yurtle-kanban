---
id: RFC-{{NUMBER}}
title: "{{TITLE}}"
type: rfc
status: draft
priority: medium
author: null
created: {{DATE}}
reviewers: []
tags: []
---

# RFC-{{NUMBER}}: {{TITLE}}

## Status

| Field | Value |
|-------|-------|
| Status | Draft |
| Author | |
| Created | {{DATE}} |
| Updated | |
| Reviewers | |

## Summary

One paragraph explanation of the proposal.

## Motivation

Why are we doing this? What problem does it solve? What use cases does it support?

## Detailed Design

### Overview

High-level description of the proposed solution.

### Implementation Details

Technical details of how this will work.

### API Changes

Any changes to public APIs or interfaces.

## Alternatives Considered

What other approaches were considered? Why were they rejected?

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| Option A | | | |
| Option B | | | |

## Drawbacks

Why should we *not* do this?

## Open Questions

- [ ] Question 1?
- [ ] Question 2?

## Implementation Plan

If accepted, how will this be implemented?

1. Phase 1: ...
2. Phase 2: ...

## References

- Link to related RFCs
- Link to external resources

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:RFC ;
   kb:id "RFC-{{NUMBER}}" ;
   kb:status kb:draft ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
