from spacy import displacy
from spacy.matcher import Matcher, PhraseMatcher

import json
import plugins
from plugins.constants import ENTITY, ATTR, REL
import sys
import networkx as nx
from py2neo import Graph
import spacy



class KGB:
    def __init__(self, nlp, graph, debug):
        self.debug = debug
        self.nlp = nlp
        self.graph = graph
        self.phrase_matcher_shapes = PhraseMatcher(self.nlp.vocab, attr="SHAPE")
        self.phrase_matcher_texts = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.slots = []
        self.actions = []
        self.mapper = {}

        loaded_plugins_str = []
        self.loaded_plugins = []
        for item in dir(plugins):
            if not (item.startswith("__") and item.endswith("__")):
                plugin = "plugins."+item+"."+item.capitalize()
                try:
                    mod = __import__('plugins.'+item, fromlist=[item.capitalize()])
                    klass = getattr(mod, item.capitalize())
                    if klass.__base__ == plugins.plugin.Plugin:
                        impl = klass()
                        impl.set_connectors(self.graph, self.nlp)
                        phrase_matcher_shapes_dict = {}
                        phrase_matcher_texts_dict = {}
                        impl.adding_matcher(self.slots, self.actions, self.mapper, phrase_matcher_shapes_dict, phrase_matcher_texts_dict)
                        for key in phrase_matcher_shapes_dict:
                            self.phrase_matcher_shapes.add(key, None, *phrase_matcher_shapes_dict[key])
                        for key in phrase_matcher_texts_dict:
                            self.phrase_matcher_texts.add(key, None, *phrase_matcher_texts_dict[key])
                        loaded_plugins_str += [plugin]
                        self.loaded_plugins += [impl]
                        try:
                            impl.run_extractor()
                            print(item)
                        except NotImplementedError as e:
                            pass
                except ModuleNotFoundError:
                    pass
                except AttributeError:
                    pass


        if self.debug:
            print("Loaded plugins", loaded_plugins_str)
            print("Mappings:", self.mapper)


    def parse(self, document):
        self.extracted_nodes_and_rels = []
        text_ = document.text
        for idx, start,end in self.phrase_matcher_shapes(document)+self.phrase_matcher_texts(document):
            new_rep = document[start:end].text.replace(" ", ".")
            # print(new_rep, idx)
            text_ = text_.replace(document[start:end].text, new_rep)
            self.extracted_nodes_and_rels += [(self.slots[idx-1], new_rep)]
        # Extracting entities
        # displacy.render(document)
        
        self.root_str = list(document.sents)[0].root.text
        a=self.root_str 
        if self.root_str not in self.actions:
            for token in document:
                if token.text.upper() in self.actions:
                    self.root_str = token.text.upper()
        print(a, self.root_str)

        self.document = self.nlp(text_)
        
        
        if self.debug:
            print('Question: {0}'.format(self.document.text))
            

        
        edges = []

        for token in self.document:
            for child in token.children:
                edges.append((token.text, child.text))
        self.G = nx.Graph(edges)

        if self.debug:
            print("Nodes", self.extracted_nodes_and_rels)
        
        self.extracted_nodes = [x for x in self.extracted_nodes_and_rels if "/" not in x[0]]
        self.extracted_rels = [x for x in self.extracted_nodes_and_rels if "/" in x[0]]
        self.extracted_entities = [x for x in self.extracted_nodes_and_rels if "<<Entity>>" == x[0]]
        self.extracted_results = self.extracted_entities
        self.extracted_results += [x for x in self.extracted_rels if x[0].split("/")[1] == ""]
        
        if self.debug:
            print("looking for:", self.extracted_results)
        self.child_attrs = {}
        self.child_attrs2 = {}
        for rel in self.extracted_rels:
            nodes_ = []
            for node in self.extracted_nodes:
                distance = float("inf")
                try:
                    distance = nx.shortest_path(self.G, source=rel[1], target=node[1]).__len__()
                except:
                    pass
                if distance != float("inf"):
                    if self.__node_has_rels(node, rel):
                        if self.debug:
                            print("connected elements",rel, node, distance)
                            nodes_ += [(distance, node)]
                    else:
                        if self.debug:
                            print("not connected elements",rel, node, distance)
                    
            nodes_.sort()
            
            if nodes_.__len__() == 0:
                continue
            
            dist, nodes = zip(*nodes_)
            if dist[0] in dist[1:]:
                ## fight best
                if self.debug:
                    print("Note: same distance for Rel/Attr with nodes")
                    print("Checking in self.graph to confirm")
                    print(nodes_, rel)
                found_attr = False
                for node_ in nodes:
                    lookup = None
                    if node_[0] == "<<Entity>>":
                        lookup = self.mapper[node_[1].lower()]
                    else:
                        lookup = node_[0]

                    if rel[0] == 'Attr/':
                        lookup = "match (n: %s) return distinct keys(n)" % lookup
                        for attr in list(self.graph.run(lookup))[0]['keys(n)']:
                            if attr.lower() == self.mapper[rel[1].lower()]:
                                nodes = [node_]
                                found_attr = True
                                break
                    elif rel[0] == 'Rel/':
                        lookup_ = "match (n: %s)-[r]-() return distinct keys(r)" % lookup
                        out_matching_list = []
                        for rels in self.graph.run(lookup_):
                            out_matching_list += rels['keys(r)']
                        if self.mapper[rel[1].lower()] + "_" + lookup.lower() in set(out_matching_list):
                            nodes = [node_]
                            found_attr = True
                            break
                    if found_attr:
                        if self.debug:
                            print("Connection found")
                        break

            if nodes[0] not in self.child_attrs2.keys():
                self.child_attrs2[nodes[0]] = [rel]
            else:
                self.child_attrs2[nodes[0]] += [rel]
            self.child_attrs[rel] = nodes[0]
        if self.debug:
            print("self.child_attrs2", self.child_attrs2)
            print("self.child_attrs", self.child_attrs)
        
        return self.__execute__()

    def __node_has_rels(self, node, rel):
        if node[0] == ENTITY:
            node_ = self.mapper[node[1].lower()]
        else:
            node_ = node[0]
        if rel[0] == REL:
            rel_ = self.mapper[rel[1].lower()]
            type_ = REL
        elif "/Rel" in rel[0]:
            rel_ = rel[0].split("/")[0]
            type_ = REL
        elif rel[0] == ATTR:
            rel_ = self.mapper[rel[1].lower()]
            type_ = ATTR
        elif "/Attr" in rel[0]:
            rel_ = rel[0].split("/")[0]
            type_ = ATTR
        if self.debug:
            print("--->",rel_, type_, ';', node, rel)
        for p in self.loaded_plugins:
            if type_ == ATTR:
                if rel_ in p.sample_attrs:
                    if p.sample_attrs[rel_]['node'] == node_: return True
            if type_ == REL:
                if rel_ in p.sample_rels:
                    for x in p.sample_rels[rel_]['nodes']:
                        if x[0] == node_: return True
        
        return False

        
    def level2_parse(self):
        node = self.extracted_nodes[0]
        inner_node = self.extracted_nodes[1]

        if self.debug:
            print("Matching nodes", node, inner_node)

        link = []
        try:
            link = nx.shortest_path(self.G, source=node[1], target=inner_node[1])[1:-1]
        except:
            pass

        for l in link:
            if len([l for x in self.document if l == x.text and x.pos_ == "VERB"]) == 0:
                link.remove(l)
        if len(link) == 0:
            link = [self.root_str]

        if self.debug:
            print("Link", link)

        node_cypher = []
        for idx, n in enumerate([node, inner_node]):
            if n[0] == "<<Entity>>":
                node_cypher += ["(n%d:%s)" % (idx, self.mapper[n[1].lower()])]
            else:
                node_cypher += ["(n%d:%s)" % (idx, n[0])]
                    
        
        if self.debug:
            print(inner_node)
            print("match %s-[r]-%s return distinct type(r)" % (node_cypher[0], node_cypher[1]))
        
        best_result = 0
        rel_action = None
        for result in self.graph.run("match %s-[r]-%s return distinct type(r)" % (node_cypher[0],
                                                                             node_cypher[1])):
            rel_ = result["type(r)"].split("_")
            simil_score = self.nlp(" ".join(rel_)).similarity(self.nlp(" ".join(link)))
            # print(result, simil)
            if best_result < simil_score:
                best_result = simil_score
                rel_action = result["type(r)"]
        
        if rel_action is None:
            rel_action = ""
        else:
            rel_action = ":%s" % rel_action
        
        rel_attrs = {}
        for child in self.child_attrs.keys():
            if child[0].split("/")[1] == 'Rel':
                node_ = self.child_attrs[child]
                if self.debug:
                    print("node_", node_)
                if node_[0] == "<<Entity>>":
                    aux = self.mapper[node_[1].lower()]
                    key_ = child[0].split("/")[0].lower() + "_" + aux.lower() # version_entity
                    rel_attrs[key_] = child[1]
                else:
                    key_ = child[0].split("/")[0].lower() + "_" + node_[0].lower()
                    rel_attrs[key_] = child[1]
        
        if self.debug:
            print("rel_attrs", rel_attrs)
        
        where_clause = ["r.%s=~'(?i)%s'"%(x, rel_attrs[x]) for x in rel_attrs.keys()]
        
        for idx, node_ in enumerate([node, inner_node]):
            if node_[0] != "<<Entity>>":
                ##Checking for synonyms
                aux = []
                for x in self.loaded_plugins:
                    y=x.check_synonym(node_[1])
                    if y is not None:
                        aux += [y]
                if len(aux) == 0:
                    aux_name = node_[1]
                else:
                    aux_name = aux[0]
                where_clause += ["n%d.name=~'(?i)%s'" % (idx, aux_name)]
            if node_ in self.child_attrs2.keys():
                for child in self.child_attrs2[node_]:
                    if child[0].split("/")[1] == "Attr":
                        where_clause += ["n%d.%s=~'(?i)%s'" % (idx, 
                                                               child[0].split("/")[0].lower(),
                                                               child[1])]
        if self.debug:
            print(where_clause)
        if len(where_clause) == 0:
            where_clause = ""
        else:
            where_clause = "where " + " and ".join(where_clause)

        if self.debug:
            print(best_result)
            print("match %s-[r%s]-%s return distinct type(r)" % (node_cypher[0],
                                                                 rel_action,
                                                                 node_cypher[1]))
            print("Rels", self.extracted_rels)
            print("Entity", self.extracted_entities)
            print("match %s-[r%s]-%s %s return distinct n0, r, n1" % (node_cypher[0],
                                                                              rel_action,
                                                                              node_cypher[1],
                                                                              where_clause))

        ret = list(self.graph.run("match %s-[r%s]-%s %s return distinct n0, r, n1" % (node_cypher[0],
                                                                              rel_action,
                                                                              node_cypher[1],
                                                                              where_clause)))
        
        results_output = []
        if self.debug:
            print("List of results:", ret)
        for r in ret:
            aux_dict = {}
            for idx, n in enumerate(self.extracted_nodes):
                if self.debug:
                    print("Extracted results", n, self.extracted_results)
                if n in self.extracted_results:
                    if self.debug:
                        print("Results:", n, r['n'+str(idx)]['name'])
                    if n[0] == "<<Entity>>":
                        aux_dict[self.mapper[n[1].lower()]] = r['n'+str(idx)]['name']
                    else:
                        aux_dict[n[0]] = r['n'+str(idx)]['name']
                if len(self.extracted_results) == 0:
                    for k in r['r'].keys():
                        aux_dict[k.split("_")[0].capitalize()] = r['r'][k]

            for child in self.child_attrs.keys():
                if child[0] == "Rel/":
                    key_ = self.mapper[child[1].lower()].lower() + "_"
                    node_ = self.child_attrs[child]
                    if node_[0] == "<<Entity>>":
                        node_[1] == self.mapper[node_[1].lower()]
                        key_ += node_[1].lower() # version_entity
                    else:
                        key_ += node_[0].lower()
                    if self.debug:
                        print("Results:", child, r['r'], key_, r['r'][key_])
                    if r['r'][key_] is not None:
                        aux_dict[self.mapper[child[1].lower()]] = r['r'][key_]
            if aux_dict == {}:
                aux_dict = True
            if aux_dict not in results_output:
                results_output += [aux_dict]
        if len(results_output) == 0:
            results_output = [None]
        return json.dumps(results_output)

    def level1_parse(self):
        if self.debug:
            print("extracted_nodes", self.extracted_nodes)
            print("root_str", self.root_str)
        
        node_cypher = ""


        where_clause = []
        if self.extracted_nodes[0][0] != "<<Entity>>":
            node_cypher = "n: %s" % self.extracted_nodes[0][0]
            ##Checking synonyms
            aux = []
            for x in self.loaded_plugins:
                y=x.check_synonym(self.extracted_nodes[0][1])
                if y is not None:
                    aux += [y]
            
            if len(aux) == 0:
                aux_name = self.extracted_nodes[0][1]
            else:
                aux_name = aux[0]

            where_clause += ["n.name=~'(?i)%s'" % aux_name]
        else:
            node_cypher = "n: %s" % self.mapper[self.extracted_nodes[0][1].lower()]

        
        best_result = 0
        rel_action = None
        if self.debug:
            print("Check actions:","match (%s)-[r]-() return distinct type(r)" % (node_cypher))

        for result in self.graph.run("match (%s)-[r]-() return distinct type(r)" % (node_cypher)):
            rel_ = result["type(r)"].split("_")
            simil_score = self.nlp(" ".join(rel_)).similarity(self.nlp(self.root_str))
            if best_result < simil_score:
                best_result = simil_score
                rel_action = result["type(r)"]
        
        if self.root_str in self.actions:
            rel_action = self.root_str
            best_result = 1

        if best_result < .5:
            rel_action = "r"
        else:
            rel_action = "r:" + rel_action
        if self.debug:
            print("rel_action", rel_action)

        added_node = None
        if rel_action != "r":
            for res in self.graph.run("match (%s)-[%s]-(d) return distinct labels(d)" % (node_cypher, rel_action)):
                if len(self.extracted_results)==0:
                    if self.debug:
                        print("Added node: ", res['labels(d)'][0])
                    added_node = ":%s" % res['labels(d)'][0]



        if self.extracted_nodes[0] in self.child_attrs2:
            for attr in self.child_attrs2[self.extracted_nodes[0]]:
                attr_ = attr[0].split("/")[0].lower()
                val_ = attr[1]

                if attr[0].split("/")[1] == 'Attr':
                    where_clause += ['n.%s=~"(?i)%s"' % (attr_, val_)]
                if attr[0].split("/")[1] == 'Rel':
                    out_ = []
                    for i in self.graph.run("match (%s)-[r]-() return distinct keys(r)" % (node_cypher)):
                        out_ += i['keys(r)']
                    for o in set(out_):
                        if o.lower() == attr_ or o.split("_")[0].lower() == attr_:
                            where_clause += ['r.%s=~"(?i)%s"' % (o, val_)]
        
        if len(where_clause) > 0:
            where_clause = "where " + " and ".join(where_clause)
        else:
            where_clause = ""
        if added_node is None: 
            node_type = ""
        else:
            node_type = added_node
        if self.debug:

            print("match (%s)-[%s]-(d%s) %s return distinct n, r, d" % (node_cypher, rel_action, node_type, where_clause))

        results_output = []
        for ret in self.graph.run("match (%s)-[%s]-(d%s) %s return distinct n, r, d" % (node_cypher, rel_action, node_type, where_clause)):
            if self.debug:
                print(ret, results_output)
            result_output = {}
            if added_node is not None:
                result_output[node_type[1:]] = ret['d']['name']
            for e_result in self.extracted_results:
                if e_result[0] == "<<Entity>>":
                    result_output[self.mapper[e_result[1].lower()]] = ret['n']['name']
                if e_result[0] == 'Attr/':
                    result_output[self.mapper[e_result[1].lower()]] = ret['n'][self.mapper[e_result[1].lower()].lower()]
                if e_result[0] == 'Rel/':
                    rel = self.mapper[e_result[1].lower()]
                    for rel_ in ret['r'].keys():
                        if rel in rel_:
                            result_output[rel_] = ret['r'][rel_]
                            break
            if result_output not in results_output:
                results_output += [result_output]
        
        return json.dumps(results_output)
    
    def __execute__(self):
        if len(self.extracted_nodes) > 2:
            return json.dumps(["No answers yet"])
        if len(self.extracted_nodes) == 2:
            return self.level2_parse()
        if len(self.extracted_nodes) == 1:
            return self.level1_parse()


# documents = [
#              self.nlp("Versions affected in Spark by SPARK-12345"),
#              self.nlp("what is the component version affected by HBASE-4321"),
#              self.nlp("who is reporting SPARK-12345"),
#              self.nlp("reporting who SPARK-12345"),
#              self.nlp("Show all Open Jiras with High Priority"),
#              self.nlp("Who is assigned to HBASE-4321"),
#              self.nlp("Open jiras for versions 2.4.0"),
#              self.nlp("What is the status of SPARK-12345"),
#              self.nlp("Is Spark 2.3.2 is affected by SPARK-12345"),
#              self.nlp("What is the Ranger version that comes with HDF 3.4.0"),
#              self.nlp("Show all open jiras reported by Jack Daniels"),
#              self.nlp("show product with high priority jiras reported by Elvis Tek"),
#              self.nlp("show high priority jiras reported by Elvis Tek"),
#              self.nlp("Who is Zeppelin SME"),
#              self.nlp("Who is SME for Zeppelin")
#             ]

# test_document(self.nlp("What is the Ranger version that comes with HDF 3.4"), True)





# print("#"*30)
# for doc in documents:
#     print(doc)
#     # displacy.render(doc)
#     k = KGB(doc, True)
#     print("JSON Output: ", k.parse())
#     print("#"*30)
    

# while True:
#     print("#"*60)
#     question = input("Add question: ")
#     question = self.nlp(question)
#     # displacy.serve(question)
#     print(KGB(question, True).parse())
#     print("#"*60)
#     print()

# doc = self.nlp("Show all open jiras reported for Apache Atlas")
# extracted_nodes_and_rels = []
# displacy.render(doc)
# query_parser(doc, True)

# Who is Zeppelin SME

# Who is SME for Zeppelin


# print(test_document(self.nlp("Show all Open Jiras with High Priority"), True))



# relationships = ["FIXED_IN",
#                  "AFFECTS",
#                  "ASSIGNED_TO",
#                  "REPORTS"]

# for rel in relationships:
#     doc_rel = self.nlp(" ".join(rel.split("_")).lower())
#     doc_estimated_rel = self.nlp("Show")
#     print(doc_rel, doc_rel.similarity(doc_estimated_rel))




# 3+ entities (and/or/if operators)
# 2 entites (rel/only operations - > relation data/destination node data/)
# 1 entity (Attribute reference)



if __name__ == "__main__":
    nlp = spacy.load('en_core_web_lg')
    print("NLP Model Loaded")
    # self.nlp = spacy.load('en')
    graph = Graph(password="admin")
    engine = KGB(nlp, graph, True)

    docs = [
        nlp("list kafka topics"),
        nlp("command to list kafka topic"),
        nlp("how to list kafka topic"),
        nlp("what is the command to list kafka")
    ]
    for doc in docs:
        print("#"*60)
        res = engine.parse(doc)
        print("#"*60)
        print(res)
        print()