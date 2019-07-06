from py2neo import Graph
import json

graph = Graph(password="admin")

import sys, os


elements = reversed(sorted(os.listdir("data/versions/")))
elements = [x for x in elements if x.endswith('.json')]

if len(elements) > 0:
    element = elements[0]


with open("data/versions/"+element, "r") as f:
    data  = json.load(f)
    for i in data:
        component = i['Product']
        version_component = i['Version']
        version_product = i['HDP']
        product = "HDP"
        match = '''merge (component: Component {name:"%s"})
        merge (product: Product {name:"%s"})
        merge (component)-[:PART_OF {version_component: "%s", version_product:"%s"}]->(product)''' % (component, product, version_component, version_product)
        print(match)
        graph.run(match)
        
