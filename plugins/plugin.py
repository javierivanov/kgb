from spacy.matcher import Matcher, PhraseMatcher
from spacy.matcher import DependencyTreeMatcher
from plugins.constants import *



class Plugin:
    def __init__(self):
        self.slots = [ENTITY, REL, ATTR]
        self.debug = False
        self.sample_slots = {}
        self.sample_entities = {}
        self.sample_rels = {}
        self.inner_slots = {}
        self.inner_rels = {}
        self.inner_attrs = {}
        self.inner_actions = {}
        self.sample_attrs = {}

    def set_connectors(self, graph, nlp):
        self.graph = graph
        self.nlp = nlp
    def adding_matcher(self,
                 slot_definitions: list,
                 action_definitions: list,
                 mapper_context: dict,
                 phrase_match_shapes: dict,
                 phrase_match_texts: dict):
        
        self.slots += self.inner_slots
        self.slots += [x + "/Rel" for x in self.inner_rels]
        self.slots += [x + "/Attr" for x in self.inner_attrs]

        action_definitions += [x for x in self.inner_actions if x not in action_definitions]
        slot_definitions += [x for x in self.slots if x not in slot_definitions]
        
        


        for elem in self.sample_entities:
            for key in self.sample_entities[elem]:
                for sub_elems in self.sample_entities[elem][key]:
                    if sub_elems not in mapper_context:
                        if " " in sub_elems:
                            mapper_context[sub_elems.replace(" ",".").lower()] = key
                        mapper_context[sub_elems] = key
                    else:
                        if self.debug:
                            print('Repeated element in Context, %s from %s' % (sub_elems, key))

        if self.debug:
            print(mapper_context)
        
        
        for u_key in [ENTITY, ATTR, REL]:
            entities_ = []
            for key in self.sample_entities[u_key]:
                if self.debug:
                    print(key, self.sample_entities[u_key][key])
                for val in self.sample_entities[u_key][key]:
                    entities_ += [self.nlp(val)]
            phrase_match_texts[slot_definitions.index(u_key)+1] = entities_


        for slot in self.sample_slots:
            if self.sample_slots[slot]['source'] == GRAPH:
                cypher_query = "MATCH (n: %s)" % slot
                if self.sample_slots[slot]['retrieve'] == SOME:
                    cypher_query += " WITH n, rand() AS r ORDER BY r RETURN DISTINCT n.name LIMIT %s" % SOME_LIMIT
                elif self.sample_slots[slot]['retrieve'] == ALL:
                    cypher_query += " RETURN DISTINCT n.name"
                slots_ = [self.nlp(result['n.name']) for result in self.graph.run(cypher_query)]
                if self.debug:
                    print(slot, cypher_query, slots_)
            elif self.sample_slots[slot]['source'] == LIST:
                slots_ = [self.nlp(x) for x in self.sample_slots[slot]['data']]

            slot_ = slot_definitions.index(slot)+1
            # slot_ = slot
            if self.sample_slots[slot]['kind'] == TEXT:
                if self.sample_slots[slot]['matching'] == SYNONYM_MATCH:
                    for synonym in self.sample_slots[slot]['synonyms']:
                        slots_ += [self.nlp(x) for x in self.sample_slots[slot]['synonyms'][synonym]]
                phrase_match_texts[slot_] = slots_

            elif self.sample_slots[slot]['kind'] == SHAPE:
                phrase_match_shapes[slot_] = slots_


        for attr in self.sample_attrs:
            if self.sample_attrs[attr]['source'] == GRAPH:
                cypher_query = "MATCH (n: %s)" % self.sample_attrs[attr]['node']
                if self.sample_attrs[attr]['retrieve'] == SOME:
                    cypher_query += " WITH n, rand() AS r ORDER BY r RETURN DISTINCT"
                    cypher_query += "n.%s LIMIT %s" % (attr.lower(), SOME_LIMIT)
                elif self.sample_attrs[attr]['retrieve'] == ALL:
                    cypher_query += " RETURN DISTINCT n.%s" % attr.lower()
                attrs_ = [self.nlp(result['n.%s' % attr.lower()]) for result in self.graph.run(cypher_query) if result['n.%s' % attr.lower()] is not None]
                if self.debug:
                    print(attr, cypher_query, attrs_)
            elif self.sample_attrs[attr]['source'] == LIST:
                attrs_ = self.sample_attrs[attr]['data']
            
            attr_ = slot_definitions.index(attr+"/Attr") + 1
            # attr_ = attr+"/Attr"
            if self.sample_attrs[attr]['kind'] == TEXT:
                phrase_match_texts[attr_] = attrs_
                if self.sample_attrs[attr]['matching'] == SYNONYM_MATCH:
                    for synonym in self.sample_attrs[attr]['synonyms']:
                        attrs_ += [self.nlp(x) for x in self.sample_attrs[attr]['synonyms'][synonym]]
            elif self.sample_attrs[attr]['kind'] == SHAPE:
                phrase_match_shapes[attr_] = attrs_


        for rel in self.sample_rels:
            if self.sample_rels[rel]['source'] == GRAPH:

                rels_ = []
                for nodes_ in self.sample_rels[rel]['nodes']:
                    node_a, node_b = nodes_
                    cypher_query = "MATCH (%s)-[r]-(%s)" % (node_a, node_b)
                    if self.sample_rels[rel]['retrieve'] == SOME:
                        cypher_query += " WITH r, rand() AS n ORDER BY n RETURN DISTINCT"
                        cypher_query += " r.%s_%s LIMIT %s" % (rel.lower(), node_a.lower(), SOME_LIMIT)
                    elif self.sample_rels[rel]['retrieve'] == ALL:
                        cypher_query += " RETURN DISTINCT r.%s_%s" % (rel.lower(), node_a.lower())
                    key_ = 'r.%s_%s' % (rel.lower(), node_a.lower())
                    rels_ += [result[key_] for result in self.graph.run(cypher_query)]

                rels_ = [self.nlp(result) for result in rels_ if result is not None]
                if self.debug:
                    print(rel, cypher_query, rels_)
            elif self.sample_rels[rel]['source'] == LIST:
                rels_ = self.sample_rels[rel]['data']
            
            rel_ = slot_definitions.index(rel+"/Rel") + 1
            # rel_ = rel+"/Rel"
            if self.sample_rels[rel]['kind'] == TEXT:
                phrase_match_texts[rel_] = rels_
            elif self.sample_rels[rel]['kind'] == SHAPE:
                phrase_match_shapes[rel_] = rels_
    
    def run_extractor(self):
        raise NotImplementedError("")
    
    def check_synonym(self, token, kind=ENTITY):
        if kind == ENTITY:
            for slot in self.sample_slots:
                if self.sample_slots[slot]['matching'] == SYNONYM_MATCH:
                    for synonym in self.sample_slots[slot]['synonyms']:
                        if token in self.sample_slots[slot]['synonyms'][synonym]:
                            return synonym
        if kind == ATTR:
            for attr in self.sample_attrs:
                if self.sample_attrs[attr]['matching'] == SYNONYM_MATCH:
                    for synonym in self.sample_attrs[attr]['synonyms']:
                        if token in self.sample_attrs[attr]['synonyms'][synonym]:
                            return synonym
        return None
    