/* App factory (edge assembly). Exported for tests; server only listens from
 * src/index.js — jest imports this module safely. */

const express = require("express");
const { redMiddleware } = require("./observability/metrics");
const ordersRouter = require("./routes/orders");

const app = express();
app.disable("x-powered-by");

app.use(redMiddleware);
app.use(ordersRouter);

module.exports = { app };
