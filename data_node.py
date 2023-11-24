from queue import Queue
from flask import Flask, make_response, request


class DataNode:
    def __init__(self, user_port):
        self.data = Queue()
        self.copy_data = Queue()
        self.port = user_port

        self.app = Flask(__name__)
        self.app.add_url_rule('/receive', 'get_data', self.get_data)
        self.app.add_url_rule('/send', 'set_data', self.set_data, methods=['POST'])
        self.app.add_url_rule('/stats', 'workload', self.workload)
        self.app.add_url_rule("/send_copy", 'set_copy_data', self.set_copy_data, methods=['POST'])

    def set_data(self):
        new_data = request.data.decode('utf-8')
        self.data.put(new_data)
        print(f"add new message = {new_data}")
        return make_response()

    def set_copy_data(self):
        new_copy = request.data.decode("utf-8")
        self.copy_data.put(new_copy)
        print(f"add new copy = {new_copy}")
        return make_response()

    def get_data(self):
        if self.data.qsize() > 0:
            return str(self.data.get())
        elif self.data.empty():
            return "None"

    def workload(self):
        return str(self.data.qsize())

    def run(self):
        self.app.run(port=self.port)


if __name__ == '__main__':
    data_node = DataNode(5000)
    data_node.run()
