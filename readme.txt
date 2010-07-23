Requirements
============

  * rrdtool
  * python 2.5+
  * twisted
  * django 1.2.1

easy_install pyopenssl
easy_install pycrypto
easy_install MySQL-python


Overview
========
The angel consists of two parts:
Angel
Bot

Angel in charge of displaying monitoring info / manipulating data etc. It's 

Installation
============

Windows
=======
Cygwin is recommanded: http://www.cygwin.com/

rrdtool for cygwin: http://www.cacti.net/downloads/rrdtool/win32/

Native rrdtool on windows is not tried.


Create  RRDs
============
rrdtool create hostname.rrd --step 60 
	DS:deliver_rate:GAUGE:60:0:U
	DS:load:GAUGE:60:0:U
	DS:speed:GAUGE:60:0:U
	DS:rps:GAUGE:60:0:U
	RRA:LAST:0.5:1:1576800
	
rrdtool create mobileweb.rrd --step 60 DS:deliver_rate:GAUGE:60:0:U DS:load:GAUGE:60:0:U DS:speed:GAUGE:60:0:U DS:rps:GAUGE:60:0:U RRA:LAST:0.5:1:16

rrdtool create mobileweb.rrd --step 60 DS:online:GAUGE:60:0:U RRA:LAST:0.5:1:16


rrdtool graph t.png --start end-1d --end 1276876740 -E --imgformat PNG --width 640 --height 480 DEF:dev=mobileweb.rrd:delivery_rate:LAST LINE1:dev#FF0000:Rate DEF:load=mobileweb.rrd:load:LAST LINE2:load#00FF00:Load DEF:raw_speed=mobileweb.rrd:speed:LAST CDEF:speed=raw_speed,1000,/ LINE3:speed#0000FF:Speed DEF:rps=mobileweb.rrd:rps:LAST LINE4:rps#00FFFF:RPS


-E --imgformat PNG
--width {width} --height {height}
DEF:load={rrd}:load:LAST
DEF:dev={rrd}:delivery_rate:LAST
CDEF:speed=raw_speed,1000,/ 
DEF:rps={rrd}:rps:LAST
LINE1:dev#FF0000:Rate
LINE2:load#00FF00:Load DEF:raw_speed={rrd}:speed:LAST
LINE3:speed#0000FF:Speed
LINE4:rps#00FFFF:RPS

rrdtool graph t1.png --start end-1d --end 1276876740 -E --imgformat PNG --width 640 --height 480 DEF:dev=mobileweb.rrd:delivery_rate:LAST LINE1:dev#FF0000 DEF:load=mobileweb.rrd:load:LAST LINE2:load#00FF00 DEF:speed=mobileweb.rrd:load:LAST 
LINE3:speed#0000FF DEF:rps=mobileweb.rrd:rps:LAST LINE4:rps#00FFFF
