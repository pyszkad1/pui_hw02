#!/usr/bin/env python3
"""
Optimal A* planner using either hmax or lmcut as an admissible heuristic.
"""

import sys
import heapq
import math
from sas_parser import parse_sas, to_strips

def get_applicable(state, strips_ops):
    """
    Return operators applicable in the current state.
    
    Args:
        state: Set of atoms true in the current state
        strips_ops: List of STRIPS operators
        
    Returns:
        List of applicable operators
    """
    applicable = []
    for op in strips_ops:
        # An operator is applicable if all preconditions are satisfied
        if all(precond in state for precond in op['pre']):
            applicable.append(op)
    return applicable

def apply_operator(state, op):
    """
    Apply an operator to a state, returning a new state.
    
    Args:
        state: Set of atoms true in the current state
        op: STRIPS operator to apply
        
    Returns:
        New state after applying the operator
    """
    # Create a copy of the current state
    new_state = state.copy()
    
    # Remove deleted atoms
    for atom in op['del']:
        if atom in new_state:
            new_state.remove(atom)
    
    # Add new atoms
    for atom in op['add']:
        new_state.add(atom)
    
    return new_state

def check_goal(state, goal_atoms):
    """
    Check if the state satisfies all goal conditions.
    
    Args:
        state: Set of atoms true in the current state
        goal_atoms: List of atoms that must be true in the goal
        
    Returns:
        True if the state satisfies the goal, False otherwise
    """
    return all(atom in state for atom in goal_atoms)

def state_to_frozenset(state):
    """
    Convert a state (set of atoms) to a frozenset for hashing.
    
    Args:
        state: Set of atoms
        
    Returns:
        Frozenset representation of the state
    """
    return frozenset(state)

def astar(initial_state, goal_atoms, strips_ops, heuristic_fn):
    """
    A* search algorithm.
    
    Args:
        initial_state: Set of atoms true in the initial state
        goal_atoms: List of atoms that must be true in the goal
        strips_ops: List of STRIPS operators
        heuristic_fn: Function that takes a state and returns a heuristic value
        
    Returns:
        (plan, cost) tuple where plan is a list of operator names or None if no plan exists
    """
    # Create initial state as a set for efficient membership testing
    initial_state_set = set(initial_state)
    
    # Calculate initial heuristic value
    initial_h = heuristic_fn(initial_state_set)
    if initial_h == math.inf:
        return None, math.inf  # Goal unreachable from start
    
    # Initialize open list with (f, g, state, plan) tuples
    # f = g + h is the total estimated cost
    initial_state_frozen = state_to_frozenset(initial_state_set)
    open_list = [(initial_h, 0, initial_state_frozen, [])]
    heapq.heapify(open_list)
    
    # closed[state_frozen] = g value (cost so far)
    closed = {initial_state_frozen: 0}
    
    expanded = 0  # Count expanded nodes
    
    while open_list:
        f, g, current_state_frozen, plan = heapq.heappop(open_list)
        expanded += 1
        
        # Convert back to set for operations
        current_state = set(current_state_frozen)
        
        # Skip if we've found a better path to this state already
        if g > closed.get(current_state_frozen, math.inf):
            continue
        
        # Check if we've reached the goal
        if check_goal(current_state, goal_atoms):
            return plan, g
        
        # Find applicable operators
        applicable_ops = get_applicable(current_state, strips_ops)
        
        # Apply each operator and add resulting states to open list
        for op in applicable_ops:
            next_state = apply_operator(current_state, op)
            next_state_frozen = state_to_frozenset(next_state)
            
            # Calculate new cost
            new_g = g + op['cost']
            
            # Only expand if we found a better path
            if new_g < closed.get(next_state_frozen, math.inf):
                closed[next_state_frozen] = new_g
                
                # Calculate heuristic for new state
                h = heuristic_fn(next_state)
                if h == math.inf:
                    continue  # Skip states from which goal is unreachable
                
                # Update open list
                f_new = new_g + h
                new_plan = plan + [op['name']]
                heapq.heappush(open_list, (f_new, new_g, next_state_frozen, new_plan))
    
    # If we exit the loop without finding a plan, no plan exists
    return None, math.inf

def main():
    if len(sys.argv) != 3:  # planner.py <task>.sas {hmax|lmcut}
        print("Usage: python planner.py <task>.sas {hmax|lmcut}")
        sys.exit(1)
    
    sasfile, heu_name = sys.argv[1], sys.argv[2]
    
    if heu_name not in ("hmax", "lmcut"):
        print("Heuristic must be 'hmax' or 'lmcut'")
        sys.exit(1)
    
    # Parse SAS file and convert to STRIPS
    vars_, domains, init_state, goal_state, ops = parse_sas(sasfile)
    init_atoms, goal_atoms, strips_ops = to_strips(domains, init_state, goal_state, ops)
    
    # Define the heuristic function based on user input
    if heu_name == "hmax":
        from hmax import compute_hmax
        heuristic = lambda state: compute_hmax(state, goal_atoms, strips_ops)
    elif heu_name == "lmcut":
        from lmcut import compute_lmcut
        heuristic = lambda state: compute_lmcut(state, goal_atoms, strips_ops)
    else:
        print(f"Heuristic '{heu_name}' not supported.")
        sys.exit(1)
    
    # Run A* search
    plan, cost = astar(init_atoms, goal_atoms, strips_ops, heuristic)
    
    if plan is None:
        print("No plan found")
    else:
        for op_name in plan:
            print(op_name)
        print(f"Plan cost: {cost}")

if __name__ == "__main__":
    main()
