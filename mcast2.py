#!/usr/bin/python

#Feed tester script

#Parameters:
BIND_IFACE=''
MCAST_FEED_IP=''
MCAST_FEED_PORT=''
verbose = False
total_bytes = False
timeout = False
data=''
import getopt, sys, IN, netifaces
import socket, select
import struct
import time
from datetime import datetime, timedelta


def usage(exit_code):
    print 'Tests a multicast feed for incoming data'
    print '%s -i <interface> -f <mcast_feed_ip> -p <mcast_feed_port>' % sys.argv[0]
    print 'Options'
    print '-i or --interface= interface to bind eg: eth0'
    print '-f or --feeed=     feed ip'
    print '-p or --port=      feed port'
    print '-v or --verbose    verbose mode, prints data'
    print '-b or --bytes=     Quit after X amount of bytes'
    print '-t or --timeout=   Quit after X amount of seconds timeout'
    sys.exit(exit_code)

#Parse Arguments
try:
    opts, args = getopt.getopt(sys.argv[1:],"i:f:p:b:t:hv",["interface=","feed","port","help","verbose"])
except getopt.GetoptError:
        usage(2)
for opt, arg in opts:
    if opt in ("-h",   "--help"):
        usage(0)
    elif opt in ("-i", "--interface"):
        BIND_IFACE= arg
    elif opt in ("-f", "--feed"):
        MCAST_FEED_IP = arg
    elif opt in ("-p", "--port"):
        MCAST_FEED_PORT = int(arg)
    elif opt in ("-b", "--bytes"):
        total_bytes = int(arg)
    elif opt in ("-t", "--timeout"):
        timeout = int(arg)
    elif opt in ("-v", "--verbose"):
        verbose = True

print "Binding to Interface %s and requesting multicast group %s:%s" % (BIND_IFACE, MCAST_FEED_IP, MCAST_FEED_PORT)
#require parameters
if not BIND_IFACE or not MCAST_FEED_IP or not MCAST_FEED_PORT:
    usage(2)



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Force Interface
local_ip=netifaces.ifaddresses(BIND_IFACE)[2][0]['addr']

# Feed port
sock.bind(('', MCAST_FEED_PORT))

# Bind it
mreq = socket.inet_aton(MCAST_FEED_IP) + socket.inet_aton(local_ip)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#if quit on bytes
if total_bytes:
    print "Will exit when %d bytes have been received" % total_bytes
byte_counter=0

#Reset Sequence
lastsequence=0

#if quit on timeout
if timeout:
    print "Will exit when %d seconds have been elapsed" % timeout
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout)
    sock.setblocking(0)

print 'waiting to receive message'
while True:
    try:
        data, address = sock.recvfrom(1024)
    except: 
        print "Waiting for data..."
    if address[0]=='10.10.20.36' and address[1]==52385 and data:
        #print "Received %d bytes" % (len(data))
        byte_counter += len(data)
        if verbose:
            #print "From: %s,Data: %s" % (address, data.encode('hex'))
            #print "From: %s,Data: %s" % (address, data[2:10].encode('hex'))
            sequence=struct.unpack_from('>Q', data,2)[0]
            #print "From: %s,Sequence: %s" % (address, sequence)
            if lastsequence > 0:
                if lastsequence + 1 != sequence:
                    print "Sequence Gaps from %d to %d" % (lastsequence, sequence)
            lastsequence=sequence
            
    if total_bytes:
        if byte_counter >= total_bytes:
            print "Data limit reached: %d bytes received" % byte_counter
            sys.exit(0)
    if timeout and  datetime.now() >= end_time:
        if byte_counter == 0:
            print "No data received, feed does not seem to work"
            sys.exit(1)
        else:
            print "Received %d bytes in %d seconds.\nFeed seems operational." % (byte_counter, timeout)
            sys.exit(0)
    #time.sleep(0.1)


