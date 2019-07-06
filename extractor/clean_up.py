from py2neo import Graph

graph = Graph(password="admin")

graph_ops = [
'''
match ()-[r]-() delete r
'''
,
'''
match (n) delete n
''']

for op in graph_ops:
    graph.run(op)