#!/usr/bin/env python

import socket
import errno
import sys
from collections import namedtuple

DEBUG = True
E_INVALID_PARAMS = 2
E_FILE_READ_FAIL = 69
E_NO_SERVER = 70
SPORT = 7735 # Well-known server port
CPORT = 7736 # Well-known client port
DATA_ID = 0b0101010101010101 # Well-known
HEADER_LEN = 8 # Bytes

# Open UDP socket for communication with server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
me = socket.gethostbyname(socket.gethostname())
sock.bind((me, CPORT))

# Build data structure for repersentating packets
pkt = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type", "data", "acked"])

# Validate the number of passed arguments
# Spec: Must have form <shost> <sport> <file_name> <N> <MSS> 
if len(sys.argv) != 6:
  print "Usage: ./client <shost> <sport> <file_name> <N> <MSS>"
  sys.exit(E_INVALID_PARAMS)

# Read data from CLI
shost = str(sys.argv[1])
sport = int(sys.argv[2])
file_name = str(sys.argv[3])
window_size = int(sys.argv[4])
mss = int(sys.argv[5])

if DEBUG:
  print "shost:", shost, "\nsport:", sport, "\nfile_name:", file_name, "\nwindow_size:", window_size, "\nmss:", mss

# Only port 7735 is allowed for this project
if sport != SPORT:
  print "Sorry, the use of port", SPORT, "is required for this project"
  sport = SPORT

def get_chk_sum(data):
  """
  Compute and return the check sum of the given data
  TODO: Stub
  """
  return 0

def valid_checksum():
  """Check the validity of a data/checksum pair"""
  return True

def craft_pkt(pkt):
  """TODO: Use ASCII encoding to send header info, not hex"""

  #TODO: Do this with one string formatting operation
  return str('%08X'%(pkt.seq_num)) + str('%04X'%(pkt.chk_sum)) \
      + str('%04X'%(pkt.pkt_type)) + str(pkt.data)

def send_pkt(pkt, sock):
  """
  Take a pkt named tuple, build the pkt and send it to the server
  """
  try:
    # Send packet to server
    sock.sendto(craft_pkt(pkt), (shost, SPORT))
  except IOError, e:
    if e.errno == errno.EPIPE:
      print "CLIENT ERROR: There is no server on", str(shost) + ":" \
        + str(sport)
    else:
      print "CLIENT ERROR: There was an IOError", e.errno
    sock.close()
    sys.exit(1)

def build_pkts(file_data):
  """Takes raw data to be sent and builds a list of pkt named tuples"""
  seq_num = 0
  pkts = []

  sent = 0
  to_send = min(mss - HEADER_LEN, len(file_data) - sent)
  while to_send > 0:
    # Build a pkt named tuple and add it to the list of packets
    pkts.append(pkt(seq_num = seq_num, chk_sum = get_chk_sum(file_data), \
      pkt_type = DATA_ID, data = file_data[sent:sent + to_send], acked = False))
    sent += to_send
    to_send = min(mss - HEADER_LEN, len(file_data) - sent)
    seq_num += 1

  # Newly built list of pkts
  return pkts


def rdt_send(file_data):
  """Send passed data reliabally, using an unreliable connection"""
  # Build packet list
  pkts = build_pkts(file_data)

  if DEBUG:
    print pkts

  oldest_unacked = 0
  unacked = 0
  while oldest_unacked < len(pkts):
    print "CLIENT: oldest_unacked < len(pkts) :", oldest_unacked, "<", len(pkts)

    # Can we send a packet, do we need to send pkt
    if unacked < window_size and (unacked + oldest_unacked) < len(pkts):
      #send_pkt(pkts[oldest_unacked], sock)
      sock.sendto(craft_pkt(pkts[oldest_unacked]), (shost, SPORT))

      if DEBUG:
        print "CLIENT: Sent pkt to", str(shost) + ":" +  str(SPORT)

      unacked += 1
      continue
    else: # Can not send pkt
      # Listen for ACKs TODO: Remove magic number
      pkt_recv_raw, addr = sock.recvfrom(4096)

      if DEBUG:
        print "CLIENT FROM SERVER:\n", addr
        print "CLIENT FROM SERVER:\n", data

      # Confirm that pkt is from the server
      if addr != SHOST:
        if DEBUG:
          print "CLIENT: Unexpected pkt from", addr
        continue

      # Decode packet
      pkt_recv = decode_pkt(pkt_recv_raw)

      # Validate pkt checksum
      if not valid_checksum(pkt_recv.data, pkt_recv.chksum):
        if DEBUG:
          print "CLIENT: Invalid checksum, dropping pkt"
        continue

      # Confirm that pkt is indeed an ACK
      if pkt.pkt_type != ACK_ID:
        if DEBUG:
          print "CLIENT: Unexpect pkt type", pkt.pkt_type, ", dropping pkt"
        continue

      # Pkt is sound
      unacked -= 1

      if DEBUG:
        print "CLIENT: Pkt is sound"

      # This is the pkt you're looking for
      if pkt_recv.seq_num == oldest_unacked:
        oldest_unacked += 1

        if DEBUG:
          print "CLIENT: oldest_unacked updated, now", oldest_unacked

  # Close server connection and exit sucessfully
  sock.close()
  sys.exit(0)


# Open file passed from CLI
try:
  fd = open(file_name, 'r')
  file_data = fd.read()
  fd.close()
except:
  print "Failed to open file:", file_name
  sys.exit(E_FILE_READ_FAIL)

if DEBUG:
  print file_name, "contents:\n", file_data

# Pass file data to reliable data transfer function
rdt_send(file_data)


