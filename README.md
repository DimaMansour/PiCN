*This is work in progress! Everything can change at any moment! :-)*

**Requires Python  >=3.6** 

# PiCN 
PiCN is a modular ICN implementation designed to support NFN and
other in network applications written in Python 3

## Modularization
PiCN consists of several Modules which run in separated processes. 
Each Module increases the abstraction, they are chained to a kind 
of execution stack.

# Quick start

```
% git clone https://github.com/cn-uofbasel/PiCN.git
% cd PiCN
% export PYTHONPATH=`pwd`

% cd examples
% mkdir ./repo
% ../PiCN/Executable/ICNDataRepository.py --repotype flic --suite ndn2013 ./repo /the/prefix 9876 &
% ./write_read.py
...

% ./write_read-flic.py
...

% ./write_read-flic-nfn.py
...

```
