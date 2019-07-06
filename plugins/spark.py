from plugins.plugin import Plugin
from plugins.constants import *
from spacy.matcher import Matcher, PhraseMatcher
from py2neo import Graph
import spacy

class Spark(Plugin):
    def __init__(self):
        
        self.inner_slots = ["Component", "Product"]
        self.inner_rels = ['Version']
        self.inner_attrs = []
        self.inner_actions = []

        self.sample_slots = {
            "Product": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'matching': EXACT_MATCH},
            "Component": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'mathching': REGEX_MATCH},
        }
        self.sample_attrs = {
            
        }
        self.sample_rels = {
            "Version": {'kind': SHAPE, 'source': GRAPH, 'retrieve': SOME, 'nodes': [('Component', 'Product'), ('Product', 'Component')], 'matching': REGEX_MATCH}
        }

        self.sample_entities = {
            ENTITY: {
                     "Component": ['components', 'component'],
                     "Product": ['product', 'products'],
                    },
            ATTR: {
                  },
            REL: {"version": ['version', 'versions']}
        }
        super().__init__()