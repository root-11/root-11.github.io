After cleaning data in the field of logistics, parsing csv files, excel files
and scrubbing `utf-8`, `utf-16` and `windows1250` data for a decade, I thought
it was overdue to synthesize my experiences into a compact clean python package.

However before I start, I want to highlight ***why***. 

First of all we're all tired of reinventing the wheel when we need to process 
a bit of data. So we pick some package and try to get it to work:

**Pandas** features pythonic slicing and an easy to navigate api, but when using 
Pandas, there's always a huge memory overhead. I never took the time
to investigate, but x10 - x20 times the raw file seems common. In my line of 
work that was often enough not to be able to use pandas at all.

**Numpy** is of course close to the metal, and thereby "fast" for data processing.
But fast is really not the problem in dirty data. It's the `None`'s or `Nan`'s
that numpy doesn't cope well with, so it would make me jump through various 
hoops to get the data into a state where numpy would be usable. Last but not
least, Numpy has become a language of it's own. I'm sorry to say it but it just 
doesn't seem pythonic anymore.

**Arrows** looks like all the great things, but it just isn't ready.

**SQLite** is great but just too slow, particularly on disk. Even with WAL off,
inserting 200,000 rows per second into a new table no fun, and after that, doing
repeated incremental queries, become painful. Creating temporary tables that help
to avoid rerunning of queries, always become necessary. A second element is that
SQLite doesn't `vacuum` itself. A user who does an outer join on 40,000 x 40,000
rows of data, generates 1,600,000,000 temporary records - or 8,000 seconds of inserts - 
which just isn't workable.

**Protobuffer** is nice for making the data portable, but the overhead of making 
dirty data fit the form, is just as laborious as implementing all the analytics 
that need to happen afterwards.


So where do we end up? We write some custom built class for the problem at hand and
discover that we've just spent 3 hours doing something that should have taken
20 minutes.

### No more! 

I listened to the old adage that good artists copy, great artist steal, and took
the best of all.

### ...Enter: [tablite](https://pypi.org/project/tablite)

A python library for tables that does everything you need.

- it handles all real world datatypes: str,float,bool,int,date,datetime,time.
- it behaves like a dict/list, so it can be learned in 10 minutes.
- it loads data and determines the data types in one line of code for `csv`, `tsv`, `txt`, `xlsx`, `xls`, `xlsm`, `ods`.
- it detects all date,time and datetime formats covered in dateutil and the turing institutes publicly available tests.
- it is portable as JSON in a single function call. 
- It has all the main stream analytics packaged: SQL join, pandas Groupby, All, Any, Filter
- It supports incremental analytics using `+=` 
- It has datatype validation
- and finally it makes YOU blazingly fast. 

Pun intended in the last line. Most packages advertise that the code they've 
made is **_blazingly fast_**. I think it's bullocks -  A package is as
fast as the underlying algorithms and programming language allows it to be. 
What matters to me is I can solve a data clean up task in about 3 minutes. 
That's fast to me. Not that I can repeatedly run through dirty
data at 4 million rows per second, but then spend all day on making the data fit 
into the framework.
   
For more details go to: [tablite](https://pypi.org/project/tablite) 
[![Build Status](https://travis-ci.com/root-11/tablite.svg?branch=master)](https://travis-ci.org/root-11/tablite) 
[![Code coverage](https://codecov.io/gh/root-11/tablite/branch/master/graph/badge.svg)](https://codecov.io/gh/root-11/tablite)

