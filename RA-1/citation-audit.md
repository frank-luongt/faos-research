---
Title: RA-1 Citation Integrity Audit (v0.1)
Status: local citation-key, live metadata, and claim-mapping pass complete
Date: 2026-05-27
Sources:
  - research-academic/papers/RA-1-Multi-Agent-Coordination/manuscript_v0.1.md
  - research-academic/papers/RA-1-Multi-Agent-Coordination/references.bib
---

# RA-1 Citation Integrity Audit

## Best Next Action

The best next action after the manuscript scaffold and response-audit appendix is citation
integrity, before LaTeX or venue formatting. The manuscript now makes literature-positioning claims,
so citation hygiene should be locked before the paper is converted into a harder-to-edit submission
format.

## Local Check Result

Local citation-key check after the live metadata pass:

| Check | Result |
| --- | ---: |
| Citation keys used in `manuscript_v0.1.md` | 17 |
| Citation keys found in `references.bib` | 17 / 17 |
| Missing citation keys | 0 |
| Bibliography entries available in `references.bib` | 37 |

No missing keys were found in the current manuscript draft.

## Live Metadata Updates

The following updates were made after checking current publisher, conference, or arXiv metadata:

| Key | Update |
| --- | --- |
| `liang2024divergent` | Corrected author order and added ACL Anthology DOI/pages. |
| `smit2024mad` | Corrected author list and added PMLR volume/pages. |
| `zhang2025overvalue` | Replaced stale author list with current arXiv v3 metadata. |
| `hong2024metagpt` | Corrected author order around Ceyao Zhang and Jinlin Wang. |
| `qian2024chatdev` | Added ACL Anthology DOI. |
| `yang2024llmvoting` | Corrected author order and added AIES DOI from arXiv related DOI metadata. |
| `kim2024mdagents` | Added to manuscript as the closest dynamic-strategy comparator. |

Live source families checked: IJCAI proceedings, ACL Anthology, PMLR, OpenReview, and arXiv.

Representative live source links used for this pass:

| Source | Link |
| --- | --- |
| IJCAI proceedings | https://www.ijcai.org/proceedings/2024/890 |
| ACL Anthology: ChatDev | https://aclanthology.org/2024.acl-long.810/ |
| ACL Anthology: Multi-Agent Debate | https://aclanthology.org/2024.emnlp-main.992/ |
| PMLR: Multiagent Debate | https://proceedings.mlr.press/v235/du24e.html |
| PMLR: Should we be going MAD? | https://proceedings.mlr.press/v235/smit24a.html |
| OpenReview: AgentVerse | https://openreview.net/forum?id=EHg5GDnyq1 |
| OpenReview: Mechanism Design | https://openreview.net/forum?id=9Ob8Kmia9E |
| arXiv: MDAgents | https://arxiv.org/abs/2404.15155 |
| arXiv: LLM Voting | https://arxiv.org/abs/2402.01766 |
| arXiv: Stop Overvaluing MAD | https://arxiv.org/abs/2502.08788 |

## Cited Key Inventory

| Key | Current use in manuscript |
| --- | --- |
| `guo2024llmmas` | Survey coverage of LLM-based multi-agent systems. |
| `chen2024llmmassurvey` | Survey coverage of applications and frontiers. |
| `tran2025collabsurvey` | Collaboration-mechanism survey framing. |
| `wu2024autogen` | Multi-agent framework example and coordination primitive. |
| `hong2024metagpt` | Role/SOP-style multi-agent framework example. |
| `qian2024chatdev` | Communicative software-development agent framework. |
| `chen2024agentverse` | Multi-agent collaboration and emergent behavior framework. |
| `li2023camel` | Role-playing communicative-agent framework. |
| `kim2024mdagents` | Closest adaptive collaboration comparator for dynamic strategy routing. |
| `du2024multiagent` | Debate as reasoning/factuality intervention. |
| `liang2024divergent` | Debate as divergent-thinking mechanism. |
| `smit2024mad` | Debate strategy critique and cost/accuracy boundary. |
| `zhang2025overvalue` | Critique of overvaluing multi-agent debate and evaluation design. |
| `yang2024llmvoting` | Collective decision-making and voting context. |
| `dutting2024mechanism` | Mechanism-design framing for LLM-generated content. |
| `hua2024gametheoretic` | Negotiation and game-theoretic agent workflow context. |
| `hammond2025risks` | Multi-agent risk and governance context. |

## Claim Mapping

| Manuscript claim family | Citation support |
| --- | --- |
| The multi-agent design space includes roles, communication mechanisms, collaboration protocols, and application settings. | `guo2024llmmas`, `chen2024llmmassurvey`, `tran2025collabsurvey` |
| Existing frameworks demonstrate role-structured multi-agent workflows. | `wu2024autogen`, `hong2024metagpt`, `qian2024chatdev`, `chen2024agentverse`, `li2023camel` |
| Adaptive collaboration can route solo/group structure by task complexity in a domain-specific setting. | `kim2024mdagents` |
| Debate can improve some reasoning or divergent-thinking tasks. | `du2024multiagent`, `liang2024divergent` |
| Debate should not be treated as a universal coordination default. | `smit2024mad`, `zhang2025overvalue` |
| Coordination mechanisms affect collective decisions, incentives, negotiation behavior, and risk. | `yang2024llmvoting`, `dutting2024mechanism`, `hua2024gametheoretic`, `hammond2025risks` |

## Remaining Citation Work

1. Run a final web/DOI verification pass after choosing the target venue, because publisher metadata
   can still change for recent 2025 preprints.
2. Decide whether to cite benchmark/evaluation entries such as `liu2024agentbench` or
   `zhu2025multiagentbench` if the Related Work expands from coordination mechanisms into benchmark
   methodology.
3. Preserve the current bounded language: RA-1 supports near-best routing, not universal
   coordination superiority.
