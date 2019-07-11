from py2neo import Graph

graph = Graph(password="admin")

graph_ops = [
'''
match ()-[r]-() delete r
'''
,
'''
match (n) delete n
'''
,
'''CREATE (jira:Jira {name:'HBASE-4321', status:"Open", priority:"High"}),
		(person1:Person {name:"person one"}),
        (person2:Person {name:"person two"}),
        (component:Component {name:"HBase"}),
        (product:Product {name:"HDP"}),
        (jira)-[:AFFECTS {version_component:"2.0.2"}]->(component),
        (person1)-[:ASSIGNED_TO {date:"June"}]->(jira),
        (person2)-[:REPORTS {date:""}]->(jira),
        (component)-[:PART_OF {version_component: "2.0.2", version_product:"3.1.0"}]->(product)
'''
,
'''merge (person1:Person {name:"person one"})
merge (person2:Person {name:"person two"})
merge (component:Component {name:"Spark"})
merge (product:Product {name:"HDP"})
merge (jira:Jira {name:'SPARK-12345', status:"Open", priority:"Low"})
merge (jira)-[:AFFECTS {version_component:"2.3.2"}]->(component)
merge (person1)-[:ASSIGNED_TO]-(jira)
merge (person2)-[:REPORTS]-(jira)
merge (component)-[:PART_OF {version_component: "2.3.2", version_product:"3.1.0"}]->(product)
'''
,
'''merge (j:Jira {name: "SPARK-12345"})
merge (c:Component {name: "Spark"})
merge (j)-[:FIXED {version_component:"2.4.0"}]->(c)'''
,
'''match (c:Component {name: "Spark"})
merge (cmd: Command {name: "Spark Submit", command:"spark-submit"})
merge (c)-[:HAS_COMMAND]->(cmd)'''
,
'''match (c:Component {name: "HBase"})
merge (cmd:Command {name:"hbase", command:"hbase"})
merge (c)-[:HAS_COMMAND]->(cmd)
''',
'''
create (c:Component {name: "Ranger"}),
        (p:Product {name:"HDF"}),
        (c)-[:PART_OF {version_component:"1.2.0", version_product:"3.4.0"}]->(p)
''',
'''merge (p: Person {name: "person one"})
merge (c: Component {name: "Spark"})
merge (p)-[:KNOWS {level_component: "SME"}]->(c)'''
]



for op in graph_ops:
    graph.run(op)