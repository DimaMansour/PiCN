import multiprocessing
import threading
import time
from fractions import Fraction as Fr
from PiCN.Processes import LayerProcess
from PiCN.Packets import Name, Interest, Content, Nack, NackReason

class NFNComputationLayer(LayerProcess):
    def __init__(self, replica_id, log_level=255):
        super().__init__(logger_name="NFNLayer (" + str(replica_id) + ")", log_level=log_level)
        self.storage = None
     #counter of number of interests per replica
    numberOfInterests = 0

    def data_from_higher(self, to_lower: multiprocessing.Queue, to_higher: multiprocessing.Queue, data):
        pass  # this is already the highest layer.

        # receive Interest from lower layer

    def data_from_lower(self, to_lower: multiprocessing.Queue, to_higher: multiprocessing.Queue, data):
        self.logger.info("Received packet")
        packet_id = data[0]
        packet = data[1]
        if isinstance(packet, Interest):
            self.logger.info("Received packet is an interest")
            self.handleInterest(packet_id, packet)
        else:
            self.logger.info("Received packet is not an interest")
            return

        # return content object (data) to the lower layer

    def return_result(self, packet_id, content: Content):
        self.queue_to_lower.put([packet_id, content])

    def return_nack(self, packet_id, interest: Interest):
        self.queue_to_lower.put([packet_id, Nack(interest.name, reason=NackReason.COMP_NOT_RUNNING,
                                                 interest=interest)])  # TODO -- choose an appropriate NACK reason

    def handleInterest(self, packet_id: int, interest: Interest):
        self.numberOfInterests += 1
        self.logger.info("number of Interests of this replica is:............" + str(self.numberOfInterests))
        components = interest.name.components
        if components[-1] == b"pNFN":
            try:
                num_params = int(components[-2])
                params = components[-num_params - 2:-2]
                params = list(map(lambda x: x.decode('utf-8'), params))
                assert (num_params < len(interest.name.components) - 2)
                function_name = components[:-num_params - 2]
                function_name = "/" + "/".join(list(map(lambda x: x.decode('utf-8'), function_name)))
            except:
                self.return_nack(packet_id, interest)
                self.logger.info("Invalid computation expression. Return NACK.")
                return
            if function_name == "/the/prefix/square1":
                arguments = [self.pinned_function_square1, params, interest.name, packet_id]
                t = threading.Thread(target=self.executePinnedFunction, args=arguments)
                t.setDaemon(True)
                t.start()
                return
            if function_name == "/the/prefix/square2":
                arguments = [self.pinned_function_square2, params, interest.name, packet_id]
                t = threading.Thread(target=self.executePinnedFunction, args=arguments)
                t.setDaemon(True)
                t.start()
                return
            if function_name == "/the/prefix/fibonacci":
                arguments = [self.fibonacci, params, interest.name, packet_id]
                t = threading.Thread(target=self.executePinnedFunction, args=arguments)
                t.setDaemon(True)
                t.start()
                return

            if function_name == "/the/prefix/bernoulli":
                arguments = [self.bernoulli, params, interest.name, packet_id]
                t = threading.Thread(target=self.executePinnedFunction, args=arguments)
                t.setDaemon(True)
                t.start()
                return

            if function_name == "/the/prefix/pascal_triangle":
                arguments = [self.pascal_triangle, params, interest.name, packet_id]
                t = threading.Thread(target=self.executePinnedFunction, args=arguments)
                t.setDaemon(True)
                #self.start = time.clock_gettime(time.CLOCK_THREAD_CPUTIME_ID)
                t.start()
                #threading.get_ident()

                #self.end = time.clock_gettime(time.CLOCK_THREAD_CPUTIME_ID)
                #self.logger.info("*********************************************" + str(self.end ) )
                return
            # if function_name == "/the/prefix/square1":
            #     result = self.pinned_function_square1(params)
            #     self.return_result(packet_id, Content(interest.name, str(result)))  # QUESTION -- return as string?
            #     self.logger.info("Result returned")
            #     return
            # elif function_name == "/the/prefix/square2":
            #     result = self.pinned_function_square2(params)
            #     self.return_result(packet_id, Content(interest.name, str(result)))  # QUESTION -- return as string?
            #     self.logger.info("Result returned")
            #     return
            else:
                self.return_nack(packet_id, interest)
                self.logger.info("Pinned function not available. Return NACK.")
                return
        else:
            self.logger.info("Received interest does not contain a computation expression")
        return
    def executePinnedFunction(self, function, params, interest_name: Name, packet_id: int ):
        result = function(params)
        content_object = Content(interest_name, str(result))
        self.queue_to_lower.put([packet_id, content_object])

    def pinned_function_square1(self, params):
        # TODO -- check if params contains valid parameters
        time.sleep(3)
        return int(pow(int(params[0]), 2))

    def pinned_function_square2(self, params):
        # TODO -- check if params contains valid parameters
        time.sleep(10)
        return int(pow(int(params[0]), 2))

    def fibonacci(self, params):
        res =[]
        x = 0
        y = 1
        while x < int(params[0]):
            res.append(x)
            x, y = y, y+x
        return res

    def bernoulli(self,params):
        t1 = time.time()
        A = [0] * (int(params[0]) + 1)
        for m in range(int(params[0])+ 1):
            A[m] = Fr(1, m + 1)
            for j in range(m, 0, -1):
                A[j - 1] = j * (A[j - 1] - A[j])
        t2 = time.time()
        exectime = t2 - t1
        self.logger.info("===============================    execution time for Bernoulli with parameter  " + str(params) + " is:  " + str(exectime))
        return A[0]

    def pascal_triangle(self,params):
        rows = [[1]]
        for i in range(int(params[0])-1):
            last_row = rows[-1]
            new_row = [1]
            for i in range(len(last_row) - 1):
                new_row.append(last_row[i] + last_row[i + 1])
            new_row.append(1)
            rows.append(new_row)
        return rows

    def ageing(self):
        pass  # ageing not necessary