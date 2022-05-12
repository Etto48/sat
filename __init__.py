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
    print("SAT> ",end='')
    sat_text = input()
    p = problem.from_complex_text(sat_text)
    ret = p.cdcl_sat()
    print("SAT" if ret else "UNSAT")
    if ret:
        print(p.solution)