import os
import sys

from parseInput import parseInput

if "__main__" == __name__:
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    


    parseInput()

