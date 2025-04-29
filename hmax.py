#!/usr/bin/env python3
"""
Compute the Hₘₐₓ heuristic value for the initial state of a SAS file.
"""

import sys
from sas_parser import SASParser

def compute_hmax(vars, init, goal, ops):
    # Initialize h-values: for each fact f, h(f) = 0 if f ∈ init else ∞
    # Then repeatedly, for any operator o and any add-effect e ∈ o.add:
    #    h(e) = min( h(e), max_{p ∈ o.pre} h(p) + o.cost )
    # Iterate until fixpoint. Finally return max_{g ∈ goal} h(g).
    #
    # Use a simple worklist or Bellman–Ford style relaxation.
    pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python hmax.py <task>.sas")
        sys.exit(1)
    parser = SASParser(sys.argv[1])
    parser.parse()
    h = compute_hmax(parser.vars, parser.init, parser.goal, parser.ops)
    print(h)

if __name__ == "__main__":
    main()
