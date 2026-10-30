#!/usr/bin/env python3
"""Go coverage gate, statement-weighted, EXCLUDING the bootstrap file(s).

Why: main.go is servers/OTel wiring that no unit test should fake-poke; the
gate must reflect business logic only. Docs: docs/testing-policy.md.

Usage: python3 check-go-coverage.py cover.out <threshold>
Exits 0 if weighted coverage meets the threshold, else exit 1 with report.
"""

import sys
from collections import Counter


def main() -> int:
    profile = sys.argv[1] if len(sys.argv) > 1 else "cover.out"
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    excluded = {"main.go"} | set(sys.argv[3:])

    covered = Counter()
    total = Counter()

    with open(profile, encoding="utf-8") as f:
        for line in f:
            if line.startswith("mode:"):
                continue
            location, _line_loc, stmts, count = line.split()
            pkg_file = location.split(":")[0].rsplit("/", 1)[-1]
            if pkg_file in excluded:
                continue
            n = int(stmts)
            total[pkg_file] += n
            if int(count) > 0:
                covered[pkg_file] += n

    if not total:
        print("WARNING: no executable statements found (were there any tests?)")
        return 1

    all_covered = sum(covered.values())
    all_total = sum(total.values())
    pct = 100.0 * all_covered / all_total
    print(f"Business-logic coverage (excluded: {', '.join(sorted(excluded))}): {pct:.2f}%")
    for pkg_file in sorted(total):
        p = 100.0 * covered[pkg_file] / total[pkg_file]
        print(f"  {pkg_file:24s} {p:6.2f}%  ({covered[pkg_file]}/{total[pkg_file]} stmts)")

    if pct + 1e-9 < threshold:
        print(f"FAIL: below required {threshold:.0f}%")
        print(f"FAIL: {pct:.2f}% < {threshold:.0f}%")
        return 1
    print(f"OK: >= {threshold:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
