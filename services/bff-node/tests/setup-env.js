/* Freezes the pricing dependency URL for the BFF's outbound http calls. */
process.env.PRICING_URL =
  process.env.PRICING_URL || "http://127.0.0.1:3101";
process.env.PORT_HTTP = "8099";
process.env.PORT_METRICS = "9099";
