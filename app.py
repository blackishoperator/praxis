#!/usr/bin/env python

import socket
import random
from threading import Thread

method0 = "POST http://e-chat.co/authentication/guest HTTP/1.1\r\n"
method1 = "POST http://e-chat.co/authentication/registration/new HTTP/1.1\r\n"
method2 = "POST http://e-chat.co/cometd/handshake HTTP/1.1\r\n"
method3 = "POST http://e-chat.co/cometd/connect HTTP/1.1\r\n"
method4 = "POST http://e-chat.co/cometd/ HTTP/1.1\r\n"
method5 = "GET http://e-chat.co/account/logout HTTP/1.1\r\n"

header0 = "Host: e-chat.co\r\n"
header1 = "Content-Type: application/x-www-form-urlencoded; charset=UTF-8\r\n"
header2 = "Content-Type: application/json; charset=UTF-8\r\n"
header3 = "Referer: http://e-chat.co/browse\r\n"
header4 = "Referer: http://e-chat.co/room/163173\r\n"
header5 = "Content-Length: "
header6 = "Cookie: "

bodies0 = "username=&password=8&rememberAuthDetails=false\r\n" #for registered users
bodies1 = "[{\"ext\":{\"chatroomId\":},\"version\":\"1.0\",\"minimumVersion\":\"0.9\",\"channel\":\"/meta/handshake\",\"supportedConnectionTypes\":[\"long-polling\",\"callback-polling\"],\"advice\":{\"timeout\":60000,\"interval\":0},\"id\":\"1\"}]"
bodies2 = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"advice\":{\"timeout\":0},\"id\":\""
bodies3 = "[{\"channel\":\"/service/chatroom/message\",\"data\":{\"messageBody\":\""

def cometd(cookie, clntId, cntId, text) :
	rqst = method4 + header0 + header2 + header6 + cookie + "\r\n" + header5 + str(76 + len(clntId) + len(cntId) + len(text)) + "\r\n\r\n" + bodies3 + text + "\"},\"id\":\"" + cntId + "\"," + clntId + "}]"
	rspn = request(rqst, "cometd")
	return rspn

def connect(cookie, clntId, cntId) :
	rqst = method3 + header0 + header2 + header6 + cookie + "\r\n" + header5 + str(93 + len(clntId) + len(cntId)) + "\r\n\r\n" + bodies2 + cntId + "\"," + clntId + "}]"
	rspn = request(rqst, "connect")
	return rspn

def handshake(cookie, roomId) :
	rqst = method2 + header0 + header2 + header6 + cookie + "\r\n" + header5 + str(204 + len(roomId)) + "\r\n\r\n" + bodies1[:22] + roomId + bodies1[22:] + "\r\n"
	rspn = request(rqst, "handshake")
	start = rspn.find("BAYEUX_BROWSER")
	end = rspn.find(";", start)
	string = rspn[start:end] + '|'
	start = rspn.find("\"clientId\"")
	end = rspn.find(",", start)
	string = string + rspn[start:end]
	return string

def register(usrnme) :
	rqst = method1 + header0 + header1 + header5 + str(46 + len(usrnme)) + "\r\n\r\n" + bodies0[:9] + usrnme + bodies0[9:] + "\r\n"
	rspn = request(rqst, "register")
	return rspn

def logout(cookie) :
	rqst = method5 + header0 + header4 + header6 + cookie + "\r\n\r\n"
	rspn = request(rqst, "logout")
	return rspn

def request(rqst, name) :
	#print '_' * 200
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("www.e-chat.co", 80))
	#print "\n[send: " + name + "]\n" + rqst
	sock.send(rqst.encode())
	#print "\n[recv: " + name + "]"
	rspn = b''
	num = ""
	eof = [b'\r', b'\n', b'\r', b'\n']
	cnt = 0
	flag = True
	while flag :
		char = sock.recv(1)
		if char != '' :
			rspn = rspn + char
		if  char == eof[cnt]:
			cnt = cnt + 1
			if cnt == 4 :
				flag = False
		else :
			cnt = 0
	temp = rspn.decode()
	index = temp.find("Content-Length: ")
	index = index + 16
	while temp[index].isdigit() :
		num = num + temp[index]
		index = index + 1
	body = sock.recv(int(num))
	rspn = rspn + body
	sock.close()
	#print rspn
	#print '_' * 200
	return rspn.decode()

def spam(i, message, roomId, txt) :
	ban = 0
	ch = 100
	locerr = 0
	#print("thread started")
	while True :
		if locerr > 400:
			print("[thread #" + str(i) + "]: exited.")
			break
		ch = ch + 1
		cntId = 2
		seed = str(ch)
		usrnme = txt + seed + str(i) + "wicked" + str(i) + seed[2] + seed[1] + seed[0] + txt
		try:
			rspn = register(usrnme)
		except:
			locerr = locerr + 1
			continue
		srt = rspn.find("\r\n\r\n100")
		if srt <= 0 :
			srt = rspn.find("\r\n\r\n15")
			if srt > 0 :
				print("[error]: generic, trying...")
				print("[recv]:\n" + rspn + "\n")
				continue
			srt = rspn.find("\r\n\r\n12")
			if srt > 0 :
				print("[error]: used, trying...")
				print("[recv]:\n" + rspn + "\n")
				continue
			srt = rspn.find("\r\n\r\n16")
			if srt > 0 :
				print("[error]: banned, exiting...")
				print("[recv]:\n" + rspn + "\n")
				break
		start = rspn.find("JSESSIONID")
		end = rspn.find(";", start)
		cookie = rspn[start:end]
		try:
			string = handshake(cookie, roomId)
		except:
			locerr = locerr + 1
			continue
		index = string.find('|')
		cookie = cookie + "; " + string[:index]
		clntId = string[index+1:]
		num = 0
		while num < 3 :
			try:
				rspn = cometd(cookie, clntId, str(cntId), message)
			except:
				locerr = locerr + 1
				continue
			cntId = cntId + 1
			num = num + 1
			check = rspn.find("\"successful\":true")
			if check < 0 :
				break
		#ban = ban + 1
	print("[thread #" + str(i) + "]: finished.")

def main() :
	#message = raw_input("message: ")
	#roomId = raw_input("roomId: ")
	#txt = raw_input("txt: ")
	message = "Buy a Zippo"
	roomId = "888"
	txt = chr(random.randint(97, 122)) + chr(random.randint(97, 122)) + chr(random.randint(97, 122)) + chr(random.randint(97, 122))
	threads = []
	print(txt)
	for i in range(8) :
		t = Thread(target=spam, args=(i, message, roomId, txt))
		threads.append(t)
		t.start()

if __name__ == '__main__' :
	main()
