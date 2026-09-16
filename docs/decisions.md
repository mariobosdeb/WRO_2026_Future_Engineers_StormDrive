# 🧠 StormDrive Engineering Decisions

This file records decisions where the team considered alternatives and selected an approach.

## Decision record template

### DR-XXX — Short title

**Date:** YYYY-MM-DD  
**Status:** Proposed / Tested / Accepted / Rejected

**Problem / constraint**  
What problem are we solving?

**Options considered**

- Option A
- Option B
- Option C

**Decision**  
We chose X instead of Y because ...

**Evidence**  
Link to test, measurement, photo, CAD revision or code commit.

**Trade-offs**  
What did we gain and what did we give up?

**Risk / mitigation**  
What could still fail and how will we verify it?

**Follow-up**  
What must be tested next?

---

## Initial records

### DR-001 — Move from V1 to V2 platform

**Status:** Accepted

The team selected a new Adeept PiCar-B platform for the European-stage development instead of continuing the V1 platform as the main development base.

The decision should be expanded with the team's actual comparison criteria and test evidence as V2 testing progresses.

### DR-002 — Separate manufacturer reference from competition implementation

**Status:** Accepted

The supplied Adeept software and documentation are used as technical reference material. StormDrive competition software will be developed and documented separately so that the repository clearly distinguishes vendor examples from the team's own implementation.

### DR-003 — Evidence before performance claims

**Status:** Accepted

Performance claims will only be added after repeatable tests produce supporting measurements. Estimated or unsupported percentages will not be presented as measured results.
