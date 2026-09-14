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

  let body = {};
  try {
    body = JSON.parse(event.body || "{}");
  } catch (e) {
    body = {};
  }

  const mode = body.mode || "all";
  const ghToken = process.env.GH_PAT || process.env.GITHUB_TOKEN;

  if (!ghToken) {
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        dispatched: false,
        message: "Pipeline trigger requested. To enable 1-click cloud dispatch from Netlify, set GH_PAT in Netlify Site Settings > Environment Variables.",
        actions_url: "https://github.com/CoachAJ/bensocialmediahub/actions"
      })
    };
  }

  try {
    const dispatchUrl = "https://api.github.com/repos/CoachAJ/bensocialmediahub/actions/workflows/pipeline.yml/dispatches";
    const res = await fetch(dispatchUrl, {
      method: "POST",
      headers: {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": `Bearer ${ghToken}`,
        "User-Agent": "PharmacistBen-MasterHub-Netlify"
      },
      body: JSON.stringify({
        ref: "main",
        inputs: { mode: mode === "dry-run" ? "all" : mode }
      })
    });

    if (res.status === 204 || res.ok) {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          dispatched: true,
          mode: mode,
          message: `Successfully dispatched GitHub Actions pipeline workflow on 'CoachAJ/bensocialmediahub' in '${mode}' mode!`,
          actions_url: "https://github.com/CoachAJ/bensocialmediahub/actions"
        })
      };
    } else {
      const errText = await res.text();
      return {
        statusCode: res.status,
        headers,
        body: JSON.stringify({
          success: false,
          error: `GitHub API error (${res.status}): ${errText}`,
          actions_url: "https://github.com/CoachAJ/bensocialmediahub/actions"
        })
      };
    }
  } catch (err) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ success: false, error: err.message })
    };
  }
};
