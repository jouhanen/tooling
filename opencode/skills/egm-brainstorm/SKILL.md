---
name: egm-brainstorm
description: Explore a problem through critical discussion and write a concept brief before independent review or drafting
license: Apache-2.0
metadata:
  opencode/autoinvoke: false
---

<!-- Portions adapted from EGM, Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
Source: skills/egm-brainstorm/SKILL.md at
464db031e7dd1b9a79803ac8ea45f55c7c20c5bc.
Changes: personal artifacts and gates, optional focused/full review, no fixed
six-lens swarm, publication, author-shell lookup, or nested synthesizer. -->

# Brainstorm with Elephant

Run only as Elephant. First read [shared workflow rules](../../resources/standards/workflow.md)
and the [concept template](../../resources/templates/concepts.md). If a required
resource is missing, stop and name it. This skill does not change permissions.

## 1. Explore the actual problem

Use supplied idea/notes as input, not an implementation request. If absent, ask
what problem the user wants to explore. Ask one open-ended question at a time,
waiting between turns. Establish current behavior, users, success criteria,
constraints, non-goals, and why the current approach is insufficient.

Read relevant local sources, distinguish observations from assumptions, challenge
the proposed solution, and compare doing nothing, reuse, and simpler alternatives.
Do not manufacture objections or rush to a draft after an arbitrary number of
questions. Reuse already supplied answers. Ask for consequential trade-offs rather
than deciding them silently. Author identity is optional unless the user wants it;
ask instead of invoking shell or inventing a name.

## 2. Capture the working concept

Once a direction is coherent, summarize it briefly and confirm the artifact
destination before the first write. Create or update concepts.md using the
template, with a concept revision and explicit pending status. Include source
evidence, rejected alternatives and who rejected them, actual decisions,
unvalidated assumptions, and open risks. Save the checkpoint in review-state.md.
Do not silently replace an existing concept or settle unanswered decisions.

Link the brief and ask the user to confirm or revise the working direction. If
they request changes, apply only the requested scope, increment the revision,
and present the updated brief. Direction approval does not approve reviewer
dispatch, drafting, or implementation.

## 3. Offer independent review

Ask whether to review the concept now, continue exploring, or keep it for later.
On an explicit review request, load egm-review in this same Elephant session with
Task concept and Target concepts.md. Recommend the focused concept preset unless
the user chooses full or an explicit subset. Let that skill collect/confirm the
assignment and perform dispatch; do not create another review implementation here.
If delegation or a required reviewer/skill is unavailable, stop and report that
the review did not run. Never simulate it in Elephant's context.

After a review, leave findings resolution to egm-resolve and preserve its approval
pause. Do not automatically repair the brief or start another round. If the user
skips review, record review as not run, not passed.

## 4. Agree on the next phase

Before drafting, reread the current brief and surface remaining decisions, risks,
and review limitations. Ask whether to draft from this revision, continue
brainstorming, or stop. On explicit drafting approval, load egm-draft with that
brief and record the approval scope; it need not ask the same gate twice.
Do not draft merely because the concept was approved. Do not publish the brief,
create repository indexes, or proceed to implementation.
