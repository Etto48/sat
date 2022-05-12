from ..problem import *


def s_sat(self,time_limit:int = -1,accepted_size:int = 50,mappings:dict[str,bool]={},depth = 0) -> bool:
    start = time.time()
    def random_split(clauses:list[clause]) -> tuple[list[clause],list[clause]]:
        left = random.choices(clauses,k=len(clauses)//2)
        right = list(set(clauses).difference(left))
        return left,right
    
    def heuristic_split(clauses:list[clause]) -> tuple[list[clause],list[clause]]:
        symbol_list = random.choice(clauses).used_symbols
        left = []
        right = []
        for c in clauses:
            if len(left)<=len(clauses)//2 and len(set(c.used_symbols).intersection(symbol_list))!=0:
                symbol_list = list(set(symbol_list+c.used_symbols))
                left.append(c)
            else:
                right.append(c)
        return left,right

    def asymmetric_split(clauses:list[clause]) -> tuple[list[clause],list[clause]]:
        left = []
        right = []
        used_indices = []
        max_symbols = len(problem(clauses).used_symbols)
        
        while len(left)==0 or len(problem(left).used_symbols) < 25:
            i = random.randint(0,len(clauses)-1)
            while i in used_indices:
                i = random.randint(0,len(clauses)-1)

            left.append(clauses[i])
            used_indices.append(i)
        right = list(set(clauses).difference(left))
        return left,right
        

    def intersecting_symbols(p1:problem,p2:problem) -> list[str]:
        left_symbols = set(p1.used_symbols)
        right_symbols = set(p2.used_symbols)
        return list(left_symbols.intersection(right_symbols))
    
    def mapped_var_count(mappings:dict[str,bool]) -> int:
        return len(set(mappings.keys()).intersection(self.used_symbols))

    def not_mapped(mappings:dict[str,bool],symbols:list[str]) -> list[str]:
        return list(set(symbols).difference(mappings.keys()))

    def nice_mapping(symbols:list[str]) -> dict[str,bool]:
        ret = {}
        for s in symbols:
            ret[s] = True if self.symbol_score(s) > 0 else False
        return ret
    
    def nice_random_mapping(symbols:list[str]) -> dict[str,bool]:
        ret = {}
        for s in symbols:
            score = self.symbol_score(s)
            if score != 0:
                ret[s] = True if score > 0 else False
            else:
                ret[s] = True if random.randint(0,1)==1 else False
        return ret

    if self.size-mapped_var_count(mappings) <= accepted_size:
        #print(f"Psize:{self.size-mapped_var_count(mappings)}")
        #problem is small, solve it in one step
        return self.dpll_sat(mappings)
    else:
        #problem is still big try to split it
        while True:
            left_c,right_c = asymmetric_split(self.clauses)
            p1 = problem(left_c)
            p2 = problem(right_c)
            intersecting = intersecting_symbols(p1,p2)
            if len(intersecting) == len(self.used_symbols):
                continue
            #print(f"Split {len(p1.used_symbols)}/{len(p1.clauses)},{len(p2.used_symbols)}/{len(p2.clauses)} intersection: {len(intersecting)}")
            to_map = not_mapped(mappings,intersecting)
            #assign now conflicting symbols
            
            new_mappings = mappings.copy()
            new_mappings.update(nice_random_mapping(to_map))
            if time_limit != -1 and time.time()-start > time_limit:
                return False
            else:
                new_limit = 10 if time_limit == -1 else time_limit - (time.time()-start)
                value = p1.s_sat(new_limit,accepted_size,new_mappings,depth+1) and p2.s_sat(new_limit,accepted_size,new_mappings,depth+1)
                if value:
                    return True

def split_sat(self,fallback:str = "dpll",time_limit:int = 0) -> bool:
    left_clauses = []
    right_clauses = []
    
    selected_symbols = [self.used_symbols[0]] #select one symbol
    while True:
        begin_selected_symbols = selected_symbols
        for c in self.clauses:
            present = False
            for s in selected_symbols:
                if s in c.used_symbols:
                    present = True
                    break
            if present:
                #add related symbols to list
                selected_symbols += c.used_symbols
                selected_symbols = list(dict.fromkeys(selected_symbols))
        if set(begin_selected_symbols) == set(selected_symbols):
            break

    if len(selected_symbols)==len(self.used_symbols):
        if fallback == "walk":
            return self.walk_sat(time_limit)
        elif fallback == "g":
            return self.g_sat(time_limit)
        elif fallback == "gw":
            return self.gw_sat(time_limit)
        elif fallback == "dpll":
            return self.dpll_sat()
        else:
            raise "Unknown fallback function"
        
    else:

        for c in self.clauses:
            present = False
            for s in selected_symbols:
                if s in c.used_symbols:
                    present = True
                    break
            if present:
                left_clauses.append(c)
            else:
                right_clauses.append(c)
        
    
        p1 = problem(left_clauses)
        p2 = problem(right_clauses)
        #print(f"splittable problem: {len(p1.used_symbols)}+{len(p2.used_symbols)}")
        return p1.split_sat(fallback,time_limit) and p2.split_sat(fallback,time_limit)