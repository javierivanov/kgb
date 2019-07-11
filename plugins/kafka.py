from plugins.plugin import Plugin
from plugins.constants import *
from spacy.matcher import Matcher, PhraseMatcher
from py2neo import Graph
import spacy

class Kafka(Plugin):
    def __init__(self):
        super().__init__()
        
        self.inner_slots = ["Component", "Element"]
        self.inner_rels = ['Command']
        self.inner_attrs = ['']
        self.inner_actions = ['LIST', 'CREATE']

        self.sample_slots = {
            "Element": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'matching': SYNONYM_MATCH, 'synonyms': {'topic': ['topics', 'topic']}},
            "Component": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'matching': REGEX_MATCH},
        }
        self.sample_attrs = {
            
        }
        self.sample_rels = {
            "Command": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'nodes': [('Component', 'Element')], 'matching': REGEX_MATCH},
        }

        self.sample_actions = {
            "LIST" : {'synonyms': ['show']}
        }


        self.sample_entities = {
            ENTITY: {
                     "Component": ['components', 'component'],
                     "Element": ['element', 'elements'],
                    },
            ATTR: {
                  },
            REL: {"Command": ["command", "commands"]}
        }
        

    def run_extractor(self):
        query =[ '''merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:LIST {command_component: "$KAFKA_HOME/bin/kafka-topics.sh --zookeeper $ZK_HOSTS --list"}]->(e)
        ''',
        '''
        merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:CREATE {command_component: "$KAFKA_HOME/bin/kafka-topics.sh --zookeeper $ZK_HOSTS --create --topic $TOPIC_NAME --replication-factor 3 --partitions 3"}]->(e)
        ''',
        '''
        merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:PRODUCE {command_component: "bin/kafka-console-producer.sh --broker-list <BrokerHosts>:<BrokerPort> --topic <topicName> --security-protocol <SASL_PLAINTEXT/PLAINTEXT/SSL/SASL_SSL>", version_component: "0.10.0"}]->(e)
        ''',
        '''
        merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:PRODUCE {command_component: "bin/kafka-console-producer.sh --broker-list <BrokerHosts>:<BrokerPort> --topic <topicName> --producer-property security.protocol <SASL_PLAINTEXT/PLAINTEXT/SSL/SASL_SSL>", version_component: "1.0.0"}]->(e)
        create (c)-[:CONSUME {command_component: "bin/kafka-console-consumer.sh --bootstrap-server <BrokerHosts>:<BrokerPort> --topic <topicName> --security-protocol <SASL_PLAINTEXT/PLAINTEXT/SSL/SASL_SSL> --from-beginning", version_component: "1.0.0"}]->(e)
        ''',
        '''
        merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:PRODUCE {command_component: "bin/kafka-console-producer.sh --broker-list <BrokerHosts>:<BrokerPort> --topic <topicName> --producer-property security.protocol <SASL_PLAINTEXT/PLAINTEXT/SSL/SASL_SSL>", version_component: "1.0.0"}]->(e)
        create (c)-[:CONSUME {command_component: "bin/kafka-console-consumer.sh --bootstrap-server <BrokerHosts>:<BrokerPort> --topic <topicName> --consumer-property security.protocol <SASL_PLAINTEXT/PLAINTEXT/SSL/SASL_SSL> --from-beginning", version_component: "1.0.0"}]->(e)
        '''
        ]
        for q in query:
            self.graph.run(q)

        #How to list{Action} kafka(Component) topics(Element)
        #Component - List - Element