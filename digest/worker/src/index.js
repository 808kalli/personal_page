/**
 * Reading digest vote endpoint.
 *
 * GET /vote?id=<canonical>&v=liked|ignored&title=...&url=...&source=...&why=...
 *
 * The click is the whole action: no confirmation page to submit, no second
 * step. Records the verdict into digest/verdicts.json in the repo via the
 * GitHub Contents API, and returns a plain confirmation page.
 *
 * Add `&format=json` (what reading.html's "add a paper" form uses) to get a
 * small `{ok:true,entry}` / `{error:...}` JSON response instead of the HTML
 * confirmation page, with CORS enabled for reading.html's own origin.
 */

const REPO = "808kalli/personal_page";
const PATH = "digest/verdicts.json";

// The only caller that needs to read the response via fetch() rather than
// just navigating to the link (email Like/Ignore clicks don't care about
// CORS at all - this is for reading.html's "add a paper" form).
const ALLOWED_ORIGIN = "https://808kalli.github.io";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function utf8ToBase64(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

function base64ToUtf8(str) {
  return decodeURIComponent(escape(atob(str)));
}

function page(title, body) {
  return new Response(
    `<!doctype html><meta charset="utf-8">
<title>${title}</title>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             max-width:480px;margin:100px auto;text-align:center;color:#333;">
${body}
</body>`,
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() } }
  );
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

const ARXIV_ID = /arxiv\.org\/(?:abs|pdf)\/([0-9]{4}\.[0-9]{4,5})/;

function decodeEntities(s) {
  return s
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#0?39;/g, "'")
    .replace(/\s+/g, " ").trim();
}

// GET /resolve?url=<paper or post url>
// Best-effort title + source lookup for the "add a paper" form's URL field,
// so pasting a link fills in the rest rather than requiring it typed by
// hand. arXiv gets a real API call (atom feed, one <entry> per id); anything
// else is a plain og:title/<title> scrape, which can't be done from the
// browser itself since arbitrary cross-origin fetches are blocked there,
// it is not a CORS problem this worker's own headers can fix on someone
// else's site. Failure here is always non-fatal: the caller falls back to
// the user typing the title in by hand, same as before this existed.
async function resolveMetadata(targetUrl) {
  const arxivMatch = targetUrl.match(ARXIV_ID);
  if (arxivMatch) {
    const resp = await fetch(
      `https://export.arxiv.org/api/query?id_list=${arxivMatch[1]}`,
      { headers: { "User-Agent": "reading-digest-resolve-worker" } }
    );
    if (!resp.ok) throw new Error(`arXiv API ${resp.status}`);
    const xml = await resp.text();
    const entry = xml.match(/<entry>([\s\S]*?)<\/entry>/);
    if (!entry) throw new Error("arXiv id not found");
    const titleMatch = entry[1].match(/<title>([\s\S]*?)<\/title>/);
    if (!titleMatch) throw new Error("no title in arXiv response");
    return { title: decodeEntities(titleMatch[1]), source: "arXiv" };
  }

  const resp = await fetch(targetUrl, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; reading-digest-resolve-worker)" },
  });
  if (!resp.ok) throw new Error(`fetch ${resp.status}`);
  const html = await resp.text();

  const og = html.match(/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']*)["']/i)
          || html.match(/<meta[^>]+content=["']([^"']*)["'][^>]+property=["']og:title["']/i);
  const plain = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = decodeEntities((og ? og[1] : plain ? plain[1] : "") || "");
  if (!title) throw new Error("no title found on page");

  let source = "";
  try { source = new URL(targetUrl).hostname.replace(/^www\./, ""); } catch {}

  return { title, source };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    if (url.pathname === "/resolve") {
      const target = url.searchParams.get("url");
      if (!target) return json({ error: "Missing url" }, 400);
      try {
        const meta = await resolveMetadata(target);
        return json(meta);
      } catch (exc) {
        return json({ error: String(exc.message || exc) }, 502);
      }
    }

    if (url.pathname !== "/vote") {
      return new Response("Not found", { status: 404, headers: corsHeaders() });
    }

    const id = url.searchParams.get("id");
    const verdict = url.searchParams.get("v");
    // "wantsJson" is how reading.html's fetch() call is told apart from a
    // plain browser navigation (an email Like/Ignore link click) so it gets
    // a small JSON ack instead of the full confirmation page.
    const wantsJson = url.searchParams.get("format") === "json";
    if (!id || (verdict !== "liked" && verdict !== "ignored")) {
      return wantsJson
        ? json({ error: "Missing or invalid id/v" }, 400)
        : new Response("Missing or invalid id/v", { status: 400, headers: corsHeaders() });
    }

    const entry = {
      id,
      verdict,
      title: (url.searchParams.get("title") || "").slice(0, 300),
      url: url.searchParams.get("url") || "",
      source: url.searchParams.get("source") || "",
      why: (url.searchParams.get("why") || "").slice(0, 300),
      recorded: new Date().toISOString(),
    };

    const apiBase = `https://api.github.com/repos/${REPO}/contents/${PATH}`;
    const headers = {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "reading-digest-vote-worker",
      "X-GitHub-Api-Version": "2022-11-28",
    };

    let sha;
    let entries = [];
    const getResp = await fetch(apiBase, { headers });
    if (getResp.status === 200) {
      const data = await getResp.json();
      sha = data.sha;
      try {
        entries = JSON.parse(base64ToUtf8(data.content));
      } catch {
        entries = [];
      }
    } else if (getResp.status !== 404) {
      const detail = await getResp.text();
      return wantsJson
        ? json({ error: `Could not read current state (${getResp.status})`, detail: detail.slice(0, 200) }, 502)
        : page(
            "Something went wrong",
            `<p>Could not read current state (${getResp.status}).</p>
             <p style="color:#888;font-size:0.85rem;">${detail.slice(0, 200)}</p>`
          );
    }

    // Re-voting on the same item replaces the earlier verdict rather than
    // duplicating it.
    entries = entries.filter((e) => e.id !== id);
    entries.push(entry);

    const putBody = {
      message: `Record ${verdict} verdict for ${id}`,
      content: utf8ToBase64(JSON.stringify(entries, null, 1) + "\n"),
      committer: { name: "reading-digest", email: "actions@github.com" },
    };
    if (sha) putBody.sha = sha;

    const putResp = await fetch(apiBase, {
      method: "PUT",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify(putBody),
    });

    if (!putResp.ok) {
      const detail = await putResp.text();
      return wantsJson
        ? json({ error: `Could not save (${putResp.status})`, detail: detail.slice(0, 300) }, 502)
        : page(
            "Something went wrong",
            `<p>Could not save your vote (${putResp.status}).</p>
             <p style="color:#888;font-size:0.85rem;">${detail.slice(0, 300)}</p>`
          );
    }

    if (wantsJson) return json({ ok: true, entry });

    const label = verdict === "liked" ? "Liked" : "Ignored";
    return page(
      label,
      `<p style="font-size:1.3rem;">${label}: ${entry.title || id}</p>
       <p style="color:#888;">You can close this tab.</p>`
    );
  },
};
