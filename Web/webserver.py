from app import app as application
from flask import Flask, request, render_template, session, redirect, url_for
from flask.ext.restful import Resource, Api
import json
import db_queries as queries

SECRET_KEY = "v5pH0wrNjiTOPMDfbBwFhzulY00bQ3ATNhaiOm1qBwriLN9w7M"

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

patient_contacts = {}
doc_contacts = {}
phone_contacts = {}
pwd_infos = {}

# NUMBER OF ECG POINTS PER PACKET
ECG_FREQ = 25
# X AXIS VALUE FOR ECG GRAPH
TIME_INTERVAL = ECG_FREQ/1000.0

@app.before_first_request
def setClientSession():
    if 'loggedIn' not in session:
        session["loggedIn"] = False
    if 'username' not in session:
        session["username"] = ""
    if 'userID' not in session:
        session["userID"] = ""
    if 'role' not in session:
        session["role"] = ""

@app.route('/home/', methods = ['GET', 'POST'])
def home():
	if request.method == "POST":
		#add code to check db for authentication
		username = request.form["username"]
		password = request.form["password"]
		
		print "%s %s" %(username, password)
		
		db = queries.db_connect()
		id = queries.userexists(db, username, password)
		print id
		if( id is not None):
			id = queries.hasCorrectCred(db, id, "Doctor")
			if(id is not None):
				session["loggedIn"] = True
				session["username"] = username
				session["userID"] = queries.userexists(db, username, password)
				session["role"] = "Clinician"
				return redirect(url_for('dochome'), code=302)
			else:
				session["loggedIn"] = "Wrong credentials"
				return render_template('home.html')
		else: # wrong authentication information
			session["loggedIn"] = "Does not exist"
			return render_template('home.html')
	else:
		return render_template('home.html')
		
@app.route('/dochome/', methods=['GET'])
def dochome():
	if request.method == "GET":
		db = queries.db_connect()
		print session["userID"]
		results = queries.getAllPatients(db, session["userID"])
		
		print results
	return render_template('dochome.html', db_results = results)
	
@app.route('/doctor/patientview/<int:patient_id>', methods=['GET'])
def viewPatient(patient_id):
	if request.method == "GET":
		db = queries.db_connect()
		results = queries.getPatientInfo(db, patient_id)
		return render_template('viewpatient.html', id = patient_id, patient_info = results)
		
@app.route('/doctor/patientview/<int:patient_id>/viewdata', methods=['GET'])
def viewPatientData(patient_id):
	if request.method == "GET":
		db = queries.db_connect()
		session_id = queries.getRecentSession(db, patient_id, session["userID"])
		print session_id
		results = queries.getSessionECG(db, session_id)
		
		# ECG processing code
		old_packet_num = 0;
		flotData = []
		x = 0
		#arrayInd = 0;
		for ecgData in results:
			rawEcgData = ecgData[0].split(" ")
			new_packet_num = int(rawEcgData[0])
			
			if ((new_packet_num - old_packet_num > 1) and (old_packet_num > 0)):
				print "missing packet from %d to %d" % (old_packet_num +1, new_packet_num -1)
				missingDataNum = (new_packet_num - old_packet_num - 1) * ECG_FREQ
				#tempIncorrectArray = []
				for dataindex in xrange(0, missingDataNum):
					tempdata = [x,0]
					flotData.append(tempdata)
					#tempIncorrectArray.append(tempdata)
					x += TIME_INTERVAL
				#flotData["incorrect"+str(arrayInd)] =  tempIncorrectArray
				#print flotData
				#arrayInd += 1
			elif(new_packet_num < old_packet_num):
				if(new_packet_num == 1):
					# the phone has restarted during the session
					old_packet_num = 0
				else:
					print "Packet out of order %d" % new_packet_num
				
			if(new_packet_num > old_packet_num):
				old_packet_num = new_packet_num
				data_length = len(rawEcgData)
				#tempCorrectArray = []
				for index in xrange(1, data_length):
					if "-" in rawEcgData[index]:
						y = - int(rawEcgData[index].replace('-', ''))
					else:
						y = int(rawEcgData[index])
					tempdata = [x, y]
					
					##### THIS IF STATEMENT WAS ADDED TO JUST VIEW THE ECG #####
					if(x < 13):
						flotData.append(tempdata)
					#tempCorrectArray.append(tempdata)
					x += TIME_INTERVAL
				#flotData["correct"+str(arrayInd)] = tempCorrectArray
				#arrayInd += 1
		#print flotData
		
		# split all numbers and match with x axis and create JSON object to be passed to template.
		# Also need to do processing to find out of order packets...
		
		return render_template('viewbiodata.html', id = patient_id, data = flotData)
		
@app.route('/clinicianprofile/', methods =['GET'])
def manageClinician():
	return render_template('dochome.html')
	
@app.route('/dochelp/', methods =['GET'])
def docHelp():
	return render_template('dochelp.html')
	
@app.route('/logout/', methods =['GET'])
def logout():
	if 'loggedIn' in session:
		session["loggedIn"] = False
	if 'username' in session:
		session["username"] = ""
	if 'userID' in session:
		session["userID"] = ""
	if 'role' in session:
		session["role"] = ""
	return render_template('home.html')

def flask_post_json():
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data != ''):
        return json.loads(request.data)
    else:
        return json.loads(request.form.keys()[0])

class doctorContacts(Resource):
	def get(self, clinician_id):
		if(len(doc_contacts) != 0):
			if(clinician_id in doc_contacts):
				return doc_contacts[clinician_id]
			else:
				return "no data"
		else:
			return "no data"
	
	def post(self, clinician_id):
		data = flask_post_json()
		doc_contact = {"address": data['address'], "name": data["name"], "id": data["id"],
		"session": data["session"], "assigned_index": data["assigned_index"]}
		doc_contacts[clinician_id] = doc_contact
		return doc_contact, 201
		
	def delete(self, clinician_id):
		if(clinician_id in doc_contacts):
			doc_contacts[clinician_id] = "no data"
			return "no data", 204
		else:
			return "no data"
		
class patientContacts(Resource):
	def get(self, clinician_id, patient_id):
		if(len(patient_contacts) != 0):
			if(clinician_id in patient_contacts):
				if(patient_id in patient_contacts[clinician_id]):
					return patient_contacts[clinician_id][patient_id]
				else:
					return "no data"
			else:
				return "no data"
		else:
			return "no data"
	
	def post(self, clinician_id, patient_id):
		data = flask_post_json()
		patient_contact = {"address": data['address'], "name": data["name"], "id": data["id"],
		"session": data["session"], "assigned_index": data["assigned_index"]}
		temp = {patient_id: patient_contact}
		patient_contacts[clinician_id] = temp
		
		return patient_contact, 201
		
	def delete(self, clinician_id, patient_id):
		if(clinician_id in patient_contacts):
			if(patient_id in patient_contacts[clinician_id]):
				patient_contacts[clinician_id][patient_id] = "no data"
				return "no data", 204
			else:
				return "no data"
		else:
			return "no data"
		
class phoneContacts(Resource):
	def get(self, macaddr):
		if(len(phone_contacts) != 0):
			if(macaddr in phone_contacts):
				print phone_contacts
				return phone_contacts[macaddr]
			else:
				return "no data"
		else:
			return "no data"
			
	def post(self, macaddr):
		data = flask_post_json()
		phone_contact = {"ssid": data['ssid'], "address": data['address']}
		phone_contacts[macaddr] = phone_contact
		return phone_contact, 201
		
	def delete(self, macaddr):
		if(macaddr in phone_contacts):
			phone_contacts[macaddr] = "no data"
			return "no data", 204
		else:
			return "no data"
		
class securityContacts(Resource):
	def get(self, rnd, macaddr):
		if(len(pwd_infos) != 0):
			if(rnd in pwd_infos):
				if(macaddr in pwd_infos[rnd]):
					return pwd_infos[rnd][macaddr]
				else:
					return "no data"
			else:
				return "no data"
		else:
			return "no data"
			
	def post(self, rnd, macaddr):
		data = flask_post_json()
		pwd_info = {"password": data['password']}
		temp = {macaddr: pwd_info}
		pwd_infos[rnd] = temp
		return pwd_info, 201
		
	def delete(self, rnd, macaddr):
		if(rnd in pwd_infos):
			if(macaddr in pwd_infos[rnd]):
				pwd_infos[rnd][macaddr] = "no data"
				return "no data", 204
			else:
				return "no data"
		else:
			return "no data"

api.add_resource(doctorContacts, '/doctors/<int:clinician_id>/')
api.add_resource(patientContacts, '/doctors/<int:clinician_id>/patients/<int:patient_id>/')
api.add_resource(phoneContacts, '/patientcmp/<string:macaddr>/')
api.add_resource(securityContacts, '/<string:rnd>/<string:macaddr>/')

if __name__ == '__main__':
	#app.debug = True
	app.run(host='0.0.0.0')