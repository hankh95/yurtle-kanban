# Hypothesis-Driven Development: Applying the Scientific Method to Software Engineering

*Adapted from [Hank Head's original blog post](https://nusy.dev/blog/hypothesis-driven-development) on HDD in practice.*

---

Four out of five hypotheses failed. And it was one of the most productive weeks we've
ever had.

I'll get to that story. But first, the problem.

## The Problem Nobody Talks About

If you build AI systems — agents that learn, reason, and remember — you've
probably discovered the same uncomfortable truth: **unit tests are necessary and
completely insufficient.**

Thousands of tests tell you whether a function returns the right value. They can't
tell you whether your agent *understands* what it learned yesterday. Whether your
orchestrator proposes sensible work assignments. Whether knowledge that one agent
learns transfers meaningfully to another. These are system-level questions, and
`assert` statements don't reach them.

Here's what usually happens: teams run experiments, look at the data, find something
that looks good, and retroactively frame it as what they were testing all along. The
research community calls this *HARKing* — Hypothesizing After Results are Known.
Nobody does it deliberately. But without pre-registered targets committed to version
control *before* data collection, there's no way to prove you weren't.

When you can't explain to a new team member *why* you believe your system is working
— when you have metrics but no pre-stated expectations, results but no proof you
didn't cherry-pick them — that's not science. That's storytelling with numbers.

## What Hypothesis-Driven Development Actually Is

Hypothesis-Driven Development is what happens when you take the scientific method
seriously and apply it to engineering. The idea isn't new — Eric Ries introduced
build-measure-learn loops in 2011, ThoughtWorks has written about hypothesis-driven
product development, and pre-registration has been standard in clinical research for
two decades.

What yurtle-kanban provides is a **toolchain-integrated workflow** that makes the
cycle frictionless:

```
IDEA → HYPOTHESIS → EXPERIMENT → ANALYSIS
```

1. **Capture the idea**: "Would entity linking help agents understand what
   they're reading earlier in their training?"
2. **Formalize a hypothesis**: "Entity enrichment increases knowledge graph density
   by at least 15%." Specific. Quantitative. Stated in advance.
3. **Design and run the experiment**: Train one agent with enrichment, one without.
   Compare. Measure.
4. **Analyze**: Did we hit the target, or didn't we?

The discipline lives in step 2. The hypothesis and its success threshold are committed
to version control *before* any data is collected. The research community calls this
**pre-registration**. It means we can't move the goalposts. We said 15%. Either we
hit it or we didn't.

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

First: HDD often starts with an idea, a suspicion, or a question — not a test.
Before you formalize a hypothesis, you do a literature review — often LLM-assisted
— to understand what prior work exists and what targets are realistic. TDD assumes
you know what to build. HDD assumes you need to figure out what's even worth building.

Second: a refuted hypothesis isn't a bug. It's data. You document it, learn from it,
and redirect. In TDD, red means "fix this." In HDD, red means "now we know something
we didn't know before." This is fail-fast, but it's not failure-focused — it's
*learning*-focused. The teams that learn fastest approach truth faster. Period.

If this sounds familiar, it should. Jeff Gothelf and Jeff Patton laid the groundwork
for hypothesis-driven product development years ago. What yurtle-kanban does is take
that intuition and wire it into methodical science — pre-registered claims, quantitative
targets, version-controlled evidence — tied to development cycles that
AI agents can accelerate. AI agents running HDD cycles compress weeks of learning
into hours. The speed demands better tooling, which is exactly what yurtle-kanban
provides.

## The Bloom Discovery: A Full Cycle

One of our early research questions: **"How do we measure whether an AI agent actually
understands what it knows?"**

Standard LLM benchmarks test recall. They ask a question, the model answers, you
check. But recall isn't understanding. A model might score 92% and have no idea
*why* any of its answers are correct.

We captured the idea in 30 seconds:

> IDEA-R-002: "How do we measure agent cognition fairly?"

Then an LLM-assisted literature review. We asked: "Is there a standard in
human education for measuring understanding versus memorization?"

Answer: **Bloom's Taxonomy** (1956, revised 2001). Six cognitive levels. L1 is
Remember — recall facts. L2 is Understand — explain concepts in your own words. L3
is Apply. L4 is Analyze. And so on up to Create.

The discovery that mattered: **no existing LLM benchmark tests L2, L3, or L4.** They
all test L1 recall with different question formats. That's not a gap — that's a
canyon.

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

Hypothesis validated. That capability came from a 30-second idea, an afternoon of literature review, and one well-designed
experiment.

## When Four Out of Five Hypotheses Fail

Now the story I promised. Our favorite example of HDD working — *because*
it went sideways.

The idea: **"Can agents predict what the user will ask next?"** Predictive processing.
We formulated five hypotheses with specific targets and ran them against a live agent.

| Hypothesis | Target | Actual | Status |
|-----------|--------|--------|--------|
| H118.1: Meaningful predictions | ≥60% accuracy | 54% | **FAILED** |
| H118.2: Improves over sessions | +15pp over 10 sessions | +0pp | **FAILED** |
| H118.3: Surprise-driven gap detection | ≥70% precision | 13.8% | **FAILED** |
| H118.4: Prediction calibration | ECE <15% | ECE = 45% | **FAILED** |
| H118.5: Trackable infrastructure | 136 tests pass | 136 tests pass | **VALIDATED** |

The plumbing worked. The cognition was fundamentally broken.

In a traditional process, this is a disaster. Months of work, core idea doesn't
hold up, quietly shelve it.

But we had something better than working code. We had **specific, documented
failure modes.** Each failed hypothesis pointed to a concrete structural problem:

- **H118.2 failed** because there were no competing prediction schemas. One way
  to predict, no way to learn alternatives.
- **H118.3 failed** because there was no mechanism to detect cognitive distortions
  in predictions.
- **H118.4 failed** because there was no distinction between fast intuitive
  responses and slower reflective ones.

Then the insight that made the failures worth more than any success: each failure
mapped to a known mechanism from **Beck's Cognitive Behavioral Therapy** framework.

| Failure | Missing CBT Mechanism | Solution |
|---------|----------------------|----------|
| No improvement over time | No competing schemas | PredictionSchemaRegistry |
| Low precision | No distortion detection | DistortionDetector |
| Poor calibration | No dual processing | DualProcessPipeline |

Clinical psychology had already solved these problems — just not for AI systems.
The failures didn't tell us what was wrong. They told us **where to look for
answers.**

Without HDD: build for months on conviction, discover problems too
late, nothing to show for it. With HDD: five tests in days, exact failure modes
identified, immediate redirect. Every failure pointed to a specific missing
mechanism.

## The Tooling That Makes It Frictionless

If this sounds heavy in process, it shouldn't. The tooling makes it nearly invisible.

All HDD artifacts are created through the CLI:

```bash
# Capture an idea (30 seconds)
yurtle-kanban idea create "Would entity linking help early understanding?" \
    --type research --push

# Literature review
yurtle-kanban literature create "Entity linking for knowledge graphs" \
    --idea IDEA-R-007 --push

# Formalize a hypothesis
yurtle-kanban hypothesis create "Entity linking increases graph density >=15%" \
    --paper 121 --target ">=15%" --push

# Create experiment protocol
yurtle-kanban experiment create EXPR-121 \
    --hypothesis H121.1 --title "Entity linking A/B study" --push

yurtle-kanban experiment run EXPR-121 --being my-agent-v2
yurtle-kanban experiment status EXPR-121
```

Each command creates the artifact from a template, allocates a unique ID, commits
to git, and pushes — atomically. The artifact's existence is in version control
the moment it's created. No forgetting to commit. No ID collisions between developers working in parallel.

Research artifacts live on a dedicated board, separate from but connected to development work:

```bash
yurtle-kanban board research     # HDD items
yurtle-kanban board              # Development work
yurtle-kanban board --all        # Everything
```

The separation matters — but so does the interconnectedness. Development flows
through backlog → in-progress → done. Research accumulates: ideas become literature
reviews become hypotheses become experiments. They're different rhythms, but they
feed each other. A validated hypothesis becomes a development task. A development
task surfaces a question that becomes a new idea. The research board is where you
figure out *what's worth building*. The development board is where you *build it*.
HDD is the bridge between the two.

### Validation and Cross-Referencing

yurtle-kanban ensures research integrity with built-in validation:

```bash
yurtle-kanban hdd registry

yurtle-kanban hdd validate
yurtle-kanban hdd validate --strict
yurtle-kanban hdd validate --json

yurtle-kanban hdd backfill --dry-run
yurtle-kanban hdd backfill
```

### Every File is Human-Readable and Machine-Queryable

Every artifact is a **[Yurtle](https://github.com/hankh95/yurtle) file** — a format that combines markdown with RDF
triples in a single document. Humans read it in a text editor. Machines query it
with graph operations. Same file, two audiences, no synchronization problem.

A hypothesis file's Turtle block:

```turtle
@prefix hyp: <https://yurtle.dev/hdd/hypothesis/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a hyp:Hypothesis ;
   hyp:paper <../../papers/PAPER-121.md> ;
   hyp:target ">=15%"^^xsd:string ;
   hyp:status hyp:active ;
   hyp:measuredBy <../../measures/M-005.md> .
```

Below the frontmatter: plain markdown. Above it: RDF triples you can query. "Show
me all active hypotheses for Paper 121." "Which experiments have no linked measures?"
"What's the validation rate across all papers?"

This dual format is what makes pre-registration verifiable by both humans and
automated analysis. The experiment protocol is markdown you can read. The success
criteria are structured data a script can check.

## Git as the Arbiter of Truth

Pre-registration deserves its own section because it's the heart of HDD and the
part that makes people uncomfortable.

Before running an experiment, you write a file specifying: the hypothesis, the
outcome measure, the target threshold, the analysis plan. Then you commit to git with `--push` and only *then*
start collecting data.

If someone challenges the results — "did you really set that target before you
saw the data?" — you point to the commit hash. Hypothesis committed at 2:00 PM.
Data collection started at 2:15 PM. Timestamps are immutable. No institutional
review board needed. **Git is the arbiter.**

This means you can't adjust targets after seeing data. You said 15% and got 12%?
That's a refutation. Not "well, 12% is close." Not "the target was aggressive."
A refutation. Document what you learned, create a new hypothesis with a refined
target, test again.

That discipline is what separates HDD from post-hoc analysis. And it's the hardest
part to adopt. Engineers debug until something works. Scientists explore data until
something is interesting. HDD says: state what you expect, test it, accept the
result.

## What We've Learned

**Pre-registration prevents wishful thinking.** Before HDD, we'd run the system,
look at the data, and declare success based on whatever looked good. Now we state
targets first. It's uncomfortable. It's honest.

**Negative results are your most valuable data.** The 4/5 failure rate was more productive than many of our successes. If we'd declared victory based on
the one passing hypothesis, we'd have shipped a broken architecture and
spent months wondering why.

**Metrics should be boring.** Dashboard shows: approval rate 86%, spawn
success 95%, target met. No excitement. That's the point. If you need excitement
to validate your system, you don't understand your system well enough.

**Implementation can outpace measurement, and that's fine — but speed will kill you
without structure.** AI agents running HDD cycles compress weeks of learning into hours. That speed is
intoxicating and dangerous. HDD prevents shipping conclusions before the evidence
is in.

## Getting Started with HDD in yurtle-kanban

### 1. Add a research board

```bash
yurtle-kanban board-add research --preset hdd --path research/
```

### 2. Capture your first idea

```bash
yurtle-kanban idea create "Does X improve Y?" --type research --push
```

### 3. Do a literature review

```bash
yurtle-kanban literature create "Prior art on X" --idea IDEA-R-001 --push
```

### 4. Formalize a hypothesis with a quantitative target

```bash
yurtle-kanban hypothesis create "X improves Y by >=15%" \
    --paper 1 --target ">=15%" --push
```

### 5. Design and run the experiment

```bash
yurtle-kanban experiment create EXPR-1 \
    --hypothesis H1.1 --title "X vs baseline" --push

yurtle-kanban experiment run EXPR-1 --being my-system-v1
```

### 6. Analyze and validate

Did you hit your target? If yes, hypothesis validated. If no, document the failure
mode, formulate a new hypothesis, and test again.

```bash
yurtle-kanban hdd registry
yurtle-kanban hdd validate
```

Every step is a file in git. Every target is committed before data collection.
Every result — success or failure — is versioned and auditable.

---

*HDD, yurtle-kanban, and the [Yurtle](https://github.com/hankh95/yurtle) knowledge format are open source under the MIT license.*

*[yurtle-kanban](https://github.com/hankh95/yurtle-kanban) ·
[Yurtle](https://github.com/hankh95/yurtle) ·
[yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib)*
