import pandas as pd
import copy

a = [[1,2,3,4], [11,12,13,14],[14,15,16,17], [5, 4, 23, 'dasd'], [5, 4, 5, 'dasd']]
b= [1]
a.sort(key=lambda x: (x[1], x[2]))

if b:
    print('aa')
print(a)


# df_columns = ['frame', 'id', 'x', 'y']
# result = pd.DataFrame(a, columns=df_columns)
#
# print(result)
#
# b = copy.deepcopy(result)
# b.insert(2, 'ff', 1)
#
# print(b)
#
# b.drop(['ff', 'x'], axis=1, inplace=True)
# print(b)
