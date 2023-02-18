import utils
import input  # import the input file
import datetime
import multiprocessing
from docplex.mp.model import Model


DO_VERBOSE_LOG = False
DO_MULTIPROCESSING_EDPROBLEMS = True
DO_MULTIPROCESSING_VARIABLES = False # Cannot create variables in parallel. It will cause an error due to the fact that the variables are not created by the same model

class Node():
    """
    A node is a combination of units that are on at time t

    Attributes:
        id: (combinationBinaryString, time)
        u: vector of boolean units that are on at time t
        b: demand at time t: 1 if the node is the source, -1 if the node is the sink, 0 otherwise
    """

    def __init__(self, combinationBinaryString: str, time, isSource=False, isSink=False):
        self.__i = combinationBinaryString
        self._t = time
        self.id = (self.__i, self._t)
        self.u = self.__getUnitsVector()
        # self._F = 0 # TODO later

        self.isSource = isSource
        self.isSink = isSink
        if isSource:
            demand = 1
        elif isSink:
            demand = -1
        else:
            demand = 0
        self.b = demand

        self.innerArcs = []
        self.outerArcs = []

    def __getUnitsVector(self):
        # return the vector of boolean units
        # that are on at time t
        # and have binary number i
        return [bool(int(digit)) for digit in self.__i]

    def isValid(self):
        # Check if the sum of the sum of the minimum power of the units that are on is greater than the demand D
        minimumPower = sum([input.Pmin[i]
                           for i in range(len(self.u)) if self.u[i]])
        maximumPower = sum([input.Pmax[i]
                           for i in range(len(self.u)) if self.u[i]])

        isMinimumPowerValid = minimumPower <= input.D[self._t]
        isMaximumPowerValid = input.D[self._t] <= maximumPower
        if not isMinimumPowerValid or not isMaximumPowerValid:
            return False

        return True

    # Create a CPlex model to solve the economic dispatch problem for the units that are on
    # and return the cost of the flow
    def _calculateFlowCost(self):
        # print("AAAA")
        if DO_VERBOSE_LOG:
            print("I'm calculating the flow cost of node", self.__str__(), "at time", self._t)
        if self.isSource:
            if DO_VERBOSE_LOG:
                print("I'm the source node, so the flow cost is 0")
            self._F = 0
            return
        if self.isSink:
            return;        
        # Create a cplex variable for each unit
        # x[i] is the power of the unit i
        # x[i] >= 0
        # x[i] <= Pmax[i]
        # x[i] >= Pmin[i] if u[i] == 1
        # x[i] <= Pmin[i] if u[i] == 0
        # sum(x[i]) == D[t]

        if DO_VERBOSE_LOG:
            print("I'm not the source node, so I'm creating the CPLEX model to solve the ED problem")
        # Create the CPLEX model
        EDmodel = Model(name=f"Economic Dispatch within node {self.__str__()}")

        # Create the power variables
        powerCplexVar = {idx: EDmodel.continuous_var(
            name='p_{0}'.format(idx)) for idx, _ in enumerate(self.u)}

        # Set the objective function
        z = EDmodel.sum(((self.u[idx]*input.c1[idx]) + (input.c2[idx] * powerCplexVar[idx]) + (
            input.c3[idx] * (powerCplexVar[idx]**2))) for idx in powerCplexVar)
        EDmodel.minimize(z)

        # Print the model information
        # EDmodel.print_information()

        '''ADD CONSTRAINTS'''
        # Constraint 1: sum(x[i]) == D[t]
        EDmodel.add_constraint(EDmodel.sum(powerCplexVar[idx] for idx in powerCplexVar) == input.D[self._t])

        # Constraint 5: Maximum generatic capacity
        for idx in powerCplexVar:
            EDmodel.add_constraint(
                powerCplexVar[idx] <= self.u[idx] * input.Pmax[idx])
        # Constraint 6: Minimum generatic capacity
        for idx in powerCplexVar:
            EDmodel.add_constraint(
                self.u[idx] * input.Pmin[idx] <= powerCplexVar[idx])
        '''END ADD CONSTRAINTS'''

        modelSolution = EDmodel.solve()
        assert modelSolution  # if null then is not feasible (but it should be)
        if DO_VERBOSE_LOG:
            print("Problem solved")
        # modelSolution.display()

        self._F = modelSolution.get_objective_value()

    def getIntegerNumber(self):
        int2 = utils.binStrToInt(self.__i)
        return int2

    def __str__(self):
        return f"Node {self.id}"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Node):
            return self.id == __o.id

        return False

def Worker_RunEDModelOnSample(nodes, return_list):
    l=[]
    for n in nodes:
        n._calculateFlowCost()
        l.append(n)
    
    return_list.extend(l)

def Worker_CreateVariables(arcs, ns, return_dict):
    UCNetworkModel = ns.model
    d={}
    for arc in arcs:
        k = arc
        v = UCNetworkModel.continuous_var(name='x_{0}_{1}'.format(arc[0], arc[1]))     
        d[k] = v
    return_dict.update(d)   

class Arc():
    def __init__(self, node1: Node, node2: Node):
        self._n1 = node1
        self._n2 = node2
        assert node1.id[1] == node2.id[1] - 1
        self.id = (self._n1.id, self._n2.id)
        self._transitionCost = Arc.calculateTransitionCost(node1, node2)
        # self.cost = node1._F + self._transitionCost # TODO Later

    def doLazyEvaluation(self):
        self._calculateOutputFlowCost()
        self._n1.outerArcs.append(self)
        self._n2.innerArcs.append(self)
        
    def _calculateOutputFlowCost(self):
        if DO_VERBOSE_LOG:
            print("\n\nI'm calculating the output flow cost of arc", self.__str__())
        # if n1 has attribute _F then it has been calculated
        if not hasattr(self._n1, '_F'):
            # Evaluate the flow cost only on nodes with an exit arc
            self._n1._calculateFlowCost()
        self.cost = self._n1._F + self._transitionCost
        if DO_VERBOSE_LOG:
            print("The output flow cost of arc", self.__str__(), "is", self.cost)


    @staticmethod
    def calculateTransitionCost(node1: Node, node2: Node):
        # if node1.isSource:
        #     return 0
        if node2.isSink:
            return 0

        u1 = node1.u
        u2 = node2.u
        assert len(u1) == len(u2)

        # save the indexes where the first vector is 0 and the second is 1
        return sum([input.startup_cost[i] for i in range(0, len(u1)) if not u1[i] and u2[i]])

    def __str__(self):
        return f"Arc: [{self._n1.id}] --> [{self._n2.id}]"

    def __iter__(self):
        return self._n1, self._n2

    def __next__(self):
        raise StopIteration

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Arc):
            if DO_VERBOSE_LOG:
                print("1) I'm comparing", self._n1, self._n2, "with", __o._n1, __o._n2)
            return self._n1 == __o._n1 and self._n2 == __o._n2
        if type(__o) is tuple and len(__o) == 2 and isinstance(__o[0], Node) and isinstance(__o[1], Node):
            if DO_VERBOSE_LOG:
                print("2) I'm comparing", self._n1, self._n2, "with", __o[0], __o[1])
            return self._n1 == __o[0] and self._n2 == __o[1]
        return False


class UC_Network():
    def __init__(self, nodes: list[Node], arcs: list[Arc]):
        self.nodes = nodes
        self.arcs = arcs

    @staticmethod
    def createModelFromInput():
        assert len(input.D) == input.nPeriodi

        assert len(input.c1) == input.nUnita
        assert len(input.c2) == input.nUnita
        assert len(input.c3) == input.nUnita
        assert len(input.Pmax) == input.nUnita
        assert len(input.Pmin) == input.nUnita
        assert len(input.min_switch_up) == input.nUnita
        assert len(input.min_switch_down) == input.nUnita
        assert len(input.startup_cost) == input.nUnita


        I = range(input.nUnita)
        T = range(input.nPeriodi)
        print("Range of units: ", I)
        print("Range of periods: ", T)

        # save all boolean combinations with I
        [combinations, nCombs] = utils.getAllBinaryStringCombinations(input.nUnita)

        # Create the nodes
        nodes = []
        print("I'm creating the source node")
        source = Node(input.initial_status, -1, isSource=True)
        nodes.append(source)

        print("I'm creating the (internal) transporation nodes")
        nodes.extend([Node(bs, t) for t in T for bs in combinations])
        print("Number of nodes created ", oldLength := len(nodes)-1)

        print("I'm creating the sink node")
        sink = Node(input.initial_status, input.nPeriodi, isSink=True)
        nodes.append(sink)

        nodes = [n for n in nodes if (n.isSource or n.isSink) or n.isValid()]
        print(
            f"I removed {(oldLength-(currLength := len(nodes)-2))/oldLength:.2f}% nodes. Current number of nodes is {currLength}")
        
        ####################################################################################################
        # Solve the Economic Dispatch Problem on each node
        print("I'm starting solving all ED problems at", now.strftime("%Y-%m-%d %H:%M:%S"))
        if DO_MULTIPROCESSING_EDPROBLEMS:
        ####################################################
            # Split the nodes in as many chunks as the number of cores and calculate the flow cost in parallel
            manager = multiprocessing.Manager()
            return_list = manager.list()
            nCores = multiprocessing.cpu_count()
            print("Number of cores: ", nCores)
            nNodes = len(nodes)
            print("Number of nodes: ", nNodes)
            nNodesPerCore = nNodes // nCores
            print("Number of nodes per core: ", nNodesPerCore)
            nNodesLastCore = nNodes - nNodesPerCore * (nCores - 1)
            print("Number of nodes on the last core: ", nNodesLastCore)

            # Create the processes
            processes = []
            for i in range(nCores):
                if i == nCores - 1:
                    processes.append(multiprocessing.Process(target=Worker_RunEDModelOnSample, args=(nodes[i * nNodesPerCore:],return_list)))
                else:
                    processes.append(multiprocessing.Process(target=Worker_RunEDModelOnSample, args=(nodes[i * nNodesPerCore:(i + 1) * nNodesPerCore],return_list)))
            # wait for all processes to finish
            for p in processes:
                p.start()

            for p in processes:
                p.join()

            nodes = [n for n in return_list]
        ####################################################
        else:
            for node in nodes:
                node._calculateFlowCost()
        print("I'm done solving all ED problems at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #############################################################################################################################

        print("I'm creating the arcs")
        '''
        s1 = datetime.datetime.now()
        arcs = []
        for idx in range(0, len(nodes)-nCombs, nCombs):
            # Get the first 24 nodes in a list
            curr = nodes[idx:idx+nCombs]
            # Get the next 24 nodes in a list
            next = nodes[idx+nCombs:idx+2*nCombs]
            # print(idx)
            # print("************ curr ************")
            # print(*curr, sep='\n')
            # print("************ next ************")
            # print(*next, sep='\n')
            # print("************************")
            # Create the arcs between the nodes in temp and the next 24 nodes
            arcs.extend([Arc(i, j) for i in curr for j in next])
        e1 = datetime.datetime.now()
        print("COOL ", len(arcs), " in time ", e1-s1)
        '''
        arcs = [Arc(i, j) for i in nodes for j in nodes if i._t == j._t - 1]
        print(f"I created {len(arcs)} arcs.")

        # Finally evaluate the flow cost on each node
        print("I'm calculating the final output flow cost on each arc")
        for arc in arcs:
            arc.doLazyEvaluation()
        print("Flow cost calculated on each arc")

        # Assert consistency
        assert hasattr(nodes[0], '_F')
        assert hasattr(arcs[0], 'cost')

        # return the network
        return UC_Network(nodes, arcs)


class UC_Model():
    UCNetworkModel = None

    @staticmethod
    def generateUCNetworkModel(myNet):
        if UC_Model.UCNetworkModel is not None:
            return UC_Model.UCNetworkModel

        UC_Model.UCNetworkModel = Model(name='Unit Commitment Problem - Network Formulation')
        UC_Model.UCNetworkModel.context.cplex_parameters.threads = 5
        # Create the variables
        print("I'm creating the variables")
        if DO_MULTIPROCESSING_VARIABLES:
            # Split the nodes in as many chunks as the number of cores and calculate the flow cost in parallel
            manager = multiprocessing.Manager()
            return_dict = manager.dict()
            nCores = multiprocessing.cpu_count()
            print("Number of cores: ", nCores)
            nArcs = len(myNet.arcs)
            print("Number of arcs: ",nArcs)
            nArcsPerCore = nArcs // nCores
            print("Number of arcs per core: ", nArcsPerCore)
            nArcsLastCore = nArcs - nArcsPerCore * (nCores - 1)
            print("Number of arcs on the last core: ", nArcsLastCore)

            # Create the processes
            processes = []
            ns = manager.Namespace()
            ns.model = UC_Model.UCNetworkModel
            for i in range(nCores):
                l=[]
                if i == nCores - 1:
                    l=[(arc._n1.id, arc._n2.id) for arc in myNet.arcs[i * nArcsPerCore:]]
                    print("last l", len(l))
                    processes.append(multiprocessing.Process(target=Worker_CreateVariables, args=(l,ns,return_dict)))
                else:
                    l=[(arc._n1.id, arc._n2.id) for arc in myNet.arcs[i * nArcsPerCore:(i + 1) * nArcsPerCore]]
                    print("l", len(l))
                    processes.append(multiprocessing.Process(target=Worker_CreateVariables, args=(l,ns,return_dict)))
            # wait for all processes to finish
            for p in processes:
                p.start()

            for p in processes:
                p.join()
            print("I FINISHED CREATING THE VARIABLES")
            print("---" * 20)
            print(type(return_dict))
            print(type(return_dict._getvalue()))
            UC_Model.UCNetworkModel = ns.model
            x = return_dict._getvalue()
        else:
            x = {(arc._n1.id, arc._n2.id): UC_Model.UCNetworkModel.integer_var(name='x_{0}_{1}'.format(arc._n1.id, arc._n2.id)) for arc in myNet.arcs}

        # each arc comes with a cost. Minimize all costed flows
        print("I'm creating the objective function")
        z = UC_Model.UCNetworkModel.sum(x[(arc._n1.id, arc._n2.id)]* arc.cost for arc in myNet.arcs)
        UC_Model.UCNetworkModel.minimize(z)

        # Flow conservation constraints
        print("I'm creating the flow conservation constraints")
        for i in myNet.nodes:
            if DO_VERBOSE_LOG:
                print("I'm creating the outer flow conservation constraint for node ", i.id)
            out_flow = UC_Model.UCNetworkModel.sum(x[(i.id, arc._n2.id)] for arc in i.outerArcs)
                                        #   for j in myNet.nodes if (i, j) in myNet.arcs)
            if DO_VERBOSE_LOG:
                print("I'm creating the inner flow conservation constraint for node ", i.id)
            in_flow = UC_Model.UCNetworkModel.sum(x[(arc._n1.id, i.id)] for arc in i.innerArcs)
            UC_Model.UCNetworkModel.add_constraint(out_flow - in_flow == i.b)
            
        # # Flow bound constraints
        # for (i,j) in arcs:
        #     UC_Model.UCNetworkModel.add_constraint(x[i,j] <= ub.get((i,j), 0))
        #     UC_Model.UCNetworkModel.add_constraint(x[i,j] >= lb.get((i,j), 0))

        # Unit commitment constraints
        assert input.min_switch_down == input.min_switch_up
        tau = input.min_switch_up
        c = 0
        for a in myNet.arcs:
            if DO_VERBOSE_LOG:
                print(f"Counter {c}/", len(myNet.arcs))
            c+=1

            # if a._n1.isSource:
            #     continue
            if a._n2.isSink:
                continue

            diffPattern = utils.getIDPatternDifferences(a._n1.id[0], a._n2.id[0])
            # if count of 1s + count of 0s = 0, continue
            n0 = diffPattern.count('0')
            n1 = diffPattern.count('1')        
            if n0 + n1 == 0:
                continue

            nonValidNodeKeys = utils.getAllNodesViolatingMinDownAndUpTime(a._n1.id, a._n2.id,  input.nPeriodi, diffPattern, tau)
            if len(nonValidNodeKeys) == 0:
                continue
            # From the outer arcs list of a.n2, search the arcs with n2.id in nonValidNodeKeys and add its inner arcs to the list
            not_valid_arcs_list = []
            for n in myNet.nodes:
                if n.id in nonValidNodeKeys:
                    not_valid_arcs_list.extend(n.innerArcs)
            # If this arc variable is 1, then all the variables in the not_valid_arcs_list must be 0
            if len(not_valid_arcs_list)>0:
                invalidArcsFlows = UC_Model.UCNetworkModel.sum(x[(not_valid_arc._n1.id, not_valid_arc._n2.id)] for not_valid_arc in not_valid_arcs_list)
                UC_Model.UCNetworkModel.add_constraint(UC_Model.UCNetworkModel.if_then(x[(a._n1.id, a._n2.id)] >= 1, invalidArcsFlows <= 0 ))
        

        print("I added all the constraints\n")
        # return UC_Model.UCNetworkModel

    @staticmethod
    def getSingletonModel():
        assert  UC_Model.UCNetworkModel is not None, "UC_Model.UCNetworkModel must be not None"
        return UC_Model.UCNetworkModel


if "__main__" == __name__:
    # import sys
    # print(sys.setrecursionlimit(100000)) # DANGER

    ######################################################
    print("****** STARTING CREATING THE NETWORK ******")
    now = datetime.datetime.now()
    myNet = UC_Network.createModelFromInput()
    after = datetime.datetime.now()
    print("****** NETWORK CREATED IN ", after-now, " ******\n\n")
    ######################################################

    
    ######################################################
    print("****** I'M CREATING THE MODEL TO SOLVE THE UNIT COMMITMENT PROBLEM ******")
    now = datetime.datetime.now()
    UC_Model.generateUCNetworkModel(myNet)
    UCNetworkModel = UC_Model.getSingletonModel()
    after = datetime.datetime.now()
    UCNetworkModel.print_information()
    print("****** UNIT COMMITMENT (NETWORK) MODEL CREATED IN ", after-now, " ******\n\n")
    ######################################################


    ######################################################
    # # solve the model and print the solution
    print("****** I'M SOLVING THE MODEL ******")
    now = datetime.datetime.now()
    modelSolution = UCNetworkModel.solve()
    after = datetime.datetime.now()
    if modelSolution:
        modelSolution.display()
        print("****** MODEL SOLVED IN ", after-now, " ******\n\n")
    else:
        print("****** MODEL NOT SOLVED ******\n\n")
    ######################################################


    ######################################################
    utils.plotNetworkWithSolution(myNet, modelSolution)
    ######################################################

