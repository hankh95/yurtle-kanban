---
id: FEAT-{{NUMBER}}
title: "{{TITLE}}"
type: feature
status: backlog
priority: medium
assignee: null
created: {{DATE}}
tags: []
---

# {{TITLE}}

## Summary

Brief description of the feature.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Design Notes

Add design considerations, technical approach, or mockups.

## Dependencies

List any dependencies on other features or external factors.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Feature ;
   kb:id "FEAT-{{NUMBER}}" ;
   kb:status kb:backlog ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
