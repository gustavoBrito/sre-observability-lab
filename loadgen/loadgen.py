"""Background traffic generator.

Runs against the BFF to keep RED metrics and burn-rate alerts meaningful
without a real frontend hitting the stack.
"""

import logging
import random
import time
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("loadgen")

BFF_URL = "http://bff:8000"

while True:
    try:
        with urllib.request.urlopen(f"{BFF_URL}/api/orders", timeout=3) as r:
            log.info("orders status=%s", r.status)
    except Exception as e:  # noqa: BLE001
        log.warning("orders failed: %s", e)
    time.sleep(random.uniform(0.2, 0.8))
