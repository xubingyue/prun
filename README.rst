this is a private proxy

we use a modified http CONNECT proxy. change it to a CONNECTX method.

pserver
=======

based on tornado: https://github.com/facebook/tornado.git

::

    local                  local                      ||        vps                     fb.com
    +--------------+       +----------------+         ||        +----------------+      +----------------+
    |              | http  |                |    https||        |                |      |                |
    | client       | --->  | Tunnel porxy   |  -------++---->   | CONNECTX proxy | ---> | remote server  |
    | chrome/prun  |       |                |         ||        |                |      |                |
    +--------------+       +----------------+         ||        +----------------+      +----------------+
                                                      ||

                                                    The Wall
1. setup CONNECTX proxy::

      #on vps
      ./pserver/pserver.py --https -p 8888

2. setup Tunnel proxy::

     ./pserver/pserver.py --upstream='https://vps.com:8888/CONNECTX' -p 8889

3. setup chrome/prun to use 127.0.0.1:8889 as proxy::

     curl -L --proxy 127.0.0.1:8889 http://www.github.com/

for debug
---------


use http between ``Tunnel proxy`` and ``CONNECTX proxy`` for debug::


    ./pserver/pserver.py -p 8888
    ./pserver/pserver.py --upstream='http://vps.com:8888/CONNECTX' -p 8889

most firewall can filter stream over http tunnel, so do not use this on production.


prun a client tool like proxychanins to make use of http/socks proxy
====================================================================

we use

    os.putenv('LD_PRELOAD', so)

to inject a so, hook the connect method of client application, so we can use:

    ./prun.py curl 'www.sina.com'

other
=====

proxy
-----

a pure python proxy server, no auth supported.
(i forget what do i want to do, maybe auth, maybe I need get a.com/xx proxy)

more python proxy:
------------------

http://proxies.xhaus.com/python/

tunning
-------

if your networking is not so stable, the connection will close frequently.


try this::

    $ echo 15 > /proc/sys/net/ipv4/tcp_retries2


