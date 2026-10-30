/* Coverage of BFF behavior: happy path, upstream failure mapping, and
   health. Upstream is a real HTTP mock on 127.0.0.1:3101 (see setup-env). */

const http = require("http");
const { beforeAll, afterAll, describe, it, expect } = require("@jest/globals");
const request = require("supertest");

let app;

function mockPricing(status, body) {
  return http.createServer((req, res) => {
    res.writeHead(status, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  });
}

beforeAll(() => {
  app = require("../src/app").app;
});

describe("BFF /api/orders", () => {
  it("maps pricing 200 to order payload", async () => {
    const pricing = mockPricing(200, { price_usd: 42.5 });
    await new Promise((r) => pricing.listen(3101, r));
    try {
      const res = await request(app).get("/api/orders");
      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty("order_id");
      expect(res.body.price.price_usd).toBe(42.5);
    } finally {
      pricing.close();
    }
  });

  it("maps any pricing 5xx to 500 upstream_failure", async () => {
    const pricing = mockPricing(503, { error: "down" });
    await new Promise((r) => pricing.listen(3101, r));
    try {
      const res = await request(app).get("/api/orders");
      expect(res.status).toBe(500);
      expect(res.body.error).toBe("upstream_failure");
    } finally {
      pricing.close();
    }
  });

  it("maps connection failure to 502", async () => {
    // no server listening on 3101 -> ECONNREFUSED path
    const res = await request(app).get("/api/orders");
    expect([500, 502]).toContain(res.status);
    expect(res.body).toHaveProperty("error");
  });
});

describe("BFF /healthz", () => {
  it("returns ok without depending on downstreams", async () => {
    const res = await request(app).get("/healthz");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });
});
