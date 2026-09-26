# Milestone 2 failure review

Prepared September 25, 2026. Human review has not been completed. This packet contains all 28 scorer-flagged model/case outputs from the saved rules, Codex, and Granite v1 runs. These are 28 outputs across 14 distinct synthetic inputs, not 28 independent meetings. Flags include possible model failures, annotation ambiguity, and scorer artifacts. Confirm the classification before counting a failure.

Use the [compact review log](failure_review_log.md), [reviewer A sheet](failure_review_reviewer_a.md), and [reviewer B sheet](failure_review_reviewer_b.md). The log includes expected and actual tasks, candidate issue categories, reviewer fields, and agreement/adjudication tables.

## Review procedure

1. Two reviewers independently read each transcript and output. Use separate copies of the score sheet; do not consult the other reviewer before scoring.
2. Judge the frozen label as well as the prediction. Record label or matching problems separately; do not silently alter the v1 benchmark or scores.
3. Score faithfulness (F), attribution (A), coverage (C), ambiguity handling (U), and clarity/usefulness (L) from 1 to 5 using Section 3 of the submission. Mark a dimension N/A when it cannot be assessed, and explain why. No output in a positive case usually warrants low coverage; it does not automatically imply an invented claim.
4. Classify each flag: model failure, scorer artifact, label/contract ambiguity, mixed, or unresolved. Quote supporting turn IDs. Record any critical unsupported commitment separately.
5. Compare independent scores: report exact agreement and within-one-point agreement per dimension, using only pairs with two numeric scores; report exclusions. Reconcile disagreements in a separate adjudication record and retain original scores.
6. Summarize 3-5 supported patterns, human-confirmed failure counts, and proposed Milestone 3 changes. This deliberately error-enriched sample cannot estimate overall quality. Add ordinary successful cases for a representative qualitative comparison.

## Policy questions to resolve

- Joint ownership: one multi-owner obligation, one record per person, or a null owner?
- Task granularity: when should two actions become two independently tracked obligations?
- Deadlines: distinguish exact source-span agreement from semantic equivalence; preserve v1 scores.
- Unknown speakers: retain supported work with a null owner rather than inventing a name.
- Paraphrases: inspect lexical false negatives such as “Preparing” versus “prepare.”

## Completion record

Reviewer A and date: __________

Reviewer B and date: __________

Outputs reviewed by both: ___ / 28. Confirmed model failures: ___. Scorer artifacts: ___. Label/contract ambiguities: ___. Mixed: ___. Unresolved: ___.

Agreement by dimension and exclusions: __________

Adjudicator and date: __________

## Case index

| Review ID | Method | Input | Scorer flags |
| --- | --- | --- | --- |
| FR01 | rules | volunteer | missed gold: g1 |
| FR02 | rules | accepted_request | unmatched prediction: 0; missed gold: g1 |
| FR03 | rules | negated | unmatched prediction: 0 |
| FR04 | rules | repeat | unmatched prediction: 1 |
| FR05 | rules | correction | deadline: g1; incomplete evidence: g1; unmatched prediction: 1 |
| FR06 | rules | quoted_promise | unmatched prediction: 0 |
| FR07 | rules | joint | owner: g1; incomplete evidence: g1 |
| FR08 | rules | assignment | missed gold: g1 |
| FR09 | rules | two_actions | missed gold: g2 |
| FR10 | codex | explicit | deadline: g1 |
| FR11 | codex | accepted_request | deadline: g1 |
| FR12 | codex | unknown_owner | missed gold: g1 |
| FR13 | codex | repeat | deadline: g1 |
| FR14 | codex | correction | deadline: g1 |
| FR15 | codex | joint | owner: g1; deadline: g1; unmatched prediction: 1 |
| FR16 | codex | assignment | deadline: g1 |
| FR17 | codex | reassignment | deadline: g1 |
| FR18 | codex | two_actions | deadline: g1; missed gold: g2 |
| FR19 | granite | explicit | deadline: g1 |
| FR20 | granite | contraction | deadline: g1 |
| FR21 | granite | accepted_request | missed gold: g1 |
| FR22 | granite | negated | unmatched prediction: 0 |
| FR23 | granite | unknown_owner | owner: g1 |
| FR24 | granite | two_owners | missed gold: g1; missed gold: g2 |
| FR25 | granite | joint | owner: g1; deadline: g1; incomplete evidence: g1 |
| FR26 | granite | assignment | unmatched prediction: 0; missed gold: g1 |
| FR27 | granite | reassignment | missed gold: g1 |
| FR28 | granite | two_actions | missed gold: g2 |

## FR01 rules volunteer

**Source:** `artifacts/evaluation/rules-v1/volunteer.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Guadalupe | 0-5000 ms: I can take responsibility for reviewing the labels.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review labels",
    "owner": "Guadalupe",
    "due_date_text": null,
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "label"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR02 rules accepted_request

**Source:** `artifacts/evaluation/rules-v1/accepted_request.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will, could you upload the slides?
- t2 | Will | 5000-10000 ms: Yes, I will do that by Monday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "upload slides",
    "owner": "Will",
    "due_date_text": "Monday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "upload",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Yes, I will do that by Monday.",
    "owner": "Will",
    "due_date_text": "Monday",
    "evidence": [
      {
        "transcript_id": "t2",
        "quote": "Yes, I will do that by Monday."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 0; missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR03 rules negated

**Source:** `artifacts/evaluation/rules-v1/negated.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Will | 0-5000 ms: I will not rerun the baseline this week.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "I will not rerun the baseline this week.",
    "owner": "Will",
    "due_date_text": null,
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will not rerun the baseline this week."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 0.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR04 rules repeat

**Source:** `artifacts/evaluation/rules-v1/repeat.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will send the report by Friday.
- t2 | Sam | 5000-10000 ms: To repeat, I will send the report by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "I will send the report by Friday.",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will send the report by Friday."
      }
    ]
  },
  {
    "title": "To repeat, I will send the report by Friday.",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t2",
        "quote": "To repeat, I will send the report by Friday."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR05 rules correction

**Source:** `artifacts/evaluation/rules-v1/correction.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will send the report by Friday.
- t2 | Sam | 5000-10000 ms: Correction: I will send the report by Monday, not Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Sam",
    "due_date_text": "Monday",
    "evidence_ids": [
      "t2"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "I will send the report by Friday.",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will send the report by Friday."
      }
    ]
  },
  {
    "title": "Correction: I will send the report by Monday, not Friday.",
    "owner": "Sam",
    "due_date_text": "Monday",
    "evidence": [
      {
        "transcript_id": "t2",
        "quote": "Correction: I will send the report by Monday, not Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1; incomplete evidence: g1; unmatched prediction: 1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR06 rules quoted_promise

**Source:** `artifacts/evaluation/rules-v1/quoted_promise.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: The example sentence in the documentation is "I will send the report by Friday." It is not an assignment.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "The example sentence in the documentation is \"I will send the report by Friday.\" It is not an assignment.",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "The example sentence in the documentation is \"I will send the report by Friday.\" It is not an assignment."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 0.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR07 rules joint

**Source:** `artifacts/evaluation/rules-v1/joint.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will and I will review the schema together by Tuesday.
- t2 | Will | 5000-10000 ms: Yes, we will both review it.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": null,
    "due_date_text": "Tuesday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Will and I will review the schema together by Tuesday.",
    "owner": "Sam",
    "due_date_text": "Tuesday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will and I will review the schema together by Tuesday."
      }
    ]
  }
]
```

**Automatic flags:** owner: g1; incomplete evidence: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR08 rules assignment

**Source:** `artifacts/evaluation/rules-v1/assignment.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will is responsible for preparing the demo by Friday.
- t2 | Will | 5000-10000 ms: Understood. I accept responsibility for preparing the demo.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "prepare demo",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "prepare",
        "create"
      ],
      [
        "demo"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR09 rules two_actions

**Source:** `artifacts/evaluation/rules-v1/two_actions.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will review the schema and send the slides by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  },
  {
    "id": "g2",
    "title": "send slides",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "I will review the schema and send the slides by Friday.",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will review the schema and send the slides by Friday."
      }
    ]
  }
]
```

**Automatic flags:** missed gold: g2.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR10 codex explicit

**Source:** `artifacts/evaluation/codex-v1/explicit.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will prepare the transcript fixture by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "prepare transcript fixture",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "prepare",
        "create"
      ],
      [
        "transcript"
      ],
      [
        "fixture"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Prepare the transcript fixture",
    "owner": "Sam",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will prepare the transcript fixture by Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR11 codex accepted_request

**Source:** `artifacts/evaluation/codex-v1/accepted_request.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will, could you upload the slides?
- t2 | Will | 5000-10000 ms: Yes, I will do that by Monday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "upload slides",
    "owner": "Will",
    "due_date_text": "Monday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "upload",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Upload the slides",
    "owner": "Will",
    "due_date_text": "by Monday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will, could you upload the slides?"
      },
      {
        "transcript_id": "t2",
        "quote": "Yes, I will do that by Monday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR12 codex unknown_owner

**Source:** `artifacts/evaluation/codex-v1/unknown_owner.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | UNKNOWN | 0-5000 ms: I will send the slides by Thursday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send slides",
    "owner": null,
    "due_date_text": "Thursday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR13 codex repeat

**Source:** `artifacts/evaluation/codex-v1/repeat.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will send the report by Friday.
- t2 | Sam | 5000-10000 ms: To repeat, I will send the report by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Send the report",
    "owner": "Sam",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will send the report by Friday."
      },
      {
        "transcript_id": "t2",
        "quote": "To repeat, I will send the report by Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR14 codex correction

**Source:** `artifacts/evaluation/codex-v1/correction.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will send the report by Friday.
- t2 | Sam | 5000-10000 ms: Correction: I will send the report by Monday, not Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Sam",
    "due_date_text": "Monday",
    "evidence_ids": [
      "t2"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Send the report",
    "owner": "Sam",
    "due_date_text": "by Monday, not Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will send the report by Friday."
      },
      {
        "transcript_id": "t2",
        "quote": "Correction: I will send the report by Monday, not Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR15 codex joint

**Source:** `artifacts/evaluation/codex-v1/joint.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will and I will review the schema together by Tuesday.
- t2 | Will | 5000-10000 ms: Yes, we will both review it.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": null,
    "due_date_text": "Tuesday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Review the schema together",
    "owner": "Sam",
    "due_date_text": "by Tuesday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will and I will review the schema together by Tuesday."
      },
      {
        "transcript_id": "t2",
        "quote": "Yes, we will both review it."
      }
    ]
  },
  {
    "title": "Review the schema together",
    "owner": "Will",
    "due_date_text": "by Tuesday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will and I will review the schema together by Tuesday."
      },
      {
        "transcript_id": "t2",
        "quote": "Yes, we will both review it."
      }
    ]
  }
]
```

**Automatic flags:** owner: g1; deadline: g1; unmatched prediction: 1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR16 codex assignment

**Source:** `artifacts/evaluation/codex-v1/assignment.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will is responsible for preparing the demo by Friday.
- t2 | Will | 5000-10000 ms: Understood. I accept responsibility for preparing the demo.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "prepare demo",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "prepare",
        "create"
      ],
      [
        "demo"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Prepare the demo",
    "owner": "Will",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will is responsible for preparing the demo by Friday."
      },
      {
        "transcript_id": "t2",
        "quote": "I accept responsibility for preparing the demo."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR17 codex reassignment

**Source:** `artifacts/evaluation/codex-v1/reassignment.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I was going to send the report, but Will is taking over.
- t2 | Will | 5000-10000 ms: Yes, I will send the report by Friday instead of Sam.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t2"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Send the report",
    "owner": "Will",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I was going to send the report, but Will is taking over."
      },
      {
        "transcript_id": "t2",
        "quote": "Yes, I will send the report by Friday instead of Sam."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR18 codex two_actions

**Source:** `artifacts/evaluation/codex-v1/two_actions.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will review the schema and send the slides by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  },
  {
    "id": "g2",
    "title": "send slides",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Review the schema and send the slides",
    "owner": "Sam",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will review the schema and send the slides by Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1; missed gold: g2.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR19 granite explicit

**Source:** `artifacts/evaluation/granite-v1/explicit.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will prepare the transcript fixture by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "prepare transcript fixture",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "prepare",
        "create"
      ],
      [
        "transcript"
      ],
      [
        "fixture"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Prepare the transcript fixture",
    "owner": "Sam",
    "due_date_text": "by Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will prepare the transcript fixture by Friday."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR20 granite contraction

**Source:** `artifacts/evaluation/granite-v1/contraction.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Will | 0-5000 ms: I'll rerun the baseline tomorrow.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "rerun baseline",
    "owner": "Will",
    "due_date_text": "tomorrow",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "rerun",
        "run"
      ],
      [
        "baseline"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Rerun Baseline",
    "owner": "Will",
    "due_date_text": "Tomorrow",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I'll rerun the baseline tomorrow."
      }
    ]
  }
]
```

**Automatic flags:** deadline: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR21 granite accepted_request

**Source:** `artifacts/evaluation/granite-v1/accepted_request.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will, could you upload the slides?
- t2 | Will | 5000-10000 ms: Yes, I will do that by Monday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "upload slides",
    "owner": "Will",
    "due_date_text": "Monday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "upload",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR22 granite negated

**Source:** `artifacts/evaluation/granite-v1/negated.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Will | 0-5000 ms: I will not rerun the baseline this week.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Not Rerun Baseline",
    "owner": "Will",
    "due_date_text": null,
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will not rerun the baseline this week."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 0.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR23 granite unknown_owner

**Source:** `artifacts/evaluation/granite-v1/unknown_owner.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | UNKNOWN | 0-5000 ms: I will send the slides by Thursday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send slides",
    "owner": null,
    "due_date_text": "Thursday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Send slides",
    "owner": "UNKNOWN",
    "due_date_text": "Thursday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will send the slides by Thursday."
      }
    ]
  }
]
```

**Automatic flags:** owner: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR24 granite two_owners

**Source:** `artifacts/evaluation/granite-v1/two_owners.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will review the schema.
- t2 | Will | 5000-10000 ms: I will test the upload endpoint.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": "Sam",
    "due_date_text": null,
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  },
  {
    "id": "g2",
    "title": "test upload endpoint",
    "owner": "Will",
    "due_date_text": null,
    "evidence_ids": [
      "t2"
    ],
    "action_terms": [
      [
        "test"
      ],
      [
        "upload"
      ],
      [
        "endpoint"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1; missed gold: g2.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR25 granite joint

**Source:** `artifacts/evaluation/granite-v1/joint.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will and I will review the schema together by Tuesday.
- t2 | Will | 5000-10000 ms: Yes, we will both review it.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": null,
    "due_date_text": "Tuesday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Review the schema together by Tuesday",
    "owner": "Sam",
    "due_date_text": null,
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "Will and I will review the schema together by Tuesday."
      }
    ]
  }
]
```

**Automatic flags:** owner: g1; deadline: g1; incomplete evidence: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR26 granite assignment

**Source:** `artifacts/evaluation/granite-v1/assignment.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: Will is responsible for preparing the demo by Friday.
- t2 | Will | 5000-10000 ms: Understood. I accept responsibility for preparing the demo.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "prepare demo",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1",
      "t2"
    ],
    "action_terms": [
      [
        "prepare",
        "create"
      ],
      [
        "demo"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Preparing the demo",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t2",
        "quote": "Understood. I accept responsibility for preparing the demo."
      }
    ]
  }
]
```

**Automatic flags:** unmatched prediction: 0; missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR27 granite reassignment

**Source:** `artifacts/evaluation/granite-v1/reassignment.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I was going to send the report, but Will is taking over.
- t2 | Will | 5000-10000 ms: Yes, I will send the report by Friday instead of Sam.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "send report",
    "owner": "Will",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t2"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "report"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[]
```

**Automatic flags:** missed gold: g1.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.

## FR28 granite two_actions

**Source:** `artifacts/evaluation/granite-v1/two_actions.json`; scorer `action-terms-v1`.

**Transcript**

- t1 | Sam | 0-5000 ms: I will review the schema and send the slides by Friday.

**Frozen expected obligations (AI-authored, not human-adjudicated)**

```json
[
  {
    "id": "g1",
    "title": "review schema",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "review"
      ],
      [
        "schema"
      ]
    ]
  },
  {
    "id": "g2",
    "title": "send slides",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence_ids": [
      "t1"
    ],
    "action_terms": [
      [
        "send",
        "share"
      ],
      [
        "slide"
      ]
    ]
  }
]
```

**Actual predicted commitments (complete commitment array)**

```json
[
  {
    "title": "Review the schema",
    "owner": "Sam",
    "due_date_text": "Friday",
    "evidence": [
      {
        "transcript_id": "t1",
        "quote": "I will review the schema and send the slides by Friday."
      }
    ]
  }
]
```

**Automatic flags:** missed gold: g2.

**Human adjudication:** Classification: ______. Supporting turn IDs and reasoning: ______. Label/scorer correction proposed: ______. Confirmed model failure and next change: ______.
