his document defines the methodology, governance, and technical controls used to **anonymize Polish complaint data** so that published / shared datasets are no longer “personal data” under the GDPR
- Techniques applied (multi‑layer, defense-in-depth).
- Why resulting output is **irreversibly anonymized** (i.e. no natural person is identifiable directly or indirectly with reasonable means).
- Risk assessment framework and thresholds.
- Controls to prevent rollback, linkage, or re-identification.

| In Scope | Out of Scope |
|----------|--------------|
| Semi-structured & unstructured (free-text complaint narratives, attachments) | Raw production databases (only accessed inside controlled pipeline) 



## 2. Design Principles (Narrative)

The system is deliberately modular. Incoming text is first normalized (homoglyph unification, removal of zero‑width characters, expansion of obfuscation markers, digit compaction). This ensures determinism for the subsequent pattern layer. spaCy’s Polish model then proposes probabilistic entity spans. Independent regex components—augmented with checksum validators—produce high‑confidence spans for rigid identifiers. A unification stage merges spans with a deterministic priority order (validated pattern > high‑confidence NER > dictionary > low‑confidence NER). Heuristics then reassess residual context for rare uniqueness amplifiers (e.g., niche occupation + small locality). Final replacements use stable category tokens (e.g., “[PERSON]”) without per‑record indexing to prevent unintended linkability.
All decisions are recorded at the category level only; raw captured substrings are never persisted beyond the in‑memory transformation boundary. This separation means auditing focuses on provenance (which detector fired) rather than reconstructing sensitive input.

## 3. Why This Meets Current Performance and Risk Objectives

Empirically, structured identifiers dominate risk severity (a leaked PESEL or IBAN is inherently higher sensitivity than a single common surname). Deterministic patterns with checksum gating push the miss probability for those fields toward negligible levels. The residual risk surface is therefore dominated by personal names and finer locality references. spaCy’s baseline recall on PERSON/GPE classes is high enough to form a solid foundation, and incremental dictionary + lemma matching raises effective recall substantially without retraining overhead. 

Crucially, the hybrid approach is “inspectable”: for any disputed omission or false positive, there is a finite, human‑comprehensible rule or model confidence threshold to adjust. This shortens root‑cause analysis time and prevents stagnation behind opaque probability layers. The speed (sub‑150 ms p95 per record on CPU) enables full‑throughput deployment without GPU scheduling complexity, and cost remains linear and predictable.


## 4. Error Surface and Containment Strategy

Typical false negatives concentrate in three zones: (1) novel or rare inflected surnames absent from training data and dictionaries; (2) aggressively obfuscated emails or phone numbers employing bracket fragmentation or visually similar characters; (3) multi‑token entities split by punctuation anomalies. Each is countered by targeted, low‑impact mitigations: lemma-based surname extension, pre‑normalization expansion tables, and token span stitching heuristics.

False positives cluster where numeric strings mimic identifiers (invoice numbers vs PESEL) or organizations are misclassified as persons. Checksum enforcement, contextual cue checking (presence of “NIP”, “KRS” labels), and a controlled whitelist of high‑frequency institution names mitigate these cheaply. This targeted posture stops us from resorting to blanket threshold relaxation—which would trade precision for recall unnecessarily.




## 4. Key Definitions

| Term | Definition | Relevance |
|------|------------|-----------|
| Personal Data | Any information relating to an identifiable natural person | Must be excluded post-process |
| Anonymization | Irreversible process rendering data not relating to an identifiable person (Recital 26) | Goal state |
| Pseudonymization | Replacing identifiers so they can still be reversed / linked with a key | Transitional only—NOT final release |
| Quasi-Identifiers | Attributes that alone or in combination may identify (e.g. postal code + age + rare occupation) | Core risk factors |
| Singling Out | Ability to isolate an individual | Must be prevented / bounded |
| Linkability | Ability to link records across datasets | Must be controlled |
| Inference Risk | Ability to deduce sensitive attribute | Must be mitigated |



## 5. Anonymization Principles Applied

1. **Data Minimization**: Only fields required for statistical / analytical purpose retained.  
2. **Layered Technique Stack**: No reliance on a single transformation.  
3. **Risk-Based**: Quantitative plus qualitative risk scoring (k-anonymity / l-diversity / disclosure risk model).  
4. **Irreversibility Enforcement**: Destruction of cryptographic materials used in any temporary pseudonymization stage.  
5. **Contextual Utility Preservation**: Maintain aggregate insights (e.g., category of complaint, broad region).  
6. **Continuous Validation**: Periodic re-identification testing as dataset evolves.

## Pros of Proposed solution 


After deterministic capture of rigid identifiers, the residual leak scenario centers on infrequent names or place references combined with auxiliary context. The hybrid pipeline reduces base probability by catching the majority of overt name tokens, abstracting IDs, and generalizing or tokenizing singularly revealing compounds when heuristics flag them. Remaining risk is therefore bounded and further mitigated by continuous sampling and rapid iteration. Importantly, any single missed contextual name—untethered from direct numeric identifiers—has sharply reduced exploitability. The monitoring approach is intentionally tuned to detect even isolated high‑severity misses, reinforcing a low residual rate posture rather than relying on aggregate statistics alone.


## 6 Monitoring 

All transformation rules, regex patterns, and dictionaries are version‑tracked. A change request includes rationale (e.g., “emergent obfuscation pattern for emails”), unit tests (pattern correctness, checksum validation), and regression results against the gold set. Automated evaluation must meet or exceed baseline metrics within tolerance. The deployment path mandates: merge to staging, run canary, collect 24h panel metrics, then approve full rollout. Rollback is immediate via previous manifest tag if any alert condition fires. The NER model version hash is recorded with each batch to enable post‑hoc forensic reconstruction of decisions.


## Summarisation 


The current hybrid spaCy NER + regex + dictionary approach strikes an intentional balance: deterministic certainty for structured sensitive patterns, probabilistic linguistic coverage for morphologically variable entities, lightweight heuristics for edge uniqueness, and a governance loop that ensures the system stays both accurate and explainable. It is proportionate to the risk profile and data characteristics we face now, scalable without specialized hardware, and trivially auditable. Future sophistication will be layered only when empirical evidence demonstrates that incremental adjustments can no longer maintain target recall and precision. Until then, this architecture is the most efficient, transparent, and controllable means to achieve robust redaction in Polish complaint text.



