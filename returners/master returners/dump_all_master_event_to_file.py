
#  MASTER RETURNER
#  v 0.1
#  Alexandre Hugla
#  12 Dec 2021
# dump_all_master_events_to_file.py


#import json

def event_return(events):                               # events is a "list"
  PythonLogfile = "/tmp/dump_events_master_returner.log"
 
  # Open local log file and log parameters
  f = open(PythonLogfile, "a")

  #Pour chaque evenement de la liste
  for event in events:                                  # event is a "dict"
    tag = event.get("tag", "")
    data = event.get("data", "")
    
    
    # On evite les tags automatiques et recurrents qui nous sont inutiles et qui sont seulement sur SSC
    #   tag : salt/raas_master/iteration  (ONLY on SSC)
    #   tag : salt/auth (ONLY on SSC)
    if (tag.find('salt/auth') != 0) and (tag.find('salt/raas_master/iteration') != 0):
      f.write("tag : %s\n" % (tag))
      #f.write("tag : %s\n" % (data))
    

  f.close()


