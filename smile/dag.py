#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import pydot
from .state import ParentState, Serial
from .utils import get_class_name

class DAG(object):
    """
    Directed Acyclic Graph (DAG) of an experiment.
    """
    def __init__(self, base_state, fontname="Verdana"):
        """
        """
        # process the base state
        if get_class_name(base_state)[0] == 'Experiment':
            # must grab the root state
            base_state = base_state._root_state
            
        # create the starting graph
        self.graph = pydot.Dot(graph_type='digraph',
                               fontname=fontname,
                               compound='true')

        # save edges
        self.edges = []

        # add all the states
        self._add_cluster(self.graph, base_state)

        # add those edges
        for e in self.edges:
            self.graph.add_edge(e)

    def _add_cluster(self, graph, cluster):
        # get class name for state
        name, cl_uname = get_class_name(cluster)

        # strip Builder
        name = name[:-7]

        # create the cluster
        clust = pydot.Cluster(cl_uname, label=name)

        # loop over children of cluster
        nodes = []
        for i, c in enumerate(cluster._children):
            if issubclass(c.__class__, ParentState):
                # call recursively
                uname,first_uname,last_uname = self._add_cluster(clust, c)

                # save in node list
                if uname is not None:
                    nodes.append({'uname':uname,
                                  'first_uname': first_uname,
                                  'last_uname': last_uname})
            else:
                # get class name for state
                name, uname = get_class_name(c)

                # strip Builder
                name = name[:-7]

                # add the child node
                clust.add_node(pydot.Node(uname, label=name))

                # save in node list (no children for first/last)
                nodes.append({'uname':uname,
                              'first_uname': None,
                              'last_uname': None})

            # add edges if necessary
            if issubclass(cluster.__class__, Serial) and i>0:
                # set defaults
                ledge = nodes[i-1]['uname']
                redge = nodes[i]['uname']
                ltail = None
                lhead = None
                if nodes[i-1]['last_uname']:
                    # coming from cluster
                    ledge = nodes[i-1]['last_uname']
                    ltail = nodes[i-1]['uname'].get_name()
                if nodes[i]['first_uname']:
                    # going to cluster
                    redge = nodes[i]['first_uname']
                    lhead = nodes[i]['uname'].get_name()

                if ltail and lhead:
                    self.edges.append(pydot.Edge(ledge, redge,
                                                 ltail=ltail,
                                                 lhead=lhead))
                elif ltail:
                    self.edges.append(pydot.Edge(ledge, redge,
                                                 ltail=ltail))
                elif lhead:
                    self.edges.append(pydot.Edge(ledge, redge,
                                                 lhead=lhead))
                else:
                    self.edges.append(pydot.Edge(ledge, redge))

        if len(nodes) > 0:
            # insert the cluster to the graph
            graph.add_subgraph(clust)

            if nodes[0]['first_uname']:
                first_uname = nodes[0]['first_uname']
            else:
                first_uname = nodes[0]['uname']
            if nodes[-1]['last_uname']:
                last_uname = nodes[-1]['last_uname']
            else:
                last_uname = nodes[-1]['uname']
        else:
            clust, first_uname, last_uname = None, None, None

        # return the cluster uname for connections
        return clust, first_uname, last_uname

    def write(self, filename, prog='dot', format='pdf'):
        self.graph.write(filename, prog=prog, format=format)

    def view_png(self):
        from IPython.display import Image, display
        plt = Image(self.graph.create_png())
        return display(plt)

    def view_svg(self):
        from IPython.display import SVG, display
        plt = SVG(self.graph.create_svg())
        return display(plt)
