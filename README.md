# Scout

Scout is a deployable browser-agent sidecar. A Playwright/Chromium worker opens the configured careers pages, follows likely job links, extracts the rendered job description, scores it against a profile keyword set, and saves reviewable role records. A separate application worker sends an approved profile plus the selected job to the OpenAI API, receives a self-contained HTML resume, and uses Chromium to render a finished PDF.

## Run locally

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000` **while that command remains running**. A local web server stops when its terminal/process stops, which is why the earlier preview URL could not be reached after this coding session ended. The browser agent performs an initial scan and scans again every six hours. Select **Scan careers sites** to queue an earlier scan.

Before starting the application worker, copy the candidate's approved information into `candidate_profile.md` and set `OPENAI_API_KEY` in your shell. Set `OPENAI_MODEL` if you want to override the default model.

## Prototype interactions

- Configure careers-page targets in `companies.json`; the included records use the actual public careers homepages rather than ATS-specific APIs.
- Set `SCOUT_KEYWORDS="product,ai,developer,platform,ml"` before launching to change the simple deterministic scoring profile.
- Select **Scan careers sites** to queue a browser visit that pulls current rendered job descriptions, scores them, and saves the feed.
- Select a scanned role and use **Tailor application** → **Open application studio** to queue a tailored resume. The worker writes a finished PDF to `data/artifacts/<job-id>.pdf`; the dashboard returns its URL in the API response.

## Deployment path

The included `docker-compose.yml` is the development deployment: one public dashboard container and one private browser-worker container sharing a volume. It is the right shape for Railway, Render, Fly.io, Google Cloud Run Jobs + Cloud Run, or a small VPS. For production, replace the shared volume with Postgres/object storage and run the browser worker as a scheduled job or queue consumer. Do not expose the browser worker to the public internet.

For the LLM stage, this repository now uses HTML—not LaTex—as the model output contract. Chromium is the renderer, so there is no fragile LaTex installation or parser. The application worker stores the model's HTML alongside the PDF, which makes every output inspectable and reproducible. In production, send jobs to a durable queue, encrypt candidate profiles, save artifacts to private object storage, and require a human review/approval step before sharing or submitting anything. OpenAI provides the model API, not general-purpose hosting for this browser-worker stack, so host these containers on your cloud account.
