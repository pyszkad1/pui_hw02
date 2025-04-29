# sas_parser.py

import sys

class SASParser:
    def __init__(self, filename):
        self.filename = filename
        self.vars = []         # list of (var_id, domain_size)
        self.init = []         # list of initial values per var
        self.goal = []         # list of (var_id, value) goals
        self.ops = []          # list of Operator instances

    def parse(self):
        # open self.filename, read sections, fill self.vars, self.init, self.goal, self.ops
        # ignore delete effects
        pass

class Operator:
    def __init__(self, name, preconditions, add_effects, cost=1):
        self.name = name
        self.pre = preconditions       # list of (var_id, value)
        self.add = add_effects         # list of (var_id, value)
        self.cost = cost               # assume 1 unless SAS encodes otherwise
