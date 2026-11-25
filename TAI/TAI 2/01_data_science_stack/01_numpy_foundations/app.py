import numpy as np



array_now= np.array([

    [10, 20, 30, 40, 50],
    [60, 70, 80, 90, 100],
    [110, 120, 130, 140, 150],
    [160, 170, 180, 190, 200]

]





,dtype=np.uint64)



print(
    array_now[2:3]  [1:3].shape  #(1, 5) why not (1,3) and yeah i am not intendig array_now[2:3 , 0:3] wich does return (1,3)
)
#
# print(
# array_now[2:3][0:3]
#
# )

#
# print(
# array_now[2:3][0:3].shape
#
# )
#
# x = array_now[2:4,0:3]
#
# print(x)