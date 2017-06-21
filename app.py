#!/usr/bin/env python

import http.client
import threading
import html

direct = ["/authentication/guest",	#0
		  "/authentication/login",	#1
		  "/account/logout",		#2
		  "/cometd/handshake",		#3
		  "/cometd/connect",		#4
		  "/cometd/"]				#5

statusFlags = {'connected': False, 'terminated': False}
users = {}
fakeList = [False, False, False, False, False]
guests = ["breathing_corpse", "solmaz", "razor", "salad shirazi", "biqam"]

class MyUser():
	def __init__(self, usrnme, passwd, roomId):
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.clntId = ''
		self.cntId = 2
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()

	def send_recv(self, method, iLink, body):
		rparams = []
		headers = {}
		headers["Host"] = "e-chat.co"
		if iLink != 2:
			headers["Connection"] = "keep-alive"
		if iLink < 2:
			headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		elif iLink > 2:
			headers["Content-Type"] = "application/json; charset=UTF-8"
		if body != None:
			headers["Content-Length"] = str(len(body))
		if self.cookie != '':
			headers["Cookie"] = self.cookie
		self.conn.request(method, direct[iLink], body, headers)
		rspn = self.conn.getresponse()
		status = rspn.status
		reason = rspn.reason
		hdlist = rspn.getheaders()
		stream = rspn.read()
		rspn.close()
		for tup in hdlist:
			if "Set-Cookie" in tup:
				newCookie = tup[1][:tup[1].find(";")]
				if self.cookie != '':
					self.cookie = self.cookie + ";" + newCookie
				else:
					self.cookie = newCookie
		return status, reason, stream

	def guest(self):
		body = "username=" + self.usrnme
		return self.send_recv("POST", 0, body)

	def login(self):
		body = "username=" + self.usrnme + "&password=" + self.passwd + "&rememberAuthDetails=false"
		return self.send_recv("POST", 1, body)

	def logout(self):
		status, reason, stream = self.send_recv("POST", 2, None)
		self.conn.close()
		return status, reason, stream

	def handshake(self):
		body = "[{\"ext\":{\"chatroomId\":" + self.roomId + "},\"version\":\"1.0\",\"minimumVersion\":\"0.9\",\"channel\":\"/meta/handshake\",\"supportedConnectionTypes\":[\"long-polling\",\"callback-polling\"],\"advice\":{\"timeout\":60000,\"interval\":0},\"id\":\"1\"}]"
		status, reason, stream = self.send_recv("POST", 3, body)
		rspn = str(stream)
		start = rspn.find("\"clientId\"")
		end = rspn.find(",", start)
		self.clntId = rspn[start:end]
		return status, reason, stream

	def metacon(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"advice\":{\"timeout\":0},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 4, body)

	def connect(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 4, body)
		
	def context(self):
		body = "[{\"channel\":\"/service/user/context/self/complete\",\"data\":{},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body)

	def message(self, text):
		body = "[{\"channel\":\"/service/chatroom/message\",\"data\":{\"messageBody\":\"" + text + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body.encode('utf-8'))

	def openbox(self, convId):
		body = "[{\"channel\":\"/service/conversation/opened\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body)

	def closbox(self, convId):
		body = "[{\"channel\":\"/service/conversation/closed\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body)

	def private(self, convId, text):
		body = "[{\"channel\":\"/service/conversation/message\",\"data\":{\"conversationUserUuid\":\"" + convId + "\",\"messageBody\":\"" + text + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body.encode('utf-8'))

def jsonParser(json, seed, roomId):
	if json.find("/chatroom/message/add") >= 0:
		start = json.find("\"messageBody\"")
		end = json.find("\",", start)
		start = start + 15
		usertext = json[start:end]
		usertext = html.unescape(usertext)
		start = json.find("\"username\"")
		end = json.find("\"}", start)
		start = start + 12
		username = json[start:end]
		username = html.unescape(username)
		print("[STATUS]: Text $ \"" + username + "\" : \"" + usertext + "\"")
	elif json.find("/chatroom/user/joined") >= 0:
		start = json.find("\"userUuid\"")
		end = json.find("\",", start)
		start = start + 12
		userUuid = json[start:end]
		start = json.find("\"username\"")
		end = json.find("\"}", start)
		start = start + 12
		username = json[start:end]
		users[userUuid] = username
		print("[STATUS]: Join $ \"" + username + "\"")
	elif json.find("/chatroom/user/left") >= 0:
		start = json.find("\"data\"")
		end = json.find("\",", start)
		start = start + 7
		userUuid = json[start + 1:end]
		if userUuid in users :
			print("[STATUS]: Left $ \"" + users[userUuid] + "\"")
	return

def split(rspn) :
	jsonList = []
	start = rspn.find("[{")
	start = start + 1
	while True :
		end = rspn.find("},{", start)
		if end < 0 :
			end = rspn.find("]")
			jsonList.append(rspn[start:end])
			break
		end = end + 1
		jsonList.append(rspn[start:end])
		start = end + 1
	return jsonList

def joinRoom(username, password, roomId):
	user = MyUser(username, password, roomId) #username password roomId
	if password != "":
		status, reason, stream = user.login()
	else:
		status, reason, stream = user.guest()
	status, reason, stream = user.handshake()
	status, reason, stream = user.metacon()
	status, reason, stream = user.context()
	return user

def fakeUser(i, username, password, roomId):
	user = joinRoom(username, password, roomId) #username password roomId
	fakeList[i] = True
	while fakeList[i] == True:
		try:
			status, reason, stream = user.connect()
		except:
			user = joinRoom(username, password, roomId)
			continue
		rspn = stream.decode('utf-8')
		if rspn.find("\"error\":\"402::Unknown client\"") >= 0:
			fakeList[i] = False
			#print("[STATUS]: \"" + username + "\" Disconnected")
	status, reason, stream = user.logout()
	return

def main():
	username = "awkward_silence"
	password = "frlm"
	roomId = "215315"
	GuestThreads = []
	for i in range(5) :
		guestThread = threading.Thread(target=fakeUser, args=(i, guests[i], "frlm", roomId, ))
		GuestThreads.append(guestThread)
		guestThread.start()
	index = 0
	user = joinRoom(username, password, roomId) #username password roomId
	statusFlags['connected'] = True
	while statusFlags['connected'] == True:
		try:
			status, reason, stream = user.connect()
		except:
			user = joinRoom(username, password, roomId)
			continue
		rspn = stream.decode('utf-8')
		#print("-" * 100)
		#print(rspn)
		jList = split(rspn)
		for json in jList:
			jsonThread = threading.Thread(target=jsonParser, args=(json, str(index), roomId, ))
			jsonThread.start()
			index += 1
			#print(json)
		if rspn.find("\"error\":\"402::Unknown client\"") >= 0:
			statusFlags['connected'] = False
		if index > 5:
			index = 0
		#print("[STATUS]: \"" + username + "\" Connected")
		for x in range(5):
			if fakeList[x] == False:
				print("[STATUS]: Fake $ \"" + guests[x] + "\" # Disconnected")
	status, reason, stream = user.logout()
	#print(str(stream))
	return

if __name__ == '__main__' :
	main()
