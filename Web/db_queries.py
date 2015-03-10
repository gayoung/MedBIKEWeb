#!/usr/bin/python
import MySQLdb

#connects to the database and returns a database object that can be passed to other query functions
def db_connect():
    return MySQLdb.connect(host="192.168.0.101", user="medbike_admin", passwd="PB-ASTUS", db="medbike")
	#return MySQLdb.connect(host="localhost", user="medbike_admin", passwd="PB-ASTUS", db="medbike")

#returns a single value
def returnSingleValue(db, query, variables):
    cursor = db.cursor()

    try:
        cursor.execute(query, variables)
    except MySQLdb.Error, e:
        print "MySQL error: %s" % str(e)
        cursor.close()
        return

    data = cursor.fetchone()

    if (data != None):
        data = data[0]
    else:
        data = None

    cursor.close()
    return data

#returns a single row
def returnSingleRow(db, query, variables):
    cursor = db.cursor()

    try:
        cursor.execute(query, variables)
    except MySQLdb.Error, e:
        print "MySQL error: %s" % str(e)
        cursor.close()
        return

    data = cursor.fetchone()
    cursor.close()
    return data

#returns all rows
def returnAllRows(db, query, variables):
    cursor = db.cursor()

    try:
        cursor.execute(query, variables)
    except MySQLdb.Error, e:
        print "MySQL error: %s" % str(e)
        cursor.close()
        return

    data = cursor.fetchall()
    cursor.close()
    return data
	
def userexists(db, username, pw):
	query = "SELECT id FROM Authentication WHERE username=AES_ENCRYPT(%s, 'PB-ASTUS') AND password=AES_ENCRYPT(%s, 'PB-ASTUS')"
	vars = [username, pw]
	return returnSingleValue(db, query, vars)
	
def hasCorrectCred(db, id, role):
	query = "SELECT id FROM Authentication WHERE id=%s AND role=AES_ENCRYPT(%s, 'PB-ASTUS')"
	vars = [id, role]
	return returnSingleValue(db, query, vars)
	
def getAllPatients(db, clinician_id):
	query = "SELECT patient_id, AES_DECRYPT(patient_number, 'PB-ASTUS'), AES_DECRYPT(fname, 'PB-ASTUS'), AES_DECRYPT(lname, 'PB-ASTUS'), date_joined, date_birth, AES_DECRYPT(email, 'PB-ASTUS') FROM patient WHERE staff_id=%s"
	vars = [clinician_id]
	return returnAllRows(db, query, vars)
	
def getPatientInfo(db, patient_id):
	query = "SELECT patient_id, AES_DECRYPT(patient_number, 'PB-ASTUS'), AES_DECRYPT(fname, 'PB-ASTUS'), AES_DECRYPT(lname, 'PB-ASTUS'), date_joined, date_birth, AES_DECRYPT(email, 'PB-ASTUS') FROM patient WHERE patient_id=%s"
	vars = [patient_id]
	return returnSingleRow(db, query, vars)
	
def getRecentSession(db, patient_id, clinician_id):
	#query = "SELECT id, date_start FROM patient_session WHERE patient_id = %s AND staff_id = %s ORDER BY date_start DESC"
	# for query testing... all data within db is with offline doctor
	query = "SELECT id FROM patient_session WHERE patient_id = %s AND staff_id = 4 ORDER BY date_start DESC"
	vars = [patient_id]
	return returnSingleRow(db, query, vars)
	
def getSessionECG(db, session_id):
	query = "SELECT AES_DECRYPT(ecg_data, 'PB-ASTUS') FROM ecg_data WHERE session_id=%s"
	vars = [session_id]
	return returnAllRows(db, query, vars)