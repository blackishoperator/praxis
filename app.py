#!/usr/bin/env python

import http.client
import threading
import queue
import html
import json
import time

direct = ["/authentication/guest",	#0
		  "/authentication/login",	#1
		  "/account/logout",		#2
		  "/cometd/handshake",		#3
		  "/cometd/connect",		#4
		  "/cometd/"]				#5

trstList = ["pixie", "Aallii", "loVely gaK", "sweety gak", "Nazanin_", "Artist Painter", "azizi", "GrumpyPersianCat"]

offence1 = ["fuck", "shit", "scum", "retarded", "ass", "arse", "gay", "homo", "rape"]
offence2 = ["sex", "cunt", "wank", "bitch"]
offence4 = ["whore", "dick", "cock", "penis", "slut"]
offence8 = [u"\u06A9\u06CC\u0631", u"\u06A9\u0648\u0633", u"\u062C\u0642", u"\u062C\u0646\u062F\u0647", u"\u06A9\u0648\u0646", u"\u0645\u0645\u0647", "kir", "kos", "jaq", "jende"]

q = queue.Queue()
p = queue.Queue()

class Shared():
	def __init__(self):
		self.exit = False
		self.cookie = ''
		self.clntId = ''
		self.cnid = 2
		self.cnidLock = threading.Lock()
		self.dataLock = threading.Lock()

	def inc_cnid(self):
		self.cnidLock.acquire()
		text = str(self.cnid)
		self.cnid += 1
		self.cnidLock.release()
		return text

	def set_cnid(self):
		self.cnidLock.acquire()
		self.cnid = 2
		self.cnidLock.release()
		return

	def get_cnid(self):
		self.cnidLock.acquire()
		cnid = self.cnid
		self.cnidLock.release()
		return cnid

	def set_cookie(self, newCookie):
		self.dataLock.acquire()
		if self.cookie != '':
			self.cookie = self.cookie + ";" + newCookie
		else:
			self.cookie = newCookie
		self.dataLock.release()
		return

	def get_cookie(self):
		self.dataLock.acquire()
		cookie = self.cookie
		self.dataLock.release()
		return cookie

	def set_clntId(self, NewclntId):
		self.dataLock.acquire()
		self.clntId = NewclntId
		self.dataLock.release()
		return

	def get_clntId(self):
		self.dataLock.acquire()
		clntId = self.clntId
		self.dataLock.release()
		return clntId

class User():
	def __init__(self, username, userUuid, isGuest):
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
		if isGuest == True:
			self.repLimit = 2
			self.capLimit = 8
			self.swrLimit = 2
			self.mutLimit = 8
		else:
			self.repLimit = 4
			self.capLimit = 8
			self.swrLimit = 8
			self.mutLimit = 4
		if self.username in trstList:
			self.isTrusted = True
		else:
			self.isTrusted = False

	def checkUser(self, userText):
		if self.isTrusted == True:
			self.lastText = userText
			return
		if self.lastText == userText:
			self.repeated += 1
		if userText.isupper() == True:
			self.capital += 1
		lowCase = userText.lower()
		wordList = lowCase.split()
		#print("[debug]: words $", wordList)
		for abuse in offence1:
			for word in wordList:
				if word.find(abuse) >= 0:
					self.swear += 1
		for abuse in offence2:
			for word in wordList:
				if word.find(abuse) >= 0:
					self.swear += 2
		for abuse in offence4:
			for word in wordList:
				if word.find(abuse) >= 0:
					self.swear += 4
		for abuse in offence8:
			for word in wordList:
				if word.find(abuse) >= 0:
					self.swear += 8
		if self.repeated >= self.repLimit or self.capital >= self.capLimit or self.swear >= self.swrLimit:
			self.repeated = 0
			self.capital = 0
			self.inMute = 0
			self.swear = 0
			self.mute = True
			self.spam += 1
		if self.inMute >= self.mutLimit:
			self.repeated = 0
			self.capital = 0
			self.inMute = 0
			self.swear = 0
			self.mute = False
		self.lastText = userText
		return

class Observer(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.clntId = ''
		self.cntId = 2
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()

	def send_recv(self, method, iLink, body):
		headers = {}
		headers["Host"] = "e-chat.co"
		if iLink < 2:
			headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		elif iLink > 2:
			headers["Content-Type"] = "application/json; charset=UTF-8"
		if iLink != 2:
			headers["Content-Length"] = str(len(body))
			headers["Connection"] = "keep-alive"
			body = body.encode('utf-8')
		if self.cookie != "":
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
				shr.set_cookie(tup[1][:tup[1].find(";")])
				self.cookie = shr.get_cookie()
		return status, reason, stream.decode('utf-8')

	def guest(self):
		body = "username=" + self.usrnme
		return self.send_recv("POST", 0, body)

	def login(self):
		body = "username=" + self.usrnme + "&password=" + self.passwd + "&rememberAuthDetails=false"
		return self.send_recv("POST", 1, body)

	def logout(self):
		status, reason, stream = self.send_recv("GET", 2, None)
		self.conn.close()
		return status, reason, stream

	def handshake(self):
		shr.set_cnid()
		body = "[{\"ext\":{\"chatroomId\":" + self.roomId + "},\"version\":\"1.0\",\"minimumVersion\":\"0.9\",\"channel\":\"/meta/handshake\",\"supportedConnectionTypes\":[\"long-polling\",\"callback-polling\"],\"advice\":{\"timeout\":60000,\"interval\":0},\"id\":\"1\"}]"
		status, reason, stream = self.send_recv("POST", 3, body)
		start = stream.find("\"clientId\"")
		end = stream.find(",", start)
		self.clntId = stream[start:end]
		shr.set_clntId(self.clntId)
		return status, reason, stream

	def metacon(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"advice\":{\"timeout\":0},\"id\":\"" + shr.inc_cnid() + "\"," + self.clntId + "}]"
		return self.send_recv("POST", 4, body)

	def connect(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"id\":\"" + shr.inc_cnid() + "\"," + self.clntId + "}]"
		return self.send_recv("POST", 4, body)

	def context(self):
		body = "[{\"channel\":\"/service/user/context/self/complete\",\"data\":{},\"id\":\"" + shr.inc_cnid() + "\"," + self.clntId + "}]"
		return self.send_recv("POST", 5, body)

	def join_room(self):
		print("[debug]: trying to join room")
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()
		if self.passwd != "":
			status, reason, stream = self.login()
		else:
			status, reason, stream = self.guest()
		status, reason, stream = self.handshake()
		status, reason, stream = self.metacon()
		status, reason, stream = self.context()
		self.alive = True
		shr.exit = False
		return

	def run(self):
		self.join_room()
		while self.alive == True:
			try:
				#print("[debug]: cnid in Master $", shr.get_cnid())
				status, reason, stream = self.connect()
				#print("[debug]: received new json")
			except:
				print("[error]: connection is lost")
				self.conn.close()
				self.join_room()
				continue
			rspn = stream
			#if rspn.find("9cd92a17-22c3-4c83-ab26-32bef7b01cc0") < 0:
			data = json.loads(rspn)
			for obj in data:
				if obj['channel'] != "/meta/connect":
					q.put(obj)
				else:
					self.alive = obj['successful']
			if shr.get_cnid() > 256:
				self.conn.close()
				self.join_room()
				print("[debug]: maximum number of requests reached")
		q.put(None)
		p.put(None)
		shr.exit = True
		status, reason, stream = self.logout()
		return

class Processor(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.userList = []
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.filter = False
		self.alive = False

	def run(self):
		while True:
			#print("[debug]: cnid in Processor $", shr.get_cnid())
			obj = q.get()
			#print("[debug]: got some data")
			if obj == None:
				break
			elif obj['channel'] == "/chatroom/message/add/" + self.roomId:
				try:
					userUuid = obj['data']['userUuid']
					username = html.unescape(obj['data']['username'])
					userText = html.unescape(obj['data']['messageBody'])
					self.message_add(userUuid, username, userText)
				except:
					print("[error]: json format has changed for /chatroom/message/add/")
					pass
			elif obj['channel'] == "/chatroom/user/joined/" + self.roomId:
				try:
					userUuid = obj['data']['userUuid']
					username = html.unescape(obj['data']['username'])
					isGuest = obj['data']['isGuest']
					self.user_join(userUuid, username, isGuest)
				except:
					print("[error]: json format has changed for /chatroom/user/joined/")
					pass
			elif obj['channel'] == "/chatroom/user/left/" + self.roomId:
				try:
					self.user_left(obj['data'])
				except:
					print("[error]: json format has changed for /chatroom/user/left/")
					pass
			elif obj['channel'] == "/service/conversation/message":
				try:
					self.private_add(obj['data']['msg'], obj['data']['key'])
				except:
					print("[error]: json format has changed for /service/conversation/message")
					pass
			#elif obj['channel'] == "/service/conversation/notification/added":
				#self.notify_add(obj)
			#elif obj['channel'][:21] == "/channel/user/friend/":
				#pass
		return

	def user_join(self, userUuid, username, isGuest):
		if self.filter == True and isGuest == True:
			pass
			#status, reason, stream = mod.userban(userUuid)
			#p.put([0, userUuid])
		else:
			user = User(username, userUuid, isGuest)
			self.userList.append(user)
			print("[debug]: user joined")
		if username == "GrumpyPersianCat":
			p.put([7, userUuid])
		return

	def user_left(self, userUuid):
		for user in self.userList:
			if user.userUuid == userUuid:
				self.userList.remove(user)
				if user.username == "GrumpyPersianCat":
					p.put([6, userUuid])
		print("[debug]: user left")
		return

	def message_add(self, userUuid, username, userText):
		i = self.find_user(userUuid)
		if i >= 0:
			self.userList[i].checkUser(userText)
			if self.userList[i].mute == True:
				p.put([2, userUuid])
				self.userList[i].inMute += 1
		else:
			user = User(username, userUuid, False)
			self.userList.append(user)
			print("[debug]: user added", len(self.userList))
		return

	def find_user(self, userUuid):
		result = -1
		for i in range(len(self.userList)):
			if self.userList[i].userUuid == userUuid:
				result = i
				break
		return result

	def seek_user(self, username):
		for user in self.userList:
			temp = username
			ratio = len(user.username.lower()) / len(username)
			if ratio >= 4:
				continue
			for char in user.username.lower():
				if char == temp[0]:
					temp = temp[1:]
					if len(temp) <= 1:
						return user.userUuid
		return None

	def private_add(self, msg, key):
		userOrdr = msg['o'] - 1
		userText = html.unescape(msg['m'])
		userText = userText.lower()
		userText = userText.replace("\\\"", "\"")
		if msg['o'] == 1:
			userUuid = key[:36]
		elif msg['o'] == 2:
			userUuid = key[36:]
		else:
			print("[error]: unexpected order", msg['o'])
			if key[:36] != "2abcce47-eda0-443d-a382-78bb4b45045e": #"9cd92a17-22c3-4c83-ab26-32bef7b01cc0"
				userUuid = key[:36]
			else:
				userUuid = key[36:]
		task = 10
		if userText[:4] == "ban ":
			target = userText[4:]
			task = 0
		elif userText[:6] == "unban ":
			target = userText[6:]
			task = 1
		elif userText[:7] == "remove ":
			target = userText[7:]
			task = 2
		else:
			p.put([5, userUuid, "i am not smart enough to interpert your order, blame it on my creator's stupidity"])
		if task < 3:
			if len(target) == 36 and target[8] == "-" and target[13] == "-" and target[18] == "-" and target[23] == "-":
				targetUserUuid = target
			else:
				targetUserUuid = self.seek_user(target)
			if targetUserUuid == None:
				targetUserUuid = self.search(target)
			if targetUserUuid != None:
				p.put([task, targetUserUuid])
				p.put([5, userUuid, "user was found"])
				#if task == 0:
					#for user in self.userList:
						#if user.userUuid == targetUserUuid:
							#self.userList.remove(user)
			else:
				p.put([5, userUuid, "no such user was found"])
		return

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
			username = username.lower()
			if username == targetUsername:
				return userUuid
		return None

class Operator(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.clntId = ''
		self.cntId = 2
		self.alive = False
		self.comt = http.client.HTTPConnection("e-chat.co")
		self.comt.connect()

	def send_recv(self, method, iLink, body):
		headers = {}
		headers["Host"] = "e-chat.co"
		headers["Content-Type"] = "application/json; charset=UTF-8"
		headers["Content-Length"] = str(len(body))
		headers["Connection"] = "keep-alive"
		body = body.encode('utf-8')
		headers["Cookie"] = shr.get_cookie()
		trynum = 0
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
		return status, reason, stream.decode('utf-8')

	def message(self, text):
		body = "[{\"channel\":\"/service/chatroom/message\",\"data\":{\"messageBody\":\"" + text + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body) #body.encode('utf-8')

	def openbox(self, convId):
		body = "[{\"channel\":\"/service/conversation/opened\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def closbox(self, convId):
		body = "[{\"channel\":\"/service/conversation/closed\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def private(self, convId, text):
		body = "[{\"channel\":\"/service/conversation/message\",\"data\":{\"conversationUserUuid\":\"" + convId + "\",\"messageBody\":\"" + text + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body) #body.encode('utf-8')	

	def addfriend(self, friendUuid):
		body = "[{\"channel\":\"/service/friends/add\",\"data\":{\"userUuid\":\"" + friendUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def removefriend(self, friendUuid):
		body = "[{\"channel\":\"/service/friends/remove\",\"data\":{\"userUuid\":\"" + friendUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def removetext(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/messages/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def removeban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def addban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/add\",\"data\":{\"targetUserUuid\":\"" + targetUuid +"\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_clntId() + "}]"
		return self.send_recv("POST", 5, body)

	def run(self):
		time.sleep(2)
		self.cookie = shr.get_cookie()
		self.clntId = shr.get_clntId()
		while True:
			#print("[debug]: cnid in Operator $", shr.get_cnid())
			cmd = p.get()
			#print("[debug]: got some task", cmd)
			if cmd == None:
				break
			elif cmd[0] == 0:
				status, reason, stream = self.addban(cmd[1])
			elif cmd[0] == 1:
				status, reason, stream = self.removeban(cmd[1])
			elif cmd[0] == 2:
				status, reason, stream = self.removetext(cmd[1])
			elif cmd[0] == 3:
				status, reason, stream = self.removefriend(cmd[1])
			elif cmd[0] == 4:
				status, reason, stream = self.addfriend(cmd[1])
			elif cmd[0] == 5:
				status, reason, stream = self.private(cmd[1], cmd[2])
			elif cmd[0] == 6:
				status, reason, stream = self.closbox(cmd[1])
			elif cmd[0] == 7:
				status, reason, stream = self.openbox(cmd[1])
			elif cmd[0] == 8:
				status, reason, stream = self.message(cmd[1])
		return

class Faker(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.clntId = ''
		self.cntId = 2
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()

	def send_recv(self, method, iLink, body):
		headers = {}
		headers["Host"] = "e-chat.co"
		if iLink < 2:
			headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		elif iLink > 2:
			headers["Content-Type"] = "application/json; charset=UTF-8"
		if iLink != 2:
			headers["Content-Length"] = str(len(body))
			headers["Connection"] = "keep-alive"
			body = body.encode('utf-8')
		if self.cookie != "":
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
		return status, reason, stream.decode('utf-8')

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
		self.cntId = 2
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

	def join_room(self):
		print("[debug]: trying to join room")
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()
		if self.passwd != "":
			status, reason, stream = self.login()
		else:
			status, reason, stream = self.guest()
		status, reason, stream = self.handshake()
		status, reason, stream = self.metacon()
		status, reason, stream = self.context()
		self.alive = True
		return

	def run(self):
		self.join_room()
		while self.alive == True:
			try:
				status, reason, stream = self.connect()
			except:
				print("[error]: connection is lost")
				self.conn.close()
				self.join_room()
				continue
			if stream.find("\"error\":\"402::Unknown client\"") >= 0 or shr.exit == True:
				self.alive = False
			elif self.cntId > 256:
				self.conn.close()
				self.join_room()
				print("[debug]: maximum number of requests reached")
		status, reason, stream = self.logout()
		return

shr = Shared()

def main():
	usrnme = "Iran_Is_Safe"
	passwd = "frlm"
	roomId = "215315"
	fod = Faker("awkward_silence", "frlm", roomId)
	fod.start()
	sod = Faker("solmaz", "frlm", roomId)
	sod.start()
	rod = Faker("razor", "frlm", roomId)
	rod.start()
	time.sleep(2)
	pod = Observer(usrnme, passwd, roomId)
	pod.start()
	mod = Processor(usrnme, passwd, roomId)
	mod.start()
	cod = Operator(usrnme, passwd, roomId)
	cod.start()
	return

if __name__ == '__main__':
	main()
