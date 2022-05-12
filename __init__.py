try:
    from .logic_node import *
    from .literal import *
    from .clause import *
    from .problem import *
    from .knowledge_base import *
except ImportError:
    from logic_node import *
    from literal import *
    from clause import *
    from problem import *
    from knowledge_base import *

if __name__ == "__main__":
    p = problem.from_complex_text("(x=>y)&(x)&(~y)")
    print(p.to_DIMACS())
    print(p.dpll_sat())