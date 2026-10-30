/* Use case: build an order quote. Aggregation + upstream error mapping live
 * here; HTTP code mapping lives in routes. No express in this file. */

const pricingClient = require("./pricingClient");
const { toOrderResponse } = require("../models/order");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const sleepFor = Number(process.env.BFF_WORK_MS_MIN ?? 40); // simulated overhead

module.exports = {
  /** @returns {{order_id, price}} or throws {code: "UPSTREAM"|"UPSTREAM_TIMEOUT"} */
  async getQuote() {
    await sleep(sleepFor + Math.random() * 80); // BFF processing overhead

    let res;
    try {
      res = await pricingClient.getPrice();
    } catch (err) {
      if (err.status === undefined) {
        // connection refused / timeout - "bad gateway" semantics
        const e = new Error(JSON.stringify(err.message ?? err));
        e.code = "UPSTREAM_TIMEOUT";
        throw e;
      }
      const e = new Error(`upstream ${err.status}`);
      e.code = "UPSTREAM";
      e.upstreamStatus = err.status;
      throw e;
    }

    let price;
    try {
      price = JSON.parse(res.body);
    } catch {
      throw Object.assign(new Error("malformed upstream payload"), { code: "UPSTREAM" });
    }

    return toOrderResponse({ price });
  },
};
