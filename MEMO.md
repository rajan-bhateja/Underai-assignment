# Migration Recommendation Memo

**To:** Engineering Lead  
**Subject:** UnderAI support-triage model migration  
**Recommendation:** Stage in shadow mode

The successful current model run used the OpenAI Responses API with zero
fallbacks. Its decisions follow policy on all 15 public cases and the three
added synthetic cases. They agree with the retiring baseline on 11/15 tickets;
the four disagreements correct policy-inconsistent baseline behavior. The
evaluator checks the output contract, policy expectations, baseline agreement,
synthetic cases, and a deliberately weakened decision. Its output is saved at
`evaluation/evaluation.txt`.

The recovered 15-ticket run used 9,923 input tokens and 476 output tokens
(10,399 total); runner timestamps indicate about 24 seconds elapsed. No cost
estimate is available because pricing was not recorded. Metrics are available in
the console output only.
This small synthetic evaluation is not sufficient to
ship directly to production. The keyword fallback remains brittle to new
wording, negation, and context; broader semantic interpretation may help, but
requires targeted evaluation.

Before production rollout, run a shadow/staged trial on a held-out set with new
paraphrases and adversarial quoted instructions. Monitor policy-critical
disagreements, fallback rate, token usage, latency, and cost; halt the trial if
the model or fallback violates identity, privacy, or incident precedence. Move
beyond shadow mode only after those checks pass and operational cost is
understood.