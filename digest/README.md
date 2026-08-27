# Reading digest

A weekly email of new papers and posts worth your time, ranked against
`interests.md` and summarised in two sentences each.

Runs as a GitHub Action every Monday at 06:00 UTC (09:00 in Athens during
summer). Nothing runs until you add the secrets below.

## Setup

**1. Anthropic API key.** Repository Settings, Secrets and variables, Actions,
New repository secret:

| Secret | Value |
| --- | --- |
| `ANTHROPIC_API_KEY` | a key from console.anthropic.com |
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

## Cost

Around 60 candidates reach the model each week, batched twelve at a time, so
roughly five calls of a few thousand tokens. Cents per week on Claude Opus 5.

## Tuning it

`interests.md` **is** the ranking prompt. It is prose, so edit it in prose. The
"Not interested" section does more work than the positive list, so when
something irrelevant gets through, add why it was wrong there.

`sources.json`:

| Key | Meaning |
| --- | --- |
| `lookback_days` | how far back to look, 8 gives the weekly run a day of overlap |
| `prefilter_keep` | how many candidates reach the model, the rest are dropped on keyword score |
| `max_items` | hard cap on the email |
| `min_interest_score` | the bar, 0 to 100. Raise it if the digest feels padded |
| `arxiv_queries` | arXiv API query strings, one request each |
| `feeds` | RSS or Atom, both parse |
| `html_indexes` | sites with no feed at all, scraped for the newest links |

`seen.json` is written back by the workflow so nothing repeats. Deleting it
makes the next run treat everything as new.

## Running it locally

```bash
pip install -r digest/requirements.txt
export ANTHROPIC_API_KEY=...
python digest/digest.py --dry-run     # rank and print, send nothing
python digest/digest.py --no-model    # just show what was collected, no API call
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
