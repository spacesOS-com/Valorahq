# -*- coding: utf-8 -*-
"""Default-deny indexing eligibility for consumer educational pages.

The manifest is an allowlist keyed by exact canonical path plus the reviewed
content/release hash. It does not bulk-change pages that are already emitted
under an older rule. A missing entry leaves that older rule in place. An
entry removes noindex only when it is a complete, current, dual-gated
educational approval. Rollback, draft, withheld, stale, malformed and
incomplete entries stay noindex and out of the sitemap.

Real-directory supply, draft cohorts and gated matching/referral routes are
separate gates. An educational guide can qualify without advisor supply, but
the roster renderer cannot, and a guide that implies verified specialists or
matching cannot qualify.

Shipped pages: none. business-owner, executive-professional and
retirement-planning are not eligible.

Example entry (do not ship until Zara, Maya and the approval references are
final for the current artifact):

{
  "path": "/find-a-financial-advisor/business-owner/",
  "artifact_sha256": "<64 lowercase hex of the rendered page with robots meta removed>",
  "purpose": "Educational guide for choosing financial help. No verified specialist roster and no matching.",
  "status": "eligible",
  "presentation": "educational-guide",
  "content_gate": {
    "reviewer": "Zara",
    "result": "pass",
    "scope": "final-content-source-claims",
    "evidence": "Final content, source and claims review of this artifact.",
    "reference": "review record id"
  },
  "integrated_qa": {
    "reviewer": "Maya",
    "result": "pass",
    "scope": "final-integrated-source-functionality-desktop-mobile",
    "evidence": "Integrated source, functionality and desktop/mobile review of this artifact.",
    "reference": "qa record id"
  },
  "approvals": [
    {"reference": "founder approval record", "note": "Per-page clearance for this path and hash."}
  ]
}

Add a page: append one exact-path object, rebuild, and confirm the renderer
and sitemap both follow catalog_include. Roll back: set that object's status
to "rolled-back" (keep the exact path) and rebuild. The page returns to
noindex and leaves the sitemap. Delete the object only to restore the older
base rule; deletion is not the rollback switch.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
POLICY = "default-deny"
CONTENT_REVIEWER = "Zara"
QA_REVIEWER = "Maya"
CONTENT_SCOPE = "final-content-source-claims"
QA_SCOPE = "final-integrated-source-functionality-desktop-mobile"
ELIGIBLE_PRESENTATION = "educational-guide"
PRESENTATIONS = {
    "educational-guide",
    "directory-roster",
    "baseline",
    "calculator",
    "content-page",
    "gated-route",
    "matching",
    "placeholder",
}
STATUSES = {"eligible", "draft", "rolled-back", "withheld"}
ENTRY_KEYS = {
    "path",
    "artifact_sha256",
    "purpose",
    "status",
    "presentation",
    "content_gate",
    "integrated_qa",
    "approvals",
}
GATE_KEYS = {"reviewer", "result", "scope", "evidence", "reference"}
CANDIDATE_PATHS = (
    "/find-a-financial-advisor/business-owner/",
    "/find-a-financial-advisor/executive-professional/",
    "/find-a-financial-advisor/retirement-planning/",
)
MANIFEST_PATH = Path(__file__).resolve().parent / "indexing-eligibility.json"
_SEGMENT = re.compile(r"^[a-z0-9](?:[a-z0-9._~&-]*[a-z0-9])?$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_ROBOTS_META = re.compile(r"<meta\b[^>]*\brobots\b[^>]*>\s*", re.I)

_override = None
_cached = None


class ManifestError(ValueError):
    """The manifest cannot be trusted. Callers must not index."""


class Entry:
    def __init__(self, data):
        self.path = data["path"]
        self.artifact_sha256 = data["artifact_sha256"]
        self.purpose = data["purpose"]
        self.status = data["status"]
        self.presentation = data["presentation"]
        self.content_gate = data.get("content_gate")
        self.integrated_qa = data.get("integrated_qa")
        self.approvals = data.get("approvals")


class Manifest:
    def __init__(self, pages):
        self.pages = pages

    def entry_for(self, path):
        if not isinstance(path, str):
            return None
        return self.pages.get(path)


def rendered_artifact_sha256(html):
    """Content/release hash. Robots markup is excluded so the decision is stable."""
    if not isinstance(html, str):
        raise ManifestError("artifact html must be a string")
    stripped = _ROBOTS_META.sub("", html)
    return hashlib.sha256(stripped.encode("utf-8")).hexdigest()


def artifact_sha256_bytes(data):
    if not isinstance(data, (bytes, bytearray)):
        raise ManifestError("artifact bytes required")
    return hashlib.sha256(bytes(data)).hexdigest()


def validate_manifest_path(path):
    if not isinstance(path, str):
        raise ManifestError("path must be a string")
    if path != path.strip() or any(ch.isspace() for ch in path):
        raise ManifestError("path is not normalized")
    if "*" in path or "?" in path or "#" in path or "\\" in path or "://" in path:
        raise ManifestError("wildcard or non-canonical path")
    if path == "/":
        return path
    if not path.startswith("/") or not path.endswith("/") or "//" in path:
        raise ManifestError("path is not an exact canonical path")
    parts = path.strip("/").split("/")
    if not parts or any(part in {"", ".", ".."} or part != part.lower() or not _SEGMENT.fullmatch(part) for part in parts):
        raise ManifestError("path is not normalized")
    return path


def _require_text(value, label):
    if not isinstance(value, str) or not value.strip() or "*" in value:
        raise ManifestError(f"{label} is missing or malformed")
    return value


def _validate_gate(value, label, reviewer, scope):
    if not isinstance(value, dict) or set(value) != GATE_KEYS:
        raise ManifestError(f"{label} fields are missing or malformed")
    if value["reviewer"] != reviewer or value["result"] != "pass" or value["scope"] != scope:
        raise ManifestError(f"{label} is not a final pass")
    _require_text(value["evidence"], f"{label} evidence")
    _require_text(value["reference"], f"{label} reference")


def _validate_approvals(value):
    if not isinstance(value, list) or not value:
        raise ManifestError("approval references are missing or malformed")
    for item in value:
        if not isinstance(item, dict) or set(item) - {"reference", "note"}:
            raise ManifestError("approval references are missing or malformed")
        reference = item.get("reference")
        if not isinstance(reference, str) or not reference.strip() or "*" in reference or reference.strip().lower() in {"all", "any"}:
            raise ManifestError("approval references are missing or malformed")
        if "note" in item and not isinstance(item["note"], str):
            raise ManifestError("approval references are missing or malformed")


def _parse_entry(raw):
    if not isinstance(raw, dict) or set(raw) - ENTRY_KEYS:
        raise ManifestError("manifest entry is malformed")
    for key in ("path", "artifact_sha256", "purpose", "status", "presentation"):
        if key not in raw:
            raise ManifestError(f"manifest entry is missing {key}")
    path = validate_manifest_path(raw["path"])
    digest = raw["artifact_sha256"]
    if not isinstance(digest, str) or not _SHA.fullmatch(digest):
        raise ManifestError("content hash is missing or malformed")
    purpose = _require_text(raw["purpose"], "purpose")
    status = raw["status"]
    presentation = raw["presentation"]
    if status not in STATUSES or presentation not in PRESENTATIONS:
        raise ManifestError("manifest entry status or presentation is malformed")
    if status == "eligible":
        if presentation != ELIGIBLE_PRESENTATION:
            raise ManifestError("only an educational guide can be eligible")
        _validate_gate(raw.get("content_gate"), "content gate", CONTENT_REVIEWER, CONTENT_SCOPE)
        _validate_gate(raw.get("integrated_qa"), "integrated QA", QA_REVIEWER, QA_SCOPE)
        _validate_approvals(raw.get("approvals"))
    else:
        for label, gate in (("content gate", raw.get("content_gate")), ("integrated QA", raw.get("integrated_qa"))):
            if gate is not None and not isinstance(gate, dict):
                raise ManifestError(f"{label} fields are missing or malformed")
        if "approvals" in raw and raw["approvals"] is not None and not isinstance(raw["approvals"], list):
            raise ManifestError("approval references are missing or malformed")
    data = dict(raw)
    data["path"] = path
    return Entry(data)


def parse_manifest(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "policy", "pages"}:
        raise ManifestError("manifest schema is malformed")
    if payload["schema_version"] != SCHEMA_VERSION or payload["policy"] != POLICY:
        raise ManifestError("manifest schema is malformed")
    pages = payload["pages"]
    if not isinstance(pages, list):
        raise ManifestError("manifest pages must be a list")
    found = {}
    for raw in pages:
        entry = _parse_entry(raw)
        if entry.path in found:
            raise ManifestError(f"duplicate manifest path {entry.path}")
        found[entry.path] = entry
    return Manifest(found)


def load_manifest(path=None):
    source = Path(path) if path is not None else MANIFEST_PATH
    if not source.is_file():
        raise ManifestError("indexing manifest is missing")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError("indexing manifest is malformed") from exc
    return parse_manifest(payload)


def get_manifest():
    if _override is not None:
        return _override
    global _cached
    if _cached is None:
        _cached = load_manifest()
    return _cached


def push_manifest(manifest):
    global _override
    _override = manifest


def reset_manifest():
    global _override, _cached
    _override = None
    _cached = None


def resolved_noindex(path, requested_noindex, eligibility=None, manifest=None):
    """Return whether the page must emit noindex.

    requested_noindex is the older renderer rule. With no manifest row, that
    rule is unchanged. A manifest row can force noindex, or clear it for one
    exact educational artifact that passed both final gates.
    """
    manifest = manifest if manifest is not None else get_manifest()
    requested = bool(requested_noindex)
    if not isinstance(path, str):
        return True
    entry = manifest.entry_for(path)
    if entry is None:
        return requested
    if entry.status in {"rolled-back", "draft", "withheld"} or entry.status != "eligible":
        return True
    ctx = eligibility or {}
    if ctx.get("draft") or ctx.get("cohort") in {"draft", "gated-route"}:
        return True
    supplied = ctx.get("artifact_sha256")
    hash_ok = isinstance(supplied, str) and supplied == entry.artifact_sha256
    educational = (
        ctx.get("cohort") == "educational"
        and ctx.get("presentation") == ELIGIBLE_PRESENTATION
        and entry.presentation == ELIGIBLE_PRESENTATION
        and not ctx.get("implies_verified_specialists")
        and not ctx.get("implies_matching")
    )
    if educational:
        return not hash_ok
    if ctx.get("cohort") == "directory-supply":
        if not ctx.get("supply_matched"):
            return True
        if supplied is not None and not hash_ok:
            return True
        return requested
    if supplied is not None and not hash_ok:
        return True
    if supplied is None:
        # An eligible claim without a bound artifact does not keep or grant indexing.
        return True
    return requested


def catalog_include(path, requested_noindex=False, eligibility=None, manifest=None):
    """Sitemap and llms inclusion. Same decision as the renderer."""
    return not resolved_noindex(path, requested_noindex, eligibility, manifest)


def manifest_grants(path, artifact_sha256, manifest=None, **flags):
    """True only when the manifest itself clears noindex for this exact artifact."""
    ctx = {
        "cohort": "educational",
        "presentation": ELIGIBLE_PRESENTATION,
        "artifact_sha256": artifact_sha256,
        "implies_verified_specialists": False,
        "implies_matching": False,
    }
    ctx.update(flags)
    return catalog_include(path, True, ctx, manifest)


def assert_bound_artifacts(manifest, hashes):
    """Fail closed when an eligible approval is missing or stale."""
    if not isinstance(hashes, dict):
        raise ManifestError("artifact hash map is malformed")
    for path, entry in manifest.pages.items():
        if entry.status != "eligible":
            continue
        current = hashes.get(path)
        if not isinstance(current, str) or not _SHA.fullmatch(current):
            raise ManifestError(f"eligible path {path} has no current artifact hash")
        if current != entry.artifact_sha256:
            raise ManifestError(f"content hash mismatch for {path}")


def public_html_path(root, canonical_path):
    root = Path(root)
    if canonical_path == "/":
        return root / "index.html"
    return root / canonical_path.strip("/") / "index.html"


def audit_public_tree(root, manifest=None):
    """Bind every eligible row to the built HTML. An empty allowlist succeeds."""
    manifest = manifest if manifest is not None else load_manifest()
    hashes = {}
    for path, entry in manifest.pages.items():
        if entry.status != "eligible":
            continue
        file_path = public_html_path(root, path)
        if not file_path.is_file():
            raise ManifestError(f"eligible path {path} has no built html")
        hashes[path] = rendered_artifact_sha256(file_path.read_text(encoding="utf-8"))
    assert_bound_artifacts(manifest, hashes)
    return manifest


def decision_noindex(payload, path, requested_noindex, eligibility=None, artifact_sha256=None):
    """Fail closed to noindex when the manifest cannot be parsed."""
    try:
        manifest = parse_manifest(payload)
    except ManifestError:
        return True
    ctx = dict(eligibility or {})
    if artifact_sha256 is not None:
        ctx["artifact_sha256"] = artifact_sha256
    return resolved_noindex(path, requested_noindex, ctx, manifest)
