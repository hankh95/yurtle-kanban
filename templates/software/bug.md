---
id: BUG-{{NUMBER}}
title: "{{TITLE}}"
type: bug
status: backlog
priority: high
assignee: null
created: {{DATE}}
tags: []
---

# {{TITLE}}

## Bug Report

### Description

What is happening?

### Expected Behavior

What should happen instead?

### Steps to Reproduce

1. Step 1
2. Step 2
3. Step 3

### Environment

- OS:
- Version:
- Browser/Runtime:

## Investigation

Add notes from investigating the bug.

## Fix

Description of the fix once implemented.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Bug ;
   kb:id "BUG-{{NUMBER}}" ;
   kb:status kb:backlog ;
   kb:priority kb:high ;
   kb:created "{{DATE}}"^^xsd:date .
```
