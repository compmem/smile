import random
from config import NUMBLOCKS, stimList, NUMPERBLOCK, MINFKDUR

random.shuffle(stimList)

blocks = []
for i in range(NUMBLOCKS):
    tempList = []
    for x in range(NUMPERBLOCK[i%len(NUMPERBLOCK)]):
        tempList.append(stimList.pop())
    tempBlock = {"study":tempList,
                 "duration":(MINFKDUR + 10*i%len(NUMPERBLOCK))}
    blocks.append(tempBlock)

random.shuffle(blocks)
