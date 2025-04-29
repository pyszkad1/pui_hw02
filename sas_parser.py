import sys
import argparse


def parse_sas(filename):
    variables = []
    var_domains = []
    initial_state = []
    goal_state = []
    operators = []

    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip()]

    idx = 0
    # First, collect variable definitions
    while idx < len(lines):
        if lines[idx] == 'begin_variable':
            var_name = lines[idx + 1]
            domain_size = int(lines[idx + 3])
            domain = lines[idx + 4 : idx + 4 + domain_size]
            variables.append(var_name)
            var_domains.append(domain)
            idx = idx + 4 + domain_size + 1  # skip past end_variable
        elif lines[idx] == 'begin_state':
            idx += 1
            for _ in range(len(variables)):
                initial_state.append(int(lines[idx])); idx += 1
        elif lines[idx] == 'begin_goal':
            idx += 1
            goal_count = int(lines[idx]); idx += 1
            for _ in range(goal_count):
                var_idx, val_idx = map(int, lines[idx].split())
                goal_state.append((var_idx, val_idx))
                idx += 1
        elif lines[idx] == 'begin_operator':
            idx += 1
            op = { 'prevails': [], 'effects': [] }
            op['name'] = lines[idx]; idx += 1
            prev_n = int(lines[idx]); idx += 1
            for _ in range(prev_n):
                var_idx, val_idx = map(int, lines[idx].split())
                op['prevails'].append((var_idx, val_idx)); idx += 1
            eff_n = int(lines[idx]); idx += 1
            for _ in range(eff_n):
                parts = list(map(int, lines[idx].split()))
                # SAS effect: [flag, var_idx, old_val, new_val]
                _, var_idx, old_val, new_val = parts
                op['effects'].append((var_idx, old_val, new_val))
                idx += 1
            op['cost'] = int(lines[idx]); idx += 1
            assert lines[idx] == 'end_operator'
            idx += 1
            operators.append(op)
        else:
            idx += 1

    return variables, var_domains, initial_state, goal_state, operators


def to_strips(var_domains, initial_state, goal_state, operators):
    # Helper to strip 'Atom ' or 'NegatedAtom '
    def strip_atom(atom):
        return atom.replace('Atom ', '').replace('NegatedAtom ', '').strip()

    # Build atom mapping
    atom_map = {}
    for i, domain in enumerate(var_domains):
        for j, atom in enumerate(domain):
            atom_map[(i, j)] = strip_atom(atom)

    # Build initial facts
    init_atoms = []
    for i, val in enumerate(initial_state):
        atom = var_domains[i][val]
        if atom.startswith('Atom'):
            init_atoms.append(strip_atom(atom))

    # Build goal facts
    goal_atoms = [ strip_atom(var_domains[i][j]) for (i, j) in goal_state ]

    # Convert operators
    strips_ops = []
    for op in operators:
        preconds = []
        # prevail conditions
        for var, val in op['prevails']:
            preconds.append(atom_map[(var, val)])
        # effect preconditions
        for var, old, new in op['effects']:
            if old >= 0:
                preconds.append(atom_map[(var, old)])
        adds, dels = [], []
        for var, old, new in op['effects']:
            if new >= 0:
                adds.append(atom_map[(var, new)])
            if old >= 0:
                dels.append(atom_map[(var, old)])
        strips_ops.append({
            'name': op['name'],
            'pre': sorted(set(preconds)),
            'add': sorted(set(adds)),
            'del': sorted(set(dels)),
            'cost': op['cost']
        })

    return init_atoms, goal_atoms, strips_ops


def main():
    parser = argparse.ArgumentParser(description='Convert SAS (FDR) to STRIPS')
    parser.add_argument('input', help='Input .sas file')
    args = parser.parse_args()

    vars_, domains, init, goal, ops = parse_sas(args.input)
    init_atoms, goal_atoms, strips_ops = to_strips(domains, init, goal, ops)

    # Print a simple STRIPS-like representation
    print('# Initial State')
    for atom in init_atoms:
        print(atom)
    print('\n# Goal State')
    for atom in goal_atoms:
        print(atom)
    print('\n# Operators')
    for op in strips_ops:
        print(f"Action: {op['name']}")
        print('  Pre:', ', '.join(op['pre']))
        print('  Add:', ', '.join(op['add']))
        print('  Del:', ', '.join(op['del']))
        print('  Cost:', op['cost'], '\n')

if __name__ == '__main__':
    main()