from __future__ import annotations

try:
    from ..problem import *
except:
    pass


def dpll_sat(self:problem,mappings:dict[str,bool] = {}) -> bool:
        def choose_literal(mappings:dict[str,bool]) -> tuple[str,bool]:
            undefined = self.undefined_symbols(mappings)
            undefined.sort(key=lambda s:abs(self.symbol_score(s)),reverse=True)
            return undefined[0],self.symbol_score(undefined[0])>0

        new_mappings = mappings.copy()
        while True:
            unit_clauses = self.unit_clauses(new_mappings)
            if len(unit_clauses) == 0:
                break
            for s in unit_clauses[0].used_symbols:
                if s not in new_mappings:
                    new_mappings[s] = True if unit_clauses[0].symbol_score(s) > 0 else False
        
        while True:
            pure_literals = self.pure_literals(new_mappings)
            if len(pure_literals) == 0:
                break
            new_mappings[pure_literals[0].name]=not pure_literals[0].negated
        
        if self.eval(new_mappings):
            self.solution = new_mappings
            return True
        elif len(new_mappings)>=len(self.used_symbols):
            return False
             
        
        selected_symbol,best_value = choose_literal(new_mappings)

        mappings1 = new_mappings.copy()
        mappings1[selected_symbol] = best_value
        mappings2 = new_mappings.copy()
        mappings2[selected_symbol] = not best_value
        return self.dpll_sat(mappings1) or self.dpll_sat(mappings2)