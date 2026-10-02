"""Build the live-reviewed modal inquiry."""
ROOT_INQUIRY_STYLE = '<style>#contact{scroll-margin-top:90px}#contact .root-inquiry{max-width:1050px}#contact .progress{font-size:13px;text-transform:uppercase;letter-spacing:.14em;color:#63705d;margin-bottom:25px}#contact .screen{display:grid;grid-template-columns:1fr 1.15fr;gap:50px;min-height:390px}#contact h1{font:42px/1.12 Georgia,serif;letter-spacing:-.02em;margin:0 0 22px}#contact p{margin:0 0 20px}#contact .fields{display:grid;grid-template-columns:1fr;gap:17px}#contact label{display:block;font-size:14px}#contact input,#contact textarea{font:16px Arial,sans-serif;width:100%;padding:16px;background:white;border:1px solid #cbc8bd;border-radius:16px;margin-top:7px}#contact textarea{height:170px;resize:vertical}#contact .choices{display:grid;gap:12px}#contact .choice{display:flex;gap:18px;align-items:center;text-align:left;border:1px solid transparent;background:#efebe0;color:#242920;padding:17px;border-radius:22px;cursor:pointer;font:16px Arial,sans-serif}#contact .choice b{font-size:13px;background:#f8f6f1;border-radius:6px;padding:5px 9px}#contact .choice[aria-checked=true]{border-color:#1e3b2a;background:#e0e8db}#contact .inquiry-nav{display:flex;justify-content:space-between;gap:20px;margin-top:35px}#contact .btn{padding:14px 24px;border-radius:24px;background:#1e3b2a;color:white;border:0;font:16px Arial,sans-serif;cursor:pointer}#contact .back{background:transparent;color:#1e3b2a;border:1px solid #babfb4}#contact .err{color:#ad2e25;font-size:14px;min-height:22px;margin-top:12px}#contact button:focus-visible,#contact input:focus-visible,#contact textarea:focus-visible{outline:3px solid #3a7057;outline-offset:3px}#contact .privacy,#contact #sendDisclosure{font-size:14px;line-height:1.6;margin-top:20px}#contact [hidden]{display:none!important}@media(max-width:650px){#contact .screen{grid-template-columns:1fr;gap:20px;min-height:0}#contact h1{font-size:33px}#contact .fields{grid-template-columns:1fr}#contact .inquiry-nav{margin-top:25px}#contact .choice{padding:15px}#contact .progress{margin-bottom:18px}}</style>'

INQUIRY_HOST_TOKEN = '<!--inquiry-form-->'


def inquiry_form_section():
    """The one reviewed five-step form. Exactly one per page (ids are unique)."""
    return '<section class="section section--paper" id="contact"><div class="container root-inquiry"><div class="progress" id="progress"></div><form id="flow" data-endpoint="https://script.google.com/macros/s/AKfycbx4mCwhZBQS-0W-UAybBeIJm67scGp4cpwAR_19l4g-FSa-XacfhNyOAPT0W0CEd0uc/exec" novalidate><div id="screen" class="screen"></div><p id="sendDisclosure" hidden>How we handle your details, including who receives them, is in our <a href="/privacy/">Privacy Policy</a>.</p><div class="err" id="error" role="alert"></div><div class="inquiry-nav"><button type="button" id="back" class="btn back">Back</button><button type="submit" id="next" class="btn">Continue</button></div></form></div></section>'


def inquiry_host(embed=False):
    """Inline home for the form (hero card, green CTA band). The dialog
    borrows the form from here while open -- see root-inquiry-modal.js.
    embed=False leaves a token for partials.page() to fill after its
    id="contact" collision rename."""
    return '<div class="inquiry-host" data-inquiry-host>' + (inquiry_form_section() if embed else INQUIRY_HOST_TOKEN) + '</div>'


def root_contact_section(with_form=True):
    return '<dialog id="rootInquiryDialog" aria-label="Send Valora an inquiry"><button type="button" class="inquiry-modal-close" aria-label="Close inquiry">Close</button>' + (inquiry_form_section() if with_form else '') + '</dialog>'

def root_hero_card():
    return '<aside class="hcard hcard--inquiry">' + inquiry_host(embed=True) + '</aside>'
