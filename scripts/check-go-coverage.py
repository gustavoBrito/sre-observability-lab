#!/usr/bin/env python3
"""Go coverage gate, statement-weighted, EXCLUDING the bootstrap file(s).

Why: bootstrap (cmd/../main.go) is servers/OTel wiring that no unit test
should fake-poke; the gate must reflect business logic. Docs:
docs/testing-policy.md.

Note: with `-coverpkg=./...` Go emits DUPLICATE rows in cover.out (each test
binary records every instrumented package, so blocks authored by other test
runs also appear with count 0). We therefore merge rows with max(count) per
unique location.

Usage: python3 check-go-coverage.py cover.out <threshold>
Exits 0 if weighted coverage meets the threshold, else exit 1 with report.
"""

import os
import sys


def main() -> int:
    profile = sys.argv[1] if len(sys.argv) > 1 else "cover.out"
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    excluded = {"main.go"} | set(sys.argv[3:])

    stmts: dict[str, int] = {}
    hit: dict[str, bool] = {}

    with open(profile, encoding="utf-8") as f:
        for line in f:
            if line.startswith("mode:"):
                continue
            location, _range, num, count = line.split()
            pkg = location.split(":")[0].rsplit(os.sep, 1)[-1].rsplit("/", 1)[-1]
            if pkg in excluded:
                continue
            n = int(num)
            current = stmts.get(location, 0)
            stmts[location] = max(current, n)
            if int(count) > 0:
                hit[location] = True

    covered = sum(stmts[loc] for loc in stmts if hit.get(loc))
    total = sum(stmts.values())

    if not total:
        print("FAIL: no executable statements found (were there any tests?)")
        return 1

    pct = 100.0 * covered / total
    print(f"Business-logic coverage (excluded: {', '.join(sorted(excluded))}): {pct:.2f}%")
    per_file: dict[str, list[int]] = {}
    for loc, n in stmts.items():
        f = loc.split(":")[0]
        per_file.setdefault(f, [0, 0])
        per_file[f][0] += n
        if hit.get(loc):
            per_file[f][1] += n
    for f in sorted(per_file):
        c, t = per_file[f]
        print(f"  {f:32s} {100.0 * c / t:7.2f}%  ({c}/{t} stmts)")

    if pct + 1e-9 < threshold:
        print(f"FAIL: {pct:.2f}% < {threshold:.0f}%")
        return 1
    print(f"OK: >= {threshold:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
