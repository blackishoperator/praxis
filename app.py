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
fakeList = [False, False, False, False, False, False]
guests = ["awkward_silence", "breathing_corpse", "solmaz", "razor", "salad shirazi", "biqam", "Iran_Is_Safe", "GrumpyPersianCat"]
muteList = []

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

	def removetext(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/messages/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body)

	def userban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/add\",\"data\":{\"targetUserUuid\":\"" + targetUuid +"\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		#print(body)
		status, reason, stream = self.send_recv("POST", 5, body)
		#print("in userban: " + stream.decode('utf-8'))
		body = "[{\"channel\":\"/service/moderator/ban/fetch\",\"data\":{},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		#print(body)
		status, reason, stream = self.send_recv("POST", 5, body)
		#print("in userban: " + stream.decode('utf-8'))
		return status, reason, stream

	def userunban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		#print(body)
		status, reason, stream = self.send_recv("POST", 5, body)
		#print("in userunban: " + stream.decode('utf-8'))
		body = "[{\"channel\":\"/service/moderator/ban/fetch\",\"data\":{},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		#print(body)
		status, reason, stream = self.send_recv("POST", 5, body)
		#print("in userunban: " + stream.decode('utf-8'))
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

def jsonParser(json, seed, roomId, mod, busy):
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
		start = json.find("\"userUuid\"")
		end = json.find("\",", start)
		start = start + 12
		userUuid = json[start:end]
		if username in muteList:
			busy.acquire()
			mod.removetext(userUuid)
			busy.release()
			print("[STATUS]: Mute $ \"" + username + "\" : \"" + usertext + "\"")
		print("[STATUS]: Room $ \"" + username + "\" : \"" + usertext + "\"")
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
		#note = username + " has joined the room"
		#busy.acquire()
		#mod.message(note)
		#busy.release()
		print("[STATUS]: Join $ \"" + username + "\"")
	elif json.find("/chatroom/user/left") >= 0:
		start = json.find("\"data\"")
		end = json.find("\",", start)
		start = start + 7
		userUuid = json[start + 1:end]
		if userUuid in users:
			#note = users[userUuid] + " has left the room"
			#busy.acquire()
			#mod.message(note)
			#busy.release()
			print("[STATUS]: Left $ \"" + users[userUuid] + "\"")
	elif json.find("/notification/added") >= 0:
		start = json.find("\"userUuid\"")
		end = json.find("\",", start)
		start = start + 12
		userUuid = json[start:end]
		start = json.find("\"username\"")
		end = json.find("\"}", start)
		start = start + 12
		username = json[start:end]
		busy.acquire()
		status, reason, stream = mod.openbox(userUuid)
		busy.release()
		userText = getText(stream.decode('utf-8'))
		print("[STATUS]: Text $ \"" + username + "\" : \"" + userText + "\"")
		if userText.find("unban ") >= 0:
			targetUser = userText[6:]
			targetUuid, result = seekUser(targetUser)
			if result == 0:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "no such user was found banned from the room")
				busy.release()
			elif result == 1:
				busy.acquire()
				status, reason, stream = mod.userunban(targetUuid)
				text = "unbanned " + targetUser
				status, reason, stream = mod.private(userUuid, text)
				busy.release()
				print("[STATUS]: Room $ Unbanned : \"" + targetUser + "\"")
			elif result == 2:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "you have no control over this specific user")
				busy.release()
		elif userText.find("ban ") >= 0:
			targetUser = userText[4:]
			targetUuid, result = seekUser(targetUser)
			if result == 0:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "no such user was found online in the room")
				busy.release()
			elif result == 1:
				busy.acquire()
				status, reason, stream = mod.userban(targetUuid)
				text = "banned " + targetUser
				status, reason, stream = mod.private(userUuid, text)
				busy.release()
				print("[STATUS]: Room $ Banned : \"" + targetUser + "\"")
			elif result == 2:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "you have no control over this specific user")
				busy.release()
		elif userText.find("remove ") >= 0:
			targetUser = userText[7:]
			targetUuid, result = seekUser(targetUser)
			if result == 0:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "no such user was found online in the room")
				busy.release()
			else:
				busy.acquire()
				status, reason, stream = mod.removetext(targetUuid)
				text = "removed texts sent by " + targetUser
				status, reason, stream = mod.private(userUuid, text)
				busy.release()
				print("[STATUS]: Room $ Cleared : \"" + targetUser + "\"")
		elif userText.find("unmute ") >= 0:
			targetUser = userText[7:]
			if targetUser in guests:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "you have no control over this specific user")
				busy.release()
			else:
				muteList.remove(targetUser)
				text = "unmuted " + targetUser
				busy.acquire()
				status, reason, stream = mod.private(userUuid, text)
				busy.release()
				print("[STATUS]: Mute $ Removed : \"" + targetUser + "\"")
		elif userText.find("mute ") >= 0:
			targetUser = userText[5:]
			if targetUser in guests:
				busy.acquire()
				status, reason, stream = mod.private(userUuid, "you have no control over this specific user")
				busy.release()
			else:
				muteList.append(targetUser)
				text = "muted " + targetUser
				busy.acquire()
				status, reason, stream = mod.private(userUuid, text)
				busy.release()
				print("[STATUS]: Mute $ Appended : \"" + targetUser + "\"")
		busy.acquire()
		status, reason, stream = mod.closbox(userUuid)
		busy.release()
		#rspn = stream.decode('utf-8')
		#print("in pars: " + rspn)
	return

def getText(rspn):
	i = 0
	start = 0
	end = len(rspn)
	while i < len(rspn):
		if rspn[i] == ']':
			break
		i += 1
	while i >= 0:
		if rspn[i] == '}':
			end = i + 1
		if rspn[i] == '{':
			start = i
			break
		i -= 1
	return rspn[start + 12:end - 20]
	
def split(rspn):
	jsonList = []
	openBrac = 0
	start = -1
	for i in range(len(rspn)):
		if rspn[i] == '{':
			if openBrac == 0:
				start = i
			openBrac += 1
		elif rspn[i] == '}':
			if openBrac == 1:
				jsonList.append(rspn[start:i + 1])
			openBrac -= 1
	return jsonList

def joinRoom(username, password, roomId, check):
	user = MyUser(username, password, roomId) #username password roomId
	if password != "":
		status, reason, stream = user.login()
		#rspn = stream.decode('utf-8')
		#print(rspn)
	else:
		status, reason, stream = user.guest()
		#rspn = stream.decode('utf-8')
		#print(rspn)
	status, reason, stream = user.handshake()
	#rspn = stream.decode('utf-8')
	#print(rspn)
	status, reason, stream = user.metacon()
	#rspn = stream.decode('utf-8')
	#print(rspn)
	status, reason, stream = user.context()
	if check == True:
		rspn = stream.decode('utf-8')
		#print(rspn)
		start = rspn.find("\"users\":{")
		if start >= 0:
			end = rspn.find("}},", start)
			if end >= 0:
				rspn = rspn[start:end + 1]
				start = 0
				index = 0
				while index < len(rspn):
					start = rspn.find("\"userUuid\"", start)
					if start < 0:
						break
					end = rspn.find("\",", start)
					start = start + 12
					userUuid = rspn[start:end]
					start = rspn.find("\"username\"", end)
					if start < 0:
						break
					end = rspn.find("\"}", start)
					start = start + 12
					username = rspn[start:end]
					users[userUuid] = username
					index = start
		#for userUuid in users:
		#	print(users[userUuid])
	return user

def fakeUser(i, username, password, roomId):
	user = joinRoom(username, password, roomId, False) #username password roomId
	fakeList[i] = True
	while fakeList[i] == True:
		try:
			status, reason, stream = user.connect()
		except:
			user = joinRoom(username, password, roomId, False)
			continue
		rspn = stream.decode('utf-8')
		if rspn.find("\"error\":\"402::Unknown client\"") >= 0:
			fakeList[i] = False
			#print("[STATUS]: \"" + username + "\" Disconnected")
	status, reason, stream = user.logout()
	return

def seekUser(targetUser):
	result = 1
	if targetUser in guests:
		result = 2
	for userUuid in users:
		if users[userUuid] == targetUser:
			#print(userUuid + " : " + users[userUuid])
			return userUuid, result
	return "", 0

#busy.acquire()
#busy.release()

def main():
	busy = threading.Lock()
	username = "Iran_Is_Safe"
	password = "frlm"
	roomId = "215315" #207920 #215315
	GuestThreads = []
	for i in range(6) :
		guestThread = threading.Thread(target=fakeUser, args=(i, guests[i], "frlm", roomId, ))
		GuestThreads.append(guestThread)
		guestThread.start()
	index = 0
	user = joinRoom(username, password, roomId, True) #username password roomId
	statusFlags['connected'] = True
	while statusFlags['connected'] == True:
		try:
			status, reason, stream = user.connect()
		except:
			user = joinRoom(username, password, roomId, True)
			continue
		rspn = stream.decode('utf-8')
		#print("-" * 100)
		#print("in rspn: " + rspn)
		jList = split(rspn)
		for json in jList:
			jsonThread = threading.Thread(target=jsonParser, args=(json, str(index), roomId, user, busy))
			jsonThread.start()
			index += 1
			#print("in main: " + json)
		if rspn.find("\"error\":\"402::Unknown client\"") >= 0:
			statusFlags['connected'] = False
		if index > 5:
			index = 0
		#print("[STATUS]: \"" + username + "\" Connected")
		#for x in range(5):
		#	if fakeList[x] == False:
		#		print("[STATUS]: Fake $ \"" + guests[x] + "\" # Disconnected")
	status, reason, stream = user.logout()
	#print(str(stream))
	return

if __name__ == '__main__' :
	main()