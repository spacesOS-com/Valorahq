Serving review matrix. Reference: sanitized Sam receipt 2026-10-01T03:06:47Z, not inferred from vercel.json. Every deviation below is PROPOSED, NOT APPROVED. Runtime assertions must run on the selected pinned image and staging domain.

| Route/behavior | Current reference | Candidate | Review/test |
| --- | --- | --- | --- |
| Static root | /usr/share/nginx/html/current, mounted release | /srv/consumer, image COPY | Intentional deployment mechanism change; 271 image bytes must match manifest |
| Listener | port 80 | 8080 | Proposed isolated managed service port; needs app agreement |
| index | index.html | index.html | Same directive; test / and /index.html bytes |
| Existing directories | try_files $uri $uri/ =404 | same | Test /team to /team/ slash redirect, /team/ and /team/index.html. Redirect Location port/host must match chosen proxy contract |
| Missing files and paths | =404 | same | Test unknown directory/file; no SPA fallback |
| JS/CSS | Cache-Control no-cache; try_files | same | Check successful/304 and missing responses, ETag/Last-Modified and conditional request behavior |
| gzip | on; types text/css application/javascript application/json image/svg+xml; min length 1024 | exact same directives | Compare Accept-Encoding gzip/identity and byte-decoded parity for eligible/ineligible/short assets |
| MIME | host top-level mime mapping not included in server receipt | pinned image /etc/nginx/mime.types | Unknown parity; operator must compare actual host include/config, JS/CSS/JSON/SVG/PNG/HTML/XML/TXT MIME headers |
| /_build/* | 404 (^~) | same | Must stay blocked |
| any /.git* path | 404 (regex) | blocked by broader dotfile regex | Existing behavior preserved; test nested and prefixed paths |
| /script.js | not redirected by supplied server config | new 301 /assets/script.js | Intentional exception, approval needed; not baseline parity |
| /styles.css | not redirected by supplied server config | new 301 /assets/styles.css | Intentional exception, approval needed; not baseline parity |
| /ops/* | normal static try_files | new 404 | Intentional access reduction, approval needed |
| other dot paths | normal static try_files except .git | new 404 | Intentional access reduction including /.gitignore; approval needed |
| /candidate-build.log and /candidate-build-sha256.json | normal static try_files | new 404 | Intentional metadata denial, approval needed |
| /vercel.json | normal static try_files | new 404 | Intentional config denial, approval needed |
| /admin/* and advisor-profile/* | normal static try_files | unchanged | Explicit audience/access policy review needed, no new broad deny implied |
| HTML/other cache defaults | no custom directive in server receipt | no custom directive | Need full global host settings and actual header/conditional tests |
| access/error logs | full global policy not in server excerpt | access off/error warn | Proposed policy, not proven parity; privacy review |
| www/apex HTTP->HTTPS, TLS, legacy redirects | external Traefik | no candidate routing changes | Preserve current complete Traefik config; not recreated/edited here |
| app.valorahq.com | separate app | untouched | No scope to change |
| guide finder / conversation | static assets unchanged | unchanged 271 bytes | Actual backend route probes/config/frozen-router receipts required; no enabling flags added |

Do not require all 271 files to return public 200. Manifest is image byte parity, while this matrix defines approved serving behavior. New denials and redirects remain held until approved. No image build, nginx runtime/HTTP, staging or physical-device test has run here.
