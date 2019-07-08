from plugins.plugin import Plugin
from plugins.constants import *
from spacy.matcher import Matcher, PhraseMatcher
from py2neo import Graph
import spacy

class Jira(Plugin):
    def __init__(self):
        super().__init__()
        
        self.inner_slots = ["Component", "Jira", "Person"]
        self.inner_rels = ['Version']
        self.inner_attrs = ["Status", "Priority"]
        self.inner_actions = []

        self.sample_slots = {
            "Person": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'matching': REGEX_MATCH},
            "Component": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'matching': REGEX_MATCH},
            "Jira": {'kind': SHAPE, 'source': GRAPH, 'retrieve': SOME, 'matching': EXACT_MATCH}
        }
        self.sample_attrs = {
            "Status": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'node': 'Jira', 'matching': EXACT_MATCH},
            "Priority": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'node': 'Jira', 'matching': EXACT_MATCH}
        }
        self.sample_rels = {
            "Version": {'kind': SHAPE, 'source': GRAPH, 'retrieve': SOME, 'nodes': [('Component', 'Jira')], 'matching': REGEX_MATCH}
        }

        self.sample_entities = {
            ENTITY: {"Jira": ['jira', 'jiras'],
                     "Component": ['components', 'component'],
                     "Person": ['who', 'engineer', 'engineers', 'person'],
                    },
            ATTR: {'Priority': ['priority'],
                   "Status": ['status'],
                   "Name": ['name']
                  },
            REL: {"Version": ['version', 'versions']}
        }
        
    
    
