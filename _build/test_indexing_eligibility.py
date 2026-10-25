# -*- coding: utf-8 -*-
"""Default-deny indexing eligibility. Malformed manifests fail closed."""
import hashlib
import json
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import indexing_eligibility as eligibility
from indexing_eligibility import (
    CANDIDATE_PATHS,
    CONTENT_SCOPE,
    ManifestError,
    QA_SCOPE,
    audit_public_tree,
    catalog_include,
    decision_noindex,
    load_manifest,
    manifest_grants,
    parse_manifest,
    push_manifest,
    rendered_artifact_sha256,
    reset_manifest,
    resolved_noindex,
    validate_manifest_path,
)
from business_owner_page import BUSINESS_OWNER_PATH, business_owner_decision
from partials import head

ROOT = Path(__file__).resolve().parent.parent
PATH = "/find-a-financial-advisor/business-owner/"
OTHER = "/find-a-financial-advisor/executive-professional/"
HTML = "<html><head><title>Guide</title></head><body><p>Educational guide.</p></body></html>"


def digest(html=HTML):
    return rendered_artifact_sha256(html)


def gate(reviewer, scope, evidence="Final review of this artifact."):
    return {
        "reviewer": reviewer,
        "result": "pass",
        "scope": scope,
        "evidence": evidence,
        "reference": "record-" + reviewer.lower(),
    }


def entry(path=PATH, html=HTML, status="eligible", presentation="educational-guide", **overrides):
    row = {
        "path": path,
        "artifact_sha256": digest(html),
        "purpose": "Educational guide. No verified specialist roster and no matching.",
        "status": status,
        "presentation": presentation,
        "content_gate": gate("Zara", CONTENT_SCOPE),
        "integrated_qa": gate("Maya", QA_SCOPE),
        "approvals": [{"reference": "founder-approval-for-this-path", "note": "Per-page clearance."}],
    }
    row.update(overrides)
    return row


def payload(pages):
    return {"schema_version": 1, "policy": "default-deny", "pages": pages}


def use(pages):
    manifest = parse_manifest(payload(pages))
    push_manifest(manifest)
    return manifest


class EligibilityTests(unittest.TestCase):
    def tearDown(self):
        reset_manifest()

    def test_shipped_manifest_has_no_eligible_pages(self):
        manifest = load_manifest()
        self.assertEqual(list(manifest.pages), [])
        for path in CANDIDATE_PATHS:
            self.assertFalse(manifest_grants(path, digest(), manifest))
            self.assertIsNone(manifest.entry_for(path))
        audit_public_tree(ROOT, manifest)

    def test_historical_note_is_not_the_manifest(self):
        with self.assertRaises(ManifestError):
            load_manifest(ROOT / "_build" / "business-owner-indexing-eligibility.json")

    def test_empty_manifest_preserves_base_rules(self):
        manifest = load_manifest()
        cases = [
            (PATH, True, {"cohort": "directory-supply", "supply_matched": False, "presentation": "directory-roster", "implies_verified_specialists": True}),
            ("/find-a-financial-advisor/retirement-planning/", False, {"cohort": "directory-supply", "supply_matched": True, "presentation": "directory-roster", "implies_verified_specialists": True}),
            ("/find-a-financial-advisor/chicago/", True, {"cohort": "directory-supply", "supply_matched": False, "presentation": "directory-roster", "implies_verified_specialists": True}),
            ("/financial-advisor-for-dentists/", True, {"cohort": "draft", "draft": True, "presentation": "content-page"}),
            ("/financial-advisor-for-physicians/", False, {"cohort": "baseline", "presentation": "content-page"}),
            ("/calculators/qsbs-issue-spotter/", True, {"cohort": "baseline", "presentation": "calculator"}),
            ("/calculators/compound-interest/", False, {"cohort": "baseline", "presentation": "calculator"}),
            ("/concierge/", True, {"cohort": "gated-route", "presentation": "gated-route"}),
            ("/find-your-advisor/", False, {"cohort": "gated-route", "presentation": "matching", "implies_matching": True}),
            ("/", False, {"cohort": "baseline", "presentation": "baseline"}),
        ]
        for path, requested, ctx in cases:
            self.assertEqual(resolved_noindex(path, requested, ctx, manifest), requested, path)
            self.assertEqual(catalog_include(path, requested, ctx, manifest), not requested, path)
        self.assertFalse(business_owner_decision(manifest))

    def test_renderer_robots_string_unchanged_when_manifest_is_empty(self):
        reset_manifest()
        for requested in (False, True):
            skipped = head("Title", "Description", path="/guides/", noindex=requested, eligibility=False)
            consulted = head("Title", "Description", path="/guides/", noindex=requested)
            self.assertEqual(skipped, consulted)
        self.assertIn('<meta name="robots" content="noindex,follow">', head("Title", "Description", path="/guides/", noindex=True))
        self.assertNotIn("noindex", head("Title", "Description", path="/guides/", noindex=False))

    def test_missing_ungated_and_draft_rows_stay_out(self):
        manifest = use([entry(path=OTHER, status="draft", content_gate=None, integrated_qa=None, approvals=None)])
        self.assertTrue(resolved_noindex(PATH, True, self.edu(), manifest))
        self.assertFalse(catalog_include(PATH, True, self.edu(), manifest))
        ungated = entry()
        ungated["content_gate"] = gate("Zara", "source-only")
        self.assertTrue(decision_noindex(payload([ungated]), PATH, False, self.edu(), digest()))
        with self.assertRaises(ManifestError):
            parse_manifest(payload([ungated]))
        art_only = entry()
        art_only["integrated_qa"] = gate("Maya", "art-only")
        with self.assertRaises(ManifestError):
            parse_manifest(payload([art_only]))
        self.assertTrue(resolved_noindex(OTHER, False, self.edu(OTHER), manifest))
        self.assertFalse(catalog_include(OTHER, False, self.edu(OTHER), manifest))

    def test_stale_and_malformed_fail_closed(self):
        manifest = use([entry()])
        stale = self.edu()
        stale["artifact_sha256"] = "0" * 64
        self.assertTrue(resolved_noindex(PATH, False, stale, manifest))
        self.assertFalse(catalog_include(PATH, False, stale, manifest))
        with self.assertRaises(ManifestError):
            eligibility.assert_bound_artifacts(manifest, {PATH: "0" * 64})
        with self.assertRaises(ManifestError):
            eligibility.assert_bound_artifacts(manifest, {})
        for bad_path in (
            "*",
            "/*",
            "/find-a-financial-advisor/*/",
            "/find-a-financial-advisor/**/",
            "/find-a-financial-advisor/business-owner",
            "/find-a-financial-advisor/business-owner/index.html",
            "find-a-financial-advisor/business-owner/",
            "https://www.valorahq.com/find-a-financial-advisor/business-owner/",
            "/Find-a-financial-advisor/business-owner/",
            "/find-a-financial-advisor/./business-owner/",
            "/find-a-financial-advisor/foo/../business-owner/",
            "//find-a-financial-advisor/business-owner/",
            "/find-a-financial-advisor/business-owner/?q=1",
            "/find-a-financial-advisor/business-owner/#x",
            "/find-a-financial-advisor/business-owner/ ",
        ):
            with self.assertRaises(ManifestError):
                validate_manifest_path(bad_path)
        with self.assertRaises(ManifestError):
            parse_manifest(payload([entry(), entry()]))
        broken = entry()
        del broken["integrated_qa"]
        with self.assertRaises(ManifestError):
            parse_manifest(payload([broken]))
        wildcard_approval = entry()
        wildcard_approval["approvals"] = [{"reference": "*"}]
        with self.assertRaises(ManifestError):
            parse_manifest(payload([wildcard_approval]))
        self.assertTrue(decision_noindex({"pages": [entry()]}, PATH, False))

    def test_only_exact_dual_passed_artifact_is_indexable_and_agrees(self):
        manifest = use([entry()])
        ctx = self.edu()
        self.assertFalse(resolved_noindex(PATH, True, ctx, manifest))
        self.assertTrue(catalog_include(PATH, True, ctx, manifest))
        rendered = head("Title", "Description", path=PATH, noindex=True, eligibility=ctx)
        self.assertNotIn("noindex", rendered)
        self.assertIn(f'href="https://www.valorahq.com{PATH}"', rendered)
        self.assertEqual("noindex" in rendered, not catalog_include(PATH, True, ctx, manifest))
        changed = HTML.replace("Educational", "Changed")
        self.assertNotEqual(digest(changed), digest())
        stale = dict(ctx)
        stale["artifact_sha256"] = digest(changed)
        self.assertTrue(resolved_noindex(PATH, False, stale, manifest))
        self.assertFalse(catalog_include(PATH, False, stale, manifest))

    def test_supply_draft_gated_and_implication_gates_stay_distinct(self):
        manifest = use([entry()])
        ctx = self.edu()
        roster = {"cohort": "directory-supply", "supply_matched": False, "presentation": "directory-roster", "implies_verified_specialists": True, "artifact_sha256": digest()}
        self.assertTrue(resolved_noindex(PATH, True, roster, manifest))
        self.assertFalse(catalog_include(PATH, True, roster, manifest))
        supplied = dict(roster)
        supplied["supply_matched"] = True
        self.assertFalse(resolved_noindex(PATH, False, supplied, manifest))
        for flag in ("implies_verified_specialists", "implies_matching"):
            blocked = dict(ctx)
            blocked[flag] = True
            self.assertTrue(resolved_noindex(PATH, True, blocked, manifest))
        draft = dict(ctx)
        draft["draft"] = True
        draft["cohort"] = "draft"
        self.assertTrue(resolved_noindex(PATH, False, draft, manifest))
        gated = dict(ctx)
        gated["cohort"] = "gated-route"
        self.assertTrue(resolved_noindex(PATH, False, gated, manifest))
        self.assertFalse(resolved_noindex("/find-your-advisor/", False, {"cohort": "gated-route", "presentation": "matching", "implies_matching": True}, manifest))

    def test_exact_path_rollback(self):
        rolled = entry(status="rolled-back", content_gate=None, integrated_qa=None, approvals=None)
        manifest = use([rolled])
        self.assertTrue(resolved_noindex(PATH, False, self.edu(), manifest))
        self.assertFalse(catalog_include(PATH, False, {"cohort": "baseline", "presentation": "baseline"}, manifest))
        self.assertFalse(resolved_noindex(OTHER, False, {"cohort": "baseline", "presentation": "baseline"}, manifest))
        self.assertTrue(catalog_include(OTHER, False, {"cohort": "baseline", "presentation": "baseline"}, manifest))
        self.assertTrue(business_owner_decision(manifest))

    def test_public_sitemap_is_valid_and_directives_are_unedited(self):
        tree = ET.parse(ROOT / "sitemap.xml")
        urls = tree.getroot().findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        self.assertGreater(len(urls), 0)
        diff = subprocess.check_output(
            ["git", "diff", "--name-only", "--", "*.html", "sitemap.xml", "robots.txt", "llms.txt", "llms-full.txt"],
            cwd=ROOT,
        )
        self.assertEqual(diff, b"")

    def edu(self, path=PATH, html=HTML):
        return {
            "cohort": "educational",
            "presentation": "educational-guide",
            "artifact_sha256": digest(html),
            "implies_verified_specialists": False,
            "implies_matching": False,
            "path": path,
        }


class HashStabilityTests(unittest.TestCase):
    def test_robots_markup_does_not_change_the_artifact_hash(self):
        bare = "<head><title>Guide</title></head>"
        tagged = '<head><meta name="robots" content="noindex,follow">\n<title>Guide</title></head>'
        indexed = '<head><meta content="index,follow" name="robots"/>\n<title>Guide</title></head>'
        self.assertEqual(rendered_artifact_sha256(bare), rendered_artifact_sha256(tagged))
        self.assertEqual(rendered_artifact_sha256(bare), rendered_artifact_sha256(indexed))
        self.assertEqual(len(digest()), 64)
        self.assertEqual(digest(), hashlib.sha256(_robots_stripped(HTML)).hexdigest())


def _robots_stripped(html):
    import re
    return re.sub(r"<meta\b[^>]*\brobots\b[^>]*>\s*", "", html, flags=re.I).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
