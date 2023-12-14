from flask import Flask, request, make_response, render_template
import requests as rq
from data_node import DataNode
import threading
from flask_socketio import SocketIO
import matplotlib.pyplot as plt
from io import BytesIO
import base64


class ControlNode:
    def __init__(self, port=5000, user_host='0.0.0.0'):
        self.user_host = user_host
        self.port = port
        self.stats = {}
        self.node_list = []

        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        self.app.config['chart_image'] = ''

        self.app.add_url_rule('/add/<address>', 'add_node', self.add_node, methods=['POST'])
        self.app.add_url_rule('/remove/<address>', 'remove_node', self.remove_node, methods=['POST'])
        self.app.add_url_rule('/list', 'list_of_nodes', self.list_of_nodes)
        self.app.add_url_rule('/stats', 'get_stats', self.get_stats)
        self.app.add_url_rule('/send', 'send_data', self.send_data, methods=['POST'])
        self.app.add_url_rule('/receive', 'receive_data', self.receive_data)
        self.app.add_url_rule('/', 'index', self.index)
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('disconnect', self.handle_disconnect)

    def add_node(self, address):
        if address not in self.node_list:
            self.node_list.append(address)
            return make_response()
        else:
            return "This address is already occupied"

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
        address_to_send = min(self.stats.items(), key=lambda item: item[1][0])[0]
        index_to_copy = self.node_list.index(address_to_send)
        if index_to_copy == len(self.node_list) - 1:
            address_to_copy = self.node_list[0]
        else:
            address_to_copy = self.node_list[index_to_copy+1]
        result = rq.post(f"http://{self.user_host}:{address_to_send}/send", data=request.data.decode("utf-8"))
        result_copy = rq.post(f"http://{self.user_host}:{address_to_copy}/sendCopy", data=request.data.decode("utf-8"))

        self.get_stats()
        self.update_diagram()

        return make_response()

    def receive_data(self):
        self.get_stats()
        address_to_receive = max(self.stats.items(), key=lambda item: item[1][0])[0]
        index_to_copy = self.node_list.index(address_to_receive)
        if index_to_copy == len(self.node_list) - 1:
            address_to_receive_copy = self.node_list[0]
        else:
            address_to_receive_copy = self.node_list[index_to_copy+1]
        result = rq.get(f"http://{self.user_host}:{address_to_receive}/receive")
        result_copy = rq.get(f"http://{self.user_host}:{address_to_receive_copy}/receiveCopy")

        with open("result.txt", "a") as file:
            if result.text != '':
                file.write(result.text + '\n')

        self.get_stats()
        self.update_diagram()
        
        return result.text.encode("utf-8")
 
    def get_stats(self):
        for i, node in enumerate(self.node_list):
            try:
                result = rq.get(f"http://{self.user_host}:{node}/stats")
            except Exception:
                if i < len(self.node_list) - 1 and i > 0:
                    rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/transfer")
                    copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=copy.text)

                    new_copy = rq.get(f"http://{self.user_host}:{self.node_list[i+1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[i-1]}/sendNewCopy", data=new_copy.text)

                elif  i >= len(self.node_list) - 1 and i > 0: 
                    rq.post(f"http://{self.user_host}:{self.node_list[0]}/transfer")
                    copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[0]}/sendNewCopy", data=copy.text)

                    new_copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[0]}/sendNewCopy", data=new_copy.text)

                elif i < len(self.node_list) - 1 and i == 0:
                    rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/transfer")
                    copy = rq.get(f"http://{self.user_host}:{self.node_list[-1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=copy.text)

                    new_copy = rq.get(f"http://{self.user_host}:{self.node_list[-1]}/receiveFullData")
                    rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=new_copy.text)

                self.stats.pop(node)
                self.node_list.pop(i)
                self.stats = self.get_stats()
                break
            else:
                if result.status_code == 200: 
                    node_stats = eval(result.text)
                    self.stats[node] = node_stats
                else:
                    if i < len(self.node_list) - 1 and i > 0:
                        rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/transfer")
                        copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=copy.text)

                        new_copy = rq.get(f"http://{self.user_host}:{self.node_list[i+1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[i-1]}/sendNewCopy", data=new_copy.text)

                    elif  i >= len(self.node_list) - 1 and i > 0: 
                        rq.post(f"http://{self.user_host}:{self.node_list[0]}/transfer")
                        copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[0]}/sendNewCopy", data=copy.text)

                        new_copy = rq.get(f"http://{self.user_host}:{self.node_list[i-1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[0]}/sendNewCopy", data=new_copy.text)

                    elif i < len(self.node_list) - 1 and i == 0:
                        rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/transfer")
                        copy = rq.get(f"http://{self.user_host}:{self.node_list[-1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=copy.text)

                        new_copy = rq.get(f"http://{self.user_host}:{self.node_list[-1]}/receiveFullData")
                        rq.post(f"http://{self.user_host}:{self.node_list[i+1]}/sendNewCopy", data=new_copy.text)

                    self.stats.pop(node)
                    self.node_list.pop(i)
                    self.stats = self.get_stats()
                    break

        return self.stats
    
    def generate_diagram(self):
        servers = list(self.stats.keys())
        main_server_load = [value[0] for value in self.stats.values()]
        copy_server_load = [value[1] for value in self.stats.values()]

        bar_width = 0.35
        index = range(len(servers))

        fig, ax = plt.subplots()
        bar1 = ax.bar(index, main_server_load, bar_width, label='Основний сервер', color='blue')
        bar2 = ax.bar([i + bar_width for i in index], copy_server_load, bar_width, label='Копія збережена в сервері', color='orange')
        ax.bar_label(bar1, padding=1)
        ax.bar_label(bar2, padding=1)

        ax.set_xlabel('Сервери')
        ax.set_ylabel('Загруженість')
        ax.set_title('Загруженість серверів')
        ax.set_xticks([i + bar_width/2 for i in index])
        ax.set_xticklabels(servers)
        ax.legend()


        # Збереження графіка в байтовий об'єкт
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        # Кодування зображення в base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return image_base64
    
    def update_diagram(self):
        self.socketio.emit('chart_updated', {'chart_image': self.generate_diagram()})

    def handle_connect(self):
        print('Client connected')

    def handle_disconnect(self):
        print('Client disconnected')

    def index(self):
        return render_template('index.html')
    
    def run(self):
        self.app.run(host=self.user_host, port=self.port, threaded=True, debug=False)
        

if __name__ == '__main__':
    with open('IP.txt', 'r') as f:
        ip = f.read()

    control_node = ControlNode(5000, ip)
    
    thread = threading.Thread(target=control_node.run)
    thread.start()

    #control_node.run()

    rq.post(f"http://{ip}:5000/add/5001")
    rq.post(f"http://{ip}:5000/add/5002")
    rq.post(f"http://{ip}:5000/add/5003")