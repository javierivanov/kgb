from plugins.plugin import Plugin
from plugins.constants import *
from spacy.matcher import Matcher, PhraseMatcher
from py2neo import Graph
import spacy

class Sme(Plugin):
    def __init__(self):
        super().__init__()
        self.inner_slots = []
        self.inner_rels = ['Level']
        self.inner_attrs = ['Shift', 'Email']
        self.inner_actions = []

        self.sample_slots = {
        }
        self.sample_attrs = {
            "Shift": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'node': 'Person', 'matching': SYNONYM_MATCH, 'synonyms': {'us.*':['us', 'america'], 'us east': ['east'], 'us west': ['pacific', 'west'], 'india.*': ['india']}},
            "Email": {'kind': SHAPE, 'source': GRAPH, 'retrieve': ALL, 'node': 'Person', 'matching': REGEX_MATCH}
        }
        self.sample_rels = {
            "Level": {'kind': TEXT, 'source': GRAPH, 'retrieve': ALL, 'nodes': [('Component', 'Person')], 'matching': EXACT_MATCH},
        }
        self.sample_actions = {
            
        }

        self.sample_entities = {
            ENTITY: {
                    },
            ATTR: {
                "Shift": ['time zone', 'timezone', 'shift'],
                "Email": ['email', 'mail', 'e-mail']
                  },
            REL: {"Level": ['knowledge', 'level'], "SME": ['Subject Matter Expert'],}
        }
        