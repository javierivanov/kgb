import pandas as pd

from py2neo import Graph
graph = Graph(password="admin")

df = pd.read_csv("data/data.csv", skiprows=1)


product_list = ['Ambari','Hdfs', 'Yarn', 'Zookeeper', 'Slider', 'Cascading', 'SmartSense',
       'Ambari(Advanced)', 'Cloudbreak', 'DPS', 'Oozie', 'Hue', 'Falcon',
       'Hive', 'Pig', 'Sqoop', 'Druid', 'Map Reduce', 'Tez', 'HBase', 'Phoenix',
       'Accumulo', 'SOLR (HDFS)', 'SOLR (Ranger)', 'Schema Registry',
       'SAM', 'Storm', 'Kafka', 'Metron', 'Flume', 'Spark', 'Zeppelin',
       'SuperSet', 'Mahout', 'Kerberos', 'Ranger', 'Knox',
       'Atlas', 'Kms']

mappings = {"Ambari(Basics)": "Ambari",
            'Ambari(Advanced)': 'Ambari',
            'SOLR (HDFS)': 'SOLR',
            'SOLR (Ranger)': 'SOLR',
            }

# s = df[product_list].describe().T['75%']
s = df[product_list].quantile(.8).T

sme = df[product_list].quantile(.95).T

for product in product_list:
    persons = df[df[product] > s[s.index == product].values[0]][['Team Member', 'Shift', 'eMaildID']].values
    persons_sme = df[df[product] > sme[sme.index == product].values[0]][['Team Member', 'Shift', 'eMaildID']].values
    if product in mappings:
        product = mappings[product]
    for person, shift, email in persons:
        query  = ' merge (p: Person {name: "%s", shift: "%s", email: "%s"})' % (person, shift, email)
        query += ' merge (c: Component {name: "%s"})' % product
        query += ' merge (p)-[:KNOWS]->(c)'
        print(query)
        graph.run(query)

    for person, _, _ in persons_sme:
        query = 'match (p:Person {name:"%s"})-[r]-(c:Component {name:"%s"}) SET r.level_component="SME"' % (person, product)
        print(query)
        graph.run(query)
