from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect  
import MySQLdb
import time
import random
import math
import serial
import matplotlib.pyplot as plt
import numpy as np
import configparser as ConfigParser

async_mode = None

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')
print (myhost)

ser=serial.Serial('/dev/ttyS3',9600)
ser.baudrate=9600

ser2=serial.Serial('/dev/ttyS2',9600)
ser2.baudrate=9600

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 

def background_thread(args):
    count = 0
    count1 = 0
    dataCounter = 0 
    dataList = []  
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    fo = open("static/files/test.txt","a+")
    data=chr(48+50)
    while True:
        emit = dict(args).get('emit')
        print(emit)
        print (args)
        socketio.sleep(0.2)
        if args:
            btnV = dict(args).get('btn_value')
            dbV = dict(args).get('db_value') 
        else:
            btnV = 'null'
            dbV = 'nieco'
        while count1<=10:
             if count1 == 0:
                 socketio.emit('my_response',
                                {'data': 'Choose your input value and start the simulation', 'count': count1},
                                namespace='/test')
             if count1 >=10:
                 socketio.emit('my_response',
                                {'data': 'Time is up', 'count': count1},
                                namespace='/test')
             if args:
                A = dict(args).get('A')
                B= int(A)
                data=chr(B) 
             else:
                A = 1
                data = chr(48+5)+chr(48)
             ser_write= ser2.write(data.encode())
             count1=count1+1
             socketio.sleep(0.5)
             
        read_ser=ser.readline()
        y=[]
        if read_ser != b'OK\n':
            y.append(float(read_ser))
            read_ser=ser.readline()
            count += 1
            dataCounter +=0.001/3
            prem = y
            if len(dataList)>0:
              print (str(dataList))
              print (str(dataList).replace("'", "\""))
            if emit == 1:
                socketio.emit('my_response',
                              {'data': prem[-1], 'count': count},
                              namespace='/test')  
        if dbV == 'start':
          fo = open("static/files/test.txt","a+")
          dataDict = {
            "x": dataCounter,
            "y": prem[-1]}
          fo.write("{"+'"y": '+str(dataCounter)+', "x": '+str(prem[-1])+"}, ")
          dataList.append(dataDict) 
        else:
          fo.close
          if len(dataList)>0:
            print (str(dataList))
            var = str(dataList).replace("'", "\"")
            print (var)
            cursor = db.cursor()
            cursor.execute("SELECT MAX(id) FROM graph")
            maxid = cursor.fetchone()
            cursor.execute("INSERT INTO graph (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, var))
            db.commit()
          dataList = []
          dataCounter = 0 
    db.close()
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
       
@app.route('/graphlive', methods=['GET', 'POST'])
def graphlive():
    return render_template('graphlive.html', async_mode=socketio.async_mode)

@app.route('/gauge', methods=['GET', 'POST'])
def gauge():
    return render_template('gauge.html', async_mode=socketio.async_mode)

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    return render_template('graph.html', async_mode=socketio.async_mode)
    
@app.route('/db')
def db():
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  cursor.execute('''SELECT  hodnoty FROM  graph''')
  rv = cursor.fetchall()
  return str(rv)    

@app.route('/dbdata/<string:num>', methods=['GET', 'POST'])
def dbdata(num):
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  print (num)
  cursor.execute("SELECT hodnoty FROM  graph WHERE id=%s", num)
  rv = cursor.fetchone()
  return str(rv[0])

@app.route('/write')
def write2file():
    fo = open("static/files/test.txt","a+")
    val = "a"
    fo.write("%s\r\n" %val)
    return "done"

@app.route('/read/<string:num>')
def readmyfile(num):
    fo = open("static/files/test.txt","r")
    rows = fo.readlines()
    return rows[int(num)-1]
       
@socketio.on('db_event', namespace='/test')
def db_message(message):   
    session['db_value'] = message['value']    

@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
    emit('my_response',
        {'data': message['value'], 'count': session['receive_count']})
 
@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('start_request', namespace='/test')
def start_request():
    session['emit'] = 1
    print (session['emit'])
    print (session)
         
@socketio.on('stop_request', namespace='/test')
def stop_request():
    session['emit'] = 0
    print (session['emit'])
    print (session)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
#    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('click_event', namespace='/test')
def db_message(message):   
    session['btn_value'] = message['value']    

@socketio.on('slider_event', namespace='/test')
def slider_message(message):  
    #print message['value']   
    session['slider_value'] = message['value']  

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)