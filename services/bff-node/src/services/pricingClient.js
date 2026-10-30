/* Interface to pricing. All outbound HTTP + timeouts live here so
 * instrumentation and deadline policy have a single place to change.
 * Tracing propagation comes from the OTel auto-instrumentation (never manual). */

const http = require("http");

const PRICING_URL = () => process.env.PRICING_URL || "http://pricing:8002";
const TIMEOUT_MS = Number(process.env.UPSTREAM_TIMEOUT_MS || 3000);

/** GET wrapper: resolves {status, body}; rejects with {status, body} on
 * upstream 4xx/5xx and {status: undefined} on network failure/timeout. */
function get(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        const result = { status: res.statusCode, body };
        if (res.statusCode >= 400) reject(result);
        else resolve(result);
      });
    });
    req.on("error", reject);
    req.setTimeout(TIMEOUT_MS, () => req.destroy(new Error("upstream timeout")));
  });
}

module.exports = {
  getPrice: async () => get(`${PRICING_URL()}/price?sku=SKU-42`),
};
