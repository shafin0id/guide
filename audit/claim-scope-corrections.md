# Claim scope corrections

This documentation and manuscript update follows direct counterexample checks of the released code. Production source files are unchanged; no new live results are claimed.

## Reproduced findings

- Mixed observed destinations: `a@corp.example` and `service-42` were both ALLOW under an unrestricted external policy; after synthesis they were ALLOW and DENY. A derived email-domain restriction rejects the non-email identifier.
- Minimality: with an absent `limit` argument, synthesis retains [1,100], while [1,1] still admits the observed call. The full policy-space least-element claim is withdrawn.
- Numeric abstraction: authority admits `limit=1000` and `limit=True`; the gate respectively returns BOUND to 100 and DENY under [1,100]. Exact argument-level correspondence is not established.
- Sensitivity: a tool with default INTERNAL sensitivity and a declared RESTRICTED column, but no column-selection parameter, receives ALLOW at INTERNAL clearance. Model/gate agreement does not establish adequate clearance enforcement.
- Malformed input: `columns=[{}]` raises TypeError rather than receiving a controlled denial. This is a robustness issue, not demonstrated unauthorised execution.

## Permitted claims

The conditional workflow model and reported finite and historical results remain available with their stated scope. Synthesis is candidate permission reduction with preservation demonstrated only on evaluated examples. The release makes no universal preservation, full-space optimality, unrestricted direct-effect tightness or complete implementation-refinement claim. Finite enumeration shares the authority constructor between the graph implementations and cannot independently validate that component.

The recorded test passes describe their existing domains; the counterexamples demonstrate missing coverage. Historical source docstrings, test names and imported audit reports may retain stronger language. This correction and docs/formal_model.md govern the current release. No missing records were reconstructed and no experiment outcomes were changed.
