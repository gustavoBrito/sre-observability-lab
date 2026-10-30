/* Bootstrap only (see AGENTS.md): servers + ports. */

const { register } = require("./observability/metrics");
const http = require("http");
const { app } = require("./app");

const PORT_HTTP = Number(process.env.PORT_HTTP || 8000);
const PORT_METRICS = Number(process.env.PORT_METRICS || 9001);

if (require.main === module) {
  // Dedicated metrics port (kept out of RED latency math)
  const metricsServer = http.createServer(async (_req, res) => {
    res.writeHead(200, { "content-type": register.contentType });
    res.end(await register.metrics());
  });
  metricsServer.listen(PORT_METRICS, () => console.log(`metrics on :${PORT_METRICS}`));

  app.listen(PORT_HTTP, () => console.log(`bff listening on :${PORT_HTTP}`));
}

module.exports = { app };
