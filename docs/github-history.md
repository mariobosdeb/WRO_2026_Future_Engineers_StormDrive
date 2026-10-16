# GitHub History and Submission Audit

This page records a read-only review of the public `main` branch history and repository metadata on 2026-10-16. It preserves the history as found; no commit date or content has been rewritten.

## Visible source timeline

| Date (UTC) | Repository evidence | What it proves |
|---|---|---|
| 2026-06-04 | First commit, `2f02be5`, adds only `README.md` (one blob in its tree). | The first repository commit contains no program source. |
| 2026-06-06 to 2026-06-13 | Arduino/configuration source and V1 project files appear in the visible history. | Earlier V1 work was committed before the 2026 event. |
| 2026-09-16 | Vendor references and WRO/V2 documentation commits appear. | The history contains a commit before the two-week milestone, but that commit does not contain the later V2 source tree. |
| 2026-10-11 08:39 UTC | Commit `f11d06f` first adds `src/v2/`, including the Python modules and C++ lattice planner. | The current V2 software entered `main` after the planned two-week-before-event date. |
| 2026-10-15 | Last main-branch snapshot reviewed here: `983e5d8`. | This is the reviewed source-history endpoint; this documentation PR is later and does not change that historical record. |

The official international event is listed for 2026-10-13 through 2026-10-16. Counting back from the first event day gives approximate milestones of 2026-08-13 (two months), 2026-09-13 (one month), 2026-09-29 (two weeks) and 2026-09-22 (three weeks for the repository link). The rules note that organizers announce exact submission timing; confirm the applicable local organizer instructions.

## What can and cannot be concluded

- The first commit is dated early enough, but its tree contains only a README. It therefore does not demonstrate the required first-commit contribution of at least one-fifth of the final code.
- V1 source existed months earlier. The first `src/v2/` code commit is `f11d06f` on 2026-10-11, after the approximate two-week milestone.
- There are commits on 2026-09-16, but their existence alone does not establish that the milestone requirements were met: the first-commit content condition is not shown, and the V2 software had not yet been added.
- The repository is public as of this review. The public API snapshot cannot establish its visibility on the submission date, the timestamp when its URL was submitted, or which commit the organizer received.
- The main branch has no GitHub tag or release in the metadata snapshot reviewed. A release template is not a published, tested release.

These are history facts, not a claim about an organizer's score or a ruling on eligibility. The timeline is not repairable by adding backdated commits. For current evidence tasks, see [TODO.md](../TODO.md).

## Sources

- [WRO 2026 Game Rules (PDF)](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.pdf)
- [WRO International Events](https://wro-association.org/competition/international-events/)
- [Visible repository commit history](https://github.com/mariobosdeb/WRO_2026_Future_Engineers_StormDrive/commits/main)
- [Repository metadata](https://api.github.com/repos/mariobosdeb/WRO_2026_Future_Engineers_StormDrive)
