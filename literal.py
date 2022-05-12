from __future__ import annotations

class literal:
    def __init__(self,name:str,negated:bool):
        self.name = name
        self.negated = negated
    def eval(self,mappings:dict[str,bool]) -> bool:
        if self.name in mappings:
            return not mappings[self.name] if self.negated else mappings[self.name]
        else:
            return False
    def __eq__(self, __o: literal) -> bool:
        return __o.name == self.name and __o.negated == self.negated

    def __ne__(self, __o: literal) -> bool:
        return __o.name != self.name or __o.negated != self.negated
    
    def __hash__(self) -> int:
        return hash((self.name,self.negated))