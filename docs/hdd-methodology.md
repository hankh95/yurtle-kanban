# Hypothesis-Driven Development: Applying the Scientific Method to AI Engineering

*A methodology guide for teams using yurtle-kanban to run rigorous, pre-registered experiments alongside their development work.*

---

Four out of five hypotheses failed. And it was one of the most productive weeks we've
ever had.

I'll get to that story. But first, the problem.

## The Problem Nobody Talks About

If you're building AI systems — agents, RAG pipelines, fine-tuned models, knowledge
graphs — you already know that unit tests are necessary and completely insufficient.

Tests tell you whether a function returns the right value. They can't tell you whether
your agent *understands* what it learned. Whether your orchestrator proposes sensible
work assignments. Whether knowledge that one agent learns transfers meaningfully to
another. These are system-level questions, and assert statements don't reach them.

Most teams handle this informally. You run the system, look at the data, find something
that looks good, and call it a win. The research community has a name for this:
*HARKing* — Hypothesizing After Results are Known. You look at the data, find something
promising, and retroactively frame it as what you were testing all along.

Nobody does this deliberately. But without pre-registered targets committed to version
control *before* data collection, there's no way to prove you weren't.

The evidence exists, but it's post-hoc and unfalsifiable. That's not science. That's
storytelling with numbers.

## What Hypothesis-Driven Development Actually Is

Hypothesis-Driven Development (HDD) is what happens when you take the scientific method
seriously and apply it to engineering. The idea isn't new — Eric Ries introduced
build-measure-learn loops in 2011, ThoughtWorks has written about hypothesis-driven
product development, and pre-registration has been standard in clinical research for
two decades.

What yurtle-kanban does is wire these practices into a toolchain-integrated workflow.
The cycle is:

```
IDEA -> LITERATURE -> HYPOTHESIS -> EXPERIMENT -> ANALYSIS
```

1. **Capture the idea**: "Would entity linking help agents understand what they're reading
   earlier in training?"
2. **Review existing work**: What does the literature say? What targets are realistic?
3. **Formalize a hypothesis**: "Entity linking increases knowledge graph density by at
   least 15%." Specific. Quantitative. Stated in advance.
4. **Design and run the experiment**: Train one agent with the feature, one without.
   Compare. Measure.
5. **Analyze**: Did we hit the target, or didn't we?

The discipline lives in step 3. The hypothesis and its success threshold are committed
to version control *before* any data is collected. The research community calls this
**pre-registration**. It means you can't move the goalposts. You said 15%. Either you
hit it or you didn't.

## How It Differs from What You Already Know

If you're a software engineer, you're thinking: "This sounds like TDD." You're close.

| | TDD | BDD | HDD |
|---|---|---|---|
| **Unit of work** | Function | Behavior | Hypothesis |
| **What you write first** | A failing test | A scenario spec | A falsifiable claim |
| **Pass criteria** | Assert equals | Gherkin steps | Quantitative target |
| **Output** | Working code | Working feature | Validated (or refuted) claim |
| **What a failure means** | Bug | Regression | Valid science |
| **Discovery phase** | None | None | Literature review |

Two differences matter.

First: HDD starts with a question, not a test. Before you formalize a hypothesis, you
do a literature review — often LLM-assisted — to understand what prior work exists and
what targets are realistic. TDD assumes you know what to build. HDD assumes you need
to figure out what's even worth building.

Second: a refuted hypothesis isn't a bug. It's data. You document it, learn from it,
and redirect. In TDD, red means "fix this." In HDD, red means "now we know something
we didn't know before." The teams that learn fastest approach truth faster. Period.

## The Bloom Discovery: A Full Cycle

One of our early research questions: **"How do we measure whether an AI agent actually
understands what it knows?"**

Standard LLM benchmarks test recall. They ask a question, the model answers, you check.
But recall isn't understanding. An agent might score 92% and have no idea *why* any of
its answers are correct.

We captured the idea in 30 seconds:

> IDEA-R-002: "How do we measure agent cognition fairly?"

Then an LLM-assisted literature review. We asked: "Is there a standard in human
education for measuring understanding versus memorization?"

Answer: **Bloom's Taxonomy** (1956, revised 2001). Six cognitive levels. L1 is
Remember — recall facts. L2 is Understand — explain concepts in your own words.
L3 is Apply. L4 is Analyze. And so on up to Create.

The discovery that mattered: **no existing LLM benchmark tests L2, L3, or L4.** They
all test L1 recall with different question formats.

Hypothesis:

> H122.1: "Bloom-based assessment captures understanding gaps that standard
> benchmarks miss."

Experiment: assess the same agent on the same material with both approaches.

Results:

| Level | Standard Benchmark | Bloom Assessment |
|-------|-------------------|-----------------|
| L1 (Remember) | 92% | 91% |
| L2 (Understand) | *not tested* | 67% |
| L3 (Apply) | *not tested* | 54% |
| L4 (Analyze) | *not tested* | 41% |

An agent scoring 92% on recall demonstrates actual understanding 67% of the time.
Applies knowledge in novel situations barely half the time. The standard benchmark
had zero visibility into any of this.

Hypothesis validated. That capability came from a 30-second idea, an afternoon of
literature review, and one well-designed experiment.

## When Four Out of Five Hypotheses Fail

Now the story I promised. Our favorite example of HDD working — *because* it went
sideways.

The idea: **"Can agents predict what the user will ask next?"** Predictive processing.
We formulated five hypotheses with specific targets and ran them.

| Hypothesis | Target | Actual | Status |
|-----------|--------|--------|--------|
| H118.1: Meaningful predictions | >=60% accuracy | 54% | **FAILED** |
| H118.2: Improves over sessions | +15pp over 10 sessions | +0pp | **FAILED** |
| H118.3: Surprise-driven gap detection | >=70% precision | 13.8% | **FAILED** |
| H118.4: Prediction calibration | ECE <15% | ECE = 45% | **FAILED** |
| H118.5: Trackable infrastructure | 136 tests pass | 136 pass | **VALIDATED** |

The plumbing worked. The cognition was fundamentally broken.

In a traditional process, this is a disaster. Months of work, core idea doesn't hold
up, quietly shelve it.

But we had something better than working code. We had **specific, documented failure
modes.** Each failed hypothesis pointed to a concrete structural problem:

- **H118.2 failed** because there were no competing prediction schemas.
- **H118.3 failed** because there was no mechanism to detect cognitive distortions.
- **H118.4 failed** because there was no distinction between fast intuitive
  responses and slower reflective ones.

Then the insight: each failure mapped to a known mechanism from **Beck's Cognitive
Behavioral Therapy** framework.

| Failure | Missing CBT Mechanism | Solution |
|---------|----------------------|----------|
| No improvement over time | No competing schemas | PredictionSchemaRegistry |
| Low precision | No distortion detection | DistortionDetector |
| Poor calibration | No dual processing | DualProcessPipeline |

Clinical psychology had already solved these problems — just not for AI systems. The
failures didn't tell us what was wrong. They told us **where to look for answers.**

Without HDD: build for months on conviction, discover problems too late, nothing to
show for it. With HDD: five tests in days, exact failure modes identified, immediate
redirect. Every failure pointed to a specific missing mechanism.

## The Tooling That Makes It Frictionless

If this sounds heavy in process, it shouldn't. yurtle-kanban makes it nearly invisible.

### Setting Up the Research Board

```bash
# Add an HDD research board alongside your development board
yurtle-kanban board-add research --preset hdd --path research/

# View both boards
yurtle-kanban board           # Development work
yurtle-kanban board research  # HDD research items
yurtle-kanban board --all     # Everything
```

The separation matters. Development flows through backlog -> in-progress -> done.
Research accumulates: ideas become literature reviews become hypotheses become
experiments. They're different rhythms, but they feed each other. A validated
hypothesis becomes a development task. A development task surfaces a question that
becomes a new idea.

### The HDD Cycle in Practice

```bash
# Phase 0: Capture an idea (30 seconds)
yurtle-kanban idea create "Would entity linking help early understanding?" \
    --type research --push

# Phase 0: Literature review
yurtle-kanban literature create "Entity linking for knowledge graphs" \
    --idea IDEA-R-007 --push

# Phase 1: Formalize a hypothesis (pre-registration!)
yurtle-kanban hypothesis create "Entity linking increases graph density >=15%" \
    --paper 121 --target ">=15%" --push

# Phase 2: Create experiment protocol
yurtle-kanban experiment create EXPR-121 \
    --hypothesis H121.1 --title "Entity linking A/B study" --push

# Phase 3: Run the experiment (timestamped, reproducible)
yurtle-kanban experiment run EXPR-121 --being my-agent-v2
yurtle-kanban experiment run EXPR-121 --being my-agent-v2 \
    --params "enrichment=wikidata,threshold=0.7"

# Check run history
yurtle-kanban experiment status EXPR-121
yurtle-kanban experiment status EXPR-121 --json  # For scripting
```

Each command creates the artifact from a template, allocates a unique ID, commits to
git, and pushes — atomically. The artifact's existence is in version control the moment
it's created. No forgetting to commit. No ID collisions between agents working in
parallel.

### Defining Measures

```bash
# Create formal metrics
yurtle-kanban measure create "Graph Density" --unit percent --category accuracy --push
yurtle-kanban measure create "Reasoning Accuracy" --unit percent --category accuracy --push
```

### Validation and Cross-Referencing

```bash
# Generate a cross-referenced registry of all HDD artifacts
yurtle-kanban hdd registry

# Validate bidirectional links (papers <-> hypotheses <-> experiments)
yurtle-kanban hdd validate
yurtle-kanban hdd validate --strict   # Warnings = errors (for CI)
yurtle-kanban hdd validate --json     # Machine-readable output
```

The `hdd validate` command catches broken references: a hypothesis that claims to
belong to a paper that doesn't exist, an experiment missing its hypothesis link, a
measure referenced but never defined. Run it in CI and broken research links fail
the build.

## Every File is Human-Readable and Machine-Queryable

Every artifact is a **Yurtle file** — markdown with RDF triples in fenced code blocks.
Humans read it in a text editor. Machines query it with graph operations. Same file,
two audiences, no synchronization problem.

A hypothesis file looks like this:

    ---
    id: H121.1
    title: "Entity linking increases graph density >=15%"
    status: active
    paper: 121
    target: ">=15%"
    created: 2026-02-15
    ---

    ```turtle
    @prefix hdd: <https://example.org/hdd/> .
    @prefix paper: <https://example.org/paper/> .

    <#H121.1> a hdd:Hypothesis ;
        hdd:paper paper:121 ;
        hdd:target ">=15%" ;
        hdd:status "active" ;
        hdd:measure "graph_density" .
    ```

    # H121.1: Entity Linking Increases Graph Density

    ## Claim
    Entity linking during ingestion increases knowledge graph density
    by at least 15% compared to baseline ingestion without entity linking.

    ## Method
    A/B comparison: train two agents on identical corpora, one with
    entity linking enabled.

    ## Success Criteria
    Graph density (edges / nodes) increases by >= 15%.

Below the frontmatter: plain markdown anyone can read. Inside the turtle block: RDF
triples you can query. "Show me all active hypotheses for paper 121." "Which experiments
have no results yet?" "What's the validation rate across all papers?"

This dual format is what makes pre-registration verifiable by both humans and automated
analysis. The experiment protocol is markdown you can read. The success criteria are
structured data a script can check.

## Git as the Arbiter of Truth

Pre-registration deserves its own section because it's the heart of HDD.

Before running an experiment, you write a file specifying: the hypothesis, the outcome
measure, the target threshold, the analysis plan, the exact command to reproduce. Then
you commit to git, record the hash, and only *then* start collecting data.

If someone challenges the results — "did you really set that target before you saw the
data?" — you point to the commit hash. Hypothesis committed at 2:00 PM. Data collection
started at 2:15 PM. Timestamps are immutable. No institutional review board needed.
Git is the arbiter.

This means you can't adjust targets after seeing data. You said 15% and got 12%? That's
a refutation. Not "well, 12% is close." Not "the target was aggressive." A refutation.
Document what you learned, create a new hypothesis with a refined target, test again.

## Dual-Board Architecture

yurtle-kanban supports multiple boards with different workflows. The standard pattern
for HDD teams is two boards:

```yaml
# .yurtle-kanban/config.yaml
boards:
  - name: development
    preset: software      # or nautical
    path: kanban-work/
    wip_limits:
      in_progress: 4
      review: 3

  - name: research
    preset: hdd
    path: research/
    wip_limits:
      active: 5           # Research can have more concurrent items
    phases:
      - discovery          # IDEA -> Literature review
      - design             # HYPOTHESIS -> Experiment protocol
      - execution          # Running experiment
      - analysis           # Comparing to targets
      - writing            # Drafting paper section

# Cross-board linking
relationships:
  implements:
    from_board: development
    to_board: research
    predicate: "expr:implements"
  spawns:
    from_board: research
    to_board: development
    predicate: "expr:spawns"
```

Research items don't count against development WIP limits. A team can have 4 features
in progress *and* 5 active experiments without hitting any limits. The boards are
separate workflows with separate rhythms, connected by cross-board relationships.

When an experiment validates a hypothesis, it spawns development work. When development
work surfaces a question, it spawns a new research idea. The research board is where
you figure out *what's worth building*. The development board is where you *build it*.

## Agent Fleet Automation

For teams running AI agent fleets — multiple coding agents working in parallel —
yurtle-kanban's HDD workflow integrates with agent orchestration.

### The Automation Loop

```
Captain ranks priority queue
    -> Bosun (LLM orchestrator) proposes work assignments
        -> Fleet dispatch reads ranked queue, spawns agents
            -> Agents complete work, create PRs
                -> Cross-agent review
                    -> Merge, clean up, dispatch next item
```

The key insight: agent orchestration and HDD reinforce each other. The Bosun reads
experiment protocols and hypothesis files to understand *what* to test. The fleet
dispatch respects WIP limits and routes tasks based on capability (training work to
GPU machines, documentation to lighter hardware). Agents complete work in isolated
git worktrees, ensuring parallel safety.

### What This Looks Like in Practice

1. **Morning scan**: The Bosun reads all backlog items, research experiments, and fleet
   state. It proposes work assignments — "EXP-1012 is ready, assign to Agent A; EXPR-130
   needs a training run, assign to GPU agent."

2. **Captain approval**: A human reviews proposals and ranks the priority queue. This
   is the human-in-the-loop that ensures agents work on the right things.

3. **Automated dispatch**: A cron job reads the ranked queue every 10 minutes. When WIP
   headroom exists, it spawns an agent in a tmux session with the expedition context.

4. **Agent execution**: The agent gets a focused prompt constructed from the expedition
   file, acceptance criteria, and fleet heuristics. It works autonomously — writes code,
   runs tests, creates a PR.

5. **Cross-review**: A different agent reviews the PR, checking for issues the
   implementing agent might have missed.

6. **Cleanup**: After merge, the monitor detects the completed session, cleans up the
   worktree, and frees the WIP slot for the next dispatch.

The fleet runs HDD cycles continuously. Experiments get proposed, approved, executed,
and analyzed — with human oversight at the approval step and full git-backed
auditability at every other step.

## What We've Learned Running HDD in Production

After a year of HDD with an AI agent fleet:

**Pre-registration prevents wishful thinking.** Before HDD, we'd run the system, look
at the data, and declare success based on whatever looked good. Now we state targets
first. It's uncomfortable. It's honest.

**Negative results are your most valuable data.** The 4/5 failure on predictive
processing was more productive than many successes. Each failure pointed to a specific
missing mechanism. If we'd declared victory based on the one passing hypothesis, we'd
have shipped broken cognitive architecture.

**Metrics should be boring.** Our fleet dashboard shows: approval rate 86%, spawn
success 95%, target met. No excitement. That's the point. If you need excitement to
validate your AI system, you don't understand your system well enough.

**Speed demands structure.** Agentic development is *fast* — three agents can ship
four features before lunch. That speed is intoxicating and dangerous. HDD prevents
shipping conclusions before the evidence is in. Without it, you drown in unverifiable
claims.

**Refutations compound.** A single refuted hypothesis teaches you one thing. A pattern
of refutations across related hypotheses reveals structural gaps. The Paper 118
failures (predictive processing) collectively pointed to missing CBT mechanisms —
a discovery no individual test could have surfaced.

## Getting Started

### Minimal Setup

```bash
# Install
pip install yurtle-kanban

# Initialize with HDD support
cd my-project
yurtle-kanban init --theme software
yurtle-kanban board-add research --preset hdd --path research/

# Start your first HDD cycle
yurtle-kanban idea create "Does X improve Y?" --type research --push
```

### The Three Rules

1. **State the target before collecting data.** Commit the hypothesis file to git
   before running the experiment. This is non-negotiable.

2. **Accept refutations as learning.** A refuted hypothesis is not a failure — it's
   data that tells you where to look next.

3. **Keep the cycle short.** IDEA -> HYPOTHESIS -> EXPERIMENT -> ANALYSIS should take
   days, not months. If it takes longer, your hypotheses are too broad.

### Integrating with CI

```bash
# Add to your CI pipeline
yurtle-kanban hdd validate --strict

# Fails if:
# - Hypotheses reference nonexistent papers
# - Experiments missing hypothesis links
# - Papers with no hypotheses defined
```

## Further Reading

- **[yurtle-kanban CLI Reference](../README.md)** — Full command documentation
- **[Theme Reference](THEMES.md)** — Software, nautical, and HDD theme details
- **[Yurtle specification](https://github.com/hankh95/yurtle)** — The Turtle-in-Markdown format
- **[yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib)** — RDFlib parser/serializer for Yurtle files
- Eric Ries, *The Lean Startup* (2011) — Build-measure-learn loops
- Jeff Gothelf & Josh Seiden, *Lean UX* (2013) — Hypothesis-driven product development
- Bloom's Taxonomy (Anderson & Krathwohl, 2001) — Cognitive level assessment framework

---

*yurtle-kanban is open source under the MIT license. HDD is a methodology, not a product
— adopt as much or as little as fits your workflow.*
