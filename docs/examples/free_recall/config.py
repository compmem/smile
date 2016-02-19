#Names of the stimulus files
filenameL = "pools/living.txt"
filenameN = "pools/nonliving.txt"

#Open the files and combine them
L = open(filenameL)
N = open(filenameN)
stimList = L.read().split('\n')
stimList.append(N.read().split('\n'))

#Open the instructions file
instruct_text = open('freekey_instructions.rst', 'r').read()

#Define the Experimental Variables
ISI = 2
IBI = 2
STIMDUR = 2
PFI = 4
FONTSIZE = 40
RSTFONTSIZE = 50
RSTWIDTH = 600

MINFKDUR = 20

NUMBLOCKS = 6
NUMPERBLOCK = [10,15,20]

