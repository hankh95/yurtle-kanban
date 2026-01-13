---
id: ISSUE-{{NUMBER}}
title: "{{TITLE}}"
type: issue
status: draft
priority: high
reporter: null
assignee: null
created: {{DATE}}
tags: []
---

# ISSUE-{{NUMBER}}: {{TITLE}}

## Summary

Brief description of the issue.

## Environment

- **Version:**
- **Platform:**
- **Configuration:**

## Steps to Reproduce

1. Step 1
2. Step 2
3. Step 3

## Expected Behavior

What should happen?

## Actual Behavior

What actually happens?

## Impact

How does this affect users/system?

- **Severity:** Critical / High / Medium / Low
- **Affected Users:** All / Some / Few
- **Workaround Available:** Yes / No

## Root Cause Analysis

Investigation notes on what caused the issue.

## Proposed Fix

How to resolve the issue.

## Verification

How to verify the fix works.

- [ ] Verification step 1
- [ ] Verification step 2

## Related

- Related issues
- Related specs

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Issue ;
   kb:id "ISSUE-{{NUMBER}}" ;
   kb:status kb:draft ;
   kb:priority kb:high ;
   kb:created "{{DATE}}"^^xsd:date .
```
