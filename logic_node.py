from __future__ import annotations

class logic_node:
    def __init__(self,node_type,arg1,arg2=None):
        self.node_type = node_type
        if node_type == "var":
            self.value = arg1
            assert arg2 == None
        elif node_type == "~":
            self.child1=arg1
            assert arg2 == None
        else:
            self.child1=arg1
            self.child2=arg2

    def from_text(text:str) -> logic_node: 
        b_depth = 0
        next_expected = ""
        split_point = -1
        split_prio = -1

        assert len(text) > 0
        def update_split_point(prio:int,point:int,split_prio,split_point) -> list[int]:
            if prio > split_prio:
                split_prio = prio
                split_point = point
                return split_prio,split_point
            else:
                return split_prio,split_point

        def remove_braces_helper(text):
            if text[0]=='(' and text[-1] == ')':
                b_depth = 0
                for c in text[1:-1]:
                    if c == '(':
                        b_depth+=1
                    elif c == ')':
                        b_depth-=1

                    if b_depth < 0:
                        return False
                return True
            else:
                return False

        while remove_braces_helper(text):
            text = text[1:-1]

        for i,c in enumerate(text):
            if len(next_expected) == 0:
                if c == "(":
                    b_depth+=1
                elif c == ")":
                    b_depth-=1
                elif c == ' ':
                    pass
                elif c == '<':
                    next_expected = "=>"
                    if b_depth == 0:
                        split_prio,split_point = update_split_point(4,i,split_prio,split_point)
                elif c == '=':
                    next_expected = '>'
                    if b_depth == 0:
                        split_prio,split_point = update_split_point(4,i,split_prio,split_point)
                elif c == '&':
                    if b_depth == 0:
                        split_prio,split_point = update_split_point(3,i,split_prio,split_point)
                elif c == '|':
                    if b_depth == 0:
                        split_prio,split_point = update_split_point(2,i,split_prio,split_point)
                elif c == '~' and i==0:
                    if b_depth == 0:
                        split_prio,split_point = update_split_point(1,i,split_prio,split_point)
                
                assert b_depth >= 0        
            else:
                assert c == next_expected[0]
                next_expected=next_expected[1:len(next_expected)]

        if split_point < 0:
            return logic_node("var",text)
        elif text[split_point]=='<':
            return logic_node("<=>",logic_node.from_text(text[0:split_point]),logic_node.from_text(text[split_point+3:len(text)]))
        elif text[split_point]=='=':
            return logic_node("=>",logic_node.from_text(text[0:split_point]),logic_node.from_text(text[split_point+2:len(text)]))
        elif text[split_point]=='~':
            return logic_node("~",logic_node.from_text(text[1:len(text)]))
        else:
            return logic_node(text[split_point],logic_node.from_text(text[0:split_point]),logic_node.from_text(text[split_point+1:len(text)]))

    def simplify(self) -> logic_node:
        if self.node_type == "var":
            return self
        elif self.node_type == "<=>":
            child1 = self.child1.simplify()
            child2 = self.child2.simplify()
            return logic_node("&",logic_node("=>",child1,child2),logic_node("=>",child2,child1))
        elif self.node_type == "=>":
            return logic_node("|",logic_node("~",self.child1.simplify()),self.child2.simplify())
        elif self.node_type == "~":
            if self.child1.node_type == "&":
                return logic_node("|",logic_node("~",self.child1.child1.simplify()),logic_node("~",self.child1.child2.simplify()))
            elif self.child1.node_type == "|":
                return logic_node("&",logic_node("~",self.child1.child1.simplify()),logic_node("~",self.child1.child2.simplify()))
            elif self.child1.node_type == "~":
                return self.child1.child1.simplify()
            else:
                return logic_node("~",self.child1.simplify())
        elif self.node_type == "|":
            if self.child1.node_type == "&":
                child2 = self.child2.simplify()
                return logic_node("&",logic_node("|",child2,self.child1.child1.simplify()),logic_node("|",child2,self.child1.child2.simplify()))
            elif self.child2.node_type == "&":
                child1 = self.child1.simplify()
                return logic_node("&",logic_node("|",child1,self.child2.child1.simplify()),logic_node("|",child1,self.child2.child2.simplify()))
            else:
                return logic_node("|",self.child1.simplify(),self.child2.simplify())
        elif self.node_type == "&":
            return logic_node("&",self.child1.simplify(),self.child2.simplify())
        else:
            return self
        
    def fully_simplify(self) -> logic_node:
        ret = self.simplify()
        old_ret_str = ""
        while old_ret_str!=str(ret):
            old_ret_str = str(ret)
            ret = ret.simplify()
        return ret

    def cnf(self) -> str:
        tmp = str(self.fully_simplify())
        ret = "("
        for c in tmp:
            if c == '&':
                ret += f"){c}("
            elif c not in ['(',')',' ']:
                ret += c
        return ret + ")"
        
            

    def __str__(self):
        if self.node_type == "var":
            return self.value
        elif self.node_type == "~":
            return f"~({str(self.child1)})"
        else:
            return f"({str(self.child1)} {self.node_type} {str(self.child2)})"