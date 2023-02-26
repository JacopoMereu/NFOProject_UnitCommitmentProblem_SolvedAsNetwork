#This module contains all the functions that are used in the main module.

'''This function returns a list of all the possible combinations of binary strings of length nUnits.
    e.g. nUnits = 3 -> ['000', '001', '010', '011', '100', '101', '110', '111']

    Args:
        nUnits (int): The length of the binary strings.
        
    Returns:
        list: A list of all the possible combinations of binary strings of length nUnits.'''
def getAllBinaryStringCombinations(nUnits):
    nCombs = 2**nUnits
    return ([intToBinStr(i, nUnits) for i in range(nCombs)], nCombs)

def intToBinStr(i, nDigits=8):
    int_to_binstr = f'{i:0{nDigits}b}'
    return int_to_binstr


def binStrToBin(binStr):
    binStr_to_bin = bin(int(binStr, 2))
    return binStr_to_bin


def binToInt(bin):
    bin_to_int = int(bin, 2)
    return bin_to_int


def binStrToInt(binStr):
    binStr_to_int = binToInt(binStrToBin(binStr))
    return binStr_to_int

###################### Network ######################
import re
def getAllBinaryStringCombinationMatchingPattern(strNumber):
    # Get a string of length n. Each character can be 0, 1 or x.
    # Return a list of all the possible combinations of binary strings of length n.
    # e.g. strNumber = 'x10x1' -> ['01001', '01011', '11001', '11011']
    # e.g. strNumber = 'x1x' -> ['010', '011', '110', '111']
    # e.g. strNumber = 'x' -> ['0', '1']
    # e.g. strNumber = '1' -> ['1']
    # e.g. strNumber = '0' -> ['0']
    # e.g. strNumber = 'xx' -> ['00', '01', '10', '11']
    # e.g. strNumber = 'xxx' -> ['000', '001', '010', '011', '100', '101', '110', '111']

    # Get the list of all the possible combinations of binary strings of length strNumber
    allCombs, _ = getAllBinaryStringCombinations(len(strNumber))
    # Create a regex pattern with strNumber
    pattern = strNumber.replace('x', '.')
    # Remove all the combinations that do not match the pattern
    allCombs = [i for i in allCombs if not re.match(pattern, i)]
    return allCombs

def getAllBinaryStringCombinationMatchingPattern(strNumber):
    # Get a string of length n. Each character can be 0, 1 or x.
    # Return a list of all the possible combinations of binary strings of length n.
    # e.g. strNumber = 'x10x1' -> ['01001', '01011', '11001', '11011']
    # e.g. strNumber = 'x1x' -> ['010', '011', '110', '111']
    # e.g. strNumber = 'x' -> ['0', '1']
    # e.g. strNumber = '1' -> ['1']
    # e.g. strNumber = '0' -> ['0']
    # e.g. strNumber = 'xx' -> ['00', '01', '10', '11']
    # e.g. strNumber = 'xxx' -> ['000', '001', '010', '011', '100', '101', '110', '111']

    # Get the list of all the possible combinations of binary strings of length strNumber
    allCombs, _ = getAllBinaryStringCombinations(len(strNumber))
    # Create a regex pattern with strNumber
    pattern = strNumber.replace('x', '.')
    # Remove all the combinations that do not match the pattern
    allCombs = [i for i in allCombs if re.match(pattern, i)]
    return allCombs

def getIDPatternDifferences(id1, id2):
    # Return a string as long as id1 and id2. Each character is x if the corresponding characters in id1 and id2 are the same. Otherwise, it is the character in id2.
    # e.g. id1 = '0000', id2 = '0011' -> 'xx11'
    # e.g. id1 = '0000', id2 = '1111' -> '1111'
    # e.g. id1 = '0000', id2 = '0000' -> '0000'
    # e.g. id1 = '0000', id2 = '0001' -> 'xxx1'
    assert len(id1) == len(id2)
    output = 'x' * len(id1)
    for i in range(len(id1)):
        if id1[i] != id2[i]:
            # Replace the character in the output string with the character in id2
            output = output[:i] + id2[i] + output[i+1:]
    # print(output)
    return output

def splitPattern(pattern):
    # Split a pattern into a list of simple patterns. Each simple pattern has all characters equal to x but one that can be 0 or 1.
    # e.g. pattern = 'x10x1' -> ['x1xxx, xx0xx', xxxx1]
    # e.g. pattern = 'x1x' -> ['x1x']
    # e.g. pattern = 'x' -> ['x']
    # e.g. pattern = '1' -> ['1']
    # e.g. pattern = '0' -> ['0']
    # e.g. pattern = 'xx' -> ['xx']
    # e.g. pattern = 'xx0' -> ['xx0']
    # e.g. pattern = 'x1x0' -> ['x1xx', 'xxx0']
    
    # count the 0s and 1s in the pattern
    n0 = pattern.count('0')
    n1 = pattern.count('1')
    # # If the sum is 1, then the pattern is a simple pattern
    if n0 + n1 == 0:
        assert False
        # return [pattern]

    simple_patterns = []
    for i in range(len(pattern)):
        if pattern[i] != 'x':
            ith_simple_pattern = ('x'*len(pattern[:i])) + pattern[i] + ('x'*len(pattern[i+1:]))
            simple_patterns.append( (ith_simple_pattern,i) )
    return simple_patterns

def negatePattern(pattern):
    # Return the negation of a pattern
    # e.g. pattern = 'x10x1' -> 'x01x0'
    # e.g. pattern = 'x1x' -> 'x0x'
    # e.g. pattern = 'x' -> 'x'
    # e.g. pattern = '1' -> '0'
    # e.g. pattern = '0' -> '1'
    # e.g. pattern = 'xx' -> 'xx'
    # e.g. pattern = 'xx0' -> 'xx1'
    # e.g. pattern = 'x1x0' -> 'x0x1'
    return pattern.replace('0', 't').replace('1', '0').replace('t', '1')

def getAllNodesViolatingMinDownAndUpTime(id1, id2, nIntervalli, pattern, tau):
    i1, t1 = id1
    i2, t2 = id2
    #1 Create pattern. P.S. pattern is already in input
    # pattern = pattern

    # 2 Split the pattern into a list of tuples (simple_pattern, i) where
    #     simple_pattern is a pattern with all characters equal to x but one that can be 0 or 1.
    #     i is the index of the character that is not x.
    pSplit = splitPattern(pattern)


    # 3 Negate the simple patterns: 0 -> 1, 1 -> 0, x -> x
    pSplit_Negated = [(negatePattern(simple_pattern),i) for (simple_pattern,i) in pSplit]

    # 4 Create an empty dictionary <string, int>. 
    # For all the simple patterns in pSplit_Negated, 
    #   get all the possible combinations of binary strings
    #       and add them to the dictionary with the value tau[i].
    #   If the key is already in the dictionary, then update the value with the maximum between the current value and tau[i].
    d = {}
    for (sp_negated, i) in pSplit_Negated:
        for p in getAllBinaryStringCombinationMatchingPattern(sp_negated):
            if p not in d:
                d[p] = tau[i]
            else:
                d[p] = max(d[p], tau[i])

    # 5 For each (node_id, window_size) in the dictionary, create a list of tuples (node_id, time) for all time in [t2+1, t2+2, ..., min(t2+window_size, nIntervalli-1)]
    output = []
    for (node_id,window_size) in d.items():
        lht = t2+1
        rht = min(t2+window_size,nIntervalli-1)
        if lht > rht:
            continue
        r = range(lht, rht)
        output.extend([(node_id,time) for time in r])

    # Return the output
    return output


###################### Draw ######################
# Get the tuple formed by a string and an integer ('1100100000', 0) from the strin "1100100000 0 1100100000 1)"
def getArcFromStrVariableName(str):
    str = str.replace("x_('", "")
    str = str.replace("', ", " ")
    str = str.replace(")_('", " ")
    str = str.replace("', ", " ")
    str = str.replace(")", "")
    id1, t1, id2, t2 = tuple(str.split(" "))
    t1 = int(t1)
    t2 = int(t2)
    return (id1, t1, id2, t2)
   
   
import matplotlib.pyplot as plt
def plotNetworkWithSolution(myNet, modelSolution, print_all_arcs=False):
    plt.figure()

    for i in myNet.nodes:
        # Plot the nodes
        plt.plot(i._t, i.getIntegerNumber(), 'o')

    if print_all_arcs:
        for arc in myNet.arcs:
            i1, t1 = arc._n1.id
            i2, t2 = arc._n2.id
            plt.plot([t1, t2], [binStrToInt(i1), binStrToInt(i2)], color='black')

    # Plot the solution arcs
    for (k,v) in modelSolution.iter_var_values():
        if k.name.startswith("x_") and v == 1:
            i1, t1, i2, t2 = (getArcFromStrVariableName(k.name))
            plt.plot([t1, t2], [binStrToInt(i1), binStrToInt(i2)], color='red')
        #plt.arrow(t1, binStrToInt(i1), t2,  binStrToInt(i2), width=1, head_width=5, head_length=2.5, color='black')

    plt.title(f'Final cost is: {modelSolution.get_objective_value()}')
    plt.show()