# Reading digest

A daily email of the 5 best papers and posts, ranked against `interests.md`
and summarised in two sentences each. Not just new ones, an archive pass
searches the same queries with no date limit, so a good paper from 2023 is
just as reachable as one from this morning. See "Old as well as new" below.

Triggered by an external cron service (cron-job.org) calling the workflow's
`workflow_dispatch` endpoint, since GitHub's own `schedule:` trigger did not
fire reliably on this repo. Nothing runs until you add the secrets below and
set up that external trigger.

## Setup

**1. Gemini API key.** Get one at aistudio.google.com, no credit card needed.
Then in Repository Settings, Secrets and variables, Actions, New repository
secret:

| Secret | Value |
| --- | --- |
| `GEMINI_API_KEY` | the key from Google AI Studio |
| `DIGEST_TO` | eliaskallioras@gmail.com |

**2. Pick a way to send mail.** Either one works, the script uses whichever it
finds.

*Resend*, the simpler option. Sign up at resend.com, free tier is 3000
emails a month, then add:

| Secret | Value |
| --- | --- |
| `RESEND_API_KEY` | the key they give you |
| `DIGEST_FROM` | optional, defaults to `onboarding@resend.dev` |

The default sender works for mail to yourself with no DNS setup. Set
`DIGEST_FROM` only once you have verified a domain with them.

*Gmail*, if you would rather not sign up for anything. Needs 2FA on the
account, then generate an app password at myaccount.google.com:

| Secret | Value |
| --- | --- |
| `GMAIL_USER` | eliaskallioras@gmail.com |
| `GMAIL_APP_PASSWORD` | the 16 character app password |

**3. Try it.** Actions tab, Reading digest, Run workflow, tick the dry run box.
That ranks everything and prints the result in the log without sending mail or
recording anything as seen.

## Without a Gemini key

If no key is set, or the key is rejected, the run does not fail. It sends the
keyword shortlist instead, with a banner saying the ranking did not run, no
interest scores, and each item's own abstract in place of a summary. That is
deliberately worse than the ranked digest, the keyword filter cannot tell an
interpretability paper from a manipulation paper that mentions features.

Fallback items go through the same cooldown as everything else once emailed
(see below), so if the key comes back before the cooldown expires they get a
proper ranking on the next run that actually collects them again.

Add `GEMINI_API_KEY` at any point and the next run ranks normally. Nothing
else changes.

## How the scoring works

The keyword score proposes, the model refines. Nothing scores from a blank
slate.

Each candidate's weighted keyword score is stretched onto a 0-100 scale (four
points per unit, capped at 90) and handed to the model as a *proposed score*.
The model does not return a score. It returns an **adjustment** between -60
and +60, which is added to the proposal and clamped to 0-100. The email shows
both, so a line reads "interest 78 (keywords said 40, +38)".

This means a failed or dim model run degrades toward the keyword ordering
rather than toward noise, and you can see at a glance when the model is doing
real work versus rubber stamping. Adjustments of 25 or more are required to
say plainly what the keywords got wrong.

The cap lives in `MAX_ADJUSTMENT` in `digest.py`. Lower it to trust the
keywords more, raise it to trust the model more.

## Blogs versus papers

arXiv puts out far more candidates than the handful of blog feeds ever will,
and casual blog prose naturally matches fewer of the exact keyword phrases a
dense technical abstract does, so blog posts start at a structural
disadvantage on both counts. A small bonus corrects for that at the two
points where it would otherwise cost a good post its spot: `BLOG_PREFILTER_BONUS`
(2 points on the raw keyword score) helps a post survive the initial cut down
to `prefilter_keep` candidates, before anything reaches the model, and
`BLOG_FINAL_BONUS` (5 points on the final 0-100 score) tips a close call in
the model's actual ranking. Neither is large enough to let a mediocre blog
post beat a genuinely strong paper, they only settle ties and near-ties in
favor of format diversity. Both constants live at the top of `digest.py`.

## Old as well as new

`arxiv_candidates` runs each query in `arxiv_queries` twice. Once as
`lookback_days` and sorted by submission date, which is what catches
something the day it appears. On its own that is also the whole problem:
sorted by date and cut off at a recent window, an older paper is never even
considered no matter how well it fits, arXiv publishes enough that the
newest matches always fill every slot. The second pass drops the date limit
entirely and sorts by relevance instead, `backlog_per_query` results per
query (5 by default), so a paper from a year ago that is a strong match for
the query gets found on its own terms.

This is also what makes the names and papers in `interests.md` more than
descriptive prose. "Analysing the Generalisation and Reliability of Steering
Vectors" is never fetched by title, it does not need to be, it is exactly
the kind of result a relevance search on `abs:"steering vector"` surfaces.
Anyone in "People and groups worth watching" who already has an `au:` query
in `arxiv_queries` gets the same treatment, their older work becomes
reachable, not just whatever they published this week. Add an `au:` query
for a name that is not tracked yet if you want the same for them.

Feeds work the same way in spirit: `feed_candidates` is not date filtered
at all now, whatever a site's RSS still lists is in play, not only entries
inside `lookback_days`. RSS itself is what keeps this bounded, most feeds
only carry a handful to a few dozen recent posts regardless.

None of this repeats itself once it has been through the cooldown described
above. The two arXiv passes and the wider feed window mean more of the
archive becomes reachable, they do not mean the same result reappears every
day, an item found in the archive pass today and not liked or ignored still
waits out `cooldown_days` like anything else before it can resurface.

## Rate limits

The Gemini free tier is generally 10 requests per minute and up to 1,500 a
day, but Google does not publish fixed numbers for its newest models, and a
brand new API key can carry a much smaller unpublished daily allowance for a
short while. `pace_seconds` in `sources.json` sleeps that long between
batches so requests never bunch up, and a 429 specifically waits 30 seconds
and retries once before giving up on that batch. That fixes bursty rate
limiting, but not real quota exhaustion, which shows up as every batch
failing even after the backoff.

If that happens, the model in use has run out for the day. Two ways out.
Wait, since it resets in 24 hours. Or switch `model.model` in `sources.json`
to a sibling model, since quotas are tracked per model, not per key, so an
untouched one (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) still has
its full allowance even when another is exhausted.

## Cost

Nothing. Around 40 candidates reach the model each day, batched eight at a
time, so roughly five requests. The Gemini free tier allows ten per minute
and no card, so a daily run of five sits far inside it.

## Marking what you like

Every item in the email has **Like** and **Ignore** links. Clicking one is
the entire action, no confirmation page to submit. The link points at a
small Cloudflare Worker (`digest/worker/`) that writes the verdict straight
into `digest/verdicts.json` in this repo via the GitHub Contents API, and
shows a plain "Liked" / "Ignored" confirmation.

Ignore is not a downvote. It carries no judgement about the research
direction and does not affect what gets suggested next, it is a record for
this one entry, nothing more. It does still do one concrete thing: Like and
Ignore are the only ways to exclude an item permanently (see the cooldown
section below), so clicking either one is what actually makes room for
something else instead of that item resurfacing after 10 days.

This does **not** feed back into ranking, for either button. It used to: past
verdicts went into the prompt as calibration, with the model told they
override `interests.md` on conflict. With only a handful of clicks total,
that meant a single misclick carried outsized weight, with no way to walk it
back except re-voting the same item, so it was removed. Ranking is driven by
`interests.md` alone.

What clicking still does: `reading.html` on the site renders the liked half
of `verdicts.json`, so it becomes a standing reading list, something you can
actually go back to later. If your taste shifts in a way you want reflected
in the ranking, edit `interests.md` directly. It is prose, edit it in prose.

## Cooldown, not permanent exclusion

An item is only ever excluded forever if you actually click Like or Ignore
on it, recorded in `verdicts.json`. Everything else, shown once and never
acted on, is only held back for `cooldown_days` (10 by default), tracked in
`shown.json` as `{canonical id: date last emailed}`.

This exists because a quiet stretch (arXiv does not announce over weekends
or US holidays, so a 2 day lookback can come back genuinely empty) used to
mean the same few candidates that already got shown, but never liked or
ignored, were gone for good, so the digest had nothing left to say. Now they
just come back after 10 days if nothing new has beaten them to it.

`shown.json` is written back by the workflow. Deleting it makes everything
eligible again immediately. It only records what was actually emailed, an
item the model scored below `min_interest_score` was never shown and stays
eligible for tomorrow's run without waiting out any cooldown.

### Deploying the vote worker

```bash
cd digest/worker
npm install -g wrangler          # once
export CLOUDFLARE_API_TOKEN=...  # a token scoped to Edit Cloudflare Workers
wrangler deploy
wrangler secret put GITHUB_TOKEN # a fine-grained PAT, Contents: read and write, this repo only
```

The deployed URL is hardcoded as `VOTE_ENDPOINT` in `digest.py`, update both
if you ever redeploy under a different name.

## Tuning it

`interests.md` **is** the ranking prompt. It is prose, so edit it in prose. The
"Not interested" section does more work than the positive list, so when
something irrelevant gets through, add why it was wrong there.

`sources.json`:

| Key | Meaning |
| --- | --- |
| `lookback_days` | how far back to look. Wider than it sounds it needs to be, arXiv's search API and Hugging Face's daily papers feed can both lag several days behind arxiv.org's own listing pages, confirmed 2026-09-08 with a 4 day gap on a fresh, uncached request. 6 gives room to absorb that without permanently losing a paper to a lookback window that closed before the index caught up. The per-item cooldown, not this, is what stops repeats |
| `cooldown_days` | how long a shown-but-unactioned item stays excluded before it is eligible again |
| `backlog_per_query` | results per arXiv query in the no-date-limit relevance pass, see "Old as well as new" |
| `prefilter_keep` | how many candidates reach the model, the rest are dropped on keyword score |
| `max_items` | hard cap on the email |
| `min_interest_score` | the bar, 0 to 100. Raise it if the digest feels padded |
| `model` | provider, model id, endpoint, batch size, timeout, and `pace_seconds` |
| `arxiv_queries` | arXiv API query strings, one request each |
| `feeds` | RSS or Atom, both parse |
| `html_indexes` | sites with no feed at all, scraped for the newest links |

Author queries are how a person gets tracked, batched with `OR` so a group of
five costs one request. The arXiv API wants full names (`au:"Neel Nanda"`),
not the `Lastname_I` form, which silently returns nothing.

Several org blogs wrap each post card in an empty anchor, so the index gives a
link and no title. Where that happens the scraper fetches the post page for
its `og:title`, one request per new link.

`verdicts.json` holds your likes and dislikes, written by the vote worker,
editing it by hand works fine too. See "Cooldown, not permanent exclusion"
above for `shown.json`.

## Running it locally

No dependencies, the script is standard library only.

```bash
export GEMINI_API_KEY=...
python3 digest/digest.py --dry-run     # rank and print, send nothing
python3 digest/digest.py --no-model    # just show what was collected, no API call
python3 digest/digest.py --test-email  # send a two line email, check delivery only
```

## What it does not do

It cannot tell you a fresh preprint is any good. A paper posted three days ago
has no citations and no reputation, so freshness and community standing pull
against each other. Rather than filter on a signal that does not exist yet,
every item carries a "Standing" line saying what actually backs it, including
"no signal yet" when that is the honest answer. Hugging Face upvote counts are
passed through where they exist, which is the one real signal available on a
week-old paper.

BAIR's blog feed is not in the source list because it was unreachable from
here. If it works from the Actions runner, add
`https://bair.berkeley.edu/blog/feed.xml` to `feeds`.

Redwood Research's feed was dropped for the same reason, a persistent 403
even with the browser user agent fallback. The feed itself moved, Substack
now 301s `redwoodresearch.substack.com/feed` to `blog.redwoodresearch.org/feed`,
but that domain is Cloudflare fronted, and Cloudflare bot management is a
common source of 403s against datacenter IP ranges like the Actions runner's,
independent of anything in the request itself. Re-add
`https://blog.redwoodresearch.org/feed` to `feeds` if it ever starts working
from the runner.
