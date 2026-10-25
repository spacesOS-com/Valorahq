"""Consent gate checks that do not contact a live endpoint."""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '_build'))
import partials  # noqa: E402

MARKERS = ('posthog.init(', 'window.reb2b', 'ddwl4m2hdecbv.cloudfront.net')


def strip_vendor_loaders(html):
    """Same removal the scoped wealth and selling-business releases apply."""
    return re.sub(
        r'<script\b[^>]*>.*?</script>',
        lambda match: '' if any(marker in match[0] for marker in MARKERS) else match[0],
        html,
        flags=re.S | re.I,
    )


def test_release_stripper_still_removes_gated_config():
    html = '<html><head>' + partials.vendor_consent_markup() + '</head></html>'
    stripped = strip_vendor_loaders(html)
    lowered = stripped.lower()
    for marker in MARKERS:
        assert marker not in lowered, marker
    assert 'vendor-consent.js' in stripped
    for release in ('owner_wealth_release.py', 'selling_business_release.py'):
        source = (ROOT / '_build' / release).read_text()
        for marker in MARKERS:
            assert marker in source


def test_behavior_without_live_endpoints():
    subprocess.run(['node', str(ROOT / 'tests/vendor-consent.test.js')], check=True, cwd=ROOT)


if __name__ == '__main__':
    test_release_stripper_still_removes_gated_config()
    test_behavior_without_live_endpoints()
    print('python vendor consent checks passed')
