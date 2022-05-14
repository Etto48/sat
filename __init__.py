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
    p = problem.from_file(sat_text)
    start = time.time()
    ret = p.dpll_sat()
    end = time.time()
    print(f"{'SAT' if ret else 'UNSAT'} in {end-start}s")
    if ret:
        print(p.solution)