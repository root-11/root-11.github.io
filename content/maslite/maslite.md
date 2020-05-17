MASLite ([pypi](https://pypi.org/project/MASlite/),[github](https://github.com/root-11/maslite)), is a 
100% python based multi-agent platform written in 639 lines of code.

It looks like if it was out of development, as has been sitting idle for quite some time, but reality is
quite the opposite: MASLite has matured over 8 years and has proven itself as a stable platform for quite some
time.

#### A BIT OF HISTORY

**Version 1**  
I first wrote MASLite the first time in 2012 when I was working on my Ph.D. project. The goals was to build an event 
processing engine for distributed supply chain optimization. To no surprise this was far from trivial, but the
first and slow version proved itself for the small job it did.

**Version 2**  
I re-wrote the engine in 2014 when I worked on an assignment problem for a freight exchange. The goal was similar - 
find the optimal assignment of cargo and vehicles, so that the two interest groups gained maximal advantages.
In contrast to the previous problem, the solution landscape was 2-3 orders of magnitude larger.
I started the work (loyal to my professors advice) with the conviction that batch processing was bad and 
that agents should react to every event. However as the agents worked their way through the message queue,
they developed - and abandoned - thousands of intermediary solutions on their way towards convergence.
Batch processing was bad, no batch processing was slow. It became obvious that the solution should be micro-batches, 
where each agent obtain a number of messages and react to these, prior to spewing out new messages. 

**Version 3**  
In 2016 I re-wrote the engine to exploit what I've learned and let the agents operate in lock-step, where
message exchange only happened after all agents had processed all messages. Lock step also meant easier debugging 
as developers could put a break point in an agent class and walk the process. Unfortunately I also fell for the
idea that multiprocessing would be a good idea. I set the scheduler to run the main python process, and spawned a
number of workers so that agents would be updated with their incoming messages, and then sent to the worker for updates.
Unfortunately this meant that the workers were waiting for the scheduler to handle the messages and give them work,
so the throughput was nothing more than 75,000 - 78,000 message per second. 

**Version 4**  
In 2018 I decided to review MASLite and get rid of the multiprocessing module. I focused on ripping out everything
that wasn't critical for the core process. As everything was running in a single python process, I added a reference
to the scheduler, so that when agents send messages they were put straight onto the mail queue instead of letting the
scheduler collect the messages. I also simplified the clock to a pure python class and avoided extra messages.
It was probably the cleanest object oriented development I had done to date. And it worked.  
Version 4 had a throughput of 275,000,000 messages per second and proved itself useful for both a commercial data-
processing framework and a new simulation engine. 
 

#### LESSONS LEARNED

In retrospect version 4 could have been written is one go. However I didn't 
have the experience and hence didn't plan it properly. In addition the literature
on multi-agent systems is a horrible mess of entangled opinions and puretanic academic interests.

If I would have appraoched the design of MASLite more systematically I would have asked myself the 
following questions:  

**1. Problem** - What problem does MASLite have to solve, and what is the project that exploits the MASlite?  
The distinction between MASlite and the project is that only in the 4th version of MASLite was the goal to 
build the software to do one thing and do that one thing well. All previous implementations were focused on 
satisfying the project requirements.  
Obviously (now) MASlite is a scheduler that handles messages exchange effectively, allows easy debugging and
and can host any kind of agents. The specialisation of the agents is delegated to the project and MASlite should
be completely agnostic hereof.

**2. Structure** - What structure _of work_ would solve the problem?  
First the development of MASLite and the project should remain separate. The goal of MASlite should be conceptual,
whilst the project should respect the particular problem at hand. This separation of concerns would have made
things simple from day one. The focus in each development group could then be to:
1. make it work.
2. make it right.
3. make it fast.
4. make it cheap.

**3. Keywords** - What _keywords_ belong to each chunk of work?  
If MASlite is reliable, testing the agents and their interactive protocols, become straight forward.
If MASlite is published in state "1. Make it work", the testing of agents and protocols can happen
without worrying about being entangled in the development of MASlite.   
The life of the project and the life MASlite are decoupled, so the project team can focus on:

1. How to design the protocols that agents require to solve problems collaboratively.  
2. To understand what happens when the problem that is being solved scales.  
3. To attempt to measure and improve performance.

There was no seperation of concern in the projects from 2012 - 2017. All work was driven by the project requirements,
and counter-intuitively this led to performance problems - because everything was entangled. Today - in version 4 -
this isn't a problem anymore.

**4. Content** - How was the delivery of the content organised?  
Delivery reflected the the project team - there was one team and it all became entagled. By separating MASLite from
the project the delivery would be cleaner. Today that applies every where, but if I would teach a developer anything
of importance, then it would be to build specialised packages and keep them portable. 

...More to follow...