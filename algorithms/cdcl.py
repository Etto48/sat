from __future__ import annotations
import random
import sys
import os
import time
try:
    from ..literal import *
    from ..clause import *
    from ..problem import *
except ImportError:
    sys.path.append(os.path.abspath('..'))
    from literal import *
    from clause import *
    from problem import *

class history:
    def __init__(self):
        self.branching:dict[int,str] = {} #level -> branched var
        self.propagate:dict[int,list[str]] = {} #level -> list of propagated vars
    
    def assign_history(self,level:int) -> list[str]: #level -> [brancing,propagate[0],...,propagate[n]]
        return [self.branching[level]]+self.propagate[level]

    def next_recent_assigned(self,level:int,literals:set[literal]) -> literal|None:
        for s in reversed(self.assign_history(level)):
            for l in literals:
                if s == l.name:
                    return l
        return None

    def delete_level(self,level:int):
        del self.branching[level]
        del self.propagate[level]

class dependency_node:
    def __init__(self,name:str):
        self.name:str = name
        self.level:int = -1
        self.value:bool|None = None
        self.parents:set[dependency_node] = set()
        self.children:set[dependency_node] = set()
        self.clause:clause|None = None
    def reset(self):
        self.level = -1
        self.value = None
        self.parents = set()
        self.children = set()
        self.clause = None
    def __str__(self):
        return str({"name":self.name,"level":self.level,"value":self.value,"parents":self.parents,"children":self.children,"clause":self.clause})

class dependency_graph:
    def __init__(self,symbols:list[str]):
        self.nodes:dict[str,dependency_node] = dict((s,dependency_node(s)) for s in symbols)

    def update(self,symbol:str,mappings:dict[str,bool],decision_level:int,clause:clause|None=None):
        node = self.nodes[symbol]
        node.value = mappings[symbol]
        node.level = decision_level
        if clause is not None:
            for s in clause.used_symbols:
                if s != symbol:
                    node.parents.add(self.nodes[s])
                    self.nodes[s].children.add(node)
            node.clause = clause

    def reset(self,symbol:str):
        self.nodes[symbol].reset()

    def __str__(self):
        return str([str(v) for k,v in self.nodes.items()])


def cdcl_sat(self:problem,time_limit:int = 0) -> bool|None:
    start_time = time.time()
    
    branching_symbols:set[str] = set()
    hist = history()
    dgraph = dependency_graph(self.used_symbols)
    mappings = {}
    decision_level = 0
    

    def unit_propagation(mappings:dict[str,bool]) -> clause|None:
        """
        A unit clause has all of its literals but 1 assigned to 0. Then, the sole
        unassigned literal must be assigned to value 1. Unit propagation is the
        process of iteratively applying the unit clause rule.
        :return: None if no conflict is detected, else return the clause
        """
        while True:
            propagation_queue:list[tuple[str,clause]] = list()
            for c in self.clauses:
                if not c.eval(mappings):
                    s = self.clause_unit(c,mappings)
                    if s is not None:
                        propagation_pair = (s,c)
                        if propagation_pair not in propagation_queue:
                            propagation_queue.append(propagation_pair)
                    elif self.clause_is_conflicting(c,mappings):
                        return c
                    else:
                        pass
            if len(propagation_queue) == 0:
                return None
            
            for symbol,c in propagation_queue:
                value = c.unit_value(symbol)
                mappings[symbol] = value
                dgraph.update(symbol,mappings,decision_level,c)
                try:
                    hist.propagate[decision_level].append(symbol)
                except KeyError:
                    pass #propagation at level 0 for some reasons that I can't understand fucks badly with python

    def conflict_analyze(c:clause) -> tuple[int,clause]:
        if decision_level == 0:
            return -1, None
        
        ###
        curr_level_assign = [dgraph.nodes[s] for s in self.used_symbols if dgraph.nodes[s].level == decision_level]
        curr_level_len = len(curr_level_assign)

        if curr_level_len == 1:
            pass
        ###

        current_level_lits:set[literal] = set()
        prev_level_lits:set[literal] = set()
        done_lits:set[literal] = set()

        pool_lits = c.literals

        while True:
            for l in pool_lits:
                if dgraph.nodes[l.name].level == decision_level:
                    current_level_lits.add(l)
                else:
                    prev_level_lits.add(l)
            
            if len(current_level_lits) == 1:
                break

            last_assigned_lit = hist.next_recent_assigned(decision_level,current_level_lits)

            done_lits.add(last_assigned_lit)

            current_level_lits.remove(last_assigned_lit)

            pool_clause = dgraph.nodes[last_assigned_lit.name].clause
            pool_lits = [l for l in pool_clause.literals if l not in done_lits] if pool_clause is not None else []

        learnt = clause([l for l in current_level_lits.union(prev_level_lits)])
        if len(prev_level_lits) != 0:
            level = max([dgraph.nodes[l.name].level for l in prev_level_lits])
        else:
            level = decision_level - 1
        
        return level, learnt

    def backtrack(level:int,mappings:dict[str,bool]):
        for var, node in dgraph.nodes.items():
            if node.level <= level:
                node.children = set([child for child in node.children if child.level <= level])
            else:
                node.reset()
                del mappings[node.name]
        
        branching_symbols = set([s for s in self.used_symbols if s in mappings and len(dgraph.nodes[s].parents)==0])

        levels = list(hist.propagate.keys())

        for k in levels:
            if k <= level:
                continue
            hist.delete_level(k)
    
    def best_symbol_value(symbol:str) -> bool:        
        #if symbol in best_mappings:
        #    return best_mappings[symbol] > 0.5
        #else:
        score = self.symbol_score(symbol)
        return score > 0


    def pick_branching_symbol(mappings:dict[str,bool]) -> tuple[str,bool]:
        unmapped_symbols = list(self.used_symbols.difference(mappings.keys()))
        unmapped_symbols.sort(key=lambda s: abs(self.symbol_score(s)),reverse=True)

        return unmapped_symbols[0], best_symbol_value(unmapped_symbols[0])

    sat_len = 0
    while time_limit == 0 or time.time() - start_time < time_limit:
        sat_len = max(len(self.sat_clauses(mappings)),sat_len)
        print(f"+{len(self.added_clauses)} {sat_len}/{len(self.clauses)} {sat_len*100/len(self.clauses):0.02f}%   ",end='\r')
        conflicting_clause = unit_propagation(mappings)
        if conflicting_clause is not None:
            level, learnt = conflict_analyze(conflicting_clause)
            if level < 0:
                return False
            self.add_clauses([learnt])
            backtrack(level,mappings)
            decision_level = level
        elif len(mappings) == len(self.used_symbols):
            assert self.eval(mappings)
            self.solution = mappings
            return True
        else:
            decision_level += 1
            symbol, value = pick_branching_symbol(mappings)
            mappings[symbol] = value
            branching_symbols.add(symbol)
            hist.branching[decision_level] = symbol
            hist.propagate[decision_level] = []
            dgraph.update(symbol,mappings,decision_level)
    return None




