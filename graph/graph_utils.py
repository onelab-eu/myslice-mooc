import ipaddress
from graph_tool.all import *

def merge_vertices(g, v1, v2):
    ip_address_property = g.vertex_properties["ip_address"]
    edge_measurements   = g.edge_properties["edge_measurements"]
    color_edge_property = g.edge_properties["color_edge"]
    width_edge_property = g.edge_properties["width_edge"]
    edges_to_remove = set()
    edges_to_add    = set()


    v1_out_ips      = []
    v1_in_ips       = []
    # First get the ips of out and in edges of v1
    for e1 in v1.out_edges():
        v1_out_ips.append((ip_address_property[e1.target()], e1))
    for e1 in v1.in_edges():
        v1_in_ips.append((ip_address_property[e1.source()], e1))
    # Reconnect out edges
    for e2 in v2.out_edges():
        # Add it if we dont have it already
        found_target = next((v1_out_ip for v1_out_ip in v1_out_ips if ip_address_property[e2.target()] == v1_out_ip[0]), None)
        if found_target is None:
            # Reconnect the original vertex to the target.
            edges_to_add.add((v1,e2.target(), edge_measurements[e2], color_edge_property[e2], width_edge_property[e2]))
        else:
            # Tag the found link with the measurement that has discovered it
            edge_measurements[found_target[1]].extend(edge_measurements[e2])
        edges_to_remove.add(e2)
    # Reconnect in edges
    for e2 in v2.in_edges():
            # Reconnect the original vertex to the source
        found_source = next((v1_in_ip for v1_in_ip in v1_in_ips if ip_address_property[e2.source()] == v1_in_ip[0]), None)
        if found_source is None:
            edges_to_add.add((e2.source(), v1, edge_measurements[e2], color_edge_property[e2], width_edge_property[e2]))
        else:
            # Tag the found link with the measurement that has discovered it
            edge_measurements[found_source[1]].extend(edge_measurements[e2])
        edges_to_remove.add(e2)

    try:
        for edge in edges_to_add:
            new_edge = g.add_edge(edge[0], edge[1])
            edge_measurements[new_edge] = edge[2]
            color_edge_property[new_edge] = edge[3]
            width_edge_property[new_edge] = edge[4]
        for edge in edges_to_remove:
            g.remove_edge(edge)
    except ValueError as e:
        print e

def remove_duplicates(total_graph):
    ip_address_property = total_graph.vertex_properties["ip_address"]
    flow_without_mda    = total_graph.vertex_properties["flow_without_mda"]
    vertices_to_remove = []
    for v1 in total_graph.vertices():
        if v1 not in vertices_to_remove and ip_address_property[v1] != "* * *":
            duplicates = find_vertex(total_graph, ip_address_property, ip_address_property[v1])
            for duplicate in duplicates:
                if duplicate != v1:
                    merge_vertices(total_graph, v1, duplicate)
                    vertices_to_remove.append(duplicate)
                    # Set the color of the node if it was the unique flow in the duplicate and a standard interface in v1
                    if flow_without_mda[duplicate] == 4 and flow_without_mda[v1] == 2 :
                        flow_without_mda[v1] = 4
    # Remove the found duplicates
    # Weird bug from the library here...
    for v in reversed(sorted(vertices_to_remove)):
        total_graph.remove_vertex(v)



def add_domain_info(g):
    ip_address_property = g.vertex_properties["ip_address"]
    domain_name         = g.vertex_properties["domain_name"]
    for v in g.vertices():
        if domain_name[v] != "":
            ip_address_property[v] = domain_name[v] + "\n(" + ip_address_property[v] + ")"

def graph_merge(g1, g2):
    g = graph_union(g1, g2, internal_props=True, include=False)
    remove_duplicates(g)
    # print " SIZE OF BIG GRAPH: " + str(sys.getsizeof(g1))
    # print " SIZE OF BIG GRAPH: " + str(sys.getsizeof(g2))
    # print "SIZE OF EDGES : " + str(sys.getsizeof(g1.edges()))
    # print "SIZE OF EDGES : " + str(sys.getsizeof(g2.edges()))
    del g1
    del g2
    return g

def graph_vertices_diff(oldg, newg):
    ip_address_property_old = oldg.vertex_properties["ip_address"]
    ip_address_property_new = newg.vertex_properties["ip_address"]
    removed         = []
    added           = []
    for v1 in oldg.vertices():
        found = False
        for v2 in newg.vertices():
            if ip_address_property_old[v1] == ip_address_property_new[v2]:
                found = True
                break
        if not found:
            removed.append(v1)

    for v2 in newg.vertices():
        found = False
        for v1 in oldg.vertices():
            if ip_address_property_old[v1] == ip_address_property_new[v2]:
                found = True
                break
        if not found :
            added.append(v2)
    return (removed, added)


def graph_edges_diff(oldg, newg):
    ip_address_property_old = oldg.vertex_properties["ip_address"]
    ip_address_property_new = newg.vertex_properties["ip_address"]

    added   = []
    removed = []

    copyoldg = Graph(oldg)
    copynewg = Graph(newg)

    for e1 in copyoldg.edges():
        print str(e1)
        found = False
        for e2 in copynewg.edges():
            if      ip_address_property_old[e1.source()] == ip_address_property_new[e2.source()] \
                and ip_address_property_old[e1.target()] == ip_address_property_new[e2.target()] :
                found = True
                copynewg.remove_edge(e2)
                break
        if not found:
            removed.append(oldg.edge(e1.source(), e1.target()))
    for e2 in copynewg.edges():
        found = False
        for e1 in copyoldg.edges():
            if      ip_address_property_old[e1.source()] == ip_address_property_new[e2.source()] \
                and ip_address_property_old[e1.target()] == ip_address_property_new[e2.target()] :
                found = True
                copyoldg.remove_edge(e1)
                break
        if not found:
            added.append(newg.edge(e2.source(), e2.target()))
    return (removed, added)

def count_duplicate(g):
    ip_address_property = g.vertex_properties["ip_address"]

    for v1 in g.vertices():
        for v2 in g.vertices():
            if v1 != v2 and ip_address_property[v1] == ip_address_property[v2] and ip_address_property[v1] != "* * *":
                print "DUPLICATE\n"

def is_ip_in_as(ip, as_prefixes):
    try:
        for subnetwork in as_prefixes:
            if ipaddress.ip_address(unicode(ip)) in ipaddress.ip_network(unicode(subnetwork)):
                return (True, subnetwork)
    except ValueError as e:
        return (False, None)
    return (False, None)

def filter_ip_addresses(g, addresses, as_prefixes):
    ip_address_property = g.vertex_properties["ip_address"]
    addresses = filter(lambda ip: is_ip_in_as(ip_address_property[ip], as_prefixes)[0] == True, addresses)
    return addresses

def filter_edges_addresses(g, edges, as_prefixes, keep_border = False):
    ip_address_property = g.vertex_properties["ip_address"]
    # If border is True, keep edges with source OR destination in AS, otherwise,
    # keep edges with source AND destination in AS
    if keep_border:
        filtered_edges = filter(lambda e :     is_ip_in_as(ip_address_property[e.source()], as_prefixes)[0]
                                            or is_ip_in_as(ip_address_property[e.target()], as_prefixes)[0], edges)
    else:
        filtered_edges = filter(lambda e:       is_ip_in_as(ip_address_property[e.source()], as_prefixes)[0]
                                            and is_ip_in_as(ip_address_property[e.target()], as_prefixes)[0], edges)

    return filtered_edges
def print_vertex_property(vertex, property):
    print str(property[vertex])

def print_vertices_property(vertices, property):
    for v in vertices:
        print_vertex_property(v, property)


