#!/usr/bin/env python3
"""Generate a human-reviewable HTML resume and render it to a finished PDF."""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from openai import OpenAI
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
DATA = ROOT / "data"
REQUESTS = DATA / "application_requests.json"
JOBS = DATA / "jobs.json"
PROFILE = ROOT / "candidate_profile.md"
ARTIFACTS = DATA / "artifacts"


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", value)


def take_requests() -> list[dict]:
    if not REQUESTS.exists():
        return []
    requests = json.loads(REQUESTS.read_text())
    REQUESTS.write_text("[]")
    return requests


def generate_html(job: dict) -> str:
    client = OpenAI()
    prompt = f"""Create a truthful, tailored one-page resume for this job and candidate.
Return ONLY a complete standalone HTML document. Do not use Markdown or LaTex. Include
embedded CSS. Do not invent employers, metrics, degrees, or skills. This will be rendered
to PDF without review, so use semantic text and a printable A4 layout.

JOB TITLE: {job['title']}
COMPANY: {job['company']}
JOB DESCRIPTION: {job['description']}

CANDIDATE PROFILE:
{PROFILE.read_text()}
"""
    response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5.4"), input=prompt)
    html = response.output_text.strip()
    if not html.lower().startswith("<!doctype html"):
        raise ValueError("Model did not return a complete HTML document")
    return html


async def render_pdf(html: str, destination: Path) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="load")
        await page.pdf(path=str(destination), format="A4", print_background=True,
                       margin={"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"})
        await browser.close()


async def process() -> None:
    DATA.mkdir(exist_ok=True); ARTIFACTS.mkdir(exist_ok=True)
    jobs = {job["id"]: job for job in json.loads(JOBS.read_text())} if JOBS.exists() else {}
    for request in take_requests():
        job = jobs.get(request.get("job_id"))
        if not job:
            continue
        job_id = safe_id(job["id"])
        html = generate_html(job)
        html_path = ARTIFACTS / f"{job_id}.html"
        pdf_path = ARTIFACTS / f"{job_id}.pdf"
        html_path.write_text(html)
        await render_pdf(html, pdf_path)
        print(f"Generated {pdf_path}")


async def worker() -> None:
    while True:
        await process()
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(worker())
