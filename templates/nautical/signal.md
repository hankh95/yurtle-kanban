---
id: SIG-{{NUMBER}}
title: "{{TITLE}}"
type: signal
status: harbor
priority: low
spotter: null
created: {{DATE}}
tags: []
---

# SIG-{{NUMBER}}: {{TITLE}}

## Signal Received

What observation or idea has been spotted?

## Interpretation

What does this signal mean for the voyage?

## Potential Value

- Opportunity 1
- Opportunity 2
- Opportunity 3

## Questions to Explore

- Question 1?
- Question 2?

## Recommended Action

Should we investigate further? Convert to expedition?

### Feasibility Assessment

- Technical complexity:
- Resource requirements:
- Strategic alignment:

## Related Signals

Other observations that may be connected.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Signal ;
   kb:id "SIG-{{NUMBER}}" ;
   kb:status kb:harbor ;
   kb:priority kb:low ;
   kb:created "{{DATE}}"^^xsd:date .
```
