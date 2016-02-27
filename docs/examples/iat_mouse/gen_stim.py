import random as rm
from config import instruct1,instruct2,instruct3,instruct4,instruct5,instruct6,instruct7

# WORDLISTS FROM Greenwald et al. 1998
filenameI = "pools/insects.txt"
filenameF = "pools/flowers.txt"
filenameP = "pools/positives.txt"
filenameN = "pools/negatives.txt"

I = open(filenameI)
F = open(filenameF)
P = open(filenameP)
N = open(filenameN)

stimListI = I.read().split('\n')
stimListF = F.read().split('\n')
stimListP = P.read().split('\n')
stimListN = N.read().split('\n')

#pop off the trailing line
stimListI.pop(len(stimListI)-1)
stimListF.pop(len(stimListF)-1)
stimListP.pop(len(stimListP)-1)
stimListN.pop(len(stimListN)-1)

def gen_blocks(type):

    sampI = rm.sample(stimListI, 10)
    sampF = rm.sample(stimListF, 10)
    sampP = rm.sample(stimListP, 10)
    sampN = rm.sample(stimListN, 10)

    #Generate the blocks
    list1 = {"left_word":"flower", "right_word":"insect", "instruct":instruct1,
             "words":([{"correct":"right", "center_word":I} for I in sampI] +
                      [{"correct":"left", "center_word":F} for F in sampF])}

    list2 = {"left_word":"positive", "right_word":"negative", "instruct":instruct2,
             "words":([{"correct":"left", "center_word":P} for P in sampP] +
                      [{"correct":"right", "center_word":N} for N in sampN])}

    list3 = {"left_word":"flower positive", "right_word":"insect negative", "instruct":instruct3,
             "words":([{"correct":"right", "center_word":I} for I in rm.sample(sampI[:], 5)] +
                      [{"correct":"left", "center_word":F} for F in rm.sample(sampF[:], 5)] +
                      [{"correct":"left", "center_word":P} for P in rm.sample(sampP[:], 5)] +
                      [{"correct":"right", "center_word":N} for N in rm.sample(sampN[:], 5)])}

    list4 = {"left_word":"flower positive", "right_word":"insect negative", "instruct":instruct4,
             "words":([{"correct":"right", "center_word":I} for I in sampI] +
                      [{"correct":"left", "center_word":F} for F in sampF] +
                      [{"correct":"left", "center_word":P} for P in sampP] +
                      [{"correct":"right", "center_word":N} for N in sampN])}

    list5 = {"left_word":"insect", "right_word":"flower", "instruct":instruct5,
             "words":[{"correct":"left", "center_word":I} for I in sampI] + [{"correct":"right", "center_word":F} for F in sampF]}

    list6 = {"left_word":"insect positive", "right_word":"flower negative", "instruct":instruct6,
             "words":([{"correct":"left", "center_word":I} for I in rm.sample(sampI[:], 5)] +
                      [{"correct":"right", "center_word":F} for F in rm.sample(sampF[:], 5)] +
                      [{"correct":"left", "center_word":P} for P in rm.sample(sampP[:], 5)] +
                      [{"correct":"right", "center_word":N} for N in rm.sample(sampN[:], 5)])}

    list7 = {"left_word":"insect positive", "right_word":"flower negative", "instruct":instruct7,
             "words":([{"correct":"left", "center_word":I} for I in sampI] +
                      [{"correct":"right", "center_word":F} for F in sampF] +
                      [{"correct":"left", "center_word":P} for P in sampP] +
                      [{"correct":"right", "center_word":N} for N in sampN])}
    rm.shuffle(list1['words'])
    rm.shuffle(list2['words'])
    rm.shuffle(list3['words'])
    rm.shuffle(list4['words'])
    rm.shuffle(list5['words'])
    rm.shuffle(list6['words'])
    rm.shuffle(list7['words'])

    #If type 1, then do critical compatible lists
    if type == 1:
        return [list1, list2, list3, list4, list5, list6, list7]
    #if type 2, then do critical incompatible lists
    else:
        return [list5, list2, list6, list7, list1, list3, list4]
#GenBlocks
BLOCKS = gen_blocks(1)
