[Graph theory](https://pypi.org/project/graph-theory/) is a reference implementation
of all the algorithms I can find that have practical implications for solving problems
which can be modelled using nodes and edges. It has been in the works for a bit
over a year, and I'm quite happy with it's balance of simplicity, readability,
maintainability and its comprehensive interface.

The classes `BasicGraph`, `Graph` and `Graph3D`, doesn't quite cover everything 
on [RosettaCode.org](http://rosettacode.org/wiki/Rosetta_Code) but I tend to 
follow it as well as time permits.

The remaining modules in graph-theory are present to support practical problem
solving. These include solvers for:

- the assignment problem (`from assignment_problem import ap_solver`)
- the weapon-target assignment problem (`from assignment_problem import wtap_solver`)
- any finite-state machine problem (`from finite_state_machine import FiniteStateMachine`)
- three graph hashing problems (`from hash import graph_hash, flow_graph_hash, merkle_tree`) 
- randomised graph generation (`from graph.random import random_xy_graph`)


The algorithms in these modules are inspired by problems faced in the field of 
logistics and supply chain management, where disruptive events are the norm: 

>The perfect plan for the moment will have it's foundation
undermined by the next disruptive event.

I believe my academic peers refer to this situation as a mixture of:

1. The Online / Realtime problem, and 
2. The maximum delayed commitment problem.

I've tried to communicate the problem that follows when inputs change after 
computation has started, but few include that in their considerations. 

So ever since I finished my Ph.D., I've taken the practical approach and simply
asked: "For the time it takes to solve this problem, does it matter if things change?"
If the answer is yes, then we need algorithms that are suitable for 
a `volatile environment`.

Such algorithms are characterised by:
 
- The have state 
- They co-evolve with changes. The don't "reset"
- They have a minimal response time and take the initial conditions from 
the previous state. If the algorithms manage to find a better solution in the time
available, they simply switch from the solution recommended in the previous state.

In plain english you can argue these algorithms are founded in the ideas of 
optimality rather than optimum: 

> In a volative environment it's better to have a quick approximate solution, that
gets you in the right direction, rather than having to wait for the perfect plan.

The goal with the additional modules is therefore to provide a guarantee that:
1. You can `yield` from the calculation at anytime and still get a reasonable 
good solution.
2. If you have enough time, you will get to the optimal solution.

Of the work I've done so far, I believe the implementations in `hash.flow_graph_hash`, 
`Graph.maximum_flow()` and the assignment problem solvers are either original 
or I have simply failed to discover references to elsewhere.

I also have solvers for the transshipment problem and a general purpose algorithm
for scheduling, but they still need a bit of work before I'm satisfied to release
them. Contact me if you want to know more about these.


