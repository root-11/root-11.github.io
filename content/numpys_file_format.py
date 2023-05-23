import numpy as np

def main():
    arr = np.array([1,2,3])
    np.save('ff.npy', arr, allow_pickle=False, fix_imports=False)
    print("done")

    org_arr = np.load('ff.npy')

    with open('ff.npy') as fi:
        s = fi.read()
        print(s)
        # "“NUMPY\x01\x00v\x00{'descr': '<i4', 'fortran_order': False, 'shape': (3,), }                                                            \n\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00"

        magic = s[:6]
        major = s[6]
        minor = s[7]
        header_length = s[8:10]
        header = s[10:header_length]
        data = s[header_length+1:]


        # fp.write(chunk.tobytes('C'))

def main2():
    arr = np.array( ["列 1", "列 2","列 3"] )
    np.save('ff3.npy', arr, allow_pickle=False, fix_imports=False)
    with open('ff3.npy') as fi:
        s = fi.read()
        print(s)
    x = 4
    org_arr = np.load('ff3.npy')

if __name__ == "__main__":
    main2()