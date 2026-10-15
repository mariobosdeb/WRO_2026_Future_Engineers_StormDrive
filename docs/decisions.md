# Engineering Decisions

The records below preserve decisions documented in the repository. They do not include the team's full alternatives or comparative test evidence.

## Decision record template

### DR-XXX — Short title

**Date:** TODO(team): Add the decision date.  
**Status:** Proposed / Tested / Accepted / Rejected

**Problem or constraint:**  
**Options considered:**  
**Decision and reason:**  
**Evidence:** Link to measurement, test, photo, model or commit.  
**Trade-offs and risks:**  
**Follow-up test:**

## Existing decisions

### DR-001 — Develop V2 on an Adeept PiCar-B platform

Existing project documentation identifies Adeept PiCar-B as the V2 base platform and separates it from the earlier V1 vehicle. TODO(team): Add the actual comparison criteria, alternatives, date and test evidence behind this choice.

### DR-002 — Separate vendor examples from competition software

The repository keeps selected Adeept examples under `vendor/adeept-picar-b2/` and StormDrive V2 software under `src/v2/`. This makes the distinction visible in the source tree. TODO(team): Verify upstream attribution, license and which files were modified.

### DR-003 — Tie performance claims to evidence

Project documentation policy is to distinguish measured results from code-derived estimates and team-reported summaries. Add physical result claims only with dated run evidence, the tested commit and configuration.
