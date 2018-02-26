from graph_tool.all import *
from graph_visualization_utils import *


def get_subgraph_dynamics(g):
    subgraph = Graph(g)
    color_edge_property = subgraph.edge_properties["color_edge"]

    for e in subgraph.edges():
        if color_edge_property[e] == default_edge_color:
            subgraph.remove_edge(e)

    vertices_to_remove = []
    for v in subgraph.vertices():
        if v.in_degree() == 0 and v.out_degree() == 0:
            vertices_to_remove.append(v)

    for v in reversed(sorted(vertices_to_remove)):
        subgraph.remove_vertex(v)


    return subgraph