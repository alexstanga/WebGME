from lark import Lark, Transformer
from lark.indenter import Indenter

grammar = r"""
start: statement+

statement: command
         | loop

command: "t." action "(" arguments ")"  -> simple_command
       | "t." action "()"               -> no_argument_command
action: STRING
loop: "for" "_" "in" "range" "(" NUMBER ")" ":" block  -> loop_block

block: statement+

arguments: argument ("," argument)*  -> multiple_arguments

argument: ESCAPED_STRING | NUMBER | "None"

COMMENT: /#.*/
%ignore COMMENT
%ignore "from svg_turtle import SvgTurtle"
%ignore "t = SvgTurtle(500, 500)"
%ignore /t\.save_as\(.+\)/

%import common.SIGNED_NUMBER -> NUMBER
%import common.NEWLINE
%import common.WS

ESCAPED_STRING: /'([^'\\]*(\\.[^'\\]*)*)'/ | /"([^"\\]*(\\.[^"\\]*)*)"/
STRING: /[a-zA-Z_][a-zA-Z_0-9]*/
%ignore WS
"""


class PyToTurtleTransformer(Transformer):
    def start(self, items):
        return {"commands": items}

    def simple_command(self, items):
        return {
            "type": "command",
            "action": items[0],
            "arguments": items[1]
        }

    def no_argument_command(self, items):
        return {
            "type": "command",
            "action": items[0],
            "arguments": []
        }

    def loop_block(self, items):
        count = items[0]
        block = items[1]
        return {
            "type": "loop",
            "iterations": count,
            "body": block
        }

    def block(self, items):
        return items

    def action(self, items):
        return str(items[0])

    def multiple_arguments(self, items):
        return list(items)

    def single_argument(self, items):
        return [items[0]]

    def argument(self, items):
        if items[0] == "None":
            return None
        return items[0]


class PyToTurtle():
    def __init__(self):
        self.transformer = PyToTurtleTransformer()
        self.parser = Lark(grammar, parser="lalr")

    def getJson(self, text):
        try:
            tree = self.parser.parse(text)
            print("Printing Tree")
            print(tree.pretty())
            return self.transformer.transform(tree)
        except Exception as e:
            return {"error": str(e)}
