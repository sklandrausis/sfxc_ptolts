#!/home/sfxc/correlation/sfxc/softs/python/bin/python3

# Copyright (c) 2007 Joint Institute for VLBI in Europe (Netherlands)
# All rights reserved.
#  
# Author(s): Nico Kruithof <Kruithof@JIVE.nl>, 2007
# 
# $Id: test_Channel_extractor.py 278 2007-07-04 07:27:05Z kruithof $


import sys, os, time, filecmp
import json as simplejson

def which (filename):
  if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
    p = os.defpath
  else:
    p = os.environ['PATH']

  pathlist = p.split (os.pathsep)

  for path in pathlist:
    f = os.path.join(path, filename)
    if os.access(f, os.X_OK):
      return f
  return None

def run_sfxc(swap, vex_file, ctrl_file):
  if not os.path.exists(vex_file):
    print ("Vex file does not exist")
    sys.exit(1)

  #construct the ctrl-filename from the vex file-name
  if ctrl_file == "":
    ctrl_file = os.path.splitext(os.path.basename(vex_file))[0]+".ctrl"

    # check if ctrl file exists, and create it if not
    if not os.path.exists(ctrl_file):
      status = os.system("vex2ccf "+vex_file+" "+ctrl_file)
      if (status != 0):
        print ("vex2ccf: returned error.")
        sys.exit(1);

      # allow the user to edit the ctrl file
      status = os.system("emacs "+vex_file+" "+ctrl_file)
      if (status != 0):
        print ("emacs: returned error.")
        sys.exit(1);

  # compute the number of processes needed from the control file
  try:
    ctrl = simplejson.load(open(ctrl_file, "r"))
  except StandardError as err:
    print ("Error loading control file : " + str(err))
    sys.exit(1);
  
 
  #run generate delay tables
  delay_directory = "."
  if "delay_directory" in ctrl:
    delay_directory = ctrl["delay_directory"]
    if delay_directory[:7] != "file://":
      print("delay_directory should start with file://")
    else:
      delay_directory = delay_directory[7:]
  
  print("Generates delay tables for each station")
  for st in ctrl["stations"]:
    cmd = "generate_delay_model "+vex_file+" "+st+" "+delay_directory + "/"+ctrl["exper_name"]+"_"+st+".del"
    print (cmd)
    status = os.system(cmd)
  
  number_of_processes = 3 + len(ctrl["channels"]) + len(ctrl["stations"])

  # run the software correlator
  if swap==1:
 
    cmd = "mpirun -v --debug-daemons --hostfile $1/$2/machines -np 8 --tmpdir $TMPDIR " + which ("sfxc") + " $1 $2  -parallel </dev/null "

  else:
      cmd = " time /home/sfxc/correlation/sfxc/softs/openmpi_1.10.6/bin/mpirun --prefix /home/sfxc/correlation/sfxc/softs/openmpi_1.10.6 -v --debug-daemons  -np 16 --hostfile machines -mca /  rankfile  " + "sfxc" + " "+ctrl_file+" "+vex_file+" | tee std_output.txt | grep -v PROGRESS" 


  print (cmd)
  status = os.system(cmd)
  if (status != 0):
    print ("sfxc: returned error.")
    sys.exit(1);

    # check if the output file is empty
    output_file = ctrl["output_file"][7:]
    if not os.path.exists(output_file):
      sys.exit(1)
    if os.stat(output_file)[6] == 0:
      sys.exit(1)

  html_directory = "."
  if "html_output" in ctrl:
    html_directory = ctrl["html_output"]
    if html_directory[:7] != "file://":
      print ("html_output should start with file://")
    else:
      html_directory = html_directory[7:]
  elif os.path.exists("../html"):
    html_directory = "../html";

  output_file = ctrl["output_file"]
  if output_file[:7] != "file://":
    print ("output_file should start with file://")
    sys.exit(1)
  else:
    output_file = output_file[7:]
    
  # run the html generator
  #cmd = "produce_html_plotpage "+vex_file+" "+output_file+" "+html_directory+" 2> /dev/null"
  #print (cmd)
  #status = os.system(cmd)

  #if (status != 0):
    #print ("produce_html_plotpage: returned error.")
    #sys.exit(1)


######### MAIN CODE
if __name__ == "__main__":
  if len(sys.argv) == 2:
    run_sfxc(0,sys.argv[1], "")
  elif len(sys.argv) == 3:
    run_sfxc(0,sys.argv[1], sys.argv[2])
  elif len(sys.argv) == 4:
    if sys.argv[1]=="-s":
      run_sfxc(1,sys.argv[2], sys.argv[3])
    else:
      print ("Usage", sys.argv[0], " [-s] <vex-file> [<ctrl-file>]")
      sys.exit(1)
  else:
    print ("Usage", sys.argv[0], " [-s] <vex-file> [<ctrl-file>]")
    sys.exit(1)

  sys.exit(0)
