offsets = [9501990, 114938, 12362, 5458, 1193, 4926, 2527, 803, 1026, 124, 750, 785, 23, 43, 21, 42]

indices = []
s = 0
for o in offsets:
    s += o
    indices.append(s)

print(indices)