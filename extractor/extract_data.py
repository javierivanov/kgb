import json
import networkx as nx
import re
data = json.load(open('asd.json', 'r'))

p = re.compile('[A-Z]+$')
nodes = list(set([x['bug'].split("-")[0] for x in data if x['bug'] is not None]))
nodes = [node for node in nodes if p.match(node) is not None]

G = nx.Graph()
for node in nodes:
    G.add_node(node)

