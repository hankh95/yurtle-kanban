---
id: SPIKE-{{NUMBER}}
title: "{{TITLE}}"
type: spike
status: draft
priority: medium
assignee: null
created: {{DATE}}
timebox: 2d
tags: [research]
---

# SPIKE-{{NUMBER}}: {{TITLE}}

## Question

What are we trying to answer or learn?

## Context

Why is this research needed? What decision depends on the outcome?

## Timebox

**Duration:** 2 days (adjust as needed)

## Scope

### In Scope

- Investigation area 1
- Investigation area 2

### Out of Scope

- What we're NOT investigating

## Approach

How will we investigate?

1. Step 1
2. Step 2
3. Step 3

## Success Criteria

What will we know when the spike is complete?

- [ ] Answer to question 1
- [ ] Answer to question 2
- [ ] Recommendation documented

## Findings

### Summary

(To be filled in after investigation)

### Details

#### Finding 1

Details...

#### Finding 2

Details...

### Recommendation

Based on findings, we recommend...

## Follow-Up Actions

- [ ] RFC-XXX: If proposal needed
- [ ] SPEC-XXX: If specification needed
- [ ] TASK-XXX: If implementation needed

## References

- Resources consulted
- Documentation reviewed

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Spike ;
   kb:id "SPIKE-{{NUMBER}}" ;
   kb:status kb:draft ;
   kb:priority kb:medium ;
   kb:tag "research" ;
   kb:created "{{DATE}}"^^xsd:date .
```
