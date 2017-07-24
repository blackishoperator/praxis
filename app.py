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

badWords = ["fuck", "shit", "scum", "retarded", "sex", "rape", "ass", "arse", "cunt", "wank", "bitch", "whore", "gay", "homo", "dick", "cock", "penis", "kir", "kos", "jaq", "jende"]
parsOdds = [u"\u06A9\u06CC\u0631", u"\u06A9\u0648\u0633", u"\u062C\u0642", u"\u062C\u0646\u062F\u0647"]
userList = []
muteList = []
fakeList = ["awkward_silence", "solmaz", "razor"]

class ChatUser():
	def __init__(self, username, userUuid, isGuest):
		self.dataLock = threading.Lock()
		self.muteLock = threading.Lock()
		self.username = username
		self.userUuid = userUuid
		self.lastText = ''
		self.repeated = 0
		self.isGuest = isGuest
		self.capital = 0
		self.inMute = 0
		self.swear = 0
		self.mute = False
		self.spam = 0
		#if isGuest == True:
			#self.repLimit = 2
			#self.capLimit = 8
			#self.swrLimit = 2
			#self.mutLimit = 8
		#else:
			#self.repLimit = 2
			#self.capLimit = 8
			#self.swrLimit = 2
			#self.mutLimit = 4

	def checkUser(self, userText):
		self.dataLock.acquire()
		if self.lastText == userText:
			self.repeated += 1
		if userText.isupper() == True:
			self.capital += 1
		lowCase = userText.lower()
		for abuse in badWords:
			if lowCase.find(abuse) >= 0:
				self.swear += 1
		for abuse in parsOdds:
			if lowCase.find(abuse) >= 0:
				self.swear += 1
		if self.repeated >= 2 or self.capital >= 16 or self.swear >= 2:
			self.repeated = 0
			self.capital = 0
			self.inMute = 0
			self.swear = 0
			self.mute = True
			self.spam += 1
		if self.inMute >= 4:
			self.repeated = 0
			self.capital = 0
			self.inMute = 0
			self.swear = 0
			self.mute = False
		self.lastText = userText
		self.dataLock.release()
		return

	def isMuted(self):
		self.muteLock.acquire()
		state = self.mute
		self.muteLock.release()
		return state

	def incMute(self):
		self.muteLock.acquire()
		self.inMute += 1
		self.muteLock.release()
		return

	def sendUser(self):
		attrList = []
		attrList.append("username: " + self.username)
		attrList.append("userUuid: " + self.userUuid)
		attrList.append("lastText: " + self.lastText)
		attrList.append("repeated: " + str(self.repeated))
		attrList.append("isGuest: " + str(self.isGuest))
		attrList.append("capital: " + str(self.capital))
		attrList.append("inMute: " + str(self.inMute))
		attrList.append("swear: " + str(self.swear))
		attrList.append("mute: " + str(self.mute))
		attrList.append("spam: " + str(self.spam))
		return attrList

class ModUser():
	def __init__(self, usrnme, passwd, roomId):
		self.dataLock = threading.Lock()
		self.comtLock = threading.Lock()
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.clntId = ''
		self.filter = False
		self.cntId = 2
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()
		self.comt = http.client.HTTPConnection("e-chat.co")
		self.comt.connect()

	def send_recv(self, method, iLink, body):
		trynum = 0
		headers = {}
		headers["Host"] = "e-chat.co"
		if iLink != 3:
			headers["Connection"] = "keep-alive"
		if iLink < 3:
			headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		elif iLink > 3:
			headers["Content-Type"] = "application/json; charset=UTF-8"
		if body != None:
			headers["Content-Length"] = str(len(body))
			body = body.encode('utf-8')
		if self.cookie != '':
			headers["Cookie"] = self.cookie
		if iLink != 4:
			self.comtLock.acquire()
			#print("[debug]: acquired comtLock")
			while trynum < 5:
				try:
					trynum += 1
					self.comt.request(method, direct[iLink], body, headers)
					rspn = self.comt.getresponse()
					status = rspn.status
					reason = rspn.reason
					hdlist = rspn.getheaders()
					stream = rspn.read()
					rspn.close()
					trynum = 6
				except:
					self.comt.close()
					self.comt = http.client.HTTPConnection("e-chat.co")
					self.comt.connect()
					continue
			self.comtLock.release()
			#print("[debug]: released comtLock")
		else:
			#print("[debug]: fetching new json")
			while trynum < 5:
				try:
					trynum += 1
					self.conn.request(method, direct[iLink], body, headers)
					rspn = self.conn.getresponse()
					status = rspn.status
					reason = rspn.reason
					hdlist = rspn.getheaders()
					stream = rspn.read()
					rspn.close()
					trynum = 6
				except:
					self.conn.close()
					self.conn = http.client.HTTPConnection("e-chat.co")
					self.conn.connect()
					continue
			#print("[debug]: received new json")
		for tup in hdlist:
			if "Set-Cookie" in tup:
				newCookie = tup[1][:tup[1].find(";")]
				if self.cookie != '':
					self.cookie = self.cookie + ";" + newCookie
				else:
					self.cookie = newCookie
		return status, reason, stream.decode('utf-8')

	def removetext(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/messages/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		return self.send_recv("POST", 5, body)

	def userban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/add\",\"data\":{\"targetUserUuid\":\"" + targetUuid +"\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		status, reason, stream = self.send_recv("POST", 5, body)
		body = "[{\"channel\":\"/service/moderator/ban/fetch\",\"data\":{},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		status, reason, stream = self.send_recv("POST", 5, body)
		return status, reason, stream

	def userunban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		status, reason, stream = self.send_recv("POST", 5, body)
		body = "[{\"channel\":\"/service/moderator/ban/fetch\",\"data\":{},\"id\":\"" + str(self.cntId) + "\"," + self.clntId + "}]"
		self.cntId += 1
		status, reason, stream = self.send_recv("POST", 5, body)
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
		return self.send_recv("POST", 5, body) #body.encode('utf-8')

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
		return self.send_recv("POST", 5, body) #body.encode('utf-8')

	def search(self, targetUsername):
		body = "targetUsername=" + targetUsername
		seek = http.client.HTTPConnection("e-chat.co")
		seek.connect()
		headers = {}
		headers["Host"] = "e-chat.co"
		headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		headers["Content-Length"] = str(len(body))
		body = body.encode('utf-8')
		seek.request("POST", "/search/users", body, headers)
		rspn = seek.getresponse()
		status = rspn.status
		reason = rspn.reason
		hdlist = rspn.getheaders()
		stream = rspn.read()
		rspn.close()
		stream = stream.decode('utf-8')
		rspn = html.unescape(stream)
		index = 0
		start = 0
		end = 0
		while index < len(rspn):
			start = rspn.find("\"userUuid\"", start)
			if start < 0:
				break
			end = rspn.find("\",", start)
			if end < 0:
				break
			userUuid = rspn[start + 12:end]
			start = end
			start = rspn.find("\"username\"", start)
			end = rspn.find("\"}", start)
			username = rspn[start + 12:end]
			username = html.unescape(username)
			if username == targetUsername:
				return userUuid
		return None

	def isAlive(self):
		self.dataLock.acquire()
		state = self.alive
		self.dataLock.release()
		return state

	def updateState(self, state):
		self.dataLock.acquire()
		self.alive = state
		self.dataLock.release()
		return

def addMessage(json, mod):
	start = json.find("\"messageBody\"")
	end = json.find("\",", start)
	start = start + 15
	userText = json[start:end]
	userText = html.unescape(userText)
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
		status, reason, stream = mod.removetext(userUuid)
		return
	i = findUser(userUuid)
	if i >= 0:
		userList[i].checkUser(userText)
		if userList[i].isMuted() == True:
			status, reason, stream = mod.removetext(userUuid)
			userList[i].incMute()
	else:
		newUser = ChatUser(username, userUuid, False)
		userList.append(newUser)
		#print("[debug]: new user added to list")

def userJoin(json, mod):
	start = json.find("\"userUuid\"")
	end = json.find("\",", start)
	start = start + 12
	userUuid = json[start:end]
	start = json.find("\"username\"")
	end = json.find("\"}", start)
	start = start + 12
	username = json[start:end]
	username = html.unescape(username)
	index = json.find("\"isGuest\"")
	field = json[index + 10:index + 14]
	isGuest = True
	if field == "fals":
		isGuest = False
	if mod.filter == True and isGuest == True:
		status, reason, stream = mod.userban(userUuid)
		return
	newUser = ChatUser(username, userUuid, isGuest)
	userList.append(newUser)
	#print("[debug]: new user joined")
	return

def userLeft(json, mod):
	start = json.find("\"data\"")
	end = json.find("\",", start)
	start = start + 7
	userUuid = json[start + 1:end]
	user = None
	i = findUser(userUuid)
	if i >= 0:
		user = userList.pop(i)
		if (user.isGuest == True and user.swear >= 1) or user.spam >= 1:
			status, reason, stream = mod.removetext(user.userUuid)
		if user.spam >= 4:
			status, reason, stream = mod.userban(user.userUuid)
	#print("[debug]: user left")
	return

def handlePM(json, mod):
	start = json.find("\"userUuid\"")
	end = json.find("\",", start)
	start = start + 12
	userUuid = json[start:end]
	start = json.find("\"username\"")
	end = json.find("\"}", start)
	start = start + 12
	username = json[start:end]
	status, reason, stream = mod.openbox(userUuid)
	#print("[debug]: opened message box")
	userText = getText(stream)
	#print("[debug]:", username, "$", userText)
	if userText[:4] == "ban ":
		targetUsername = userText[4:]
		targetUserUuid = mod.search(targetUsername)
		if targetUserUuid != None:
			status, reason, stream = mod.userban(targetUserUuid)
			status, reason, stream = mod.private(userUuid, "user was found")
		else:
			status, reason, stream = mod.private(userUuid, "no such user was found")
	elif userText[:6] == "unban ":
		targetUsername = userText[6:]
		targetUserUuid = mod.search(targetUsername)
		if targetUserUuid != None:
			status, reason, stream = mod.userunban(targetUserUuid)
			status, reason, stream = mod.private(userUuid, "user was found")
		else:
			status, reason, stream = mod.private(userUuid, "no such user was found")
	elif userText[:5] == "mute ":
		targetUsername = userText[5:]
		muteList.append(targetUsername)
		text = "muted " + targetUsername
		status, reason, stream = mod.private(userUuid, text)
	elif userText[:7] == "unmute ":
		targetUsername = userText[7:]
		muteList.remove(targetUsername)
		text = "unmuted " + targetUsername
		status, reason, stream = mod.private(userUuid, text)
	elif userText == "clear mute":
		muteList.clear()
		status, reason, stream = mod.private(userUuid, "mute list cleared")
	elif userText[:7] == "remove ":
		targetUsername = userText[7:]
		targetUserUuid = mod.search(targetUsername)
		if targetUserUuid != None:
			status, reason, stream = mod.removetext(targetUserUuid)
			status, reason, stream = mod.private(userUuid, "user was found")
		else:
			status, reason, stream = mod.private(userUuid, "no such user was found")
	elif userText[:7] == "filter ":
		state = userText[7:]
		if state == "on":
			mod.filter = True
			status, reason, stream = mod.private(userUuid, "guest filter set on")
		elif state == "off":
			mod.filter = False
			status, reason, stream = mod.private(userUuid, "guest filter set off")
	elif userText[:8] == "inquire ":
		targetUsername = userText[8:]
		i = seekUser(targetUsername)
		if i >= 0:
			user = userList[i]
			attrList = user.sendUser()
			for attr in attrList:
				status, reason, stream = mod.private(userUuid, attr)
		else:
			status, reason, stream = mod.private(userUuid, "no such user was found")
	status, reason, stream = mod.closbox(userUuid)
	#print("[debug]: closed message box")
	return

def findUser(userUuid):
	result = -1
	for i in range(len(userList)):
		user = userList[i]
		if user.userUuid == userUuid:
			result = i
			break
	return result

def seekUser(username):
	result = -1
	for i in range(len(userList)):
		user = userList[i]
		if user.username == username:
			result = i
			break
	return result

def joinRoom(username, password, roomId, check):
	user = ModUser(username, password, roomId) #username password roomId
	if password != "":
		status, reason, stream = user.login()
	else:
		status, reason, stream = user.guest()
	status, reason, stream = user.handshake()
	status, reason, stream = user.metacon()
	status, reason, stream = user.context()
	user.updateState(True)
	return user

def getText(rspn):
	txt = "}],\""
	cnt = 0
	i = 0
	start = 0
	end = len(rspn)
	while i < len(rspn):
		if rspn[i] == txt[cnt]:
			cnt += 1
			if cnt == 4:
				break
		else:
			cnt = 0
		i += 1
	while i >= 0:
		if rspn[i] == '}':
			end = i + 1
		if rspn[i] == '{':
			start = i
			break
		i -= 1
	userText = html.unescape(rspn[start + 12:end - 20])
	return userText

def fakeUser(username, password, roomId):
	fake = joinRoom(username, password, roomId, False)
	while fake.isAlive() == True:
		try:
			status, reason, stream = fake.connect()
		except:
			fake = joinRoom(username, password, roomId, False)
			continue
		rspn = stream
		if rspn.find("\"error\":\"402::Unknown client\"") >= 0:
			fake.updateState(False)
	status, reason, stream = fake.logout()
	return

def main():
	username = "Iran_Is_Safe"
	password = "frlm"
	roomId = "215315" #207920 #215315
	for fake in fakeList:
		fakeThread = threading.Thread(target=fakeUser, args=(fake, password, roomId, ))
		fakeThread.start()
	user = joinRoom(username, password, roomId, False) #username password roomId
	while user.isAlive() == True:
		try:
			status, reason, stream = user.connect()
		except:
			user = joinRoom(username, password, roomId, False)
			continue
		rspn = stream
		txt = "\"channel\":\""
		cnt = 0
		openBrac = 0
		openChan = 0
		first = 0
		last = 0
		start = -1
		for i in range(len(rspn)):
			if openBrac > 0 and rspn[i] == txt[cnt]:
				cnt += 1
				if cnt == 11:
					first = i + 1
					openChan += 1
					cnt = 0
			else:
				cnt = 0
			if openChan > 0 and first < i and rspn[i] == "\"":
				last = i
				openChan = 0
			if rspn[i] == '{':
				if openBrac == 0:
					start = i
				openBrac += 1
			elif rspn[i] == '}':
				if openBrac == 1:
					json = rspn[start:i + 1]
					channel = rspn[first:last]
					if channel == "/chatroom/message/add/" + roomId:
						roomThread = threading.Thread(target=addMessage, args=(json, user, ))
						roomThread.start()
					elif channel == "/chatroom/user/joined/" + roomId:
						joinThread = threading.Thread(target=userJoin, args=(json, user, ))
						joinThread.start()
					elif channel == "/chatroom/user/left/" + roomId:
						leftThread = threading.Thread(target=userLeft, args=(json, user, ))
						leftThread.start()
					elif channel == "/service/conversation/notification/added":
						prvtThread = threading.Thread(target=handlePM, args=(json, user, ))
						prvtThread.start()
					elif channel == "/meta/connect":
						if json.find("\"error\":\"402::Unknown client\"") >= 0:
							user.updateState(False)
				openBrac -= 1
	status, reason, stream = user.logout()
	return

if __name__ == '__main__':
	main()