# Delivery of Eventually-Available Data

This how-to..


## Sample Topology

![Sample Topology](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/setup.png "Sample Topology")

For both approaches, our sample topology simply consists of a packet forwarder which hands over computation result requests to a computation node.

* Nodes are connected via UDP faces: The packet forwarder listens on port 9000 and the computation server on on port 8000.
* A forwarding rule is configured on the packet fowarder to forward interests prefixed with `/the/prefix` to the computation node.
* The computation node comes with a function store where services are saved. When starting a computation node, the service `/the/prefix/square` is automatically added.
* The reader of this how-to will request eventually-available computation results via the forwarder from the computation server. for this purpose, client tools are available which implement the consumption logic. In real-world applications, this logic would be implemented by the client application.


## Preparation

Requirements: Make sure, that git and python3.6+ is available on your system. PiCN is tested on Linux and Mac OS X. Windows is also supported but not extensively tested.

If not already available on your machine, clone PiCN from Github:
```console
you@machine:~$ git clone https://github.com/cn-uofbasel/PiCN.git
```

To start nodes and manage these from the command line, PiCN comes with scripts.

Add the core PiCN tools to your PATH (bash):
```console
you@machine:~$ PATH=$PATH:`pwd`/PiCN/starter
```

Also add tools for eventually-available data retrieval tools to your PATH (bash):
```console
you@machine:~$ PATH=$PATH:`pwd`/PiCN/Playground/starter
```
We recommend to add these lines to ~/.bashrc (bash).

If the tools are available, you see usage information after typing the following commands:

```console
you@machine:~$ picn-forwarder --help
```

```console
you@machine:~$ picn-heartbeat-forwarder --help
```


## Heartbeat Approach

### Starting Nodes

Open a terminal and type the following commmand to start a packet forwarding node on UDP port 9000:

```console
you@machine:~$ picn-heartbeat-forwarder --port 9000
```

Type in another terminal the following command to start the computation server on UDP port 8000:

```console
you@machine:~$ picn-heartbeat-server --port 8000
```

You should see something similar to the following.

![Heartbeat Forwarder Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-heartbeat-forwarder.png "Heartbeat Forwarder Output")

![Heartbeat Server Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-heartbeat-server.png "Heartbeat Server Output")

Once we send packets through the network, additional log information is shown.

### Forwarding Rule

To configure a forwarding rule from forwarder to computation server, type in another terminal:

```console
you@machine:~$ picn-mgmt --ip 127.0.0.1 --port 9000 newface 127.0.0.1:8000:0
you@machine:~$ picn-mgmt --ip 127.0.0.1 --port 9000 newforwardingrule /the/prefix:0
```

### Request Content

```console
you@machine:~$ picn-heartbeat-peek --port 9000 --plain /the/prefix/square/5/1/hNFN
```

![Heartbeat Peek Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-heartbeat-peek.png "Heartbeat Peek Output")

## Two-Phase Request Approach

### Starting Nodes

Open a terminal and type the following commmand to start a packet forwarding node on UDP port 9000:

```console
you@machine:~$ picn-relay --port 9000
```

Type in another terminal the following command to start the computation server on UDP port 8000:

```console
you@machine:~$ picn-twophase-server --port 8000
```

You should see something similar to the following.

![Forwarder Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-twophase-forwarder.png "Forwarder Output")

![Two-Phase Server Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-twophase-server.png "Two-Phase Server Output")

Once we send packets through the network, additional log information is shown.

### Forwarding Rule

To configure a forwarding rule from forwarder to computation server, type in another terminal:

```console
you@machine:~$ picn-mgmt --ip 127.0.0.1 --port 9000 newface 127.0.0.1:8000:0
you@machine:~$ picn-mgmt --ip 127.0.0.1 --port 9000 newforwardingrule /the/prefix:0
```

### Request Content

```console
you@machine:~$ picn-twophase-peek --port 9000 --plain /the/prefix/square/5/1/pNFN
```

![Two-Phase Peek Output](https://raw.githubusercontent.com/cn-uofbasel/PiCN/master/PiCN/Playground/docs/img/screenshot-twophase-peek.png "Two-Phase Peek Output")
