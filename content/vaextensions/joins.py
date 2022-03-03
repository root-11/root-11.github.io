import vaex
import random

def make_name(used_names):
        count_name = 'composite_key'
        while count_name in used_names:
            count_name = f"{count_name}{random.getrandbits()}"
        return count_name


def composite_join(left_df, right_df, left_keys, right_keys, left_columns=None, right_columns=None, how='left'):
    """
    high level composite join 
    """
    if left_columns is None:
        left_columns = list(left_df.columns)
    if right_columns is None:
        right_columns = list(right_df.columns)

    # limit left df to output columns
    

    # create composite key for left dataframe
    left_key_column = make_name(left_df.column_names + right_df.column_names)  # in case the columns 1,2,3 and 123 exist, we add some temporary randomness.

    # left_temp = left_df.groupby(by=left_keys).agg({left_key_column:vaex.agg.count()})
    # index = {(tuple(d_row[k] for k in left_keys)):ix for ix,d_row in left_temp.iterrows()}

    # def key(index, row):
    #     return index.get(tuple(row))

    # left_df[left_key_column] = left_df.apply(key, arguments=[index, left_df[left_keys]])
    # left_df[left_key_column] = index.get(tuple(row[k] for k in left_keys))
    # left_df[left_key_column] = key(index, left_df[left_keys], left_keys)

    left_df[left_key_column] = left_df[left_keys[0]].astype('str')
    for k in left_keys[1:]:
        left_df[left_key_column] += "," + left_df[k].astype('str')
    
    left_join_df = left_df[[left_key_column] + left_columns ]

    # create composite key for right dataframe
    right_key_column = make_name("".join(right_keys))
    right_df[right_key_column] = right_df[right_keys[0]].astype('str')
    for k in right_keys[1:]:
        right_df[right_key_column] += "," + right_df[k].astype('str')

    # limit right df to outout columns
    right_join_df = right_df[[right_key_column] + right_columns]

    # utilise vaex.join
    allow_duplication = False if how == 'inner' else True

    output_df = left_join_df.join(right_join_df, left_on=left_key_column, right_on=right_key_column, how=how, allow_duplication=allow_duplication)
    # remove the temporary columns
    left_df.delete_virtual_column(left_key_column)
    right_df.delete_virtual_column(right_key_column)
    output_df.delete_virtual_column(left_key_column)
    return output_df


def test():
    import vaex
    from itertools import combinations_with_replacement

    L = list(combinations_with_replacement(range(5), 3)) * 2
    a = [i[0] for i in L]
    b =[i[1] for i in L]
    c = [i[2] for i in L]
    df_left = vaex.from_arrays(a=a,b=b,c=c)
    d = [i*10 for i in c]
    df_right = vaex.from_arrays(a=a,b=b, d=d)

    chunk_size = 10
    left_columns = ['a','c'] 
    right_columns = ['d']
    kwargs = {
        "left_df": df_left, "right_df": df_right,
        "left_keys": ['a','b'], "right_keys": ['a','b'], 
        "left_columns": left_columns, "right_columns": right_columns
    }

    new_df = composite_join(**kwargs)
    print(new_df)
   

if __name__ == "__main__":
    test()