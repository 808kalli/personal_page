/**
 * Reading digest vote endpoint.
 *
 * GET /vote?id=<canonical>&v=liked|ignored&title=...&url=...&source=...&why=...
 *
 * The click is the whole action: no confirmation page to submit, no second
 * step. Records the verdict into digest/verdicts.json in the repo via the
 * GitHub Contents API, and returns a plain confirmation page.
 */

const REPO = "808kalli/personal_page";
const PATH = "digest/verdicts.json";

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
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } }
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/vote") {
      return new Response("Not found", { status: 404 });
    }

    const id = url.searchParams.get("id");
    const verdict = url.searchParams.get("v");
    if (!id || (verdict !== "liked" && verdict !== "ignored")) {
      return new Response("Missing or invalid id/v", { status: 400 });
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
      return page(
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
      return page(
        "Something went wrong",
        `<p>Could not save your vote (${putResp.status}).</p>
         <p style="color:#888;font-size:0.85rem;">${detail.slice(0, 300)}</p>`
      );
    }

    const label = verdict === "liked" ? "Liked" : "Ignored";
    return page(
      label,
      `<p style="font-size:1.3rem;">${label}: ${entry.title || id}</p>
       <p style="color:#888;">You can close this tab.</p>`
    );
  },
};
