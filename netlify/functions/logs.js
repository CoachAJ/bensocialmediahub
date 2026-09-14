exports.handler = async function(event, context) {
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  const ghToken = process.env.GH_PAT || process.env.GITHUB_TOKEN;
  const authHeaders = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "PharmacistBen-MasterHub-Netlify"
  };
  if (ghToken) {
    authHeaders["Authorization"] = `Bearer ${ghToken}`;
  }

  let lines = [];
  let runStatus = "idle";

  try {
    const res = await fetch("https://api.github.com/repos/CoachAJ/bensocialmediahub/actions/runs?per_page=1", {
      headers: authHeaders
    });
    if (res.ok) {
      const data = await res.json();
      const latestRun = (data.workflow_runs || [])[0];
      if (latestRun) {
        runStatus = latestRun.status === "in_progress" || latestRun.status === "queued" ? "running" : "completed";
        lines.push(`[GITHUB ACTIONS] Run #${latestRun.run_number} (${latestRun.name})`);
        lines.push(`[STATUS] State: ${latestRun.status} | Conclusion: ${latestRun.conclusion || "Pending..."}`);
        lines.push(`[UPDATED] Last updated: ${latestRun.updated_at}`);
        lines.push(`[VIEW RUN] ${latestRun.html_url}`);
      }
    }
  } catch (err) {
    lines.push(`[NETLIFY] Monitoring active. Ready for next scheduled daily cron at 12:00 UTC.`);
  }

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({
      lines: lines,
      next_index: lines.length,
      status: runStatus
    })
  };
};
