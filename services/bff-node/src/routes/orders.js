/* Interface adapters (thin): status codes come from typed service errors. */

const express = require("express");
const ordersService = require("../services/orders");

const router = express.Router();

router.get("/api/orders", async (req, res) => {
  try {
    const order = await ordersService.getQuote();
    res.status(200).json(order);
  } catch (err) {
    switch (err.code) {
      case "UPSTREAM_TIMEOUT":
        res.status(502).json({ error: "upstream_failure" });
        break;
      case "UPSTREAM":
      default:
        res.status(500).json({ error: "upstream_failure" });
    }
  }
});

router.get("/healthz", (_req, res) => {
  res.status(200).json({ status: "ok" });
});

module.exports = router;
