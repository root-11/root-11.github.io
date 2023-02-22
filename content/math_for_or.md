# Math for Operations Research...

> Programming is one of the most difficult branches of applied mathematics; the poorer mathematicians had better remain pure mathematicians.
> 
> --E. W. Dijkstra

> Is math programming?<br>
> It's math in the sense that it requires abstract thought about algorithms etc.<br>
> It's engineering when it involves planning schedules, deliverables, testing.<br>
> It's art when you have no idea how it's going to eventually turn out.<br>
>
> [SO community](https://stackoverflow.com/a/137560/1186019)

---------

As a mathematician trying to plug problems with solutions, I am constantly challenged in maintaining and growing my portfolio of tricks so I can a method to solve any specifiable problem. The beauty of software and open source collaboration is that I don't have to solve the same problem twice. Once the software is written, I can share the library and move on to new challenges.

I mainly operate in the domain of logistics where the atomic unit is a box, so it may surprise you how difficult it is to prove that there is no better way to run a supply chain given a systems' variety of orders, products, mechatronics, operating costs and constraints of scheduling. Here's a flavour of a what I can meet on a typical week:

- **time-series**, determine trends and boundaries
- **data-cleaning**, determine errors in terabyte sized datasets, make substitutions, replace missing values (data imputation).
- **forecasting**, determine trends and make projections given future expectations and render projections as synthetic data.
- **optimization**, which in general is minimize or maximize some objective function. Note that this is system optimization, so problems are often beyond CPLEX or GUROBI limits, so a mixture of heuristics, genetic algorithms and fine tuned initial conditions are required to make problems solveable.
- **fault-handling**, and more importantly the control strategies that autonomously cope with faults. 
- **mechatronic system-design** where my contribution merely is how to exploit a system of lifts, sorters and conveyors to handle incoming and outgoing flows at once. This is akin to solving routing problems that have to cope with traffic jams.
- **system-design**, as all algorithms have to run on hardware and with time constraints, so understanding the limits of the world-to-model interface and designing the computer systems to match this, is a large part of the work.
- **digital-system-design**, which is focused on organising data to match use cases.
- **discrete and continues stochastics**, where translation of equipment- and human-fatigue curves influence the performance of a system. This includes detection of anomalies and drift of stochastic attributes.
- **combinatorics**, where any short-cut is worth gold interms of reducing computational complexity. The adaptive response-time for solutions are critical in real-time systems, so knowledge of wave-collapse functions are essential.
- **handling variation**. A domain where theoretical mathematicians often over-simplify to make the problem fit their methods, but where the methods simply wont work in the field of logistics.
- **human and robotic ergonomics**, and how different layouts and designs of workstations influence the performance. Smaller spaces allow for specialization and thereby faster operation, but reduces the variety that can be handled. So there's always a sweet spot.
- **competitive analysis**. Amongst all the varieties possible the final answer to what may be the best solution often comes down to a competitive analysis of optimized systems. The bottom line is total cost of ownership as the sum of installation costs, material costs, operating costs (including maintenance, FTEs and mWh).
- **stateless- vs. statefull-algorithms of all kinds**. This includes search, scheduling, routing, discrete fourier transform, multi-agent systems.

With challenges spanning such a broad range of topics it is no surprise that noone will ever know it all. 
The theoretical fields of mathematics such as graph-theory, relational-database-theory, set-theory, and game-theory interweave with more application oriented fields such as mixed integer and linear programming, discrete event simulation, decision analysis under undercertainty, materials requirement planning and scheduling. Most academics would refer to this intersection of topics as "classical operations-research" but I would like to throw a "modern" nuance into the equation: We solve problems using programs. As the simplicity of the textbook solutions easily can be dismissed as overly simplistic, the next - and somewhat obvious - step is to debate what good libraries are to solve some of these problems.

## What does a "modern" operations researcher need to know?

Due to the nature of the work, I'm very fond of the hands-on appraoch to learning:


![linkedin.com/in/aurimas-griciunas](/content/artwork/aurimas-griciunas.png)


**Start with basic processes** - e.g. learn to solve problems with Python including:

- test driven development [with pytest](https://docs.pytest.org/en/7.2.x/contents.html).
- [version control with github](https://github.com/skills/introduction-to-github) including how to create branches and contribute to development with a partner. 
- organising your code to enable you to package [python packages](https://github.com/root-11/root-11.github.io/blob/master/content/code_organisation.ipynb). 
- learn how to use [virtual environments](https://docs.python.org/3/library/venv.html) to manage dependencies.

Learning to communicate what you know is equally important, so learn to use [jupyter notebooks](https://jupyter.org/) with [markdown](https://daringfireball.net/projects/markdown/syntax) and [mathjax](https://jojozhuang.github.io/tutorial/mathjax-cheat-sheet-for-mathematical-notation/) [*](https://math.meta.stackexchange.com/questions/5020/mathjax-basic-tutorial-and-quick-reference)

A final note is that I would recommend to use [VScode](https://code.visualstudio.com/) as the IDE, although this is a personal choice. Don't try to code in `nodepad++` as it will leave your productivity at 1/10 of everyone else around you.


**Learn popular tooling** - e.g. *batch processing* using numpy, scipy or *incremental processing* using graph-theory, tablite. Learn also how to exploit sympy for solving equations and how to manage [workflows with github](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python).

- [numpy](https://numpy.org/doc/stable/index.html) provides many powerful tools for ___numeric___ data. 
- [scipy](https://docs.scipy.org/doc/scipy/tutorial/general.html) provides optimized routines for a range of functions and should be the starting point and benchmark. If the methods here are too generic or slow for your needs learn about them and use them as your test and benchmark functions.
- [sympy](https://docs.sympy.org/latest/index.html#)  which is great for solving equations.
- [google ortools](https://developers.google.com/optimization/introduction/python) which provides a comprehensive range of research tools developed at Google.

These packages are dominantly "batch processors", which mean that they consume a complete set of inputs and returns a result. This is in contrast to "incremental processors" where algorithms react to or propagate changes in a "virtual world". The difference between batch and incremental is very important as most modern OR-analytics is batch based, whilst most planners and controllers will be incremental. I won't dive deeper into this, aside from mentioning that batch-based optimization often require total control of the system in scope, where the reality in logisitcs often is more akin to a negotiation over committed and uncommitted time horizons.

**Really understand the fundamentals** - e.g. profiling, parallel processing. If you've reached this level of understanding you have probably exhausted all options above. You've tried and tested well known solutions to problems and you are stuck. This level is about learning how to make yourself "unstuck" and knowing the difference between optimum and satisfycing.

- If optimization is where you feel your strengths live, then [puLP](https://coin-or.github.io/pulp/index.html) and [scipy.milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html) are mandatory. Having written genetic algorithms from scratch, confidently be able to construct an evaluation function for the state of a system and knowing how to exploit parallel programming to explore large solution landscapes in a coordinated manner are lessons that you will have struggled with and now appreciate.

- If statistics is where you feel your strengths are, you must know about the [fast fourier transformation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.fftconvolve.html#scipy.signal.fftconvolve). You may wonder "but why?" The FFT is [such a strong tool for abstration of both discrete and continuous probabilities](https://www.youtube.com/watch?v=KuXjwB4LzSA) that there's no way around it.

- If Agent-based system design is your forte, the [maslite](https://github.com/root-11/maslite) must be no.1.

- If network analysis is where you find the most interesting challenges, then [graph-theory](https://github.com/root-11/graph-theory) and [networkx](https://networkx.org/) are mandatory.


**Specialize** - e.g. commit deep focus on solving fundamental problems.

You are now onto new horizons. There are no textbooks, so all that I can recommend is to engage with the special interest groups (SIG) on the topic. You're now on your own!


---------

Again the list above is not an exhaustive list of answers. It's a hint that has matured over the past 20 years of career. I recon it will mature more.

/B

