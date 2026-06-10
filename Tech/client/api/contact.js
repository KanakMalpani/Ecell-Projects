export default async function handler(request, response) {
  if (request.method !== "POST") {
    response.setHeader("Allow", "POST");
    return response.status(405).json({ error: "Method not allowed" });
  }

  const scriptUrl = process.env.GOOGLE_SCRIPT_URL;
  if (!scriptUrl) {
    return response.status(503).json({
      error: "Google Sheets automation is not configured yet.",
      hint: "Set GOOGLE_SCRIPT_URL in Vercel project environment variables.",
    });
  }

  try {
    const upstream = await fetch(scriptUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request.body),
    });

    const text = await upstream.text();
    let payload = { success: true };

    try {
      payload = JSON.parse(text);
    } catch {
      payload = { success: upstream.ok, raw: text };
    }

    if (!upstream.ok) {
      return response.status(502).json({ error: "Google Script request failed", details: payload });
    }

    return response.status(200).json({ success: true, message: "Inquiry saved to Google Sheets." });
  } catch (error) {
    return response.status(500).json({ error: error.message || "Submission failed" });
  }
}
