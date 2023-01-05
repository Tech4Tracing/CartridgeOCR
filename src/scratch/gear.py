# print the coordinates of the outline of a gear
# with 12 rectangular spokes
import math

r1 = 6.5
r2 = 9
rinner = 3
spokes = 8
print("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path fill="none" 
  stroke="currentColor" 
  stroke-linecap="round" stroke-width="1" 
  d=\"""")
for i in range(0, spokes):
    angle = i * 2 * math.pi / spokes - math.pi / spokes / 2
    fudge = 5*math.pi/180
    if i==0:
        angle0 = angle - math.pi / spokes + fudge
        x0 = r1 * math.cos(angle0)
        y0 = r1 * math.sin(angle0)
        print(f"M{x0+10},{y0+10}")
    x1 = r1 * math.cos(angle-fudge)
    y1 = r1 * math.sin(angle-fudge)
    x2 = r2 * math.cos(angle)
    y2 = r2 * math.sin(angle)
    #print(x1+10, y1+10)
    #print(x2+10, y2+10)
    print(f"A{r1},{r1} 0 0,1 {x1+10},{y1+10}")
    print(f"L{x2+10},{y2+10}")        
    x1 = r2 * math.cos(angle + math.pi / spokes)
    y1 = r2 * math.sin(angle + math.pi / spokes)
    x2 = r1 * math.cos(angle + math.pi / spokes + fudge)
    y2 = r1 * math.sin(angle + math.pi / spokes + fudge)
    print(f"A{r2},{r2} 0 0,1 {x1+10},{y1+10}")
    print(f"L{x2+10},{y2+10}")
    #print(x1+10, y1+10)
    #print(x2+10, y2+10)
print(f"M{rinner+10},{10}")
print(f"A{rinner},{rinner} 0 1,0 {10-rinner},{10}")
print(f"A{rinner},{rinner} 0 1,0 {10+rinner},{10}")
print("""\"/>
</svg>""")