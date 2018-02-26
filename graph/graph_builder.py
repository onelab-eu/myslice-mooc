import re
import ipaddress
import json
from graph_tool.all import *
from graph_utils import *
from graph_visualization_utils import *

############### TRACEROUTE OPTIONS ###########
max_ttl = 30
max_interfaces = 16

############### GLOBALS   ##############################

global_stars_counter = 0

global_private_address_counter = 0

def find_hop_flow(indexes_by_hop, hop, flow_id):
    candidates_parents = indexes_by_hop[hop]
    for candidate_parent in candidates_parents:
        flows = candidates_parents[candidate_parent]
        for flow in flows:
            if flow == flow_id:
                return candidate_parent




def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)


private_ip_regex = "(^127\.)|" \
                   "(^10\.)|" \
                   "(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|" \
                   "(^192\.168\.)"

private_ip_regex_pattern = re.compile(private_ip_regex)

def is_private(ip_address):
    return re.match(private_ip_regex_pattern, ip_address)

def assign_private_id_ip(ip_address_reply, source_ip, private_ips):
    third_dot_index = findnth(ip_address_reply, ".", 3)
    unique_private_ip = ""
    if ip_address_reply.startswith("192."):
        unique_private_ip = ip_address_reply[third_dot_index:] + "/16:" + source_ip
    elif ip_address_reply.startswith("172."):
        unique_private_ip = ip_address_reply[third_dot_index:] + "/12:" + source_ip
    elif ip_address_reply.startswith("10."):
        unique_private_ip = ip_address_reply[third_dot_index:] + "/8:" + source_ip
    private_ips[ip_address_reply] = unique_private_ip
    return unique_private_ip

def init_data_structures():
    ips = {}
    indexes_by_hop = {}
    private_ips = {}
    # Init the indexes_by_hop
    for i in range(0, max_ttl):
        indexes_by_hop[i] = {}

    return (ips, indexes_by_hop, private_ips)


def init_properties(graph):
    # Setup the properties of what information we want to keep in the graph.
    ip_address  = graph.new_vertex_property("string")
    graph.vertex_properties["ip_address"] = ip_address
    domain_name = graph.new_vertex_property("string")
    graph.vertex_properties["domain_name"] = domain_name
    flows_by_vertex     = graph.new_vertex_property("vector<int>")
    edge_measurements = graph.new_edge_property("vector<string>")
    graph.edge_properties["edge_measurements"] = edge_measurements
    # Init vertex flow_without_mda_property
    flow_without_mda = graph.new_vertex_property("int")
    # 1 corresponds to source, 2 to ip interface, 3 to destination, 4 to a flow_id for richness option.
    graph.vertex_properties["flow_without_mda"] = flow_without_mda

    return (ip_address, domain_name, flow_without_mda, edge_measurements)


def init_edge_visualization_properties(graph):
    color_edge_property = graph.new_edge_property("vector<float>")
    graph.edge_properties["color_edge"] = color_edge_property

    width_edge_property = graph.new_edge_property("float")
    graph.edge_properties["width_edge"] = width_edge_property

    return (color_edge_property, width_edge_property)

def init_visualization_properties(graph):
    # Visualization properties
    color_property = graph.new_vertex_property("vector<float>")
    graph.vertex_properties["color_property"] = color_property
    text_position_property = graph.new_vertex_property("int")
    graph.vertex_properties["text_position_property"] = text_position_property
    font_size_property = graph.new_vertex_property("int")
    graph.vertex_properties["font_size_property"] = font_size_property
    size_property = graph.new_vertex_property("int")
    graph.vertex_properties["size_property"] = size_property

    return (color_property, text_position_property, font_size_property, size_property)

def init_source_vertex(graph, source_name, ips, indexes_by_hop, ip_address,
                       domain_name, flow_without_mda,  color_property, text_position_property,
                       font_size_property, size_property, nslookup):
    # Index 1 is the source

    # Check if we have the source public ip.
    # Convert to a string in case of ripe measurement
    str_source_name = str(source_name)
    if str_source_name in nslookup:
        source_ip = nslookup[str_source_name]
    else:
        raise ValueError
    ips[source_ip] = 0
    # Add all the flows for hop 0
    indexes_by_hop[0] = {0: []}
    for i in range(1, 10000):
        indexes_by_hop[0][0].append(i)
    graph.add_vertex()
    ip_address[graph.vertex(0)] = source_ip
    domain_name[graph.vertex(0)] = source_name
    flow_without_mda[graph.vertex(0)] = 1

    # Visualization properties for source
    color_property[graph.vertex(0)] = red_color
    text_position_property[graph.vertex(0)] = True
    font_size_property[graph.vertex(0)] = 12
    size_property[graph.vertex(0)] = 40

    return source_ip

def get_reached_flows(results):
    flows = []
    last_hop_replies = results[len(results) - 1]["result"]
    for reply in last_hop_replies:
        if reply["from"] != "*" :
            flows.append(reply["flow_id"])

    return flows

def build_graph_from_json(id, paris_traceroute_output, source_name, nslookup):

    dst_addr = paris_traceroute_output["dst_addr"]
    dst_name = paris_traceroute_output["dst_name"]


    (ips, indexes_by_hop, private_ips) = init_data_structures()


    graph = Graph()

    (ip_address, domain_name, flow_without_mda, edge_measurements) = init_properties(graph)

    (color_property, text_position_property, font_size_property, size_property) = init_visualization_properties(graph)

    (color_edge_property, width_edge_property) = init_edge_visualization_properties(graph)

    source_ip = init_source_vertex(graph,
                                   source_name,
                                   ips,
                                   indexes_by_hop,
                                   ip_address,
                                   domain_name,
                                   flow_without_mda,
                                   color_property,
                                   text_position_property,
                                   font_size_property,
                                   size_property,
                                   nslookup)

    index_node = 1
    # Rebuild the graph from output
    results = paris_traceroute_output["result"]
    # Pre filter the flows that have reached the destination
    unique_flow = min(get_reached_flows(results))
    for result_by_hop in results:

        hop = result_by_hop["hop"]
        replies = result_by_hop["result"]

        has_only_star = True

        for reply in replies:
            is_new_node = False
            ip_address_reply = reply["from"]

            if ip_address_reply != "*":
                has_only_star = False



            if ip_address_reply not in ips:

                if ip_address_reply not in private_ips:
                    # Handle the private ips case
                    if is_private(ip_address_reply) is not None:
                        ip_address_reply = assign_private_id_ip(ip_address_reply, source_ip, private_ips)


                    ips[ip_address_reply] = index_node
                    graph.add_vertex()
                    ip_address[graph.vertex(index_node)] = ip_address_reply
                    # Corresponds to blue color
                    if ip_address_reply == dst_addr:
                        domain_name[graph.vertex(index_node)]    = dst_name
                        # Corresponds to red color
                        color_property[graph.vertex(index_node)] = green_color
                        text_position_property[graph.vertex(index_node)]   = 0
                        font_size_property[graph.vertex(index_node)]       = 12
                        size_property[graph.vertex(index_node)]            = 40

                    else:
                        color_property[graph.vertex(index_node)] = blue_color
                        text_position_property[graph.vertex(index_node)]   = -1
                        font_size_property[graph.vertex(index_node)] = 8
                        size_property[graph.vertex(index_node)] = 4
                    is_new_node = True
                else:
                    ip_address_reply = private_ips[ip_address_reply]
            flow_id = reply["flow_id"]

            # Add this flow to the node
            indexes_hop = indexes_by_hop[hop]
            index_ip    = ips[ip_address_reply]
            if index_ip not in indexes_hop:
                indexes_by_hop[hop][index_ip] = []
            indexes_by_hop[hop][index_ip].append(flow_id)
            # Find the corresponding flow in the previous TTL.
            parent = find_hop_flow(indexes_by_hop, hop - 1, flow_id)
            if parent is not None:
                # Here we keep only one edge by pair of nodes, but it should be a parameter of the algorithm
                if graph.edge(parent, index_ip) is None:
                    graph.add_edge(parent, index_ip)
            else:
                # Lets reconnect if the ttl - 1 is all stars
                previous_hop_replies = indexes_by_hop[hop - 1]
                previous_hop_only_stars = True
                star_index = -1
                for index in previous_hop_replies.keys():
                    if ip_address[graph.vertex(index)].find("* * *") == -1:
                        previous_hop_only_stars = False
                        break
                    else :
                      star_index = index
                # If the previous hop has only stars, we can get his only key
                if previous_hop_only_stars and graph.edge(star_index, index_ip) is None:
                    graph.add_edge(star_index, index_ip)

            if is_new_node:

                index_node = index_node + 1
            # Tag it if this is a first flow that has reached the destination
            if flow_id == unique_flow and ip_address_reply != dst_addr:
                flow_without_mda[index_ip] = 4
            elif flow_id == unique_flow and ip_address_reply == dst_addr:
                flow_without_mda[index_ip] = 3
            elif ip_address_reply != dst_addr:
                if flow_without_mda[index_ip] != 4:
                    flow_without_mda[index_ip] = 2
        if has_only_star:
            stars = find_vertex(graph, ip_address, "*")
            for only_star in stars:
                # Check if we are at the good hop
                if only_star in indexes_by_hop[hop]:
                    ip_address[graph.vertex(only_star)] = "* * *"
                    global global_stars_counter
                    ips["* * *"+str(global_stars_counter)] = ips.pop("*")
                    global_stars_counter = global_stars_counter + 1

    # Put the edges property on all edges
    for edge in graph.edges():
        edge_measurements[edge]   = [id]
        color_edge_property[edge] = default_edge_color
        width_edge_property[edge] = default_edge_width

    return graph




def color_graph(g, as_prefixes, options):
    ip_address_property = g.vertex_properties["ip_address"]
    color = g.vertex_properties["color_property"]
    flow_without_mda = g.vertex_properties["flow_without_mda"]
    graph_type = options["graph_type"]
    if graph_type == "richness":
        for v in g.vertices():
            # 1 is source
            if flow_without_mda[v] == 1:
                color[v] = red_color
            # 2 is standard flow id with MDA
            elif flow_without_mda[v] == 2:
                color[v] = black_color
            # 3 is destination
            elif flow_without_mda[v] == 3:
                color[v] = green_color
            elif flow_without_mda[v] == 4:
                color[v] = light_blue_color
    elif graph_type == "as_mapping":
        for v in g.vertices():
            try:
                for subnetwork in as_prefixes:
                    if ipaddress.ip_address(unicode(ip_address_property[v])) in ipaddress.ip_network(unicode(subnetwork)):
                        if flow_without_mda[v] != 3:
                            color[v] = light_blue_color
                        else:
                            color[v] = green_color
                        break
                    else:
                        if flow_without_mda[v] == 1:
                            color[v] = red_color
                        else:
                            color[v] = yellow_color
            # Exception if private ip adress
            except ValueError as e:
                color[v] = black_color
                continue

def remove_useless_stars(output):
    result_by_hop = output["result"]
    for result in result_by_hop:
        stars_to_remove = []
        hop = result["hop"]
        replies = result["result"]
        has_only_star = True
        for reply in replies:
            ip_address_reply = reply["from"]
            if ip_address_reply != "*":
                has_only_star = False
            else:
                stars_to_remove.append(reply)
        if not has_only_star:
            for to_remove in stars_to_remove:
                replies.remove(to_remove)

def has_reached_destination(output, dst_ip):
    result_by_hop = output["result"]
    last_hop = result_by_hop[len(result_by_hop) - 1]["result"]
    for reply in last_hop:
        ip_reply = reply["from"]
        if ip_reply == dst_ip:
            return True
    return False

def compute_graph_from_db(iter, nslookup, as_prefixes, options):
    g = Graph()

    for document in iter:
        id          = document["id"]
        output      = document["stdout"]
        source_name = document["node"]
        if document["type"] == "ripe":
            output       = output.replace("u'", "\"")
            output       = output.replace("'","\"")
            ripe_output  = json.loads(output)
            # The json parsed is an array of one element
            # subgraph     = build_graph_from_json(ripe_output[0], source_name, "")
        elif document["type"] == "ple":
            paris_traceroute_output = ""
            try:
                paris_traceroute_output = json.loads(document["stdout"])
            except ValueError as e:
                print "Found an error in ", output
                print "Exception raised", e
                continue
            dst_name                = paris_traceroute_output["dst_name"]
            dst_ip                  = paris_traceroute_output["dst_addr"]
            # Test if the Paris_traceroute has reached his destination
            is_reachable = has_reached_destination(paris_traceroute_output, dst_ip)

            if is_reachable:
                # Pre filter stars that are not relevant
                remove_useless_stars(paris_traceroute_output)
                subgraph = build_graph_from_json(id, paris_traceroute_output, source_name, nslookup)

                g = graph_merge(g, subgraph)


                color_graph(g, as_prefixes, options)

    return g


def compute_graph_from_db_s_d(s_d, nslookup, as_prefixes, options):
    id = s_d["id"]
    output = s_d["stdout"]
    source_name = s_d["node"]

    paris_traceroute_output = ""
    try:
        paris_traceroute_output = json.loads(s_d["stdout"])
    except ValueError as e:
        print "Found an error in ", output
        print "Exception raised", e
    dst_name = paris_traceroute_output["dst_name"]
    dst_ip = paris_traceroute_output["dst_addr"]
    # Test if the Paris_traceroute has reached his destination
    is_reachable = has_reached_destination(paris_traceroute_output, dst_ip)
    subgraph = Graph()
    if is_reachable:
        # Pre filter stars that are not relevant
        remove_useless_stars(paris_traceroute_output)
        subgraph = build_graph_from_json(id, paris_traceroute_output, source_name, nslookup)

        color_graph(subgraph, as_prefixes, options)

    return subgraph
