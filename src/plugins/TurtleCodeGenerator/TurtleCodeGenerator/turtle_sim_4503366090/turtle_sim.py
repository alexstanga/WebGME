

from svg_turtle import SvgTurtle

t = SvgTurtle(500, 500)

t.goto(200, 200)
t.color('red')
t.penup()
t.forward(10)
t.pendown()
for _ in range(4):
    t.left(90)
    t.forward(10)
t.penup()

t.save_as('turtle.svg')