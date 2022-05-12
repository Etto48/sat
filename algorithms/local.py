from __future__ import annotations
import random
import time
try:
    from ..problem import *
except ImportError:
    pass

def random_mapping(self:problem,used_symbols:list[str]) -> dict[str,bool]:
    ret = {}
    for s in used_symbols:
        ret[s] = (random.randint(0,1) == 1)
    return ret

def heuristic_mapping(self:problem,used_symbols:list[str]) -> dict[str,bool]:
    ret = {}
    for s in self.used_symbols:
        score = self.symbol_score(s)
        if score != 0 and random.choice([True,False]):
            ret[s] = True if score > 0 else False
        else:
            ret[s] = random.choice([True,False])
    return ret

def walk_sat(self:problem, time_limit: int = 0, limit: int = -1) -> bool:
    start_time = time.time()

    def optimize_step(mappings: dict[str, bool]):
        symbols = list(self.pick_unsat_clause(mappings).used_symbols)
        symbols.sort(key=lambda s: self.mapped_symbol_sat_score(mappings, s), reverse=True)
        choice = symbols[0]
        mappings[choice] = not mappings[choice]

    def random_step(mappings: dict[str, bool]):
        choice = random.choice(list(self.used_symbols))
        mappings[choice] = not mappings[choice]

    mappings = self.heuristic_mapping(self.used_symbols)

    flips = 0
    max_sat = 0
    while(time_limit == 0 or start_time+time_limit >= time.time()):
        current_sat = len(self.sat_clauses(mappings))
        max_sat = max(current_sat,max_sat)

        #print(f"Max: {max_sat}/{len(self.clauses)} Current: {current_sat}  ",end="\r")
        
        if self.eval(mappings):
            return True
        if flips == limit:
            return False

        

        if random.randint(0, 1) == 1:
            optimize_step(mappings)
        else:
            random_step(mappings)
        flips += 1
    return False

def g_sat(self:problem, time_limit: int = 0,limit:int = -1) -> bool:
    start_time = time.time()
    def optimize_step(mappings: dict[str, bool]):
        symbols = list(self.used_symbols)
        symbols.sort(key=lambda s : self.mapped_symbol_score(mappings, s), reverse=True)
        choice = self.used_symbols[0]
        mappings[choice] = not mappings[choice]
    def random_step(mappings: dict[str, bool]):
        choice = random.choice(list(self.used_symbols))
        mappings[choice] = not mappings[choice]

    mappings = self.heuristic_mapping(self.used_symbols)

    flips = 0
    while(time_limit == 0 or start_time+time_limit >= time.time()):
        if self.eval(mappings):
            return True
        if flips == limit:
            return False

        if random.randint(0, 1) == 1:
            optimize_step(mappings)
        else:
            random_step(mappings)
        flips += 1
    return False

def gw_sat(self:problem, time_limit: int = 0, local_max_limit:int = 10) -> bool:
    start_time = time.time()
    def optimize_step(mappings: dict[str, bool]):
        symbols = list(self.pick_unsat_clause(mappings).used_symbols)
        symbols.sort(key=lambda s : self.mapped_symbol_score(mappings, s), reverse=True)
        choice = symbols[0]
        mappings[choice] = not mappings[choice]
    def random_step(mappings: dict[str, bool]):
        choice = random.choice(list(self.used_symbols))
        mappings[choice] = not mappings[choice]
    
    mappings = self.heuristic_mapping(self.used_symbols)
    new_max_found_at = time.time()
    max_sat_clauses = 0
    while(time_limit == 0 or start_time+time_limit >= time.time()):
        current_sat_clauses = len(self.sat_clauses(mappings))
        #print(f"Max: {max_sat_clauses}/{len(self.clauses)} Current: {current_sat_clauses}  ",end="\r")
        if self.eval(mappings):
            return True
        if current_sat_clauses > max_sat_clauses:
            new_max_found_at = time.time()
            max_sat_clauses = max(current_sat_clauses,max_sat_clauses)
        
        if time.time() - new_max_found_at > local_max_limit:
            #print(f"Restart {max_sat_clauses}/{len(self.clauses)}              ")
            new_max_found_at = time.time()
            max_sat_clauses = 0
            mappings = self.heuristic_mapping(self.used_symbols)
        else:
            if random.randint(0, 1) == 1:
                optimize_step(mappings)
            else:
                random_step(mappings)
        
    return False
