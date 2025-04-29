#!/usr/bin/env python3
"""
Compute the Hₘₐₓ heuristic value for the initial state of a SAS file.
"""

import sys
import math
from sas_parser import parse_sas, to_strips

def compute_hmax(init_atoms, goal_atoms, strips_ops):
    """
    Compute the h_max heuristic value for a given state.
    
    In the delete-relaxation, we ignore delete effects and assume facts
    once achieved remain true. This makes h_max admissible.
    
    Args:
        init_atoms: List of atoms true in the initial state
        goal_atoms: List of atoms that must be true in the goal state
        strips_ops: List of operators in STRIPS format (dictionaries with name, pre, add, del, cost)
        
    Returns:
        The h_max value (max over all goal facts)
    """
    # Initialize h-values: h(fact) = 0 if fact is in initial state, else infinity
    h_values = {}
    
    # Set initial state atoms to 0, all others to infinity
    for atom in init_atoms:
        h_values[atom] = 0
    
    # Bellman-Ford style relaxation until fixpoint
    changed = True
    iteration = 0
    
    while changed:
        iteration += 1
        changed = False
        
        for op in strips_ops:
            # Check if all preconditions are reachable
            max_pre_h = 0
            all_preconditions_reachable = True
            
            for precond in op['pre']:
                if precond not in h_values:
                    h_values[precond] = math.inf  # Initialize if not seen before
                
                if h_values[precond] == math.inf:
                    all_preconditions_reachable = False
                    break
                max_pre_h = max(max_pre_h, h_values[precond])
            
            if not all_preconditions_reachable:
                continue
            
            # Operator is applicable, compute new h-value for its effects
            new_h = max_pre_h + op['cost']
            
            # Update add effects (delete effects are ignored in h_max)
            for add_atom in op['add']:
                if add_atom not in h_values:
                    h_values[add_atom] = new_h
                    changed = True
                elif new_h < h_values[add_atom]:
                    h_values[add_atom] = new_h
                    changed = True
    
    # Check if all goal atoms are reachable
    max_goal_h = 0
    for goal_atom in goal_atoms:
        if goal_atom not in h_values:
            h_values[goal_atom] = math.inf
        
        if h_values[goal_atom] == math.inf:
            return math.inf  # Goal unreachable
        
        max_goal_h = max(max_goal_h, h_values[goal_atom])
    
    return max_goal_h

def main():
    if len(sys.argv) != 2:
        print("Usage: python hmax.py <task>.sas")
        sys.exit(1)
    
    # Use the new parser functions
    vars_, domains, init_state, goal_state, ops = parse_sas(sys.argv[1])
    init_atoms, goal_atoms, strips_ops = to_strips(domains, init_state, goal_state, ops)
    
    h = compute_hmax(init_atoms, goal_atoms, strips_ops)
    print(h)

if __name__ == "__main__":
    main()
