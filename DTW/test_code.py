import pandas as pd

a = [[1,2,[3,4] ], [2,3,[4,5]]]

df = pd.DataFrame(a, columns=['x', 'y', 'z', 'x'])

print(df)