try:
    from .problem import *
except ImportError:
    from problem import *

class knowledge_base:
    def __init__(self):
        self.rules = []

    def add_rule(self,rule:str):
        self.rules.append(rule)

    def get_rules(self) -> str:
        ret = ""
        for i,r in enumerate(self.rules):
            if i == len(self.rules)-1:
                ret += f"({r})"
            else:
                ret += f"({r})&"
        return ret

    def __str__(self):
        return f"KB: {str(self.rules)}"

    def is_implied(self,statement:str) -> bool:
        compiled_rules = f"({self.get_rules()})&~({statement})"
        p = problem.from_complex_text(compiled_rules)
        return not p.cdcl_sat()
    
    def is_ammisible(self,statement:str) -> bool:
        compiled_rules = f"({self.get_rules()})&({statement})"
        p = problem.from_complex_text(compiled_rules)
        return p.cdcl_sat()