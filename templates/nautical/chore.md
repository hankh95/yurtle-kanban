---
id: CHORE-{{NUMBER}}
title: "{{TITLE}}"
type: chore
status: harbor
priority: low
assignee: null
created: {{DATE}}
tags: [maintenance]
---

# CHORE-{{NUMBER}}: {{TITLE}}

## Problem Statement

What needs to be cleaned up, maintained, or improved?

## Work Items

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Completion Criteria

How to know when the chore is done.

## Ship's Log

### {{DATE}}

Chore identified.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Chore ;
   kb:id "CHORE-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:low ;
   kb:tag "maintenance" ;
   kb:created "{{DATE}}"^^xsd:date .
```
