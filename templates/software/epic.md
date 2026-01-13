---
id: EPIC-{{NUMBER}}
title: "{{TITLE}}"
type: epic
status: backlog
priority: medium
assignee: null
created: {{DATE}}
tags: []
children: []
---

# {{TITLE}}

## Vision

High-level description of what this epic achieves.

## Goals

- Goal 1
- Goal 2
- Goal 3

## Success Metrics

How will we know this epic is successful?

## Features

List of features that make up this epic:

- [ ] FEAT-XXX: Feature 1
- [ ] FEAT-XXX: Feature 2
- [ ] FEAT-XXX: Feature 3

## Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Description | Pending |
| Phase 2 | Description | Pending |
| Phase 3 | Description | Pending |

## Risks

- Risk 1: Mitigation strategy
- Risk 2: Mitigation strategy

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Epic ;
   kb:id "EPIC-{{NUMBER}}" ;
   kb:status kb:backlog ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
