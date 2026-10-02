"""Conversation release preparation. Default-off, independent of guide finder.

Only the exact reviewed 12 page contexts can receive chat. Existing PostHog and RB2B loaders are preserved on these pages.
Widget elements use ph-no-capture; project settings are reviewed separately.
Enabling this build switch is a separate reviewed deployment decision.
"""
import hashlib
import json
import os
import re

CONVERSATION_UI_ENABLED = os.environ.get('VALORA_CONVERSATION_UI_ENABLED') == 'true'

def prepare_conversation_surfaces(root):
    if not CONVERSATION_UI_ENABLED:
        return
    config_path = os.path.join(root, 'assets', 'conversation-context-draft.json')
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    if any(config.get(k) is not True for k in ('approved','noticeApproved','collectionApproved')):
        raise ValueError('Conversation UI contract is not approved')
    version = hashlib.sha1(open(os.path.join(root, 'assets', 'conversation.js'), 'rb').read()).hexdigest()[:8]
    css_version = hashlib.sha1(open(os.path.join(root, 'assets', 'floating-v9.css'), 'rb').read()).hexdigest()[:8]
    for page in config['pages']:
        path = page['path']
        if not re.fullmatch(r'/(?:[a-z0-9&-]+/)*', path):
            raise ValueError('Invalid reviewed path')
        file = os.path.join(root, path.strip('/'), 'index.html')
        with open(file, encoding='utf-8') as f:
            html = f.read()
        # Preserve existing vendor loaders exactly. Replay disclosure and
        # project masking settings are separate reviewed enable gates.
        html = html.replace('<div id="valora-concierge" hidden></div>', '<div id="valora-conversation" data-endpoint="https://api.valorahq.com/api/valora/conversation" data-intake-route="/#contact" data-intake-label="Send an inquiry" hidden></div>')
        # No endpoint is inserted here. Reviewed deployment config must supply it separately.
        inline = json.dumps(config, separators=(',', ':')).replace('<', '\\u003c')
        scripts = '<script>window.ValoraConversationConfig=' + inline + ';</script><script src="/assets/conversation.js?v=' + version + '"></script>'
        html, count = re.subn(r'<script src="/assets/concierge.js(?:\?v=[a-z0-9]+)?"></script>', lambda _: scripts, html)
        if count != 1:
            raise ValueError('Ambiguous guide-finder script on ' + path)
        html = html.replace('width=device-width, initial-scale=1.0', 'width=device-width, initial-scale=1.0, interactive-widget=resizes-content')
        html = html.replace('</head>', '<link rel="stylesheet" href="/assets/floating-v9.css?v=' + css_version + '"></head>')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
