#!python

'''
  Author: Ricky Martinez
  Task:
    This script gets information that was submitted to the InterfaceError table in the DB. It parses 
    through the information and makes adds a flag to recurring errors. This flag is
    used to highlight the errors on the Interface page. From the information obtained through
    the DB, a page called NEW_HTML_INTERFACE is generated. These files are generated daily and
    saved in their respective directory (<year>/<month>/<date>/NEW_HTML_INTERFACE.html)
   -After writing the files, permissions on file are changed (the file is written with no
    permissions, initially
'''

import jinja2
import cgi
import cgitb
import MySQLdb
import datetime
import tempfile
import os
import shutil
import subprocess


cgitb.enable()
os.umask(0o777)
templates = jinja2.Environment(loader = jinja2.FileSystemLoader(searchpath="templates"))

###############
debug_list = []
###############
result_dict = {}

#Create temp file
#tf = tempfile.NamedTemporaryFile()
#tf_path = tf.name
#CREATE timestamp
timestamp = datetime.datetime.today()
year = timestamp.year
month = '{:02d}'.format(timestamp.month)
day = '{:02d}'.format(timestamp.day)

def ConnectDatabase():
  #GET DB info
  with open('pythonmysql.ini','r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
      if i == 0:
        host = line[:-1]
      elif i == 1:
        username = line[:-1]
      elif i == 2:
        password = line[:-1]
      elif i == 3:
        socket = line[:-1]
  #CONNECT to DB
  try:
    db = MySQLdb.connect(host=host,user=username,passwd=password, db="NMG",unix_socket=socket)
  except Exception as e:
    print("Unable to establish DB connection")
    print (e)
    sys.exit()
    db = None;

  return db;

def MakeDict(cursor):
  flag =0
  #Get information
  select_query = "SELECT i.* FROM InterfaceError i left join PortInfoTable p on (p.switch =i.device and p.port =i.interface) where (p.duplex != 'half' or p.duplex is null) and (inputerror >= '5' or crc>5 or collisions >='10') and DATE(timestamp)=CURDATE() ORDER BY inputerror DESC;"
  cursor.execute(select_query)
  select_res = cursor.fetchall()

  select_query2 = "SELECT i.* FROM InterfaceError i left join PortInfoTable p on (p.switch =i.device and p.port =i.interface) where (p.duplex != 'half' or p.duplex is null) and (inputerror >= '5' or crc>5 or collisions >='10') and DATE(timestamp) = CURDATE()-1 ORDER BY inputerror DESC;"
  cursor.execute(select_query2)
  select_res2 = cursor.fetchall()

  for i in select_res:
    for p in select_res2:
      flag = 0
      if i[1] == p[1]:
        flag = 1
        break

    if not "info" in result_dict:
      result_dict["info"] = []

    result_dict["info"].append({
      "timestamp"       : i[0],
      "device"          : i[1],
      "interface"       : i[2],
      "inputError"      : i[3],
      "outputError"     : i[4],
      "CRC"             : i[5],
      "collisions"      : i[6],
      "reset"           : i[7],
      "flag"            : flag,
    })
  return result_dict;


def main():
  try:
    #Get database obj
    db = ConnectDatabase();
    cur = db.cursor()
    print("Connected to database\n")
  except Exception as e:
    db = None
    cur = None
    print("Unable to connect to database\n")
    print(e)

  try:
    query_res = MakeDict(cur)
    print("Got DB information\n")
  except Exception as e:
    query_res = None
    print("Error getting information from Database\n")
    print(e);
  return query_res

query_res = main()


template = templates.get_template("InterfaceErrorReport_new.html")
file_name = 'InterfaceErrReport.html'.format(year,month,day)
with open(file_name,'w+')as f:
  try:
    f.write(template.render(debug_list=debug_list, query_res=query_res, timestamp=timestamp))
    print("Created File: {}\n".format(file_name))
  except Exception:
    print("Error creating file: {}".format(file_name))
# File is created with no permissions
# Set permissions
try:
  subprocess.call(['chmod','0644',file_name])
  print("Permissions set for: {}".format(file_name))
except Exception:
  print("Error while changing permissions for: {}".format(file_name));
