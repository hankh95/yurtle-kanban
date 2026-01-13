---
id: HAZ-{{NUMBER}}
title: "{{TITLE}}"
type: hazard
status: harbor
priority: critical
reporter: null
created: {{DATE}}
tags: []
---

# HAZ-{{NUMBER}}: {{TITLE}}

## Hazard Report

### Description

What danger or problem has been identified?

### Impact

What damage could this cause if not addressed?

### First Observed

When and where was this hazard first noticed?

## Investigation

### Cause Analysis

Root cause investigation notes.

### Affected Systems

What parts of the ship/project are affected?

## Resolution

### Proposed Fix

How to eliminate or mitigate the hazard.

### Verification

How to confirm the hazard is resolved.

## Ship's Log

### {{DATE}}

Hazard reported.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Hazard ;
   kb:id "HAZ-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:critical ;
   kb:created "{{DATE}}"^^xsd:date .
```
