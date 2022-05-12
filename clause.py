try:
    from .literal import *
except ImportError:
    from literal import *

class clause:
    def __init__(self,literals:list[literal]):
        self.literals = literals
        self.used_symbols:set[str] = set()
        for l in self.literals:
            self.used_symbols.add(l.name)
    def eval(self,mappings:dict[str,bool]) -> bool:
        for l in self.literals:
            if l.eval(mappings):
                return True
        return False
    def symbol_score(self,symbol:str) -> int:
        ret = 0
        for l in self.literals:
            if l.name == symbol:
                ret += -1 if l.negated else 1
        return ret
    
    def unit_value(self,symbol:str) -> bool:
        return True if self.symbol_score(symbol) > 0 else False