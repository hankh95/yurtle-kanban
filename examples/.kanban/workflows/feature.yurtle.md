---
type: kanban-workflow
id: feature-workflow
version: 1
applies_to: feature
---

# Feature Workflow

Defines valid state transitions for features. This workflow is enforced
by the kanban service when moving items between columns.

## State Machine

Features follow a defined lifecycle from backlog to completion:

```
  +---------+      +-------+      +-------------+
  | Backlog | ---> | Ready | ---> | In Progress |
  +---------+      +-------+      +-------------+
                       |                 |
                       v                 v
                  +---------+      +----------+
                  | Blocked |<---->|  Review  |
                  +---------+      +----------+
                                        |
                                        v
                                   +------+
                                   | Done |
                                   +------+
```

## State Definitions

```yurtle
@prefix workflow: <https://yurtle.dev/kanban/workflow/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@base <https://yurtle.dev/kanban/workflow/feature/> .

<state/backlog>
    a workflow:State ;
    workflow:name "Backlog" ;
    workflow:isInitial "true"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/ready>" ;
    workflow:description "Ideas and features waiting to be prioritized" .

<state/ready>
    a workflow:State ;
    workflow:name "Ready" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/in_progress>,<state/blocked>,<state/backlog>" ;
    workflow:description "Prioritized and ready to be worked on" .

<state/in_progress>
    a workflow:State ;
    workflow:name "In Progress" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/review>,<state/blocked>,<state/ready>" ;
    workflow:description "Actively being implemented" .

<state/blocked>
    a workflow:State ;
    workflow:name "Blocked" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/ready>,<state/in_progress>" ;
    workflow:description "Waiting on external dependency or blocker" .

<state/review>
    a workflow:State ;
    workflow:name "Review" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "false"^^xsd:boolean ;
    workflow:transitions "<state/done>,<state/in_progress>" ;
    workflow:description "Implementation complete, awaiting review" .

<state/done>
    a workflow:State ;
    workflow:name "Done" ;
    workflow:isInitial "false"^^xsd:boolean ;
    workflow:isTerminal "true"^^xsd:boolean ;
    workflow:transitions "" ;
    workflow:description "Feature completed and deployed" .
```

## Transition Rules

Optional validation rules that can be applied when entering states:

```yurtle
@prefix workflow: <https://yurtle.dev/kanban/workflow/> .
@base <https://yurtle.dev/kanban/workflow/feature/> .

<rule/require_assignee>
    a workflow:Rule ;
    workflow:appliesTo <state/in_progress> ;
    workflow:condition "item.assignee is not None" ;
    workflow:message "Must have an assignee before starting work" .

<rule/require_description>
    a workflow:Rule ;
    workflow:appliesTo <state/ready> ;
    workflow:condition "len(item.description or '') > 10" ;
    workflow:message "Description should be at least 10 characters" .
```

## State Descriptions

| State | Entry Criteria | Exit Criteria |
|-------|----------------|---------------|
| **Backlog** | Idea captured | Prioritized for work |
| **Ready** | Scope clear, prioritized | Assigned and started |
| **In Progress** | Actively being worked | Work complete, needs review |
| **Blocked** | External dependency or issue | Blocker resolved |
| **Review** | Implementation complete | Reviewed and approved |
| **Done** | All acceptance criteria met | N/A (terminal) |
