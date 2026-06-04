---
Title: RA-1 Problem-Class Rater Protocol v1
Status: ready-for-independent-rating
Date: 2026-05-03
Purpose: Validate problem-class labels before freezing RA-1 v0.1 experimental design
---

# RA-1 Problem-Class Rater Protocol v1

## Objective

Independently label each selected RA-1 task with one of five problem classes. The goal is to test whether the task-to-class mapping is reproducible by a second rater before the RA-1 hypothesis matrix is frozen.

## Unit of Rating

Rate the task as written in `tasks_ra1.json`. Use the task question and ground-truth intent, not the predicted strategy, when assigning the problem class.

## Problem Classes

| Code | Name | Label when the task primarily asks for... | Predicted strategy |
|---|---|---|---|
| PC1 | High-uncertainty risk decision | A decision under incomplete evidence where multiple interpretations could be reasonable | consensus |
| PC2 | Conflicting-objective tradeoff | A recommendation balancing two or more legitimate but competing objectives | debate |
| PC3 | Novel design synthesis | A new operating model, product, program, or architecture requiring cross-functional integration | synthesis |
| PC4 | Structured compliance verification | A deterministic check against rules, thresholds, definitions, or required controls | consensus |
| PC5 | Ambiguous-requirement clarification | Turning vague input into clarified requirements, handoffs, or an executable plan | synthesis |

## Rating Instructions

1. Read the task question.
2. Read the ground-truth answer only to understand task intent.
3. Assign exactly one problem class.
4. Add confidence from 1 to 5.
5. Add a short rationale when confidence is below 4 or when two classes seem plausible.

## Tie-Break Rules

- If the task asks for a new design or program, choose PC3 even if the design includes risk or compliance elements.
- If the task asks whether a situation passes a known threshold or regulation, choose PC4.
- If the task asks to decide between competing goals, choose PC2.
- If the task is uncertain but does not present a direct tradeoff, choose PC1.
- If the task mainly asks to clarify vague language into requirements, choose PC5.

## Agreement Target

Proceed to freeze if Cohen's kappa is at least 0.70. If kappa is below 0.70, reconcile labels, revise ambiguous tasks, and rerun the rater pass.

## Files

- Selected task corpus: `tasks_ra1.json`
- Current labels: `task_selection_v1.csv`
- Blank rater template: `rater_labels_template_v1.csv`

