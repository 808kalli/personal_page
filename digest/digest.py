#!/usr/bin/env python3
"""Weekly reading digest.

Polls arXiv, Hugging Face daily papers, and a set of blog feeds, ranks what
comes back against digest/interests.md, and emails the survivors with a short
summary of each.

Run locally with --dry-run to see the ranking without sending anything.
"""

from __future__ import annotations

import argparse
import calendar
import email.utils
import html
import json
import os
import re
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
UA = "reading-digest/1.0 (+https://github.com/808kalli/personal_page)"
MODEL = "claude-opus-5"
REPO = os.environ.get("GITHUB_REPOSITORY", "808kalli/personal_page")

# Words that earn a candidate a place in the shortlist the model actually
# reads. Deliberately generous, the model does the real judging.
# Weighted so a genuine core match outranks a pile of near-miss application
# papers when the shortlist is cut. The model still does the real judging.
PREFILTER_TERMS = {
    5: ["mechanistic interpretab", "sparse autoencoder", "superposition",
        "attribution graph", "circuit trac", "activation steering",
        "monosemantic", "compounding error", "action chunk"],
    3: ["interpretab", "probing", "probe ", "world model", "emergent",
        "distribution shift", "behavior clon", "behaviour clon",
        "representation engineering", "linear probe", "steering vector"],
    1: ["circuit", "feature", "activation", "latent", "representation",
        "vision-language-action", "vla", "manipulation", "policy", "robot",
        "imitation", "demonstration", "offline rl", "offline reinforcement",
        "generalis", "generaliz", "scaling", "pre-train", "pretrain",
        "calibration", "reward", "teleoperation"],
}


# ──────────────────────────── candidates ────────────────────────────

@dataclass
class Item:
    uid: str
    title: str
    url: str
    source: str
    summary: str = ""
    authors: str = ""
    published: str = ""
    signal: str = ""          # community signal, e.g. HF upvotes
    score: int = 0            # model's interest score
    why: str = ""
    blurb: str = ""
    credibility: str = ""
    extras: dict = field(default_factory=dict)

    def prefilter_score(self) -> int:
        text = f"{self.title} {self.summary}".lower()
        return sum(weight for weight, terms in PREFILTER_TERMS.items()
                   for t in terms if t in text)


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


ARXIV_ID = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})")


def canonical(url: str) -> str:
    """One id per paper, whether it arrived from arXiv or Hugging Face."""
    match = ARXIV_ID.search(url)
    if match:
        return f"arxiv:{match.group(1)}"
    return url.rstrip("/")


def clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def arxiv_candidates(queries: list[str], since: datetime, per_query: int = 40) -> list[Item]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out: list[Item] = []
    for i, query in enumerate(queries):
        if i:
            time.sleep(3)  # arXiv asks for one request every three seconds
        params = urllib.parse.urlencode({
            "search_query": query,
            "start": 0,
            "max_results": per_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        try:
            raw = fetch(f"https://export.arxiv.org/api/query?{params}")
            root = ET.fromstring(raw)
        except Exception as exc:  # a bad query should not kill the run
            print(f"  arxiv query failed ({query[:40]}...): {exc}", file=sys.stderr)
            continue

        for entry in root.findall("a:entry", ns):
            published = clean(entry.findtext("a:published", default="", namespaces=ns))
            try:
                when = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                continue
            if when < since:
                continue
            link = clean(entry.findtext("a:id", default="", namespaces=ns))
            authors = [clean(a.findtext("a:name", default="", namespaces=ns))
                       for a in entry.findall("a:author", ns)]
            out.append(Item(
                uid=link,
                title=clean(entry.findtext("a:title", default="", namespaces=ns)),
                url=link,
                source="arXiv",
                summary=clean(entry.findtext("a:summary", default="", namespaces=ns))[:1500],
                authors=", ".join(authors[:8]) + (" et al." if len(authors) > 8 else ""),
                published=when.strftime("%Y-%m-%d"),
                signal="new preprint, no community signal yet",
            ))
    return out


def huggingface_candidates(since: datetime) -> list[Item]:
    out: list[Item] = []
    try:
        raw = fetch("https://huggingface.co/api/daily_papers?limit=100")
        payload = json.loads(raw)
    except Exception as exc:
        print(f"  huggingface daily papers failed: {exc}", file=sys.stderr)
        return out

    for row in payload:
        paper = row.get("paper") or {}
        pid = paper.get("id") or row.get("id")
        if not pid:
            continue
        published = row.get("publishedAt") or paper.get("publishedAt") or ""
        try:
            when = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            when = datetime.now(timezone.utc)
        if when < since:
            continue
        upvotes = paper.get("upvotes") or 0
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        out.append(Item(
            uid=f"https://arxiv.org/abs/{pid}",
            title=clean(paper.get("title") or row.get("title")),
            url=f"https://arxiv.org/abs/{pid}",
            source="HF daily papers",
            summary=clean(paper.get("summary"))[:1500],
            authors=", ".join(authors[:8]) + (" et al." if len(authors) > 8 else ""),
            published=when.strftime("%Y-%m-%d"),
            signal=f"{upvotes} upvotes on Hugging Face daily papers",
            extras={"upvotes": upvotes},
        ))
    return out


def feed_candidates(feeds: list[dict], since: datetime) -> list[Item]:
    """Parse both RSS 2.0 and Atom without pulling in a dependency."""
    out: list[Item] = []
    for feed in feeds:
        try:
            root = ET.fromstring(fetch(feed["url"]))
        except Exception as exc:
            print(f"  feed failed ({feed['name']}): {exc}", file=sys.stderr)
            continue

        atom = "{http://www.w3.org/2005/Atom}"
        entries = root.findall(f".//{atom}entry") or root.findall(".//item")
        for entry in entries:
            def pick(*names: str) -> str:
                for n in names:
                    node = entry.find(f"{atom}{n}")
                    if node is None:
                        node = entry.find(n)
                    if node is not None and (node.text or node.get("href")):
                        return node.text or node.get("href", "")
                return ""

            link = pick("link")
            if not link:
                node = entry.find(f"{atom}link")
                link = node.get("href", "") if node is not None else ""
            title = clean(pick("title"))
            if not link or not title:
                continue

            when = None
            for raw_date in (pick("published", "updated", "pubDate"),):
                if not raw_date:
                    continue
                try:
                    when = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except ValueError:
                    parsed = email.utils.parsedate_tz(raw_date)
                    if parsed:
                        when = datetime.fromtimestamp(
                            calendar.timegm(parsed[:9]) - (parsed[9] or 0), timezone.utc)
            if when is None or when < since:
                continue

            out.append(Item(
                uid=link,
                title=title,
                url=link,
                source=feed["name"],
                summary=clean(pick("summary", "description", "content"))[:1500],
                published=when.strftime("%Y-%m-%d"),
                signal=f"published on {feed['name']}",
            ))
    return out


def index_candidates(indexes: list[dict]) -> list[Item]:
    """Sites with no feed at all. Scrape the newest links off an index page.

    There are no dates here, so recency comes from seen.json instead: a link
    that has not been judged before is treated as new.
    """
    out: list[Item] = []
    for index in indexes:
        try:
            page = fetch(index["url"]).decode("utf8", "replace")
        except Exception as exc:
            print(f"  index failed ({index['name']}): {exc}", file=sys.stderr)
            continue

        pattern = re.compile(index["link_pattern"])
        seen_here: set[str] = set()
        for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                                     page, re.S | re.I):
            if not pattern.search(href) or href in seen_here:
                continue
            seen_here.add(href)
            title = clean(text)
            if not title:
                continue
            out.append(Item(
                uid=urllib.parse.urljoin(index["url"], href),
                title=title,
                url=urllib.parse.urljoin(index["url"], href),
                source=index["name"],
                published="undated",
                signal=f"posted on {index['name']}",
            ))
            if len(seen_here) >= index.get("max_links", 5):
                break
    return out


# ──────────────────────────── feedback ────────────────────────────
#
# There is no server behind this, so a verdict travels as a prefilled GitHub
# issue: the email links open the new-issue form with the title and body
# already written, and submitting takes one more click. The next run reads
# those issues, folds them into feedback.json, and closes them.

def feedback_url(item: Item, verdict: str) -> str:
    title = f"[{verdict}] {item.title}"[:180]
    body = (f"{item.url}\n\nSource: {item.source}\n\n"
            f"Why (optional, one line, it is used to calibrate future ranking):\n")
    query = urllib.parse.urlencode({
        "title": title, "body": body, "labels": "digest-feedback"})
    return f"https://github.com/{REPO}/issues/new?{query}"


def ingest_feedback(path: Path, close: bool = True) -> list[dict]:
    """Read open feedback issues, append them to feedback.json, close them."""
    entries = json.loads(path.read_text()) if path.exists() else []
    known = {e["title"] for e in entries}

    try:
        raw = fetch(f"https://api.github.com/repos/{REPO}/issues"
                    "?state=open&per_page=50&labels=digest-feedback")
        issues = json.loads(raw)
    except Exception as exc:
        print(f"  could not read feedback issues: {exc}", file=sys.stderr)
        return entries

    token = os.environ.get("GITHUB_TOKEN")
    added = 0
    for issue in issues:
        match = re.match(r"\[(liked|disliked)\]\s*(.+)", issue.get("title", ""), re.I)
        if not match:
            continue
        verdict, title = match.group(1).lower(), match.group(2).strip()
        note = ""
        for line in (issue.get("body") or "").splitlines():
            line = line.strip()
            if line and not line.startswith(("http", "Source:", "Why (optional")):
                note = line[:200]
                break
        if title not in known:
            entries.append({"verdict": verdict, "title": title, "note": note,
                            "added": datetime.now(timezone.utc).strftime("%Y-%m-%d")})
            known.add(title)
            added += 1

        if close and token:
            try:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/issues/{issue['number']}",
                    data=json.dumps({"state": "closed"}).encode(), method="PATCH",
                    headers={"Authorization": f"Bearer {token}",
                             "Accept": "application/vnd.github+json",
                             "User-Agent": UA})
                urllib.request.urlopen(req, timeout=20).close()
            except Exception as exc:
                print(f"  could not close issue #{issue['number']}: {exc}",
                      file=sys.stderr)

    if added:
        print(f"  ingested {added} new verdicts")
        path.write_text(json.dumps(entries[-500:], indent=1))
    return entries


def calibration(entries: list[dict], per_side: int = 12) -> str:
    """The most recent verdicts, as examples the ranker has to respect."""
    liked = [e for e in entries if e["verdict"] == "liked"][-per_side:]
    disliked = [e for e in entries if e["verdict"] == "disliked"][-per_side:]
    if not liked and not disliked:
        return ""

    def block(label: str, rows: list[dict]) -> str:
        if not rows:
            return ""
        lines = "\n".join(
            f'  - "{e["title"]}"' + (f' ({e["note"]})' if e.get("note") else "")
            for e in rows)
        return f"{label}\n{lines}\n"

    return (
        "\n\nThe reader has rated past suggestions. These are real verdicts "
        "from them, so where they conflict with the written profile above, "
        "the verdicts win. Infer what the pattern is rather than matching "
        "titles literally.\n\n"
        + block("Wanted more like these:", liked)
        + block("Wanted fewer like these:", disliked)
    )


# ──────────────────────────── ranking ────────────────────────────

class Judgement(BaseModel):
    index: int
    interest: int          # 0-100, how interesting Elias would find it
    why: str               # one line, what makes it a match or not
    summary: str           # two sentences on what the work actually says
    credibility: str       # what backs it, or what is missing


class Judgements(BaseModel):
    items: list[Judgement]


SYSTEM = """You rank new papers and blog posts for one specific reader and \
summarise the ones worth their time. The reader's interest profile follows. \
Judge against that profile only, not against general importance.

{profile}

For each candidate return:
  interest    0-100. How much would THIS reader want to read it. Be harsh. \
Most papers should land under 40. Reserve 80+ for work that clearly sits in \
the core interests and says something new. A paper in an adjacent field that \
is excellent but off profile scores low, that is correct.
  why         One line. Name the specific interest it hits, or say why it is \
off profile. Do not restate the title.
  summary     Two sentences on what the work actually claims and shows. \
Concrete. No "this paper explores" throat clearing.
  credibility What backs this work: recognisable authors or groups, a venue, \
community signal. If it is a fresh preprint with no track record you can see, \
say so plainly. Never invent citations, venues, or affiliations. Say \
"no signal yet" when there is none.

Write in plain prose. Do not use em dashes, en dashes, or semicolons."""


class RankingUnavailable(Exception):
    """No usable Anthropic credentials, or every batch failed."""


def matched_terms(item: Item) -> list[str]:
    text = f"{item.title} {item.summary}".lower()
    hits = [t.strip() for terms in PREFILTER_TERMS.values()
            for t in terms if t in text]
    return sorted(set(hits), key=len, reverse=True)[:5]


def rank(items: list[Item], profile: str, notes: str = "",
         batch_size: int = 12) -> list[Item]:
    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as exc:
        raise RankingUnavailable(f"client unavailable: {exc}") from exc

    ranked: list[Item] = []

    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        lines = []
        for i, item in enumerate(batch):
            lines.append(
                f"[{i}] {item.title}\n"
                f"    source: {item.source} ({item.published})\n"
                f"    authors: {item.authors or 'not listed'}\n"
                f"    signal: {item.signal}\n"
                f"    abstract: {item.summary[:1200] or 'not available'}"
            )
        prompt = (
            "Judge every candidate below and return one entry per candidate, "
            "keeping the index.\n\n" + "\n\n".join(lines)
        )

        try:
            response = client.messages.parse(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM.format(profile=profile) + notes,
                messages=[{"role": "user", "content": prompt}],
                output_format=Judgements,
            )
        except Exception as exc:
            # A credentials problem will fail every remaining batch the same
            # way, so stop now rather than burning through the rest. The SDK
            # raises a plain TypeError when no key resolves at all.
            fatal = (
                getattr(exc, "status_code", None) in (401, 403)
                or isinstance(exc, (anthropic.AuthenticationError,
                                    anthropic.PermissionDeniedError))
                or "authentication" in str(exc).lower()
            )
            if fatal:
                raise RankingUnavailable(f"no usable credentials: {exc}") from exc
            print(f"  ranking batch failed: {exc}", file=sys.stderr)
            continue

        for judgement in response.parsed_output.items:
            if not 0 <= judgement.index < len(batch):
                continue
            item = batch[judgement.index]
            item.score = judgement.interest
            item.why = judgement.why
            item.blurb = judgement.summary
            item.credibility = judgement.credibility
            ranked.append(item)

    if not ranked:
        raise RankingUnavailable("every batch failed")

    ranked.sort(key=lambda i: i.score, reverse=True)
    return ranked


def unranked(items: list[Item], limit: int) -> list[Item]:
    """Fallback when the model is unreachable.

    No scores and no summaries, because inventing either would be worse than
    admitting the ranking did not run. Each item carries the first part of its
    own abstract and the keywords that matched.
    """
    picked = sorted(items, key=lambda i: i.prefilter_score(), reverse=True)[:limit]
    for item in picked:
        sentences = re.split(r"(?<=[.!?]) ", item.summary)
        item.blurb = " ".join(sentences[:2])[:400] or "No abstract available."
        item.why = "Matched " + ", ".join(matched_terms(item)) if matched_terms(item) \
            else "Matched nothing specific, included on source alone."
        item.credibility = item.signal
    return picked


# ──────────────────────────── output ────────────────────────────

def render_html(items: list[Item], considered: int, degraded: str = "") -> str:
    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    rows = []
    for item in items:
        rows.append(f"""
      <tr><td style="padding:0 0 30px 0;">
        <div style="font:600 16px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
          <a href="{html.escape(item.url)}" style="color:#2f6fd0;text-decoration:none;">{html.escape(item.title)}</a>
        </div>
        <div style="font:400 12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:#8a8f98;padding-top:4px;">
          {html.escape(item.source)} &middot; {html.escape(item.published)}{f" &middot; interest {item.score}" if item.score else ""}
        </div>
        <div style="font:400 14px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#333;padding-top:10px;">
          {html.escape(item.blurb)}
        </div>
        <div style="font:400 13px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#5b6068;padding-top:8px;">
          <strong style="color:#333;">{"Keywords" if degraded else "Why you"}:</strong> {html.escape(item.why)}<br>
          <strong style="color:#333;">Standing:</strong> {html.escape(item.credibility)}
        </div>
        <div style="font:400 12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;padding-top:10px;">
          <a href="{html.escape(feedback_url(item, 'liked'))}" style="color:#2f8a5b;text-decoration:none;">More like this</a>
          <span style="color:#c7ccd3;">&nbsp;&nbsp;/&nbsp;&nbsp;</span>
          <a href="{html.escape(feedback_url(item, 'disliked'))}" style="color:#b4553f;text-decoration:none;">Less like this</a>
        </div>
      </td></tr>""")

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f6f7f9;">
<table role="presentation" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#fff;border-radius:10px;padding:32px;">
  <tr><td style="font:600 20px/1.3 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding-bottom:4px;">Reading digest</td></tr>
  <tr><td style="font:400 13px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:#8a8f98;padding-bottom:{"14px" if degraded else "28px"};">
    {today} &middot; {len(items)} of {considered} candidates
  </td></tr>
  {f'<tr><td style="background:#fff6e5;border:1px solid #f0dcb0;border-radius:6px;padding:12px 14px;margin-bottom:20px;font:400 13px/1.6 -apple-system,BlinkMacSystemFont,sans-serif;color:#7a5a1a;">Ranking did not run, so this is the keyword shortlist only. No interest scores and no summaries, the text below is each abstract in its own words. Reason: {html.escape(degraded)}</td></tr><tr><td style="height:20px;"></td></tr>' if degraded else ''}
  {''.join(rows) if rows else '<tr><td style="font:400 14px/1.6 sans-serif;color:#5b6068;">Nothing cleared the bar this week.</td></tr>'}
  <tr><td style="border-top:1px solid #e6e8eb;padding-top:20px;font:400 12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:#a0a5ad;">
    Ranked against digest/interests.md. The rating links open a prefilled GitHub
    issue, one more click submits it, and next week's ranking takes it into account.
  </td></tr>
</table>
</body></html>"""


def render_text(items: list[Item], considered: int, degraded: str = "") -> str:
    lines = [f"Reading digest, {len(items)} of {considered} candidates", ""]
    if degraded:
        lines += [f"Ranking did not run ({degraded}). Keyword shortlist only,",
                  "no scores and no summaries, the text below is each abstract.", ""]
    for item in items:
        lines += [
            item.title,
            f"  {item.source} | {item.published}" + (f" | interest {item.score}" if item.score else ""),
            f"  {item.blurb}",
            f"  {'Keywords' if degraded else 'Why you'}: {item.why}",
            f"  Standing: {item.credibility}",
            f"  {item.url}",
            f"  more like this: {feedback_url(item, 'liked')}",
            f"  less like this: {feedback_url(item, 'disliked')}",
            "",
        ]
    return "\n".join(lines)


def send(subject: str, html_body: str, text_body: str, to: str) -> None:
    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        payload = json.dumps({
            "from": os.environ.get("DIGEST_FROM", "onboarding@resend.dev"),
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }).encode()
        req = urllib.request.Request(
            "https://api.resend.com/emails", data=payload, method="POST",
            headers={"Authorization": f"Bearer {resend_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("  sent via Resend:", resp.status)
        return

    gmail_user = os.environ.get("GMAIL_USER")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
    if gmail_user and gmail_pass:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = to
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print("  sent via Gmail SMTP")
        return

    raise SystemExit(
        "No delivery credentials. Set RESEND_API_KEY, or GMAIL_USER plus "
        "GMAIL_APP_PASSWORD, as repository secrets."
    )


# ──────────────────────────── main ────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="rank and print, send nothing, record nothing")
    parser.add_argument("--no-model", action="store_true",
                        help="skip ranking, just list what was collected")
    args = parser.parse_args()

    config = json.loads((HERE / "sources.json").read_text())
    profile = (HERE / "interests.md").read_text()
    seen_path = HERE / "seen.json"
    seen = set(json.loads(seen_path.read_text())) if seen_path.exists() else set()
    # Items listed in a fallback email were never judged, so they are tracked
    # apart: they should not repeat next week, but they should still get a real
    # ranking the first time a working key exists.
    listed_path = HERE / "seen_unranked.json"
    listed = set(json.loads(listed_path.read_text())) if listed_path.exists() else set()

    feedback = ingest_feedback(HERE / "feedback.json", close=not args.dry_run)
    notes = calibration(feedback)
    if notes:
        print(f"  calibrating on {len(feedback)} past verdicts")

    since = datetime.now(timezone.utc) - timedelta(days=config["lookback_days"])
    print(f"Collecting since {since:%Y-%m-%d}")

    candidates: list[Item] = []
    candidates += arxiv_candidates(config["arxiv_queries"], since)
    if config.get("huggingface_daily_papers"):
        candidates += huggingface_candidates(since)
    candidates += feed_candidates(config["feeds"], since)
    candidates += index_candidates(config.get("html_indexes", []))
    print(f"  collected {len(candidates)}")

    by_uid: dict[str, Item] = {}
    for item in candidates:
        uid = canonical(item.uid)
        if uid in seen:
            continue
        # arXiv and HF surface the same paper, keep whichever carries a signal
        existing = by_uid.get(uid)
        if existing is None or item.extras.get("upvotes", 0) > existing.extras.get("upvotes", 0):
            by_uid[uid] = item
    fresh = list(by_uid.values())
    print(f"  {len(fresh)} unseen after dedupe")

    if not fresh:
        print("Nothing new.")
        return 0

    fresh.sort(key=lambda i: i.prefilter_score(), reverse=True)
    shortlist = fresh[:config["prefilter_keep"]]
    dropped = len(fresh) - len(shortlist)
    if dropped:
        print(f"  prefilter dropped {dropped} lowest-matching candidates")

    if args.no_model:
        for item in shortlist:
            print(f"  [{item.prefilter_score():2}] {item.source}: {item.title}")
        return 0

    degraded = ""
    try:
        ranked = rank(shortlist, profile, notes)
        keep = [i for i in ranked
                if i.score >= config["min_interest_score"]][:config["max_items"]]
        print(f"  {len(keep)} cleared the bar of {config['min_interest_score']}")
    except RankingUnavailable as exc:
        # Keep the banner readable, the full error stays in the job log.
        degraded = ("no Anthropic API key is configured for this repository"
                    if "credentials" in str(exc).lower() else str(exc)[:140])
        print(f"  ranking unavailable: {exc}", file=sys.stderr)
        ranked = []
        pool = [i for i in shortlist if canonical(i.uid) not in listed]
        keep = unranked(pool, config["max_items"])
        print(f"  falling back to {len(keep)} keyword matches", file=sys.stderr)

    subject = (f"Reading digest, {len(keep)} unranked, {datetime.now():%d %b}"
               if degraded else
               f"Reading digest, {len(keep)} papers, {datetime.now():%d %b}")
    html_body = render_html(keep, len(shortlist), degraded)
    text_body = render_text(keep, len(shortlist), degraded)

    if args.dry_run:
        print("\n" + text_body)
        return 0

    if keep:
        send(subject, html_body, text_body, os.environ["DIGEST_TO"])

    # Only record what the model actually judged, so a failed batch retries.
    seen.update(canonical(i.uid) for i in ranked)
    seen_path.write_text(json.dumps(sorted(seen)[-4000:], indent=0))

    if degraded:
        listed.update(canonical(i.uid) for i in keep)
        listed_path.write_text(json.dumps(sorted(listed)[-4000:], indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
