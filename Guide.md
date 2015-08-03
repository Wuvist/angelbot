Title: guide

Adding new server & sample widget

This guide shows how to add a new server and a widget taking single gauge value for monitor into angelbot.

#Example in ubuntu linux

# Deployment #

This guide will help you deploy angelbot

# Install depend  package or software #
  * sudo apt-get install mysql
  * sudo apt-get install python-setuptools
  * sudo apt-get install build-essential
  * sudo easy\_install pyopenssl  or  sudo apt-get install python-pyopenssl
  * sudo apt-get install python-twisted-conch
  * sudo easy\_install pycrypto
  * sudo apt-get install libmysqlclient-dev
  * sudo easy\_install MySQL-python
  * sudo apt-get install python-mysqldb
  * sudo apt-get install rrdtool
  * sudo apt-get install python-rrdtool
  * sudo apt-get install OpenSSL-dev
  * sudo apt-get install python-django
  * sudo apt-get install python-matplotlib
# Get Code #
  * svn checkout http://angelbot.googlecode.com/svn/trunk/ angelbot
# Configuration #
  * Edit file angelbot/web/AngelWeb/settings.py like:
    * 12.DATABASE\_ENGINE = 'mysql'----#  'postgresql', 'mysql', 'sqlite3' or 'oracle'.
    * 13.DATABASE\_NAME = 'angeldb'----# Or path to database file if using sqlite3.
    * 14.DATABASE\_USER = 'root'----# Not used with sqlite3.
    * 15.DATABASE\_PASSWORD = '' ----# Not used with sqlite3.
    * 16.DATABASE\_HOST = ''-----# Set to empty string for localhost. Not used with sqlite3.
    * 17.DATABASE\_PORT = ''----# Set to empty string for default. Not used with sqlite3.

  * Specify your rrd path:
    * 85.RRD\_PATH = '/Users/Wuvist/source/angelbot/rrds/'
# Run Angelbot #
  * use angelbot/web/AngelWeb/manage.py syncdb   #auto create tables;in halfway, it will ask you enter to create superadmin username&password,please enter and remember it.
  * use angelbot/web/AngelWeb/manage.py runserver 127.0.0.1:8000   #browser enter http://127.0.0.1:8000/       you will see one light blue angelbot homepage, congratulation ! you done it! of course you can use your superadmin username&password login.
# Add Server #
  * Using http://angelbot/admin portal to add a new server definition.
  * Only the server name is critical here. server\_type is for reference. IP, username, password fields are actually dummy, could input anything. Actual server login credential are currently hardcoded in bot's hosts.py file.
# Add RRD #
  * Using http://angelbot/admin portal to add a new rrd. RRD defines the data store for recording data.
  * RRD name must be unique, it's the actual filename for RRD file created
  * setting field is actually the supplementing parameter passed to rrdtool when creating rrd file, for single number, input: --step 60 DS:online:GAUGE:60:0:U RRA:LAST:0.5:1:525600
  * --step 60: Indicate this data need to be updated every 60 seconds. DS & RRA defines the data store for 1 year. 525600 = 60 24 365
  * Please refers to rrdtool documents for details: http://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html
  * Once the rrd definition is created, visit http://angelbot/rrd/
  * Click create to create actual rrd file or review its info.
# Add Widget #
  * Widget defines the how should Angel present data from a defined RRD.
  * Again, widgets are created in admin portal.
  * Server & Category are optional fields. Rrd and Graph def are critical here.
  * A sample graph widget showing single line will be: DEF:online={rrd}:online:LAST LINE:online#ff8882:Online
  * Above definition actually follows rrdtool's graph parameter (http://oss.oetiker.ch/rrdtool/doc/rrdgraph.en.html)
  * {rrd} will be replaced with actual rrd file name.
# Updating Data #
  * Once a Rrd file & widget are defined, external could start sending data to bot periodically.
  * http://angel:8080/rrd?rrd={RRD Name}&ds={Dummy ds Name}&v={Value}
  * Above API is a simple wrapper for rrdupdate cmd: http://oss.oetiker.ch/rrdtool/doc/rrdupdate.en.html
  * Notes:
    * API will round current time to nearest minute.
    * DS has multiple value could be updated using multiple v parameter like:
      * http://angel:8080/rrd?rrd={RRD Name}&ds={Dummy ds Name}&v={Value1}&v={Value2}&v={Value3}