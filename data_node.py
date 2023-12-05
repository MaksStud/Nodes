from queue import Queue
from flask import Flask, make_response, request


class DataNode:
    def __init__(self, user_port, user_host='0.0.0.0'):
        self.data = Queue()
        self.copy_data = Queue()
        self.port = user_port
        self.user_host = user_host

        self.app = Flask(__name__)
        self.app.add_url_rule('/receive', 'get_data', self.get_data)
        self.app.add_url_rule('/receiveCopy', 'get_data_from_copy', self.get_data_from_copy)
        self.app.add_url_rule('/send', 'set_data', self.set_data, methods=['POST'])
        self.app.add_url_rule('/sendNewCopy', 'set_full_copy', self.set_full_copy, methods=['POST'])
        self.app.add_url_rule('/stats', 'workload', self.workload)
        self.app.add_url_rule('/sendCopy', 'set_copy_data', self.set_copy_data, methods=['POST'])
        self.app.add_url_rule('/transfer', 'transferring_data', self.transferring_data, methods=['POST'])
        self.app.add_url_rule('/receiveFullData', 'get_full_data', self.get_full_data)

    def set_data(self):
        '''Додає нові дані'''
        new_data = request.data.decode('utf-8')
        self.data.put(new_data)
        print(f"add new message = {new_data}")
        return make_response()

    def set_full_copy(self):
        '''отримвє нову копію ноди'''
        self.copy_data = Queue()
        new_copy = request.data.decode('utf-8')
        new_copy_data = eval(new_copy)
        for element in new_copy_data:
            self.copy_data.put(element)
        return make_response()

    def transferring_data(self):
        '''Переносить комію даних в основний потік'''
        while not self.copy_data.qsize() == 0:
            element = self.copy_data.get()
            self.data.put(element)
        return 'Transfer is done'

    def set_copy_data(self):
        '''Додає нову комію'''
        new_copy = request.data.decode("utf-8")
        self.copy_data.put(new_copy)
        print(f"add new copy = {new_copy}")
        return make_response()

    def get_full_data(self):
        '''повертає список всіх елементів черги'''
        if not self.data.empty():
            return str(list(self.data.queue))
        elif self.data.empty():
            return "no data"

    def get_data(self):
        '''Віддає дані'''
        if self.data.qsize() > 0:
            return str(self.data.get())
        elif self.data.empty():
            return "None"

    def get_data_from_copy(self):
        '''Віддає дані з копії'''
        if self.copy_data.qsize() > 0:
            return str(self.copy_data.get())
        elif self.copy_data.empty():
            return "None"

    def workload(self):
        '''Повертає загруженість'''
        return str((self.data.qsize(), self.copy_data.qsize()))

    def run(self):
        self.app.run(host=self.user_host, port=self.port, threaded=True, debug=True)
