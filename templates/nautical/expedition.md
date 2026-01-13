---
id: EXP-{{NUMBER}}
title: "{{TITLE}}"
type: expedition
status: harbor
priority: medium
assignee: null
created: {{DATE}}
tags: []
related: []
depends_on: []
---

# EXP-{{NUMBER}}: {{TITLE}}

## Objective

What this expedition aims to achieve.

## Hypothesis

The core assumption to validate. What we believe will work.

## Success Criteria

- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Measurable outcome 3

## Phases

### Phase 1: Foundation

- [ ] Deliverable 1
- [ ] Deliverable 2

### Phase 2: Implementation

- [ ] Deliverable 3
- [ ] Deliverable 4

### Phase 3: Validation

- [ ] Test/verify results
- [ ] Document findings

## Navigation Notes

Technical approach, constraints, and considerations.

## Ship's Log

### {{DATE}}

Initial expedition planning.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Expedition ;
   kb:id "EXP-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
