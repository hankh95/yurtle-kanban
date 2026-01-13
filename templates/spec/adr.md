---
id: ADR-{{NUMBER}}
title: "{{TITLE}}"
type: adr
status: proposed
priority: medium
author: null
created: {{DATE}}
decision_date: null
tags: [architecture]
supersedes: null
superseded_by: null
---

# ADR-{{NUMBER}}: {{TITLE}}

## Status

**Proposed** | Accepted | Deprecated | Superseded

## Context

What is the issue that we're seeing that motivates this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

### Positive

- Benefit 1
- Benefit 2

### Negative

- Tradeoff 1
- Tradeoff 2

### Neutral

- Side effect 1

## Alternatives Considered

### Alternative 1: [Name]

**Description:** What is this alternative?

**Pros:**
- Pro 1

**Cons:**
- Con 1

**Why rejected:** Reason

### Alternative 2: [Name]

**Description:** What is this alternative?

**Pros:**
- Pro 1

**Cons:**
- Con 1

**Why rejected:** Reason

## Implementation

If accepted, how will this be implemented?

## Related Decisions

- ADR-XXX: Related decision
- RFC-XXX: Related proposal

## References

- External resources
- Documentation

## Notes

Additional context or discussion points.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:ADR ;
   kb:id "ADR-{{NUMBER}}" ;
   kb:status kb:proposed ;
   kb:priority kb:medium ;
   kb:tag "architecture" ;
   kb:created "{{DATE}}"^^xsd:date .
```
