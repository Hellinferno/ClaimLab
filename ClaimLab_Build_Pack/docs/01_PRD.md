# Product Requirements Document

**Product:** ClaimLab · **Release:** Hackathon first version · **Status:** Approved direction; proposed implementation boundary

## Problem and audience

Students reading technical papers can struggle to connect notation, prerequisites, and practical behavior. The initial audience is university students and early researchers learning AI/ML methods. Ravi's combined vision is a visual teacher and experimentation agent that changes its approach using evidence from the learner's work.

## Product outcome

A student supplies a supported PDF section, chooses a question, sees a stepwise explanation, participates on a shared board, investigates a small experiment, and attempts a new application. The system records why it selected a teaching change and whether later evidence supported progress.

The first supported topic family is attention: softmax sensitivity, scaling, and causal masking. Coverage is deliberately explicit. Unsupported sections receive an honest boundary rather than fabricated experiments.

## Core requirements

| ID | Priority | Requirement |
| --- | --- | --- |
| P0-01 | Required | Create an isolated guest owner and learning session |
| P0-02 | Required | Upload and parse a bounded native-text PDF with per-page extraction status |
| P0-03 | Required | Attach explanations to validated page and text anchors |
| P0-04 | Required | Choose a focused question and supported concept/prerequisite path |
| P0-05 | Required | Let the agent draw and update meaningful whiteboard objects step by step |
| P0-06 | Required | Accept student selection, connection answers, annotations, and text responses |
| P0-07 | Required | Execute the three reviewed experiment recipes with bounded configurable inputs |
| P0-08 | Required | Visualize actual checked outputs with run identity and stale-state handling |
| P0-09 | Required | Collect predictions and independent application attempts |
| P0-10 | Required | Use learner evidence to change a later teaching action |
| P0-11 | Required | Persist and resume session state under the same guest identity |
| P0-12 | Required | Expose concise source, execution, and teaching-decision evidence |
| P0-13 | Required | Handle parsing, model, job, and numerical failures without invented success |
| P0-14 | Required | Enforce ownership, key secrecy, and execution isolation |
| P0-15 | Required | Demonstrate actual Meta model calls in live mode |
| P0-16 | Required | Implement user deletion and enforced retention cleanup |

## Later scope

P1 includes richer sketch interpretation, accessible speech input/output, additional experiment families, and more paper layouts. P2 includes broad textbook support, multi-user classrooms, account-based cross-device history, and validated longer-term personalization. These do not displace missing P0 behavior.

## Non-goals for this release

No arbitrary code execution, full-paper autonomous reproduction, custom foundation-model training, medical/political advice workflows, or claims to support every subject. Freehand strokes may be saved as annotations; semantic interpretation is limited to supported structured interactions.

## Experience principles

Teach one meaningful step at a time. Keep the source reachable. Make the student's action consequential. Separate evidence from inference. Preserve context during interruptions. Avoid treating slow responses or explicit presentation preferences as ability diagnoses. Show precise numerical visuals from computation.

## Success evidence

Technical success: a supported upload-to-lesson flow, real experiment runs, independent checks, a recorded adaptation, and a new application all work under the selected deployment limits. Learning success is a research question: pilot observations must report participants, assistance, tasks, and limitations. No predetermined learning-gain target is presented as a fact.

## Release decision

Every P0 criterion in [scope and acceptance](02_SCOPE_AND_ACCEPTANCE.md) must pass or be explicitly reported as a remaining release blocker. If time is short, cut later features; do not remove real experimentation, student interaction, or the observation loop and still claim the combined vision is complete.
