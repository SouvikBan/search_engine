import sys
import os

def getname(pt):
    return str(pt)+'_index.txt'

def merge_2_files(pt1, pt2):
    if pt1 == pt2:
        return
    f1 = open(getname(pt1), 'r')
    f2 = open(getname(pt2), 'r')
    f3 = open('temp.txt', 'w')
    l1 = f1.readline().strip('\n')
    l2 = f2.readline().strip('\n')
    while (l1 and l2):
        word1 = l1.split(":")[0]
        word2 = l2.split(":")[0]
        if word1 < word2:
            f3.write(l1 + '\n')
            l1 = f1.readline().strip('\n')
        elif word2 < word1:
            f3.write(l2 + '\n')
            l2 = f2.readline().strip('\n')
        else:
            list1 = l1.strip().split(":")[1:]
            lis1 = ' '.join([str(elem) for elem in list1]) 
            list2 = l2.strip().split(':')[1:]
            lis2 = ' '.join([str(elem) for elem in list2]) 
            f3.write(word1 + ':' + lis1 + lis2 + '\n')
            l1 = f1.readline().strip('\n')
            l2 = f2.readline().strip('\n')
    while l1:
        f3.write(l1 + '\n')
        l1 = f1.readline().strip('\n')
    while l2:
        f3.write(l2 + '\n')
        l2 = f2.readline().strip('\n')
    os.remove(getname(pt1))
    os.remove(getname(pt2))
    os.rename('temp.txt', getname(pt1 // 2))
    f3.close()
    f1.close()
    f2.close()

r = 34

while r != 1:
    for i in range(0, r, 2):
        if i + 1 == r:
            new_name = i // 2
            os.rename(getname(i), getname(i // 2))
            break
        merge_2_files(i, i+1)
    if r % 2 == 1:
        r = r // 2 + 1
    else:
        r = r // 2
    print("Number of files left: " + str(r))

