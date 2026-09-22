#!/usr/bin/env python3
"""A browser worker that discovers jobs from careers sites, not undocumented ATS APIs.

Run it in Docker with Playwright/Chromium installed. It keeps the browser capability
separate from the public dashboard and writes normalized, reviewable job records.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).parent
DATA = ROOT / "data"
CONFIG = json.loads((ROOT / "companies.json").read_text())
KEYWORDS = [word.strip().lower() for word in os.getenv("SCOUT_KEYWORDS", "product,ai,developer,platform,ml").split(",")]


def score(title: str, description: str) -> int:
    text = f"{title} {description}".lower()
    return min(99, 55 + 9 * sum(keyword in text for keyword in KEYWORDS))


def text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


async def extract_company(page: Page, company: dict) -> list[dict]:
    await page.goto(company["careers_url"], wait_until="domcontentloaded", timeout=60_000)
    # Generic discovery intentionally confines navigation to links named like job openings.
    links = await page.locator("a").evaluate_all("""links => links.map(a => ({
        title: (a.innerText || '').trim(), url: a.href
      })).filter(x => x.title && x.url && /job|career|position|opening|role/i.test(x.title + x.url))""")
    unique = {link["url"]: link for link in links if link["url"].startswith("http")}
    jobs = []
    for link in list(unique.values())[:100]:
        detail = await page.context.new_page()
        try:
            await detail.goto(link["url"], wait_until="domcontentloaded", timeout=45_000)
            body = text((await detail.locator("body").inner_text())[:20_000])
            title = text((await detail.locator("h1").first.inner_text()) if await detail.locator("h1").count() else link["title"])
            if len(body) < 200 or len(title) < 3:
                continue
            identifier = hashlib.sha256(f"{company['name']}:{link['url']}".encode()).hexdigest()[:16]
            jobs.append({"id": identifier, "company": company["name"], "title": title,
                         "location": "See source page", "url": link["url"], "description": body,
                         "match_score": score(title, body), "scanned_at": datetime.now(UTC).isoformat()})
        finally:
            await detail.close()
    return jobs


async def scan() -> None:
    DATA.mkdir(exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        jobs = []
        for company in CONFIG:
            try:
                jobs.extend(await extract_company(page, company))
            except Exception as error:  # keep other companies scanning if one site changes
                print(f"{company['name']} scan failed: {error}")
        await browser.close()
    (DATA / "jobs.json").write_text(json.dumps(sorted(jobs, key=lambda job: job["match_score"], reverse=True), indent=2))
    (DATA / "scan.request").unlink(missing_ok=True)


async def worker() -> None:
    interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "21600"))
    while True:
        if not (DATA / "jobs.json").exists() or (DATA / "scan.request").exists():
            await scan()
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(worker())
