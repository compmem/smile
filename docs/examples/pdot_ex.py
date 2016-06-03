#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


import pydot

g = pydot.Dot(graph_type='digraph',fontname="Verdana", compound='true')

c_exp = pydot.Cluster('exp',label='Experiment')


c_exp.add_node(pydot.Node('inst',label='Instructions'))

c_trial = pydot.Cluster('trial',label='Trial')
c_trial.add_node(pydot.Node('text',label='Text'))
c_trial.add_node(pydot.Node('resp',label='Response'))

c_exp.add_subgraph(c_trial)

c_exp.add_node(pydot.Node('debrief',label='Debrief'))

g.add_subgraph(c_exp)

g.add_edge(pydot.Edge('inst','text',lhead=c_trial.get_name()))
g.add_edge(pydot.Edge('text','resp'))
g.add_edge(pydot.Edge('resp','debrief',ltail=c_trial.get_name()))


g.write('ex_graph.pdf', prog = 'dot', format = 'pdf')

