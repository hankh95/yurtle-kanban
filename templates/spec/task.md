---
id: TASK-{{NUMBER}}
title: "{{TITLE}}"
type: task
status: draft
priority: medium
assignee: null
created: {{DATE}}
spec: null
parent: null
tags: []
---

# TASK-{{NUMBER}}: {{TITLE}}

## Description

What needs to be implemented.

## Specification Reference

**Spec:** SPEC-XXX (if applicable)

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Checklist

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3
- [ ] Write tests
- [ ] Update documentation

## Technical Notes

Implementation details and considerations.

## Testing

How to test this task.

## Definition of Done

- [ ] Code complete
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Task ;
   kb:id "TASK-{{NUMBER}}" ;
   kb:status kb:draft ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
