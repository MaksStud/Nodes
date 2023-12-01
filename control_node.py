from flask import Flask, request, make_response
import requests as rq
from data_node import DataNode
import threading


class ControlNode:
    def __init__(self, port=5000, user_host='0.0.0.0'):
        self.user_host = user_host
        self.port = port
        self.stats = {}
        self.node_list = []

        self.app = Flask(__name__)
        self.app.add_url_rule('/add/<address>', 'add_node', self.add_node, methods=['POST'])
        self.app.add_url_rule('/remove/<address>', 'remove_node', self.remove_node, methods=['POST'])
        self.app.add_url_rule('/list', 'list_of_nodes', self.list_of_nodes)
        self.app.add_url_rule('/stats', 'get_stats', self.get_stats)
        self.app.add_url_rule('/send', 'send_data', self.send_data, methods=['POST'])
        self.app.add_url_rule('/receive', 'receive_data', self.receive_data)

    def add_node(self, address):
        self.node_list.append(address)
        return make_response()

    def remove_node(self, address):
        try:
            self.node_list.remove(address)
            return make_response()
        except ValueError:
            return "Address is not present"

    def list_of_nodes(self):
        return self.node_list

    def send_data(self):
        self.get_stats()
        address_to_send = min(self.stats, key=self.stats.get)
        index_to_copy = self.node_list.index(address_to_send)
        if index_to_copy == len(self.node_list) - 1:
            address_to_copy = self.node_list[0]
        else:
            address_to_copy = self.node_list[index_to_copy+1]
        result = rq.post(f"http://{self.user_host}:{address_to_send}/send", data=request.data.decode("utf-8"))
        result_copy = rq.post(f"http://{self.user_host}:{address_to_copy}/send_copy/{address_to_send}", data=request.data.decode("utf-8"))
        return make_response()

    def receive_data(self):
        self.get_stats()
        address_to_recieve = max(self.stats, key=self.stats.get)
        result = rq.get(f"http://{self.user_host}:{address_to_recieve}/receive")
        print(result.text)
        return result.text.encode("utf-8")
 
    def get_stats(self):
        first_stats = self.stats

        self.stats = {}
        for node in self.node_list:
            result = rq.get(f"http://{self.user_host}:{node}/stats")
            if result.status_code == 200: 
                node_stats = int(result.text)
                self.stats[node] = node_stats
            else:
                self.stats.pop(node)

        if len(first_stats) > len(self.stats):
            crashed_node = 0

            unpacked_first_stats = list(first_stats.items())
            unpacked_new_stats = list(self.stats.items())
            for i in range(len(unpacked_first_stats)):
                if unpacked_first_stats[i] not in unpacked_new_stats:
                    crashed_node = i

            if i == len(unpacked_first_stats) - 1:
                rq.post(f"http://{self.user_host}:{unpacked_first_stats[0][0]}/transfer")
            else:
                rq.post(f"http://{self.user_host}:{unpacked_first_stats[i+1][0]}/transfer")

            

        return self.stats
    
    def run(self):
        self.app.run(host=self.user_host, port=self.port, threaded=True)


if __name__ == '__main__':
    ip = '172.16.193.67'

    control_node = ControlNode(5000, ip)
    data1 = DataNode(5001, ip)
    data2 = DataNode(5002, ip)
    data3 = DataNode(5003, ip)
    
    thread1 = threading.Thread(target=control_node.run)
    thread1.start()

    thread2 = threading.Thread(target=data1.run)
    thread2.start()

    thread3 = threading.Thread(target=data2.run)
    thread3.start()

    thread4 = threading.Thread(target=data3.run)
    thread4.start()

    rq.post(f"http://{ip}:5000/add/5001")
    rq.post(f"http://{ip}:5000/add/5002")
    rq.post(f"http://{ip}:5000/add/5003")