---
id: VOY-{{NUMBER}}
title: "{{TITLE}}"
type: voyage
status: harbor
priority: high
captain: null
created: {{DATE}}
tags: []
expeditions: []
---

# VOY-{{NUMBER}}: {{TITLE}}

> **Strategic Goal:** High-level description of what this voyage achieves.

## Destination

Where we're heading and why it matters.

## Charted Course

### Leg 1: Departure

Expeditions in this phase:
- [ ] EXP-XXX: Expedition 1
- [ ] EXP-XXX: Expedition 2

### Leg 2: Open Waters

Expeditions in this phase:
- [ ] EXP-XXX: Expedition 3
- [ ] EXP-XXX: Expedition 4

### Leg 3: Approach

Expeditions in this phase:
- [ ] EXP-XXX: Expedition 5

## Success Metrics

How will we know we've arrived?

- Metric 1: Target value
- Metric 2: Target value

## Hazards & Risks

- Hazard 1: Mitigation strategy
- Hazard 2: Mitigation strategy

## Captain's Notes

Strategic considerations and decisions.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Voyage ;
   kb:id "VOY-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:high ;
   kb:created "{{DATE}}"^^xsd:date .
```
