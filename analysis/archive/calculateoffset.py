offsets = [9580777, 32083, 4025, 3381, 9298, 5463, 2356, 3242, 4699, 362, 862, 120, 127, 85, 12, 49]

indices = []
s = 0
for o in offsets:
    s += o
    indices.append(s)

print(indices)