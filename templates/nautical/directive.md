---
id: DIR-{{NUMBER}}
title: "{{TITLE}}"
type: directive
status: harbor
priority: medium
issuer: captain
assignee: null
created: {{DATE}}
tags: []
parent: null
---

# DIR-{{NUMBER}}: {{TITLE}}

## Orders

Clear directive from command.

## Execution Plan

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Completion Criteria

How to know when the directive is fulfilled.

## Authority

Who issued this directive and why.

## Ship's Log

### {{DATE}}

Directive issued.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Directive ;
   kb:id "DIR-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:medium ;
   kb:created "{{DATE}}"^^xsd:date .
```
