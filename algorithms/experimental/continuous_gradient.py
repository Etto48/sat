from __future__ import annotations
from cmath import sqrt

from scipy.misc import derivative
import random
import time
import math

try:
    from ...problem import *
    from ...clause import *
except ImportError:
    pass

def cg_sat_finalizer(self:problem,time_limit:int = 0,mappings:dict[str,bool]={}) -> bool:
    start_time = time.time()
    def score(mappings: dict[str,bool],symbol:str) -> int:
        mappings[symbol] = not mappings[symbol]
        sc = len(self.sat_clauses(mappings))
        mappings[symbol] = not mappings[symbol]
        return sc

    def best_symbol(symbols:list[str],mappings: dict[str,bool]) -> str:
        best_symbol = None
        best_value = None
        for s in symbols:
            if best_symbol is None:
                best_symbol = s
                best_value = score(mappings,s)
            else:
                sc = score(mappings,s)
                if sc > best_value:
                    best_value = sc
                    best_symbol = s
        return best_symbol



    def optimize_step(mappings: dict[str, bool]):
        #symbols = self.used_symbols
        symbols = self.pick_unsat_clause(mappings).used_symbols
        choice = best_symbol(symbols,mappings)
        mappings[choice] = not mappings[choice]
    def random_step(mappings: dict[str, bool]):
        choice = random.choice(list(self.used_symbols))
        mappings[choice] = not mappings[choice]
    sat_clauses = 0
    while time_limit == 0 or start_time-time.time() < time_limit:
        if self.eval(mappings):
            print()
            self.solution = mappings
            return True
        else:
            if random.choice([True,False]):
                optimize_step(mappings)
            else:
                random_step(mappings)
        sat_clauses = max(len(self.sat_clauses(mappings)),sat_clauses)
        print(f"SAT: {sat_clauses}/{len(self.clauses)}          ",end="\r")

    print()
    return False

def cg_sat(self:problem,time_limit:int = 0) -> bool:
    start_time = time.time()

    def cap(x:float) -> float:
        return max(min(x,1),0)

    def get_float_function() -> str:
        ret = ""
        for i,c in enumerate(self.clauses):
            ret += "("
            for j,l in enumerate(c.literals):
                ret += f"(1-{l.name})" if l.negated else l.name
                if j != len(c.literals)-1:
                    ret += "+"
            ret += ")"
            if i != len(self.clauses)-1:
                ret += "*" 
        return ret

    def fitness(mappings:dict[str,float]) -> float:
        ret = 1
        for c in self.clauses:
            c_val = 0
            for l in c.literals:
                c_val = max((1-mappings[l.name]) if l.negated else mappings[l.name],c_val)
            ret *= min(c_val,1)
        ret = math.pow(ret,1/len(self.clauses))
        return ret

    def gradient_helper(symbol:str,value:float,mappings:dict[str,float]) -> float:
        new_mappings = mappings.copy()
        new_mappings[symbol] = value
        return fitness(new_mappings)

    def noise() -> dict[str,float]:
        ret = {}
        mod = 0
        for s in self.used_symbols:
            ret[s] = random.random()
            mod += ret[s]**2
        mod = math.sqrt(mod)
        for s in self.used_symbols:
            ret[s] /= mod
        return ret

    def gradient(mappings:dict[str,float]) -> dict[str,float]:
        ret = {}
        for s in self.used_symbols:
            ret[s] = derivative(lambda x:gradient_helper(s,x,mappings),mappings[s],dx=1e-2)
        return ret

    def update_mappings(mappings:dict[str,float],step:float = 1e-4,noise_mod:float = 0.1) -> float:
        """
        Returns the square of the modulus of the gradient, use it to restart if in a local maximum
        """
        grad = gradient(mappings)
        n = noise()
        grad_mod = 0
        for s in self.used_symbols:
            grad_mod += grad[s]**2
        grad_mod = math.sqrt(grad_mod)

        for s in self.used_symbols:
            mappings[s] += step*(grad[s])
            mappings[s] = cap(mappings[s])
            
        return grad_mod
    
    def initial_assignment() -> dict[str,float]:
        return dict([(s,random.random()) for s in self.used_symbols])

    def to_bool(mappings:dict[str,float]) -> dict[str,bool]:
        ret = {}
        for s in self.used_symbols:
            #assert mappings[s] == 1 or mappings[s] == 0
            #if mappings[s] > 0.8 or mappings[s] < 0.2:
            ret[s] = mappings[s] > 0.5
        return ret

    def random_flip(mappings:dict[str,float]):
        choice = random.choice(list(self.used_symbols))
        mappings[choice] = 1 - mappings[choice]
    

    mappings = initial_assignment()

    count = 0
    restart = 0
    sq_gradient_mod = 0
    grad_limit = 0.04
    while time_limit == 0 or time.time() - start_time < time_limit:
        current_fitness = fitness(mappings)
        #if last_fitness == current_fitness:
        #    break
        #last_fitness = current_fitness
        print(f"fitness: {current_fitness:0.012f} iteration: {count} restarts: {restart} |Df|: {sq_gradient_mod}/{grad_limit} SAT: {len(self.sat_clauses(to_bool(mappings)))}/{len(self.clauses)}                     ",end="\r")
        if current_fitness == 1:
            if self.eval(to_bool(mappings)):
                self.solution = to_bool(mappings)
                return True
            break
        sq_gradient_mod = update_mappings(mappings,1,0.1)
        if sq_gradient_mod < grad_limit:
            break
        count+=1
        
        
        

    print()
    return self.cg_sat_finalizer(0 if time_limit == 0 else time_limit-(start_time-time.time()),to_bool(mappings))
    #return self.cdcl_sat(0 if time_limit == 0 else time_limit-(start_time-time.time()),mappings)