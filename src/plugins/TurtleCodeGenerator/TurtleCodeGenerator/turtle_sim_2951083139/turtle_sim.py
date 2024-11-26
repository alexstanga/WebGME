

from svg_turtle import SvgTurtle

t = SvgTurtle(500, 500)

t.color('black')
t.color('blue')
t.clear()
for _ in range(1):
    t.forward(1)
    t.color('black')
    t.goto(0, 0)
    t.left(1)
t.clear()
for _ in range(4):
    t.clear()
    t.color('black')

t.save_as('turtle.svg')