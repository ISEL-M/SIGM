# normalizacao

import math

x = 3 + 3.5 * 5
y = 4 + 4.9 * 5

norma = math.sqrt( x ** 2  + y ** 2 )
xN = x / norma
yN = y / norma


print( x )
print( y )

print( xN )
print( yN )
