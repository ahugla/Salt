
import json
import requests

def returner(ret):
  
  PythonLogfile = "/tmp/returnerLog.log"
  MinionConfigFile = "/etc/salt/minion"
  vRLI_SERVER = "vrli.cpod-vrealize.az-fkd.cloud-garage.net"
  vRLI_PORT = "9000"
  

  # get salt Master
  fminion = open(MinionConfigFile, "r")
  for line in fminion:
    if ("master:") in line:
      line2 = line
      if not ("#") in line2:
        pos=line2.find(":") + 1
        line3 = line2[pos:]
        TEMP=line3.replace(" ","")
        TEMP=TEMP.replace("\n","")
        SALT_MASTER=TEMP.replace("\r","")
  fminion.close()


  # Open local log file and log parameters
  f = open(PythonLogfile, "a")
  f.write("\n\n\n****** NEW EXECUTION *******\n")
  f.write("MinionConfigFile : %s\n" % (MinionConfigFile))
  f.write("SALT_MASTER : %s\n" % (SALT_MASTER))
  f.write("vRLI_SERVER : %s\n" % (vRLI_SERVER))
  f.write("vRLI_PORT : %s\n" % (vRLI_PORT))


  # Get an usable payload fom salt execution 
  strRet=json.dumps(ret)        # obligatoire pour transformer le ret (dictionnaire) en string utilisable (avec " au lieu de ')
  jsonRet=json.loads(strRet)    # obligatoire pour pouvoir parser
  #for key in jsonRet:
  #  newline = "KEY : %s ---> VALUE : %s\n" % (key,jsonRet[key])    
  #  f.write(newline)


  # On recupere les arguments (type=liste) et on les transforme pour que cele ne pose pas de probleme ensuite dans le 'json.loads'
  #argument=['aa','bb','cc']
  argument=jsonRet["fun_args"]
  argStr=""
  for arg in argument:
    argStr = "%s-%s" % (argStr,arg)    # concatenate all arg and add - between them
  argStr2 = argStr[1:]                 # remove first - if exist
  if len(argStr2) == 0:                # set value 'N/A' if no arg
    argStr2 = "N/A"


  # Message to sent to VRLI
  messageLog = "Salt Execution, ParentMaster: %s, ReturnerKind: Minion, Function: %s, StateFile: %s, Minion: %s, IsSuccess: %s" % (SALT_MASTER,jsonRet["fun"],argStr2,jsonRet["id"],jsonRet["success"])
  messagevRLI= '{"messages":[{"text":"%s"}]}'  % (messageLog)
  #f.write("\n%s" % (messagevRLI))

  
  URL = "http://%s:%s/api/v1/messages/ingest/1" % (vRLI_SERVER, vRLI_PORT)
  headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
  messagevRLIDic = json.loads(messagevRLI)    # convert JSON to Dictionnary 
  #f.write(URL)
  #f.write("\n%s" % (headers))
  f.write("PAYLOAD: %s\n" % (messagevRLIDic))
  resp = requests.post(URL, verify=False, headers=headers, json=messagevRLIDic)
  if resp.status_code != 200:
     f.write("ERROR : Event NOT send to Log Insight\n")
  else:
     f.write("SUCCESS : Event sent to Log Insight\n")


  # Commande pour voir le payload:
  # salt-call --local --metadata test.ping --out=pprint

  f.close()
