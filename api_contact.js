// Vercel serverless function behind the /contact/ form.
// Copied to deploy/api/contact.js by build_site.py, so it ships with the site.
//
// Sends through Brevo, which is already authenticated on this domain (DKIM CNAMEs
// and an SPF include are live), so the mail is signed as yoniverseproductions.com
// rather than arriving from a third party form service.
//
// Needs one environment variable in Vercel: BREVO_API_KEY

const TO = "yoni@yoniverseproductions.com";
const FROM_NAME = "Yoniverse site";

// must stay identical to TRADE_GROUPS in build_site.py, or valid submissions bounce
const TRADES = [
  "HVAC", "Plumbing", "Electrical", "Roofing", "Garage doors",
  "More than one of these", "Another home service",
  "Remodeling, ADU or new build", "Real estate agent or brokerage",
  "Creator, artist or channel",
];
const BUDGETS = [
  "$2,000 to $3,000", "$4,000 to $5,000",
  "$10,000 to $15,000", "Not sure yet",
];

const esc = (s) =>
  String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const clean = (v, max) => String(v == null ? "" : v).trim().slice(0, max);

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  let b = req.body;
  if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { b = {}; } }
  b = b || {};

  // Honeypot. A real person never fills this; bots fill every field they find.
  // Return success so the bot does not learn it was caught.
  if (clean(b.website, 200)) return res.status(200).json({ ok: true });

  const name    = clean(b.name, 120);
  const email   = clean(b.email, 200);
  const phone   = clean(b.phone, 40);
  const company = clean(b.company, 160);
  const city    = clean(b.city, 120);
  const trade   = clean(b.trade, 80);
  const budget  = clean(b.budget, 40);
  const message = clean(b.message, 4000);

  const errors = {};
  if (!name) errors.name = "Please add your name.";
  if (!email) errors.email = "Please add an email address.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) errors.email = "That email address does not look right.";
  if (!company) errors.company = "Please add your company, handle or channel.";
  if (!city) errors.city = "Please add your city.";
  if (!TRADES.includes(trade)) errors.trade = "Please pick what you do.";
  if (!BUDGETS.includes(budget)) errors.budget = "Please pick a monthly range.";

  if (Object.keys(errors).length) {
    return res.status(400).json({ ok: false, errors });
  }

  const key = process.env.BREVO_API_KEY;
  if (!key) {
    console.error("BREVO_API_KEY is not set");
    return res.status(500).json({
      ok: false,
      error: "The form is not connected yet. Please email " + TO + " directly.",
    });
  }

  const rows = [
    ["Name", name], ["Email", email], ["Phone", phone || "not given"],
    ["Company / handle", company], ["City", city], ["Trade", trade], ["Monthly budget", budget],
  ];
  const table = rows
    .map(([k, v]) =>
      `<tr><td style="padding:6px 14px 6px 0;color:#6F7C86;font:13px system-ui">${esc(k)}</td>` +
      `<td style="padding:6px 0;color:#101315;font:15px system-ui"><b>${esc(v)}</b></td></tr>`)
    .join("");

  const html =
    `<div style="font:15px/1.55 system-ui,-apple-system,sans-serif;color:#101315">` +
    `<p style="margin:0 0 4px;font-size:13px;color:#6F7C86">New enquiry from yoniverseproductions.com</p>` +
    `<h2 style="margin:0 0 16px;font-size:20px">${esc(company)} &middot; ${esc(city)}</h2>` +
    `<table style="border-collapse:collapse;margin-bottom:18px">${table}</table>` +
    (message
      ? `<p style="margin:0 0 6px;font-size:13px;color:#6F7C86">What they said</p>` +
        `<div style="white-space:pre-wrap;padding:14px;background:#F4F5F6;border-radius:8px">${esc(message)}</div>`
      : `<p style="color:#6F7C86">No message left.</p>`) +
    `<p style="margin-top:18px;font-size:13px;color:#6F7C86">Reply straight to this email and it goes to ${esc(name)}.</p>` +
    `</div>`;

  const text = rows.map(([k, v]) => k + ": " + v).join("\n") +
    (message ? "\n\nMessage:\n" + message : "");

  try {
    const r = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": key, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({
        sender: { name: FROM_NAME, email: TO },
        to: [{ email: TO }],
        // hitting reply in the inbox answers the client, not the website
        replyTo: { email, name },
        subject: `${company} (${city}) - ${trade} - ${budget}`,
        htmlContent: html,
        textContent: text,
      }),
    });

    if (!r.ok) {
      const detail = await r.text();
      console.error("Brevo rejected the send:", r.status, detail);
      return res.status(502).json({
        ok: false,
        error: "We could not send that. Please email " + TO + " directly.",
      });
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error("Send failed:", err);
    return res.status(502).json({
      ok: false,
      error: "We could not send that. Please email " + TO + " directly.",
    });
  }
}
