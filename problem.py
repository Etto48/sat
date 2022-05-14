from __future__ import annotations
from ast import Import
try:
    from .literal import *
    from .clause import *
    from .logic_node import *
except ImportError:
    from literal import *
    from clause import *
    from logic_node import *

import random
import time
import os

class problem:
    try:
        from .algorithms.dpll import dpll_sat
        from .algorithms.cdcl import cdcl_sat
        from .algorithms.local import random_mapping
        from .algorithms.local import heuristic_mapping
        from .algorithms.local import walk_sat
        from .algorithms.local import g_sat
        from .algorithms.local import gw_sat
        from .algorithms.experimental.continuous_gradient import cg_sat
        from .algorithms.experimental.continuous_gradient import cg_sat_finalizer
    except ImportError:
        from algorithms.dpll import dpll_sat
        from algorithms.cdcl import cdcl_sat
        from algorithms.local import random_mapping
        from algorithms.local import heuristic_mapping
        from algorithms.local import walk_sat
        from algorithms.local import g_sat
        from algorithms.local import gw_sat
        from algorithms.experimental.continuous_gradient import cg_sat
        from algorithms.experimental.continuous_gradient import cg_sat_finalizer

    def __init__(self,clauses:list[clause]):
        self.score_cache = {}
        self.showup_cache = {}
        self.clauses = clauses
        self.added_clauses:list[clause] = []
        self.used_symbols:set[str] = set()
        for c in self.clauses:
            self.used_symbols = self.used_symbols.union(c.used_symbols)
        self.difficulty_score = len(self.clauses)/len(self.used_symbols)
        self.O = 2**len(self.used_symbols)
        self.size = len(self.used_symbols)
        self.solution:dict[str,bool]|None = None

    def add_clauses(self,clauses:list[clause]):
        self.score_cache = {}
        self.showup_cache = {}
        self.clauses += clauses
        self.added_clauses += clauses
        for c in self.clauses:
            self.used_symbols = self.used_symbols.union(c.used_symbols)
        self.difficulty_score = len(self.clauses)/len(self.used_symbols)
        self.O = 2**len(self.used_symbols)
        self.size = len(self.used_symbols)
        self.solution = None

    def remove_added_clauses(self):
        self.score_cache = {}
        self.showup_cache = {}
        for c in self.added_clauses:
            if c in self.clauses:
                self.clauses.remove(c)
        self.added_clauses = []
        for c in self.clauses:
            self.used_symbols = self.used_symbols.union(c.used_symbols)
        self.difficulty_score = len(self.clauses)/len(self.used_symbols)
        self.O = 2**len(self.used_symbols)
        self.size = len(self.used_symbols)
        self.solution = None

    def from_text(text:str) -> problem:
        current_literal_list = []
        clause_list = []
        is_negative = False
        literal_name = ""
        b_count = 0
        for c in text:
            if c=='(':
                b_count += 1
            elif c==')':
                b_count -= 1
            elif c==' ':
                pass
            elif c=='&':
                current_literal_list.append(literal(literal_name,is_negative))
                is_negative = False
                literal_name = ""
                clause_list.append(clause(current_literal_list))
                current_literal_list = []
            elif c=='|':
                current_literal_list.append(literal(literal_name,is_negative))
                is_negative = False
                literal_name = ""
            elif c=='~':
                is_negative = True
            else:
                literal_name+=c

            if b_count < 0:
                raise "Wrong braces"
            
        if b_count != 0:
            raise "Wrong braces"
        current_literal_list.append(literal(literal_name,is_negative))
        clause_list.append(clause(current_literal_list))
        return problem(clause_list)

    def from_complex_text(text:str) -> problem:
        return problem.from_text(logic_node.from_text(text).cnf())

    def from_file(path:str) -> problem:
        with open(path) as file:
            lines = file.readlines()
        clause_list = []
        literal_count = 0
        clause_count = 0
        for l in lines:
            if l[0] == 'c':
                pass
            elif l[0] == 'p':
                str_list = l.split()
                assert str_list[1] == "cnf"
                literal_count = int(str_list[2])
                clause_count = int(str_list[3])
            elif l[0] == '%':
                break
            else:
                str_list = l.split()
                assert str_list.pop()[0] == '0'
                int_list = [int(x) for x in str_list]
                literal_list = [literal("x"+str(abs(x)),x<0) for x in int_list]
                clause_list.append(clause(literal_list))
        ret = problem(clause_list)
        assert len(ret.used_symbols) == literal_count
        assert len(ret.clauses) == clause_count
        return ret

    def to_DIMACS(self) -> list[str]:
        symbol_numbers = {}
        for i,s in enumerate(self.used_symbols):
            symbol_numbers[s]=i+1
        ret = [f"p cnf {len(self.used_symbols)} {len(self.clauses)}"]
        for c in self.clauses:
            ret_line = ""
            for l in c.literals:
                ret_line += f"{symbol_numbers[l.name] * (-1 if l.negated else 1)} "
            ret_line += "0\n"
            ret.append(ret_line)
        return ret
    
    def __str__(self):
        ret = ""
        for i,c in enumerate(self.clauses):
            ret += '('
            for j,l in enumerate(c.literals):
                ret+= "~" if l.negated else ""
                ret+= l.name
                if j!=len(c.literals)-1:
                    ret+="|"
            ret += ')'
            if i!=len(self.clauses)-1:
                ret += '&'
        return ret

    def eval(self,mappings:dict[str,bool]) -> bool:
        for c in self.clauses:
            if not c.eval(mappings):
                return False
        return True

    def symbol_score(self,symbol:str) -> int:
        if symbol not in self.score_cache:
            ret = 0
            for c in self.clauses:
                ret += c.symbol_score(symbol)
            self.score_cache[symbol]=ret
            return ret
        else:
            return self.score_cache[symbol]

    def mapped_symbol_score(self,mappings:dict[str,bool],symbol: str) -> int:
        if symbol not in self.used_symbols:
            raise "Symbol not used"
        return -self.symbol_score(symbol) if mappings[symbol] else self.symbol_score(symbol)

    def mapped_symbol_sat_score(self,mappings:dict[str,bool],symbol:str) -> int:
        ret = 0
        clauses = self.sat_clauses(mappings)
        for c in clauses:
            ret += c.symbol_score(symbol)
        ret *= -1 if mappings[symbol] else self.symbol_score(symbol)
        return ret
            
    def mapped_symbol_unsat_score(self,mappings:dict[str,bool],symbol:str) -> int:
        ret = 0
        clauses = self.unsat_clauses(mappings)
        for c in clauses:
            ret += c.symbol_score(symbol)
        ret *= -1 if mappings[symbol] else self.symbol_score(symbol)
        return ret

    def symbol_showup_rate(self,symbol:str) -> int:
        if symbol not in self.showup_cache:
            ret = 0
            for c in self.clauses:
                if symbol in c.used_symbols:
                    ret += 1
            self.score_cache[symbol]=ret
            return ret
        else:
            return self.score_cache[symbol]

    def sat_clauses(self,mappings:dict[str,bool]) -> list[clause]:
        sat_list = []
        for c in self.clauses:
            if c.eval(mappings):
                sat_list.append(c)
        return sat_list

    def unsat_clauses(self,mappings:dict[str,bool]) -> list[clause]:
        unsat_list = []
        for c in self.clauses:
            if not c.eval(mappings):
                unsat_list.append(c)
        return unsat_list

    def pick_unsat_clause(self,mappings:dict[str,bool]) -> clause:
        return random.choice(self.unsat_clauses(mappings))

    def undefined_symbols(self,mappings:dict[str,bool]) -> list[str]:
        ret = []
        for s in self.used_symbols:
            if s not in mappings:
                ret.append(s)
        return ret 

    def clause_is_conflicting(self,c:clause,mappings:dict[str,bool]) -> bool:
        for s in c.used_symbols:
            if s not in mappings:
                return False
        return not c.eval(mappings)

    def clause_unit(self,c:clause,mappings:dict[str,bool]) -> str|None:
        """
        :return: None if clause is not unit, unit literal symbol if clause is unit
        """
        count = 0
        ret = None
        for s in c.used_symbols:
            if s not in mappings:
                count += 1
                if count > 1:
                    return None
                else:
                    ret = s
        return ret

    def unit_clauses(self,mappings:dict[str,bool]) -> list[clause]:
        ret = []
        for c in self.unsat_clauses(mappings):
            count = 0
            for l in c.literals:
                if l.name not in mappings:
                    count += 1
            if count == 1:
                ret.append(c)
        return ret
    
    def pure_literals(self,mappings:dict[str,bool]) -> list[literal]:
        ret = []
        for s in self.used_symbols:
            if s not in mappings:
                scores = []
                for c in self.unsat_clauses(mappings):
                    if s in c.used_symbols:
                        scores.append(c.symbol_score(s))
                set_scores = set(scores)
                if len(set_scores) == 1:
                    ret.append(literal(s,scores[0]<0))
        return ret

    