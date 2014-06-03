#!/usr/bin/env python

"""
Imports VFR data to Oracle Spatial database

Requires GDAL/OGR library version 1.11 or later.

One of input options must be given:
       --file
       --type

Usage: vfr2oci [-f] [-e] [--file=/path/to/vfr/filename] [--date=YYYYMMDD] [--type=ST_ABCD|OB_000000_ABCD] [--layer=layer1,layer2,...] [--geom=OriginalniHranice|GeneralizovaneHranice]
                          --dbname <database name>
                         [--user <user name>] [--passwd <password>] [--host <host name>]
                         [--overwrite] 

       -e          Extended layer list statistics 
       -d          Save downloaded VFR data in currect directory (--type required)
       --file      Path to xml.gz file
       --date      Date in format 'YYYYMMDD'
       --type      Type of request in format XY_ABCD, eg. 'ST_UKSH' or 'OB_000000_ABCD'
       --layer     Import only selected layers separated by comma (if not given all layers are processed)
       --geom      Preferred geometry 'OriginalniHranice' or 'GeneralizovaneHranice' (if not found or not given than first geometry is used)
       --dbname    Output Oracle database
       --user      User name
       --passwd    Password
       --host      Host name
       --overwrite Overwrite existing Oracle tables
"""

import os
import sys
import atexit
from getopt import GetoptError

from vfr4ogr.ogr import check_ogr, open_file, list_layers, convert_vfr, check_log
from vfr4ogr.utils import fatal, message, parse_xml_gz, compare_list
from vfr4ogr.parse import parse_cmd

# print usage
def usage():
    print __doc__

def main():
    # check requirements
    check_ogr()
    
    # parse cmd arguments
    options = { 'dbname' : None, 'user' : None, 'passwd' : None, 'host' : None, 
                'overwrite' : False, 'extended' : False, 'layer': [], 'geom' : None, 'download' : False}
    try:
        filename = parse_cmd(sys.argv, "heod", ["help", "overwrite", "extended",
                                              "file=", "date=", "type=", "layer=", "geom=",
                                              "dbname=", "user=", "passwd=", "host="],
                             options)
    except GetoptError, e:
        usage()
        if str(e):
            fatal(e)
        else:
            sys.exit(0)
    
    # open input file by GML driver
    ids = open_file(filename)
    
    if options['user'] is None:
        # list available layers and exit
        layer_list = list_layers(ids, options['extended'])
        if options['extended'] and os.path.exists(filename):
            compare_list(layer_list, parse_xml_gz(filename))
    else:
        if not options['user'] or not options['passwd']:
            fatal("--user and --passwd required")
            
        odsn = "OCI:%s/%s" % (options['user'], options['passwd'])
        if options['host']:
            odsn += "@%s" % options['host']
        if options['dbname']:
            odsn += "/%s" % options['dbname']
        
        os.environ['NLS_LANG'] = 'american_america.UTF8' # fix encoding issue
        lco_options = [ "srid=2065", "INDEX=OFF", "MULTI_LOAD=OFF" ]  ### TODO: 5514
                                                                      ### TODO: fix MULTI_LOAD (currently it crashes)
        time = convert_vfr(ids, odsn, "OCI", options['layer'], options['overwrite'], lco_options, options['geom'])
        message("Time elapsed: %d sec" % time)
    
    ids.Destroy()
    
    return 0

if __name__ == "__main__":
    atexit.register(check_log)
    sys.exit(main())
