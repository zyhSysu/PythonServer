#!/usr/bin/env python

import socket, select

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(50)
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)

try:
	data = {}
	length = {}
	byteLength = {}
	connections = {}

	while True:
		events = epoll.poll(1)

		for fileno, event in events:
			if event & select.EPOLLHUP or event & select.EPOLLERR:
				epoll.unregister(fileno)

				if connections.has_key(fileno):
					connections[fileno].close()

					del connections[fileno]

				if length.has_key(fileno):
					del length[fileno]

				if data.has_key(fileno):
					del data[fileno]

				print "Client disconnected"
			elif fileno == serversocket.fileno() and event & select.EPOLLIN:
				connection, address = serversocket.accept()
				connection.setblocking(0)
				epoll.register(connection, select.EPOLLIN)

				connections[connection.fileno()] = connection

				#print address[0] + ": " + str(address[1]) + " connected"
			elif event & select.EPOLLIN:
				if length.has_key(fileno):

					#print "Begin to collect real data"

					remainLen = length[fileno]

					dataReceived = connections[fileno].recv(remainLen)

					data[fileno] += dataReceived

					remainLen -= len(dataReceived)

					if remainLen == 0:
						if data[fileno] == "exit":
							epoll.modify(fileno, 0)
							connections[fileno].shutdown(socket.SHUT_RDWR)
						else:
							epoll.modify(fileno, select.EPOLLOUT)
						
							del length[fileno]
					else:
						length[fileno] = remainLen
				else:
					#print "Waiting for packet length info..."

					curBytesNum = 0

					if byteLength.has_key(fileno):
						curBytesNum = len(byteLength[fileno])
					else:
						byteLength[fileno] = ""

					intBytes = connections[fileno].recv(4 - curBytesNum)

					byteLength[fileno] += intBytes

					if len(byteLength[fileno]) == 4:
						if length.has_key(fileno):
							raise SystemError

						length[fileno] = int(byteLength[fileno], 16)

						data[fileno] = ""

						#print "Packet length " + str(length[fileno])

						del byteLength[fileno]
					else:
						pass
			elif event & select.EPOLLOUT:
				bytesWritten = connections[fileno].send(data[fileno])
				
				data[fileno] = data[fileno][bytesWritten:]

				if len(data[fileno]) == 0:
					epoll.modify(fileno, select.EPOLLIN)
					
					del data[fileno]

				#print "Send data to client"
except SystemError:
	print "Server Error - connection is already in byteLength"
finally:
	epoll.unregister(serversocket.fileno())
	epoll.close()

	serversocket.close()
