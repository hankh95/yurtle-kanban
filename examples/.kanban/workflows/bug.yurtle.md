---
type: kanban-workflow
id: bug-workflow
version: 1
applies_to: bug
---

# Bug Workflow

Simplified workflow for bug tracking. Bugs can skip the review stage
for quick fixes.

## State Machine

```
  +---------+      +-------------+      +------+
  | Backlog | ---> | In Progress | ---> | Done |
  +---------+      +-------------+      +------+
       |                 |
       v                 v
  +---------+      +---------+
  |  Ready  | <--> | Blocked |
  +---------+      +---------+
```

## State Definitions

```yurtle
@prefix workflow: <https://yurtle.dev/kanban/workflow/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@base <https://yurtle.dev/kanban/workflow/bug/> .

<state/backlog>
    a workflow:State ;
    workflow:name "Backlog" ;
    workflow:isInitial "true"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/ready>,<state/in_progress>" ;
    workflow:description "Reported bugs waiting for triage" .

<state/ready>
    a workflow:State ;
    workflow:name "Ready" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/in_progress>,<state/blocked>,<state/backlog>" ;
    workflow:description "Triaged and ready to fix" .

<state/in_progress>
    a workflow:State ;
    workflow:name "In Progress" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/done>,<state/blocked>,<state/ready>" ;
    workflow:description "Actively being fixed" .

<state/blocked>
    a workflow:State ;
    workflow:name "Blocked" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/ready>,<state/in_progress>" ;
    workflow:description "Cannot be fixed due to blocker" .

<state/done>
    a workflow:State ;
    workflow:name "Done" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "true"^^xsd:boolean ;
    workflow:transitions "" ;
    workflow:description "Bug fixed and verified" .
```
