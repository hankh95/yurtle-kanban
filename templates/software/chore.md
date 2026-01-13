---
id: CHORE-{{NUMBER}}
title: "{{TITLE}}"
type: task
status: backlog
priority: low
assignee: null
created: {{DATE}}
tags: [chore, maintenance]
---

# {{TITLE}}

## Problem Statement

What needs to be cleaned up, maintained, or improved?

## Work Items

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Completion Criteria

How to know when the chore is done.

## Notes

Additional context or considerations.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Task ;
   kb:id "CHORE-{{NUMBER}}" ;
   kb:status kb:backlog ;
   kb:priority kb:low ;
   kb:tag "chore", "maintenance" ;
   kb:created "{{DATE}}"^^xsd:date .
```
