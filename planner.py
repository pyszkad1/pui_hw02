#!/usr/bin/env python3
"""
Optimal A* planner using either hmax or lmcut as an admissible heuristic.
"""

import sys
import heapq
from sas_parser import SASParser

def get_applicable(state, ops):
    # Efficiently return list of ops whose pre ⊆ state.
    # TODO: you can build an index (e.g. precondition tree) for speed.
    return [o for o in ops if all(state[v] == val for (v, val) in o.pre)]

def astar(initial_state, goal, ops, heuristic_fn):
    # A* search: open list is a heap of (f = g + h, g, state, plan)
    # Keep a closed dict mapping state → best g.
    pass

def main():
    if len(sys.argv) != 4 or sys.argv[2] not in ("hmax", "lmcut"):
        print("Usage: python planner.py <task>.sas {hmax|lmcut}")
        sys.exit(1)
    sasfile, heu = sys.argv[1], sys.argv[2]
    parser = SASParser(sasfile)
    parser.parse()
    if heu == "hmax":
        from hmax import compute_hmax as heuristic
    else:
        from lmcut import compute_lmcut as heuristic

    plan, cost = astar(parser.init, parser.goal, parser.ops,
                       lambda s: heuristic(parser.vars, s, parser.goal, parser.ops))
    if plan is None:
        print("No plan found")
    else:
        for op_name in plan:
            print(op_name)
        print(f"Plan cost: {cost}")

if __name__ == "__main__":
    main()
