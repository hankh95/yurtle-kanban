---
id: TASK-{{NUMBER}}
title: "{{TITLE}}"
type: task
status: backlog
priority: medium
assignee: null
created: {{DATE}}
tags: []
parent: null
---

# {{TITLE}}

## Description

What needs to be done.

## Checklist

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Notes

Additional context or implementation notes.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Task ;
   kb:id "TASK-{{NUMBER}}" ;
   kb:status kb:backlog ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
