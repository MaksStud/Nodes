from data_node import DataNode

with open('IP.txt', 'r') as file:
        ip = file.read()

data_node = DataNode(5001, ip)

data_node.run()