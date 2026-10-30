/* Outward API shape - what the client sees. Mapping function (no class). */

function toOrderResponse({ price }) {
  if (!price || typeof price !== "object") return { order_id: "ord-" + Date.now(), price: {} };
  return {
    order_id: "ord-" + Date.now(),
    price,
  };
}

module.exports = { toOrderResponse };
