#!/usr/bin/env python3
"""
Compute the LM-Cut heuristic value for the initial state of a SAS file,
with deterministic tie-breaking in the justification graph.
"""

import sys
import math
import copy
from collections import defaultdict
from sas_parser import parse_sas, to_strips

def compute_hmax_values(init_atoms, goal_atoms, strips_ops, artificial_goal=None):
    """
    Compute h^max values for all facts.
    
    In the delete-relaxation, we ignore delete effects and assume facts
    once achieved remain true.
    """
    # Initialize h-values
    h_values = {}
    
    # Set initial atoms to 0
    for atom in init_atoms:
        h_values[atom] = 0
    
    # Add artificial goal if provided
    if artificial_goal:
        h_values[artificial_goal] = math.inf
    
    # Fixed-point computation for h^max
    changed = True
    while changed:
        changed = False
        for op in strips_ops:
            # Skip operators with unreachable preconditions
            max_pre_h = 0
            achievable = True
            
            for precond in op['pre']:
                if precond not in h_values:
                    h_values[precond] = math.inf
                    achievable = False
                    break
                
                if h_values[precond] == math.inf:
                    achievable = False
                    break
                
                max_pre_h = max(max_pre_h, h_values[precond])
            
            if not achievable:
                continue
            
            # Compute new h-value for effects
            new_h = max_pre_h + op['cost']
            
            # Update h-values for add effects (delete effects ignored in relaxation)
            for add_effect in op['add']:
                if add_effect not in h_values:
                    h_values[add_effect] = new_h
                    changed = True
                elif new_h < h_values[add_effect]:
                    h_values[add_effect] = new_h
                    changed = True
    
    return h_values

def find_landmarks(init_atoms, goal_atoms, strips_ops):
    """
    Compute disjunctive action landmarks using LM-Cut technique.
    """
    if not goal_atoms:
        return 0  # No goals, h=0
    
    # Total heuristic value
    total_h = 0
    
    # Create copies of operators to modify their costs
    ops_copy = copy.deepcopy(strips_ops)
    
    # Create artificial goal fact and goal operator
    artificial_goal = "ARTIFICIAL-GOAL"
    goal_op = {
        'name': "achieve-goal",
        'pre': goal_atoms.copy(),
        'add': [artificial_goal],
        'del': [],
        'cost': 0
    }
    ops_copy.append(goal_op)
    
    # Main loop for LM-Cut
    while True:
        # Step 1: Compute h^max values
        h_values = compute_hmax_values(init_atoms, goal_atoms, ops_copy, artificial_goal)
        
        # Check if goal is reachable
        if artificial_goal not in h_values or h_values[artificial_goal] == math.inf:
            break  # Goal unreachable, no more landmarks
        
        # Check if goal already achieved
        if h_values[artificial_goal] == 0:
            break  # Goal reached with zero cost
        
        # Step 2: Build justification graph
        # For each fact, find operators that achieve it
        achievers = defaultdict(list)  # atom -> list of operators
        
        # For each operator, find its critical parent (precondition with max h-value)
        critical_parents = {}  # op_name -> (precond, h_value)
        
        for op in ops_copy:
            if op['cost'] <= 0:
                continue  # Skip zero-cost operators for landmarks
            
            # Find critical parent (precondition with highest h-value)
            max_pre_h = -1
            critical_pre = None
            
            for precond in op['pre']:
                if precond not in h_values:
                    continue
                pre_h = h_values.get(precond, math.inf)
                
                if pre_h == math.inf:
                    continue  # Skip unreachable preconditions
                
                # Use deterministic tie-breaking if h-values are equal
                if critical_pre is None or pre_h > max_pre_h or (pre_h == max_pre_h and precond > critical_pre):
                    max_pre_h = pre_h
                    critical_pre = precond
            
            if critical_pre is not None:
                critical_parents[op['name']] = (critical_pre, max_pre_h)
                
                # For each add effect, check if this operator achieves it optimally
                for add_effect in op['add']:
                    if add_effect not in h_values:
                        continue
                    
                    add_h = h_values[add_effect]
                    # Check if operator achieves fact with correct cost (h(add) = h(pre) + cost)
                    if abs(add_h - (max_pre_h + op['cost'])) < 1e-6:
                        achievers[add_effect].append((op['name'], critical_pre))
        
        # Step 3: Find cut
        # Start from goal and follow justification graph backwards
        # Build goal zone and precondition zone
        goal_zone = {artificial_goal}
        precondition_zone = set()
        
        # Add goal operator's preconditions to precondition zone
        for precond in goal_op['pre']:
            if h_values.get(precond, math.inf) > 0:  # Only if not in initial state
                precondition_zone.add(precond)
        
        # Expand zones until fixpoint
        while precondition_zone:
            next_precondition_zone = set()
            
            for atom in precondition_zone:
                for op_name, critical_pre in achievers.get(atom, []):
                    if critical_pre and h_values.get(critical_pre, math.inf) > 0:
                        if critical_pre not in goal_zone:
                            next_precondition_zone.add(critical_pre)
            
            goal_zone.update(precondition_zone)
            precondition_zone = next_precondition_zone
        
        # Find cut operators
        cut_ops = []
        
        for atom in goal_zone:
            for op_name, critical_pre in achievers.get(atom, []):
                if critical_pre not in goal_zone:
                    # Find the operator object by name
                    for op in ops_copy:
                        if op['name'] == op_name:
                            cut_ops.append(op)
                            break
        
        if not cut_ops:
            break  # No valid cut found, done
        
        # Use minimum cost of cut operators as landmark cost
        min_cost = min((op['cost'] for op in cut_ops), default=0)
        
        if min_cost <= 0:
            break  # Zero-cost cut, we're done
        
        # Add landmark cost to heuristic
        total_h += min_cost
        
        # Reduce costs of cut operators
        for op in cut_ops:
            op['cost'] -= min_cost
    
    return total_h

def compute_lmcut(init_atoms, goal_atoms, strips_ops):
    """Compute LM-Cut heuristic for a state."""
    return find_landmarks(init_atoms, goal_atoms, strips_ops)

def main():
    if len(sys.argv) != 2:
        print("Usage: python lmcut.py <task>.sas")
        sys.exit(1)
    
    # Use the new parser functions
    vars_, domains, init_state, goal_state, ops = parse_sas(sys.argv[1])
    init_atoms, goal_atoms, strips_ops = to_strips(domains, init_state, goal_state, ops)
    
    h = compute_lmcut(init_atoms, goal_atoms, strips_ops)
    print(h)

if __name__ == "__main__":
    main()
