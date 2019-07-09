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
        self.inner_actions = ['LIST']

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
        query = '''merge (c: Component {name:'Kafka'})
        merge (e: Element {name: 'Topic'})
        create (c)-[:LIST {command_component: "$KAFKA_HOME/bin/kafka-topics.sh --zookeeper $ZK_HOSTS --list"}]->(e)
        '''
        self.graph.run(query)

        #How to list{Action} kafka(Component) topics(Element)
        #Component - List - Element