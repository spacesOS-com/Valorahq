# Verified live checkpoint, October 7, 2026

This is source reconciliation only, not a release or content rewrite.

Baseline: consumer-oct7-tech-art-v1, 481 manifest-listed relative paths.
Host manifest SHA256: 87887c3d2614e96ee572e0dce34aa195b067a3c0e4260bdd23ada87689ce205c.
Extraction archive SHA256: b9e066aed4d18a7989680ad362cd640aebd9a0f5666a1888bb541f5bb62b8ff0.
Archive mode/time metadata is local, not host-original. File bytes verified.

The baseline imports exact current public HTML, runtime assets and recovered
source modules. Main-only _build/data/for-advisors.json is removed because it
is not in the current host baseline. Main-only assets/lead-capture.js is also
removed; the repository automation .github/workflows/claude.yml is preserved
unchanged and tracked as a repo-only file. Historical candidate-build receipts are
retained as historical bytes only; they are not the authoritative manifest.

## Build contract

`python3 _build/build.py` validates source/runtime bytes and public outputs.
It fails on any changed, missing or extra checkpoint file. It does not rewrite
or restore files. Approved scope changes require explicit manifest revisions
reviewed alongside their diffs. No acceptance or overwrite switch exists.

The deployed legacy generator is preserved byte-for-byte at
`_build/generator_legacy.py`; its original hash is in host-original-sha256.txt.
The replacement build entry is a validator. The 97 existing generated-route
drifts are quarantined in generator-drift.json; their exact served bytes are
versioned under reviewed-output. The unchanged public routes are also tracked
as current public files and public-output.json. Snapshots never overwrite a
changed working file at build end.

`python3 _build/build.py --audit-generators` copies the checkpoint into a
throwaway directory, runs legacy generation there, and returns nonzero when
any byte differs. It does not write the source tree. Legacy generation may
read its existing public feed sources; no form or inquiry is submitted.
This audit is not a production build and must not be deployed.

Repair generators in small reviewed groups. Preserve live inquiry behavior:
main's extra reviewedNoticeAccepted and ValoraLeads send behavior is absent
from the deployed runtime and is not imported. Preserve directory-disabled,
provider-off, consent/routing, existing tracking and indexing state.

## Pending scoped overlays

First-meeting art plus one sentence is included in the active checkpoint
consumer-oct7-first-meeting-art-word-v1 after reported guarded promotion at
14:45:32 IST and independent public target/six-asset hash readback.
Original tech-art-v1 provenance remains unchanged. Full host487 apply/readback receipts are retained in the revised checkpoint.
Zara live pixel verification remains tracked separately. Expected page hash after four substitutions:
8912741fdf10da79e0f9bc296d9d0d7b2e476bf9290b162692e7191299e12472.
Six new assets belong under assets/prepare-first-financial-advisor-meeting/.
That checkpoint remains the reviewed record of the seven-path promotion.
No inspection/preview HTML is deployment source.

## Active validator

`python3 _build/build.py` validates `_release/checkpoints/consumer-oct25-vendor-consent-v1`.

`consumer-oct7-first-meeting-art-word-v1` and `consumer-oct7-tech-art-v1` stay the previously reviewed bytes, including their `reviewed-output/` trees and manifests. `_build/live-reviewed/` stays the frozen generator input. The October 25 checkpoint records the working-tree hashes for the vendor-consent scope, including `reviewed-output/` copies of the quarantined drift paths. October 7 host receipts stay in the previous checkpoint only. The new directory follows the guarded-promotion shape: a new checkpoint, prior reviewed bytes left in place.

The first-meeting pagepack/original authoring archive was not recovered.
Current HTML and SVG bytes are release provenance, not authoring provenance.
