# Valora CMS

Staff-only content system for Valora, served at `valorahq.com/cms`. It runs the daily content
engine (3 advisor articles + 3 consumer pages) and is API-first: the editor is a client of the
same admin API and MCP server that agents use.

## What it does

| Area | Behaviour |
|---|---|
| Roles | **Writer** creates and edits drafts. **QA** is the only role that can approve; approving publishes (or schedules). **Admin** manages people, tokens, routes and redirects. |
| Workflow | `draft → in-review → approved → published`, or `→ scheduled → published`. Editing an approved or published article returns it to draft for a fresh QA pass; the live copy stays up meanwhile. |
| Article | title, slug, Markdown body, author persona, type (`advisor-article` \| `consumer-page`), status, meta title/description, canonical, OG image, answer-first summary, FAQ blocks (rendered with FAQPage JSON-LD), key takeaways, extra structured data. |
| Illustration | Required before approval. PNG/JPEG/WebP up to 3 MB, with alt text. |
| Links | Outbound links get UTM parameters at render time (`utm_source`, `utm_medium`, `utm_campaign=<slug>`). Links to valorahq.com and spacesos.com are left alone. |
| Publishing | Consumer pages are committed as `_build/content-packs/<slug>.json` and rendered by the existing build at `valorahq.com/<route>/<slug>/`. Advisor articles are committed as `_build/insights-articles/<slug>.json` and rendered by `_build/insights_site.py` into `/_insights-site/` for `insights.spacesos.com`. The build regenerates sitemaps, robots.txt, llms.txt and the RSS feed. |
| Deploy | A publish is one commit to the repository; the existing GitHub → Dokploy flow deploys it. If `CMS_DEPLOY_HOOK_URL` is set the CMS also calls it. |
| Preview | Every draft has a staging URL rendered with the real page templates. A signed link (7 days) opens without signing in. |
| Calendar | `Today` shows the six slots and status. **Done = QA-passed and published**; `GET /stats/daily` exposes the count. |
| Redirects | Managed by admins. Each becomes a forwarding page at the old address, and `_build/generated/redirects.nginx.conf` holds matching 301 rules for nginx. |
| Audit | Every action is logged with actor, time and channel (`ui`, `api`, `mcp`, `system`). |
| AI | Draft from a topic, edit by instruction (each change is accepted or skipped by a person), topic ideas, and a compliance check. All of it reads **brand memory**, which is kept in the database, not in the public repo. |
| Site pages | The existing hand-built pages (advisor landing page, original guides, team, legal) can be edited as structured content. Saving publishes, so only QA and admins can save. |

Phase 2 hooks exist in the data model only (no UI): `advisors`, `voice_profiles`,
`advisor_approvals`, and on each article `advisor_id`, `voice_profile_id`,
`compliance_checklist`, `advisor_approval`, `syndication`.

Not in v1: advisor-facing UI, comments, Ghost migration.

## Run it locally

```bash
export CMS_SESSION_SECRET="$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")"
export CMS_BOOTSTRAP_ADMIN_EMAIL="you@example.com"
export CMS_BOOTSTRAP_ADMIN_PASSWORD="<12+ characters>"
CMS_AI_MOCK=1 node cms/server.js      # http://localhost:8000/cms/
```

Local mode writes published files into this working tree and reruns `python3 _build/build.py`;
nothing is sent to GitHub. `CMS_AI_MOCK=1` returns canned AI answers so no API key is needed.
Requires Node 22.13+ (built-in SQLite) and Python 3.

## Deploy on Dokploy

1. New application from this repository, Dockerfile path `cms/Dockerfile`, build context `/`.
2. Mount a persistent volume at `/data` (the SQLite database: accounts, drafts, audit log).
3. On the `valorahq.com` domain, route the path prefixes `/cms` and `/api/cms` to this service (port 8000). Do not strip the prefix.
4. Set the environment variables below.
5. For the blog: add a static application for `insights.spacesos.com` that runs the same build (`python3 _build/build.py`) and serves the `_insights-site` folder. Do this only when you are ready to replace Ghost; existing Ghost posts are not migrated.

| Variable | Purpose |
|---|---|
| `CMS_SESSION_SECRET` | 32+ random characters. Signs sessions and preview links. |
| `CMS_BOOTSTRAP_ADMIN_EMAIL`, `CMS_BOOTSTRAP_ADMIN_PASSWORD`, `CMS_BOOTSTRAP_ADMIN_NAME` | Creates the first admin on first start only. Remove afterwards. |
| `CMS_STORAGE` | `github` in production (set by the Dockerfile). |
| `CMS_GITHUB_TOKEN` | Fine-grained token with **Contents: read and write** on the site repository only. If `main` is protected, allow this token to push. |
| `CMS_GITHUB_REPO`, `CMS_GITHUB_BRANCH` | Default `spacesOS-com/Valorahq`, `main`. |
| `CMS_DEPLOY_HOOK_URL` | Optional Dokploy deploy webhook, called after each publish. |
| `ANTHROPIC_API_KEY` | Enables the AI features. Without it everything else still works. |
| `CMS_AI_MODEL` | Default `claude-sonnet-5-5`. |
| `CMS_TIMEZONE` | Day boundary for the calendar and daily count. Default `America/New_York`. |
| `CMS_SITE_URL`, `CMS_INSIGHTS_URL` | Default `https://www.valorahq.com`, `https://insights.spacesos.com`. |

## Admin API

Base `/api/cms/v1`. People use the session cookie; agents send `Authorization: Bearer vcms_…`
(a token created by an admin for a specific person, with that person's role).

| Method and path | Role | What it does |
|---|---|---|
| `POST /login`, `POST /logout`, `GET /me` | any | Session |
| `GET /articles?status=&type=&date=&q=` | any | List |
| `POST /articles` | any | Create a draft (`type`, `title`, any article field) |
| `GET /articles/:id` | any | Full article, outstanding problems, preview URL |
| `PATCH /articles/:id` | any | Edit fields |
| `DELETE /articles/:id` | owner / QA / admin | Delete an unpublished article |
| `PUT /articles/:id/illustration` | any | `{ content_type, data_base64, alt }` |
| `POST /articles/:id/submit` | any | Draft → in review |
| `POST /articles/:id/request-changes` | QA | In review → draft, with `{ note }` |
| `POST /articles/:id/approve` | QA | Approve and publish, or schedule with `{ publish_at }` |
| `POST /articles/:id/publish` | QA / admin | Retry a publish that failed |
| `POST /articles/:id/unpublish` | admin | Remove from the site |
| `GET /articles/:id/preview-url`, `GET /preview/:id` | any | Staging preview |
| `GET /calendar?date=`, `GET /stats/daily?date=` | any | Six slots; done count |
| `POST /ai/draft`, `/ai/edit`, `/ai/check`, `/ai/ideas` | any | AI helpers |
| `GET /site-pages`, `GET/PUT /site-pages/:kind/:id` | read: any, write: QA / admin | Existing site pages |
| `GET /brand-memory`, `PUT /brand-memory` | read: any, write: admin | What the AI knows |
| `GET/POST /users`, `PATCH /users/:id`, `POST /users/:id/tokens`, `GET /tokens`, `DELETE /tokens/:id` | admin | People and agent tokens |
| `GET /routes`, `PATCH /routes/:key` | read: any, write: admin | Where each kind of page is published |
| `GET /redirects`, `POST /redirects`, `DELETE /redirects/:id` | read: any, write: admin | Redirects |
| `GET /audit?target_id=&limit=` | QA / admin | Audit log |
| `GET/POST /advisors` | admin | Phase 2 hook |

## MCP

Streamable HTTP at `/api/cms/mcp`, same Bearer token, same permissions. Tools:
`list_articles`, `get_article`, `create_article`, `update_article`, `set_illustration`,
`submit_for_review`, `request_changes`, `approve_article`, `unpublish_article`,
`delete_article`, `get_preview_url`, `get_calendar`, `get_daily_count`, `list_redirects`,
`add_redirect`, `get_audit_log`.

```json
{ "mcpServers": { "valora-cms": { "type": "http", "url": "https://www.valorahq.com/api/cms/mcp",
    "headers": { "Authorization": "Bearer ${VALORA_CMS_TOKEN}" } } } }
```
