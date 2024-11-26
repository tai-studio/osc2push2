from pythonosc import dispatcher
from pythonosc import osc_server
from threading import Thread
import queue

class OSCServer:
    def __init__(self, ip = "127.0.0.1", port=50055):
        self.dispatcher = dispatcher.Dispatcher()

        self.queues = {}
        self.handles = {}

        self.server = osc_server.ThreadingOSCUDPServer(
            (ip, port), self.dispatcher)

    def addCmd(self, oscAddr: str, handler_factory):
        if oscAddr in self.queues:
            # remove all occurences
            self.dispatcher.unmap(oscAddr, self.handles[oscAddr])
            while not self.queues[oscAddr].empty():
                self.queues[oscAddr].clear()
        else:
            self.queues[oscAddr] = queue.Queue()

        self.handles[oscAddr] = self.dispatcher.map(
            oscAddr, handler_factory(self.queues[oscAddr]))
        return self

    def getLastValFor(self, oscAddr, defaultVal):
        val = defaultVal
        queue = self.queues[oscAddr]
        while not queue.empty():
            val = queue.get()
            queue.task_done()
        return val

    def getQueueFor(self, oscAddr):
        queue = self.queues[oscAddr]
        return queue


    def start(self):
        print("Starting OSC Server")
        print(f"Serving on {self.server.server_address}")
        thread = Thread(target=self.server.serve_forever)
        thread.start()
        return self

    def stop(self):
        self.server.server_close()
        self.server.shutdown()
        return self
