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

  let manifestCounts = {
    existing_shorts: 0,
    podcast_episodes: 0,
    quizzes: 0
  };

  // 1. Fetch live manifest from GitHub repo
  try {
    const rawManifestUrl = "https://raw.githubusercontent.com/CoachAJ/bensocialmediahub/main/data/processed.json";
    const res = await fetch(rawManifestUrl);
    if (res.ok) {
      const data = await res.json();
      manifestCounts.existing_shorts = (data.existing_shorts || []).length;
      manifestCounts.podcast_episodes = (data.podcast_episodes || []).length;
      manifestCounts.quizzes = Math.max(manifestCounts.podcast_episodes, 0);
    }
  } catch (err) {
    console.warn("Could not fetch raw manifest from GitHub:", err);
  }

  // 2. Buffer Queue Stats (if BUFFER_ACCESS_TOKEN configured in Netlify)
  let bufferQueues = {
    tiktok: { count: 2, limit: 10 },
    instagram: { count: 3, limit: 10 },
    x: { count: 1, limit: 10 }
  };

  const bufferToken = process.env.BUFFER_ACCESS_TOKEN;
  if (bufferToken) {
    try {
      const profileMapStr = process.env.BUFFER_PROFILE_MAP_JSON || "{}";
      const profileMap = JSON.parse(profileMapStr);
      for (const [pid, platform] of Object.entries(profileMap)) {
        if (bufferQueues[platform]) {
          const res = await fetch(`https://api.bufferapp.com/1/profiles/${pid}/updates/pending.json?access_token=${bufferToken}`);
          if (res.ok) {
            const data = await res.json();
            bufferQueues[platform].count = data.total || 0;
          }
        }
      }
    } catch (e) {
      console.warn("Buffer queue fetch error:", e);
    }
  }

  const responsePayload = {
    queues: bufferQueues,
    manifest: manifestCounts,
    health: {
      gemini: Boolean(process.env.GEMINI_API_KEY),
      buffer: Boolean(bufferToken),
      drive: Boolean(process.env.GDRIVE_SERVICE_ACCOUNT_JSON),
      rss: true
    },
    current_status: "idle",
    deployment: "Netlify Cloud Master Hub"
  };

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify(responsePayload)
  };
};
