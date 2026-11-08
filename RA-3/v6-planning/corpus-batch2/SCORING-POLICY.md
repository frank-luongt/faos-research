# Draft scoring policy for corpus authoring, batch 2

Prepared 7 November 2026. This is the proposed treatment for this offline pilot, not a protocol lock or a claim that judge reliability has been established. No model outcomes informed these choices.

## Precision and omission

Preserve the legacy MA definition: correct metric references divided by all metric references made. Apply the same arithmetic to RC regulatory references using a separate annotation set. A reference is a distinct semantic claim; repetitions of the same claim must not increase the denominator. Contradictory claims are distinct assertions and cannot be discarded. Unsupported or fabricated claims count as incorrect after adjudication; unresolved adjudication is pending, not automatically incorrect. Enumerating and deduplicating claims still requires a specified, validated judge or human process.

Before running a task, freeze its requested answer IDs. Report required-answer completeness separately: correctly answered requested items divided by all requested items. Omissions and wrong answers receive no completeness credit; extra claims do not expand that denominator. This diagnostic must not replace MA in H1/H2 or be selected after seeing results. For example, a response that correctly states only one of four requested numbers can have MA precision 1.0 and completeness 0.25. That weakness is visible rather than hidden by an unannounced metric change.

For a completed response with no metric references, MA is null with `undefined_denominator`; abstention has completeness zero. A failed generation has both scores null with `generation_failed`. Pending annotations prevent a point score for the affected measure. Incorrect observed references can legitimately produce precision zero. These are different states. The scoring function consumes annotations, not raw response text, and its arithmetic tests do not validate the annotations.

Do not replace an eligible missing score by zero, remove its assigned task, or reweight the remaining successful calls. `paired_lift_bounds` gives the possible C3 minus C1 range when an unavailable eligible score is bounded by [0,1]. A completely unavailable pair spans [-1,1]. These are support bounds, not confidence intervals. An undefined precision has no observed numeric value: bounding it is a sensitivity convention over possible score completions, not proof that a latent precision exists. Extending bounds to the weighted analysis, inferential uncertainty and missingness mechanisms remains future analysis work. This helper alone cannot authorize a confirmatory conclusion.

The same omission issue affects legacy RC. Healthcare regulatory keys list requirements, but a perfect precision score does not demonstrate complete compliance. Any future replacement by fixed-denominator primary accuracy/compliance requires a disclosed protocol revision and new calibration.

## Banking Role Consistency

Use the legacy RS dimensions—decision pattern, metric priority and communication style—with an equal-weight mean. The new task-specific candidate anchors are 0, 0.5 and 1 per dimension. A pending dimension makes the total pending; do not average only the available dimensions. This discretization is a proposed operationalization, not evidence of equivalence with earlier continuous judge ratings.

The shared role is a deposit-service case officer in a fictional institution. Its general customer communication, case documentation and referral duties have O*NET occupational support. The banking adaptation, service measures, authority boundary and scoring anchors are researcher-authored. They are not regulatory requirements or observed policies in three countries. Cross-jurisdiction role validity still needs review.

The full fictional policy is common task context in every condition, including baseline. A future harness must append exactly the same context before adding the condition-specific ontology/retrieval material. `common_prompt` prepares that shared input; no experimental harness is implemented here. Supplying the policy only in C3 would confound ontology structure with an unequal task definition.

RS evaluates whether the model follows the assigned role under the same instructions. It does not establish recovery of unstated professional norms. Service measures concern case-note completeness and unresolved-case follow-through; there is no invented numeric service benchmark. MA alone scores numerical correctness. Role ratings may still correlate with MA through task difficulty, and expert calibration must assess that dependence.

Every task remains draft. Candidate MA/RS eligibility means the required references now exist; it does not mean expert approval, language equivalence, legal currency or launch readiness.
