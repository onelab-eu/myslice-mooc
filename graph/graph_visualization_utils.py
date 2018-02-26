from graph_tool.all import *

############### Visualization OPTIONS ################
red_color          = [0.5, 0, 0, 0.9]

green_color        = [0, 0.5, 0, 0.9]

blue_color         = [0, 0, 0.5, 0.9]

yellow_color       = [0.8, 0.8, 0, 0.9]

light_blue_color   = [0, 0, 0.9, 0.9]

black_color        = [0.5, 0.5, 0.5, 0.9]

default_edge_color = [0.179, 0.203,0.210, 0.8]

default_edge_width = 0.2

def color_dynamic_edges(g, removed, color):
    edge_color = g.edge_properties["color_edge"]

    edge_width = g.new_edge_property("float")
    g.edge_properties["width_edge"] = edge_width

    for e in g.edges():
        edge_color[e] = default_edge_color
        edge_width[e] = default_edge_width
    for e in removed:
        edge_color[e] = color
        edge_width[e] = 1.5


def graph_topology_draw(g):
    pos = sfdp_layout(g, C=200.0, K=150)
    # pos = arf_layout(g1)
    graph_draw(g, pos=pos, vertex_text=g.vertex_properties["ip_address"]
               , vertex_font_size=1, vertex_size=2, edge_pen_width=0.2, edge_marker_size=6
               # ,aspect = 12,
               , output_size=(1500, 750), output=None
               , vertex_fill_color=g.vertex_properties["color_property"])


def graph_topology_draw_dynamics(g):
    pos = sfdp_layout(g, C=200.0, K=150)
    # pos = arf_layout(g1)
    graph_draw(g, pos=pos, vertex_text=g.vertex_properties["ip_address"]
               , vertex_font_size=1, vertex_size=2, edge_marker_size=6
               # ,aspect = 12,
               , edge_color = g.edge_properties["color_edge"]
               , edge_pen_width = g.edge_properties["width_edge"]
               , output_size=(1500, 750), output=None
               , vertex_fill_color=g.vertex_properties["color_property"])