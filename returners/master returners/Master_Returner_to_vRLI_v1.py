#  EXEMPLE de MASTER RETURNER:  SSC :     /usr/lib/python3.6/site-packages/sseape/returners/sseapi_return.py
#                               Salt Open /usr/lib/python3.6/site-packages/salt/returners/cassandra_cql_return.py
#
#  MASTER RETURNER
#  v 1.0
#  Alexandre Hugla
#  12 Dec 2021
#  alex_event_returner1.py
#
#  USAGE :
#  -----
#  Requires LogInsight config to be set:
#  A. On Salt Master Open Source
#     Put in '/etc/salt/master.d/event_return.conf':
#       vrli_return:
#         address:  vrli.cpod-vrealize.az-fkd.cloud-garage.net
#         port: 9000
#  B. On Saltconfig (SSC)
#     Put in '/etc/salt/master.d/vrli.conf':
#       vrli_return:
#         address:  vrli.cpod-vrealize.az-fkd.cloud-garage.net
#         port: 9000
#



import json
import requests


def event_return(events):    # events is a "list"
  PythonLogfile = "/tmp/event_returnerLog.log"
  ReturnerKind = "Master_Returner"

  # Open local log file and log parameters
  f = open(PythonLogfile, "a")

  # retrieve options  and get masterFQDN, vRLI_SERVER and vRLI_PORT
  opts=json.dumps(__opts__)
  #f.write(str(opts))                    # =>  permet de le voir au format json (avec "")
  jsonopts=json.loads(opts)
  grains=jsonopts["grains"]
  #f.write(str(grains))
  masterFQDN=grains["fqdn"]
  VRLIsettings=jsonopts["vrli_return"]
  vRLI_SERVER=VRLIsettings["address"]
  vRLI_PORT=VRLIsettings["port"]

  #Pour chaque evenement de la liste
  for event in events:                  # event is a "dict"
    tag = event.get("tag", "")
    data = event.get("data", "")
    minion_name = data.get("id")
    Function = data.get("fun")
    isSuccess = data.get("success")
    target = data.get("tgt")
    '''
    #purely log
    if (tag.find('salt/auth') != 0) and (tag.find('salt/raas_master/iteration') != 0):
      f.write("all tag : %s\n" % (tag))
      #f.write("all data : %s\n" % (data))
    '''

    # Find if event is a return of a job execution
    # Do not log to vRLI if Function = 'saltutil.find_job'
    # Il faut aussi que function existe sinon on se retrouve avec des logs Function=None
    #INUTILE : if (tag.find('ret') != -1) and (tag.find('salt/auth') != 0) and (Function != "saltutil.find_job") and (Function):
    if (tag.find('ret') != -1) and (Function != "saltutil.find_job") and (Function):
      f.write("C est un retour d'execution\n")
      f.write("tag : %s\n" % (tag))
      #f.write("data : %s\n" % (data))
      '''
      f.write("minion_name : %s\n" % (minion_name))
      f.write("target : %s\n" % (target))
      f.write("ReturnerKind : %s\n" % (ReturnerKind))
      f.write("Function : %s\n" % (Function))
      f.write("isSuccess : %s\n" % (isSuccess))
      '''
      # Get State File if exist, N/A if not
      statefile = func_GET_STATE_FILE(Function,data,"fun_args")


      #Envoie a Log Insight
      func_VRLI_CREATE_AND_SEND(f,masterFQDN,Function,statefile,minion_name,isSuccess,vRLI_SERVER,vRLI_PORT)


    else:
      #f.write("Ce n'est pas un retour d'execution\n")
      # On gere le cas de timeout minion dans SSC (tag..../complete). Pas de gestion de timeout sur le  Salt Master Open Source
      if (tag.find('complete') != -1):
        f.write("SSC timeout\n")
        isSuccess="TIMEOUT"
        all_minion_name=data["missing"]    # =>  ['vra-006613.cpod-vrealize.az-fkd.cloud-garage.net', 'vra-006612.cpod-vrealize.az-fkd.cloud-garage.net']
        statefile = func_GET_STATE_FILE(Function,data,"arg")
        for minion_name in all_minion_name:
          func_VRLI_CREATE_AND_SEND(f,masterFQDN,Function,statefile,minion_name,isSuccess,vRLI_SERVER,vRLI_PORT)


  f.close()


# Create message and send it to Log Insight
def func_VRLI_CREATE_AND_SEND(f,masterFQDN,Function,statefile,minion_name,isSuccess,vRLI_SERVER,vRLI_PORT):
  # Create Message
  messageLog = "Salt Execution, ParentMaster: %s, ReturnerKind: Master_Returner, Function: %s, StateFile: %s, Minion: %s, IsSuccess: %s" % (masterFQDN,Function,statefile,minion_name,isSuccess)
  messagevRLI= '{"messages":[{"text":"%s"}]}'  % (messageLog)
  f.write("PAYLOAD: %s\n" % (messagevRLI))
  # Send to Log Insight
  URL = "http://%s:%s/api/v1/messages/ingest/1" % (vRLI_SERVER, vRLI_PORT)
  headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
  messagevRLI_JSON = json.loads(messagevRLI)
  resp = requests.post(URL, verify=False, headers=headers, json=messagevRLI_JSON)
  if resp.status_code != 200:
    f.write("   => ERROR : Event NOT send to Log Insight\n")
  else:
    f.write("   => SUCCESS : Event sent to Log Insight\n")
  retour = "func_VRLI_CREATE_AND_SEND terminée"
  return retour


def func_GET_STATE_FILE(Function,data,argname):
  # Get State File if exist, N/A if not
  # argname is "fun_args" (common return)  or "arg" (tag 'complete' in SSC)
  # 'fun_args' or 'arg' is interesting only if the Function is 'state.apply'
  statefile = "N/A"
  if (Function == "state.apply"):
    argStr=""
    argnames=data[argname]      #  is a "list"
    for argname in argnames:    #  is a "str"
      argStr = "%s-%s" % (argStr,argname)         # concatenate all arg and add '-' between them
    statefile = argStr[1:]                        # remove first '-' if exist
    statefile = func_CLEAN_STATE_FILE(statefile)  # if secops we clean the state file
  return statefile


# state file are complex in secops so we clean
# if Vulnerability, statefile = vman.policy_assess_u-{'queue': True, 'pillar': {'policy_filename': '64766296-9b81-4558-bc25-c0f3712cd9d1_20'}
# if Compliance, statefile = locke.policy_assess_u-{'queue': True, 'pillar': {'policy_uuid': 'b98c8ceb-1d41-4f69-86f2-3422e19137f9', 'policy_filename': 'b9'}
def func_CLEAN_STATE_FILE(statefile_in):
  statefile_out = statefile_in
  if (statefile_in.find("vman.policy_assess") != -1):
    statefile_out = "vman.policy_assess"
  if (statefile_in.find("locke.policy_assess") != -1):
    statefile_out = "locke.policy_assess"
  return statefile_out



# les retours dont identifé par : tag : salt/job/20211203122055473529/ret/vra-001517.cpod-vrealize.az-fkd.cloud-garage.net

# les tags "salt/auth" sont a eviter pour limiter la log (certificats)
# n existe que dans SSC

# En cas de non retour du minion (par exemple pour absence):
  #Dans SSC:
    #tag : salt/job/20211206132826022514/complete
    #data de test.ping  : {'returned': [], 'missing': ['vra-006605'], 'fun': 'test.ping', 'arg': [], '_stamp': '2021-12-06T13:29:00.063231', '_master_path': ['saltstack_enterprise_installer']}
    #data de state.apply: {'returned': [], 'missing': ['vra-006605'], 'fun': 'state.apply', 'arg': ['alex_vim'], '_stamp': '2021-12-07T16:48:07.576132', '_master_path': ['saltstack_enterprise_installer']}

  #Dans Salt Open Source (master only):
    # RIEN n'est indiqué !!

#SECOPS:
# if Vulnerability, statefile = vman.policy_assess_u-{'queue': True, 'pillar': {'policy_filename': '64766296-9b81-4558-bc25-c0f3712cd9d1_20'}
# if Compliance, statefile = locke.policy_assess_u-{'queue': True, 'pillar': {'policy_uuid': 'b98c8ceb-1d41-4f69-86f2-3422e19137f9', 'policy_filename': 'b9'}
# we do not have in the events statistics about criticity nor standards => we cannot do it in returners
