## Summary

Moves the advisor articles out of `/insights/` in the public URL plan. Stacked on #53 (`cursor/sitemap-advisor-hub-redirects-7292`). No deploy in this PR. Nothing here changes the live nginx, Traefik, or Ghost process.

This repo does not contain the advisor articles. `insights/` has the household index and six hand-built articles only. There is no Ghost theme, no Ghost `routes.yaml`, and no proxy config. `advisor-resources`, `can-chatgpt-find-your-firm`, `smartasset-alternatives`, the newsletter-unsubscribe post, and the video-transcript post are not files here. The two inventory rows marked `main=Y` (the transcript post and the newsletter-unsubscribe post) still have no HTML in this tree, so they are treated as Ghost, same as the other 51.

`advisor-resources` is a Ghost page, not a static page. It becomes the `/for-advisors/insights/` index.

## What changed in the repo

- Sitemap lists the 53 new post URLs, `/for-advisors/insights/`, and `/for-advisors/can-chatgpt-find-your-firm/`. Ghost URLs have no `<lastmod>`. File-backed URLs still use `git log -1 --format=%cs` of the HTML file.
- `/insights/` title, description, Open Graph, and Twitter tags are household-facing, and the visible heading matches.
- The six household articles point the "All insights" button at `/insights/`. Nav and footer `/#insights` links are unchanged.
- `robots.txt` keeps the old Ghost admin disallows and adds the same three under `/for-advisors/insights/`.
- Route list: `_build/advisor_insight_routes.json`.

`python3 _build/build.py` passes.

## Validation

| Check | Result |
| --- | --- |
| Advisor posts moved in the URL plan | 53 |
| Duplicate redirects, targets missing | 16 of 16 missing |
| Household articles kept at `/insights/<slug>/` | 6 |
| Sitemap URLs before | 84, all with lastmod |
| Sitemap URLs after | 139 = 84 with lastmod + 55 without |
| Advisor `/insights/<slug>/` left in the sitemap | 0 |
| Ampersand URLs | 0 |
| File-backed lastmod vs `git log -1 --format=%cs` | 0 mismatches |
| Distinct file-backed lastmod dates | 4 (2026-10-15, 2026-10-16, 2026-10-21, 2026-10-25) |
| Checkpoint | PASS |

The 55 Ghost sitemap URLs are 53 posts + the index + the ChatGPT page. They 404 until the server move below. lastmod is omitted because this git tree has never stored those pages. Ghost `updated_at` lives on the server and was not copied in.

## CTO steps after review

Apply this on the host that currently proxies `/insights/` to Ghost 5.130. The repo has no nginx or Traefik config. If both proxies are in front of the site, put the 301s on the outer one. Do not deploy this branch to do that.

### 1. Ghost `url`

In `config.production.json` (no trailing slash):

```json
"url": "https://www.valorahq.com/for-advisors/insights"
```

Restart Ghost. Keep the existing listen port (2368 unless the current proxy uses another). `proxy_pass` must not strip `/for-advisors/insights`, because Ghost serves the subdirectory itself.

### 2. Delete the prefix proxy for `/insights/`

A location prefix for `/insights/` that proxies to Ghost swallows the household index and the six articles. Remove it. Do not replace it with another prefix rule.

### 3. nginx

`map` goes in the `http` block. The `return` is in the `server` block, so it runs in the rewrite phase before location selection. `$uri` has no query string. `$is_args$args` puts the query back on the 301. Both slash forms are listed. These keys are absent on purpose: `/insights`, `/insights/`, and the six household slugs.

```nginx
map $uri $insights_redirect {
    default "";
    /insights/ai-search-is-eating-the-referral-game-heres-what-advisors-do-in-the-next-12-months /for-advisors/insights/ai-search-is-eating-the-referral-game-heres-what-advisors-do-in-the-next-12-months/
    /insights/ai-search-is-eating-the-referral-game-heres-what-advisors-do-in-the-next-12-months/ /for-advisors/insights/ai-search-is-eating-the-referral-game-heres-what-advisors-do-in-the-next-12-months/
    /insights/geo-vs-seo-advisory-firm-website /for-advisors/insights/geo-vs-seo-advisory-firm-website/
    /insights/geo-vs-seo-advisory-firm-website/ /for-advisors/insights/geo-vs-seo-advisory-firm-website/
    /insights/how-can-an-advisory-firm-check-what-ai-answers-say-about-it-a-20-question-starter-panel /for-advisors/insights/how-can-an-advisory-firm-check-what-ai-answers-say-about-it-a-20-question-starter-panel/
    /insights/how-can-an-advisory-firm-check-what-ai-answers-say-about-it-a-20-question-starter-panel/ /for-advisors/insights/how-can-an-advisory-firm-check-what-ai-answers-say-about-it-a-20-question-starter-panel/
    /insights/how-can-an-ria-check-whether-its-important-pages-are-indexable /for-advisors/insights/how-can-an-ria-check-whether-its-important-pages-are-indexable/
    /insights/how-can-an-ria-check-whether-its-important-pages-are-indexable/ /for-advisors/insights/how-can-an-ria-check-whether-its-important-pages-are-indexable/
    /insights/how-can-an-ria-get-clients-from-chatgpt-and-ai-search /for-advisors/insights/how-can-an-ria-get-clients-from-chatgpt-and-ai-search/
    /insights/how-can-an-ria-get-clients-from-chatgpt-and-ai-search/ /for-advisors/insights/how-can-an-ria-get-clients-from-chatgpt-and-ai-search/
    /insights/how-can-an-ria-measure-referral-source-quality /for-advisors/insights/how-can-an-ria-measure-referral-source-quality/
    /insights/how-can-an-ria-measure-referral-source-quality/ /for-advisors/insights/how-can-an-ria-measure-referral-source-quality/
    /insights/how-should-a-financial-advisor-add-ai-discovery-measurement-to-a-marketing-plan /for-advisors/insights/how-should-a-financial-advisor-add-ai-discovery-measurement-to-a-marketing-plan/
    /insights/how-should-a-financial-advisor-add-ai-discovery-measurement-to-a-marketing-plan/ /for-advisors/insights/how-should-a-financial-advisor-add-ai-discovery-measurement-to-a-marketing-plan/
    /insights/how-should-a-financial-advisor-choose-a-niche /for-advisors/insights/how-should-a-financial-advisor-choose-a-niche/
    /insights/how-should-a-financial-advisor-choose-a-niche/ /for-advisors/insights/how-should-a-financial-advisor-choose-a-niche/
    /insights/how-should-a-small-advisory-firm-budget-and-test-video-marketing /for-advisors/insights/how-should-a-small-advisory-firm-budget-and-test-video-marketing/
    /insights/how-should-a-small-advisory-firm-budget-and-test-video-marketing/ /for-advisors/insights/how-should-a-small-advisory-firm-budget-and-test-video-marketing/
    /insights/how-should-an-advisor-handle-a-prospect-checking-an-explanation-with-chatgpt /for-advisors/insights/how-should-an-advisor-handle-a-prospect-checking-an-explanation-with-chatgpt/
    /insights/how-should-an-advisor-handle-a-prospect-checking-an-explanation-with-chatgpt/ /for-advisors/insights/how-should-an-advisor-handle-a-prospect-checking-an-explanation-with-chatgpt/
    /insights/how-should-an-advisory-firm-correct-wrong-names-addresses-and-services-in-ai-answers /for-advisors/insights/how-should-an-advisory-firm-correct-wrong-names-addresses-and-services-in-ai-answers/
    /insights/how-should-an-advisory-firm-correct-wrong-names-addresses-and-services-in-ai-answers/ /for-advisors/insights/how-should-an-advisory-firm-correct-wrong-names-addresses-and-services-in-ai-answers/
    /insights/how-should-an-advisory-firm-make-a-chart-understandable-without-relying-on-the-image /for-advisors/insights/how-should-an-advisory-firm-make-a-chart-understandable-without-relying-on-the-image/
    /insights/how-should-an-advisory-firm-make-a-chart-understandable-without-relying-on-the-image/ /for-advisors/insights/how-should-an-advisory-firm-make-a-chart-understandable-without-relying-on-the-image/
    /insights/how-should-an-ria-build-a-website-claim-review-ledger /for-advisors/insights/how-should-an-ria-build-a-website-claim-review-ledger/
    /insights/how-should-an-ria-build-a-website-claim-review-ledger/ /for-advisors/insights/how-should-an-ria-build-a-website-claim-review-ledger/
    /insights/how-should-an-ria-choose-its-first-ai-search-content-topic-without-a-huge-prompt-dataset /for-advisors/insights/how-should-an-ria-choose-its-first-ai-search-content-topic-without-a-huge-prompt-dataset/
    /insights/how-should-an-ria-choose-its-first-ai-search-content-topic-without-a-huge-prompt-dataset/ /for-advisors/insights/how-should-an-ria-choose-its-first-ai-search-content-topic-without-a-huge-prompt-dataset/
    /insights/how-should-an-ria-choose-which-public-documents-belong-in-an-answer-engine /for-advisors/insights/how-should-an-ria-choose-which-public-documents-belong-in-an-answer-engine/
    /insights/how-should-an-ria-choose-which-public-documents-belong-in-an-answer-engine/ /for-advisors/insights/how-should-an-ria-choose-which-public-documents-belong-in-an-answer-engine/
    /insights/how-should-an-ria-explain-fees-before-a-first-call /for-advisors/insights/how-should-an-ria-explain-fees-before-a-first-call/
    /insights/how-should-an-ria-explain-fees-before-a-first-call/ /for-advisors/insights/how-should-an-ria-explain-fees-before-a-first-call/
    /insights/how-should-an-ria-turn-a-client-service-model-into-a-written-service-calendar /for-advisors/insights/how-should-an-ria-turn-a-client-service-model-into-a-written-service-calendar/
    /insights/how-should-an-ria-turn-a-client-service-model-into-a-written-service-calendar/ /for-advisors/insights/how-should-an-ria-turn-a-client-service-model-into-a-written-service-calendar/
    /insights/how-should-an-ria-turn-a-linkedin-explanation-into-a-source-backed-answer-on-its-website /for-advisors/insights/how-should-an-ria-turn-a-linkedin-explanation-into-a-source-backed-answer-on-its-website/
    /insights/how-should-an-ria-turn-a-linkedin-explanation-into-a-source-backed-answer-on-its-website/ /for-advisors/insights/how-should-an-ria-turn-a-linkedin-explanation-into-a-source-backed-answer-on-its-website/
    /insights/how-should-an-ria-turn-recurring-prospect-questions-into-an-ai-search-answer-backlog /for-advisors/insights/how-should-an-ria-turn-recurring-prospect-questions-into-an-ai-search-answer-backlog/
    /insights/how-should-an-ria-turn-recurring-prospect-questions-into-an-ai-search-answer-backlog/ /for-advisors/insights/how-should-an-ria-turn-recurring-prospect-questions-into-an-ai-search-answer-backlog/
    /insights/how-should-an-ria-write-a-value-proposition-a-prospect-can-test /for-advisors/insights/how-should-an-ria-write-a-value-proposition-a-prospect-can-test/
    /insights/how-should-an-ria-write-a-value-proposition-a-prospect-can-test/ /for-advisors/insights/how-should-an-ria-write-a-value-proposition-a-prospect-can-test/
    /insights/how-to-evaluate-an-advisor-marketing-firm /for-advisors/insights/how-to-evaluate-an-advisor-marketing-firm/
    /insights/how-to-evaluate-an-advisor-marketing-firm/ /for-advisors/insights/how-to-evaluate-an-advisor-marketing-firm/
    /insights/how-to-find-high-intent-leads-before-your-competitors /for-advisors/insights/how-to-find-high-intent-leads-before-your-competitors/
    /insights/how-to-find-high-intent-leads-before-your-competitors/ /for-advisors/insights/how-to-find-high-intent-leads-before-your-competitors/
    /insights/how-to-generate-more-linkedin-leads-using-your-existing-network /for-advisors/insights/how-to-generate-more-linkedin-leads-using-your-existing-network/
    /insights/how-to-generate-more-linkedin-leads-using-your-existing-network/ /for-advisors/insights/how-to-generate-more-linkedin-leads-using-your-existing-network/
    /insights/how-to-get-your-firm-recommended-by-chatgpt-and-perplexity /for-advisors/insights/how-to-get-your-firm-recommended-by-chatgpt-and-perplexity/
    /insights/how-to-get-your-firm-recommended-by-chatgpt-and-perplexity/ /for-advisors/insights/how-to-get-your-firm-recommended-by-chatgpt-and-perplexity/
    /insights/how-to-warm-up-linkedin-prospects-before-your-first-message /for-advisors/insights/how-to-warm-up-linkedin-prospects-before-your-first-message/
    /insights/how-to-warm-up-linkedin-prospects-before-your-first-message/ /for-advisors/insights/how-to-warm-up-linkedin-prospects-before-your-first-message/
    /insights/lead-generation-strategies-for-financial-advisors /for-advisors/insights/lead-generation-strategies-for-financial-advisors/
    /insights/lead-generation-strategies-for-financial-advisors/ /for-advisors/insights/lead-generation-strategies-for-financial-advisors/
    /insights/should-an-ria-gate-an-educational-checklist-or-leave-it-public /for-advisors/insights/should-an-ria-gate-an-educational-checklist-or-leave-it-public/
    /insights/should-an-ria-gate-an-educational-checklist-or-leave-it-public/ /for-advisors/insights/should-an-ria-gate-an-educational-checklist-or-leave-it-public/
    /insights/smartasset-alternatives /for-advisors/insights/smartasset-alternatives/
    /insights/smartasset-alternatives/ /for-advisors/insights/smartasset-alternatives/
    /insights/viral-coach-alternatives /for-advisors/insights/viral-coach-alternatives/
    /insights/viral-coach-alternatives/ /for-advisors/insights/viral-coach-alternatives/
    /insights/what-counts-as-a-qualified-inbound-inquiry-for-a-small-ria /for-advisors/insights/what-counts-as-a-qualified-inbound-inquiry-for-a-small-ria/
    /insights/what-counts-as-a-qualified-inbound-inquiry-for-a-small-ria/ /for-advisors/insights/what-counts-as-a-qualified-inbound-inquiry-for-a-small-ria/
    /insights/what-should-a-financial-advisor-put-on-an-about-page /for-advisors/insights/what-should-a-financial-advisor-put-on-an-about-page/
    /insights/what-should-a-financial-advisor-put-on-an-about-page/ /for-advisors/insights/what-should-a-financial-advisor-put-on-an-about-page/
    /insights/what-should-a-solo-ria-automate-first /for-advisors/insights/what-should-a-solo-ria-automate-first/
    /insights/what-should-a-solo-ria-automate-first/ /for-advisors/insights/what-should-a-solo-ria-automate-first/
    /insights/what-should-a-solo-ria-include-in-a-business-continuity-handoff /for-advisors/insights/what-should-a-solo-ria-include-in-a-business-continuity-handoff/
    /insights/what-should-a-solo-ria-include-in-a-business-continuity-handoff/ /for-advisors/insights/what-should-a-solo-ria-include-in-a-business-continuity-handoff/
    /insights/what-should-a-solo-ria-publish-each-week-to-build-trust /for-advisors/insights/what-should-a-solo-ria-publish-each-week-to-build-trust/
    /insights/what-should-a-solo-ria-publish-each-week-to-build-trust/ /for-advisors/insights/what-should-a-solo-ria-publish-each-week-to-build-trust/
    /insights/what-should-an-advisory-firm-carry-over-when-moving-its-newsletter-to-a-new-sending-platform /for-advisors/insights/what-should-an-advisory-firm-carry-over-when-moving-its-newsletter-to-a-new-sending-platform/
    /insights/what-should-an-advisory-firm-carry-over-when-moving-its-newsletter-to-a-new-sending-platform/ /for-advisors/insights/what-should-an-advisory-firm-carry-over-when-moving-its-newsletter-to-a-new-sending-platform/
    /insights/what-should-an-advisory-firm-check-before-publishing-a-transcript-of-an-educational-video /for-advisors/insights/what-should-an-advisory-firm-check-before-publishing-a-transcript-of-an-educational-video/
    /insights/what-should-an-advisory-firm-check-before-publishing-a-transcript-of-an-educational-video/ /for-advisors/insights/what-should-an-advisory-firm-check-before-publishing-a-transcript-of-an-educational-video/
    /insights/what-should-an-advisory-firm-check-before-turning-a-full-planning-explanation-into-a-one-page-client-summary /for-advisors/insights/what-should-an-advisory-firm-check-before-turning-a-full-planning-explanation-into-a-one-page-client-summary/
    /insights/what-should-an-advisory-firm-check-before-turning-a-full-planning-explanation-into-a-one-page-client-summary/ /for-advisors/insights/what-should-an-advisory-firm-check-before-turning-a-full-planning-explanation-into-a-one-page-client-summary/
    /insights/what-should-an-advisory-firm-check-before-using-a-connected-account-dashboard /for-advisors/insights/what-should-an-advisory-firm-check-before-using-a-connected-account-dashboard/
    /insights/what-should-an-advisory-firm-check-before-using-a-connected-account-dashboard/ /for-advisors/insights/what-should-an-advisory-firm-check-before-using-a-connected-account-dashboard/
    /insights/what-should-an-advisory-firm-check-for-keyboard-navigation-on-its-website /for-advisors/insights/what-should-an-advisory-firm-check-for-keyboard-navigation-on-its-website/
    /insights/what-should-an-advisory-firm-check-for-keyboard-navigation-on-its-website/ /for-advisors/insights/what-should-an-advisory-firm-check-for-keyboard-navigation-on-its-website/
    /insights/what-should-an-advisory-firm-check-when-the-same-guide-exists-as-a-webpage-and-a-pdf /for-advisors/insights/what-should-an-advisory-firm-check-when-the-same-guide-exists-as-a-webpage-and-a-pdf/
    /insights/what-should-an-advisory-firm-check-when-the-same-guide-exists-as-a-webpage-and-a-pdf/ /for-advisors/insights/what-should-an-advisory-firm-check-when-the-same-guide-exists-as-a-webpage-and-a-pdf/
    /insights/what-should-an-advisory-firm-preserve-before-transferring-a-clients-cost-basis-records /for-advisors/insights/what-should-an-advisory-firm-preserve-before-transferring-a-clients-cost-basis-records/
    /insights/what-should-an-advisory-firm-preserve-before-transferring-a-clients-cost-basis-records/ /for-advisors/insights/what-should-an-advisory-firm-preserve-before-transferring-a-clients-cost-basis-records/
    /insights/what-should-an-advisory-firm-record-when-a-subscriber-replies-to-a-newsletter /for-advisors/insights/what-should-an-advisory-firm-record-when-a-subscriber-replies-to-a-newsletter/
    /insights/what-should-an-advisory-firm-record-when-a-subscriber-replies-to-a-newsletter/ /for-advisors/insights/what-should-an-advisory-firm-record-when-a-subscriber-replies-to-a-newsletter/
    /insights/what-should-an-advisory-firm-test-in-a-crm-export-before-switching-tools /for-advisors/insights/what-should-an-advisory-firm-test-in-a-crm-export-before-switching-tools/
    /insights/what-should-an-advisory-firm-test-in-a-crm-export-before-switching-tools/ /for-advisors/insights/what-should-an-advisory-firm-test-in-a-crm-export-before-switching-tools/
    /insights/what-should-an-advisory-firm-test-in-a-newsletters-unsubscribe-path-before-sending /for-advisors/insights/what-should-an-advisory-firm-test-in-a-newsletters-unsubscribe-path-before-sending/
    /insights/what-should-an-advisory-firm-test-in-a-newsletters-unsubscribe-path-before-sending/ /for-advisors/insights/what-should-an-advisory-firm-test-in-a-newsletters-unsubscribe-path-before-sending/
    /insights/what-should-an-ria-check-before-using-a-client-testimonial /for-advisors/insights/what-should-an-ria-check-before-using-a-client-testimonial/
    /insights/what-should-an-ria-check-before-using-a-client-testimonial/ /for-advisors/insights/what-should-an-ria-check-before-using-a-client-testimonial/
    /insights/what-should-an-ria-record-when-a-client-complaint-reaches-the-wrong-person /for-advisors/insights/what-should-an-ria-record-when-a-client-complaint-reaches-the-wrong-person/
    /insights/what-should-an-ria-record-when-a-client-complaint-reaches-the-wrong-person/ /for-advisors/insights/what-should-an-ria-record-when-a-client-complaint-reaches-the-wrong-person/
    /insights/what-should-an-ria-request-before-a-first-prospect-call /for-advisors/insights/what-should-an-ria-request-before-a-first-prospect-call/
    /insights/what-should-an-ria-request-before-a-first-prospect-call/ /for-advisors/insights/what-should-an-ria-request-before-a-first-prospect-call/
    /insights/what-should-an-ria-verify-before-putting-localbusiness-markup-on-its-website /for-advisors/insights/what-should-an-ria-verify-before-putting-localbusiness-markup-on-its-website/
    /insights/what-should-an-ria-verify-before-putting-localbusiness-markup-on-its-website/ /for-advisors/insights/what-should-an-ria-verify-before-putting-localbusiness-markup-on-its-website/
    /insights/when-does-an-ria-need-a-service-page-instead-of-another-blog-post /for-advisors/insights/when-does-an-ria-need-a-service-page-instead-of-another-blog-post/
    /insights/when-does-an-ria-need-a-service-page-instead-of-another-blog-post/ /for-advisors/insights/when-does-an-ria-need-a-service-page-instead-of-another-blog-post/
    /insights/when-should-an-ria-update-merge-or-retire-an-old-article /for-advisors/insights/when-should-an-ria-update-merge-or-retire-an-old-article/
    /insights/when-should-an-ria-update-merge-or-retire-an-old-article/ /for-advisors/insights/when-should-an-ria-update-merge-or-retire-an-old-article/
    /insights/when-should-an-ria-use-a-niche-landing-page-instead-of-a-location-page /for-advisors/insights/when-should-an-ria-use-a-niche-landing-page-instead-of-a-location-page/
    /insights/when-should-an-ria-use-a-niche-landing-page-instead-of-a-location-page/ /for-advisors/insights/when-should-an-ria-use-a-niche-landing-page-instead-of-a-location-page/
    /insights/which-ai-crawlers-should-an-ria-allow-for-search-and-which-controls-cover-model-training /for-advisors/insights/which-ai-crawlers-should-an-ria-allow-for-search-and-which-controls-cover-model-training/
    /insights/which-ai-crawlers-should-an-ria-allow-for-search-and-which-controls-cover-model-training/ /for-advisors/insights/which-ai-crawlers-should-an-ria-allow-for-search-and-which-controls-cover-model-training/
    /insights/your-first-ten-clients-as-a-solo-ria-where-they-actually-come-from /for-advisors/insights/your-first-ten-clients-as-a-solo-ria-where-they-actually-come-from/
    /insights/your-first-ten-clients-as-a-solo-ria-where-they-actually-come-from/ /for-advisors/insights/your-first-ten-clients-as-a-solo-ria-where-they-actually-come-from/
    /insights/advisor-resources /for-advisors/insights/
    /insights/advisor-resources/ /for-advisors/insights/
    /insights/can-chatgpt-find-your-firm /for-advisors/can-chatgpt-find-your-firm/
    /insights/can-chatgpt-find-your-firm/ /for-advisors/can-chatgpt-find-your-firm/
}
```

```nginx
server {
    if ($insights_redirect != "") {
        return 301 https://www.valorahq.com$insights_redirect$is_args$args;
    }

    # Exact matches beat any later prefix. These are the static files from this repo.
    location = /insights/ { try_files /insights/index.html =404; }
    location = /insights/beneficiary-forms-override-will/ { try_files /insights/beneficiary-forms-override-will/index.html =404; }
    location = /insights/family-conversation-before-retirement/ { try_files /insights/family-conversation-before-retirement/index.html =404; }
    location = /insights/market-drop-before-retirement/ { try_files /insights/market-drop-before-retirement/index.html =404; }
    location = /insights/realistic-withdrawal-rate-today/ { try_files /insights/realistic-withdrawal-rate-today/index.html =404; }
    location = /insights/rsus-bonus-not-lottery-ticket/ { try_files /insights/rsus-bonus-not-lottery-ticket/index.html =404; }
    location = /insights/when-roth-conversion-worth-tax-bill/ { try_files /insights/when-roth-conversion-worth-tax-bill/index.html =404; }

    # Longer prefix than /for-advisors/. Does not match /insights/.
    location /for-advisors/insights/ {
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass http://127.0.0.1:2368;
        proxy_redirect off;
    }

    # Outside the Ghost subdirectory. See the open question below.
    location = /for-advisors/can-chatgpt-find-your-firm/ {
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://127.0.0.1:2368/for-advisors/insights/can-chatgpt-find-your-firm/;
    }
    location = /for-advisors/can-chatgpt-find-your-firm {
        return 301 https://www.valorahq.com/for-advisors/can-chatgpt-find-your-firm/$is_args$args;
    }
}
```

Location order that matters:

1. Server-level `return 301` for exact map keys, before any location is chosen.
2. `location =` for `/insights/` and the six articles. These win over a prefix.
3. `location /for-advisors/insights/` proxies to Ghost. It does not match `/insights/` or `/for-advisors/`.
4. `location = /for-advisors/can-chatgpt-find-your-firm/` is outside that prefix.

### 4. Traefik

Same precedence, higher number wins. Do not add a PathPrefix router for `/insights` that points at Ghost.

- Priority 100: exact Path match for `/insights/` and for each of the six household slugs, served by the static file service.
- Priority 90: PathPrefix `/for-advisors/insights/` to the Ghost service, with the path left intact (X-Forwarded-Proto, X-Forwarded-For, Host).
- Priority 100: exact Path `/for-advisors/can-chatgpt-find-your-firm/` to Ghost with a replacePath middleware of `/for-advisors/insights/can-chatgpt-find-your-firm/`. ReplacePath keeps the query string.
- Redirect router, priority 110, only for the old advisor paths (not the six, not `/insights/`):

```yaml
http:
  middlewares:
    advisor-insights-redirect:
      redirectRegex:
        permanent: true
        regex: "^https://www\\.valorahq\\.com/insights/(?P<slug>SLUG)/?(\\?.*)?$"
        replacement: "https://www.valorahq.com/for-advisors/insights/${slug}/${2}"
```

`SLUG` is the alternation of the 53 post slugs in the map above. `advisor-resources` needs its own middleware to `/for-advisors/insights/`. `can-chatgpt-find-your-firm` needs its own middleware to `/for-advisors/can-chatgpt-find-your-firm/`. The router rule is `Path()` for each old path with and without the trailing slash, not a prefix.

### 5. Ghost routes and redirects

Preferred, test on 5.130 before production. Routes are matched before collections, so `/` can be the page while posts stay at `/{slug}/` under the new `url`:

```yaml
routes:
  /:
    data: page.advisor-resources
    template: page

collections:
  /:
    permalink: /{slug}/
    template: index

taxonomies:
  tag: /tag/{slug}/
  author: /author/{slug}/
```

Ghost redirects (relative to the Ghost `url`, so this is `/for-advisors/insights/advisor-resources/` to the index):

```json
[
  {"from": "/advisor-resources/", "to": "/", "permanent": true},
  {"from": "/advisor-resources", "to": "/", "permanent": true}
]
```

Do not put the old `/insights/<slug>/` URLs in Ghost redirects. After the `url` change, Ghost never receives those requests. nginx or Traefik owns them.

If 5.130 will not render `page.advisor-resources` at `/` while the collection permalink is `/{slug}/`, use this exact location instead of the routes change. It is more specific than the prefix proxy:

```nginx
location = /for-advisors/insights/ {
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass http://127.0.0.1:2368/for-advisors/insights/advisor-resources/;
}
location = /for-advisors/insights {
    return 301 https://www.valorahq.com/for-advisors/insights/$is_args$args;
}
```

### 6. Sixteen duplicate redirects — do not enable yet

Every canonical target is missing from this repo. A 301 today would land on a 404. The rules, once those `index.html` files exist:

```nginx
# Leave this map unused until every target index.html exists.
map $uri $insights_duplicate_redirect {
    default "";
    /insights/401k-rollover /find-a-financial-advisor/401k-rollover/
    /insights/401k-rollover/ /find-a-financial-advisor/401k-rollover/
    /insights/budgeting-cash-flow /find-a-financial-advisor/budgeting-cash-flow/
    /insights/budgeting-cash-flow/ /find-a-financial-advisor/budgeting-cash-flow/
    /insights/charitable-giving /find-a-financial-advisor/charitable-giving/
    /insights/charitable-giving/ /find-a-financial-advisor/charitable-giving/
    /insights/equity-compensation /find-a-financial-advisor/equity-compensation/
    /insights/equity-compensation/ /find-a-financial-advisor/equity-compensation/
    /insights/job-loss /find-a-financial-advisor/job-loss/
    /insights/job-loss/ /find-a-financial-advisor/job-loss/
    /insights/long-term-care /find-a-financial-advisor/long-term-care/
    /insights/long-term-care/ /find-a-financial-advisor/long-term-care/
    /insights/marriage /find-a-financial-advisor/marriage/
    /insights/marriage/ /find-a-financial-advisor/marriage/
    /insights/new-baby /find-a-financial-advisor/new-baby/
    /insights/new-baby/ /find-a-financial-advisor/new-baby/
    /insights/pension-annuity /find-a-financial-advisor/pension-annuity/
    /insights/pension-annuity/ /find-a-financial-advisor/pension-annuity/
    /insights/relocating-states /find-a-financial-advisor/relocating-states/
    /insights/relocating-states/ /find-a-financial-advisor/relocating-states/
    /insights/roth-conversion /find-a-financial-advisor/roth-conversion/
    /insights/roth-conversion/ /find-a-financial-advisor/roth-conversion/
    /insights/self-employed-retirement-plans /find-a-financial-advisor/self-employed-retirement-plans/
    /insights/self-employed-retirement-plans/ /find-a-financial-advisor/self-employed-retirement-plans/
    /insights/what-records-should-i-find-if-an-inherited-traditional-ira-may-have-nondeductible-contributions /find-a-financial-advisor/what-records-should-i-find-if-an-inherited-traditional-ira-may-have-nondeductible-contributions/
    /insights/what-records-should-i-find-if-an-inherited-traditional-ira-may-have-nondeductible-contributions/ /find-a-financial-advisor/what-records-should-i-find-if-an-inherited-traditional-ira-may-have-nondeductible-contributions/
    /insights/what-should-a-nonspouse-beneficiary-check-before-moving-an-inherited-traditional-ira /find-a-financial-advisor/what-should-a-nonspouse-beneficiary-check-before-moving-an-inherited-traditional-ira/
    /insights/what-should-a-nonspouse-beneficiary-check-before-moving-an-inherited-traditional-ira/ /find-a-financial-advisor/what-should-a-nonspouse-beneficiary-check-before-moving-an-inherited-traditional-ira/
    /insights/what-should-i-record-when-i-revoke-an-automatic-bank-payment-authorization /find-a-financial-advisor/what-should-i-record-when-i-revoke-an-automatic-bank-payment-authorization/
    /insights/what-should-i-record-when-i-revoke-an-automatic-bank-payment-authorization/ /find-a-financial-advisor/what-should-i-record-when-i-revoke-an-automatic-bank-payment-authorization/
    /insights/year-end-tax /find-a-financial-advisor/year-end-tax/
    /insights/year-end-tax/ /find-a-financial-advisor/year-end-tax/
}
```

```nginx
# Do not add this return until the sixteen files exist.
# if ($insights_duplicate_redirect != "") {
#     return 301 https://www.valorahq.com$insights_duplicate_redirect$is_args$args;
# }
```

Missing targets:

- `find-a-financial-advisor/401k-rollover/index.html`
- `find-a-financial-advisor/budgeting-cash-flow/index.html`
- `find-a-financial-advisor/charitable-giving/index.html`
- `find-a-financial-advisor/equity-compensation/index.html`
- `find-a-financial-advisor/job-loss/index.html`
- `find-a-financial-advisor/long-term-care/index.html`
- `find-a-financial-advisor/marriage/index.html`
- `find-a-financial-advisor/new-baby/index.html`
- `find-a-financial-advisor/pension-annuity/index.html`
- `find-a-financial-advisor/relocating-states/index.html`
- `find-a-financial-advisor/roth-conversion/index.html`
- `find-a-financial-advisor/self-employed-retirement-plans/index.html`
- `find-a-financial-advisor/what-records-should-i-find-if-an-inherited-traditional-ira-may-have-nondeductible-contributions/index.html`
- `find-a-financial-advisor/what-should-a-nonspouse-beneficiary-check-before-moving-an-inherited-traditional-ira/index.html`
- `find-a-financial-advisor/what-should-i-record-when-i-revoke-an-automatic-bank-payment-authorization/index.html`
- `find-a-financial-advisor/year-end-tax/index.html`

## Curl checklist

Today, before the server edit, `/for-advisors/insights/` is a 404. After the edit:

```bash
# Advisor post. Expect 301 to the new URL.
curl -sI https://www.valorahq.com/insights/smartasset-alternatives/

# Query string kept.
curl -sI "https://www.valorahq.com/insights/geo-vs-seo-advisory-firm-website/?q=1"

# Newsletter and transcript posts, called out in the inventory.
curl -sI https://www.valorahq.com/insights/what-should-an-advisory-firm-test-in-a-newsletters-unsubscribe-path-before-sending/
curl -sI https://www.valorahq.com/insights/what-should-an-advisory-firm-check-before-publishing-a-transcript-of-an-educational-video/

# Index page, not the old slug.
curl -sI https://www.valorahq.com/insights/advisor-resources/

# ChatGPT page leaves the Ghost subdirectory.
curl -sI https://www.valorahq.com/insights/can-chatgpt-find-your-firm/

# Household index and six articles stay 200 from this repo. Not redirects.
curl -sI https://www.valorahq.com/insights/
curl -sI https://www.valorahq.com/insights/beneficiary-forms-override-will/
curl -sI https://www.valorahq.com/insights/family-conversation-before-retirement/
curl -sI https://www.valorahq.com/insights/market-drop-before-retirement/
curl -sI https://www.valorahq.com/insights/realistic-withdrawal-rate-today/
curl -sI https://www.valorahq.com/insights/rsus-bonus-not-lottery-ticket/
curl -sI https://www.valorahq.com/insights/when-roth-conversion-worth-tax-bill/

# Ghost after the move. 404 until then.
curl -sI https://www.valorahq.com/for-advisors/insights/
curl -sI https://www.valorahq.com/for-advisors/insights/smartasset-alternatives/
curl -sI https://www.valorahq.com/for-advisors/can-chatgpt-find-your-firm/
```

Expected `Location` headers:

- `/insights/smartasset-alternatives/` → `https://www.valorahq.com/for-advisors/insights/smartasset-alternatives/`
- the geo URL with `?q=1` → `https://www.valorahq.com/for-advisors/insights/geo-vs-seo-advisory-firm-website/?q=1`
- both long posts → the same slug under `/for-advisors/insights/`
- `/insights/advisor-resources/` → `https://www.valorahq.com/for-advisors/insights/`
- `/insights/can-chatgpt-find-your-firm/` → `https://www.valorahq.com/for-advisors/can-chatgpt-find-your-firm/`

Do not curl-enable `/insights/401k-rollover/` as a 301 until `find-a-financial-advisor/401k-rollover/index.html` exists. Same for the other fifteen.

## Open questions

- `can-chatgpt-find-your-firm` cannot live natively outside the Ghost `url`. The proxy above shows the post at `/for-advisors/can-chatgpt-find-your-firm/`, and Ghost will still emit a canonical under `/for-advisors/insights/can-chatgpt-find-your-firm/`. If Ghost also 301s to that canonical, the public URL bounces back. Needs a theme-level canonical override, or a decision to keep the post inside the Ghost subdirectory.
- Whether `page.advisor-resources` can own `/` on Ghost 5.130 without moving posts under a second prefix. The nginx exact-location fallback is the alternative, with the same canonical caveat.
- Ghost will publish its own sitemap under the new `url`. `/sitemap.xml` in this repo also lists those URLs, without lastmod. Worth deciding whether both should be submitted.
- The sixteen `/find-a-financial-advisor/` targets are not in the repo. No stub pages were added.
