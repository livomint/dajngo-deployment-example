#/usr/bin/env python

#----------------------------------------------------------------------------------------
# Author: Jong Cheol Jeong (korjcjeong@yahoo.com, people.eecs.ku.edu/~jjeong)
# 	  Bioinformatics center, The University of Kansas
#----------------------------------------------------------------------------------------

# for MDAnalysis
import sys
from MDAnalysis import *
from MDAnalysis.analysis.align import *
import math
import numpy as np

# for server side jobs
import os
import string
import random
import subprocess

# import others
import pprint
import pickle
import re
from datetime import datetime

# for using sqlite3
import sqlite3
import stanalyzer

# for local functions and classes
from stanalyzer import *

#**********************************************************************
# *  This function analyzer the system box through all trajectories
#
#**********************************************************************

#///////////////////////////////////////////////////////////////////////////
# Get job information
# -- Use following codes to make your own function
#///////////////////////////////////////////////////////////////////////////
#frame_Unit = 0.005;

exe_file = sys.argv[0];
in_file  = sys.argv[1];
para_idx = int(sys.argv[2]);         # parameter index for multiple jobs in a same form

#out_file = sys.argv[2];

print '##### execution file: {} ######'.format(exe_file);
print 'input file: {}'.format(in_file);
#print 'output file: {}'.format(out_file);

#print 'Reading pickle...'
fid_in = open(in_file, 'rb');
dic = pickle.load(fid_in);
fid_in.close();

# variables in binary file
para_pkeys      = dic["para_pkeys"];        # gui_parameter primary keys obtained from job submitting
job_pkey        = dic["job_pkey"];          # gui_job primary keys obtained from job submitting
job_title       = dic["job_title"];         # gui_job title
prj_pkey        = dic["pkey"];              # gui_project primary key beloning to current job
prj_title       = dic["ptitle"];            # gui_project title beloning to current job
SESSION_HOME    = dic["session_home"];      # default session home directory: ~/dJango_home/media/user_id
OUTPUT_HOME     = dic["output_home"];       # output directory given by user
PBS_HOME        = dic["pbs_home"];          # directory where PBS script is written (i.e. for using cluster)
ANALYZER_HOME   = dic["analyzer_home"];     # directory where all analyzers are located (i.e. the location of this file)
MEDIA_HOME      = dic["media_home"];        # media directory ~/dJango_home/media
DB_FILE         = dic["dbName"];            # database file name and full location 
base_path       = dic["base_path"];         # base location of input files
path_output     = dic["path_output"];       # the location of output directory
path_python     = dic["path_python"];       # python path to run analyzers
structure_file  = dic["structure_file"];    # full path of structure file (i.e. PDB, PSF, etc)
pdb_file        = dic["pdb_file"];          # full path of PDB file (i.e. PDB)
pbs             = dic["pbs"];               # PBS script for using cluster machine
num_frame	= dic["num_frame"];         # number of frames in the first trajectory file
num_atoms	= dic["num_atoms"];         # number of atomes in the system
num_files	= dic["num_files"];         # number of files chosen
num_ps	        = str(dic["num_ps"]);       # simulation time ps/frame

#print "*********** NUM_PS = "
#print num_ps;

trajectoryFile = [];                        # the list of trajectory files
for i in range(len(dic["trajectory"])):
    trajectoryFile.append(dic["trajectory"][i]);



# Identifying my parameters
#print "******* Show me the Dictionary ***********"
#print dic

myPara = get_myfunction(exe_file, dic);
fName = myPara[0];      # name of function except '.py'
pInfo = myPara[1];      # parameter information pInfo[0] = "number of parameters"
paras = myPara[2];      # actual parameters paras[0] contains 'the number of parameters'
para_pkey = myPara[3];  # primary key of parameter table contating this analzyer function.
rmodule   = "{0}{1}".format(exe_file[:len(exe_file)-3], para_idx);  # running module name (e.g. box0)
outFile   = paras[2][para_idx];			# pInfo[2] : output file name (list)

#print "================= Okay Show me my parameters in box.py ===================="
#print fName
#print pInfo
#print paras
#print para_pkey
#print "================= DONE ===================="
# display all local variables
#pprint.pprint(dic)

# Updating DB: running Job
# 0 - submit job
# 1 - Running job
# 2 - Error occurred
# 3 - Completed
#print "para_pkey: "
#print para_pkey

stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
conn = sqlite3.connect(DB_FILE);
c    = conn.cursor();
for i in range(len(para_pkey)):
    query = """UPDATE gui_parameter SET status = "RUNNING" WHERE id = {}""".format(para_pkey[i]);
    c.execute(query);
    conn.commit();
conn.close();

# Update values into gui_outputs
conn = sqlite3.connect(DB_FILE);
c    = conn.cursor();
# find gui_outputs related to current processing
#query = """SELECT id FROM gui_outputs WHERE job_id = {0} and name = "{1}" """.format(job_pkey[0], rmodule);
jobName = "{}_{}".format(rmodule, outFile);
query = """SELECT id FROM gui_outputs WHERE job_id = {0} and name = "{1}" """.format(job_pkey[0], jobName);
c.execute(query);
row = c.fetchone();
pk_output = row[0];     # primary key for gui_outputs
try:    
    query = """UPDATE gui_outputs SET status = "Running" WHERE id = {0}""".format(pk_output);
    c.execute(query);
    conn.commit();
    conn.close();
except:
    conn = sqlite3.connect(DB_FILE);
    c    = conn.cursor();
    query = """UPDATE gui_outputs SET status = "Failed" WHERE id = {0}""".format(pk_output);
    c.execute(query);
    conn.commit();
    conn.close();
    

#///////////////////////////////////////////////////////
# print gui_job and gui_parameter table
#///////////////////////////////////////////////////////
#stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
#conn = sqlite3.connect(DB_FILE);
#c    = conn.cursor();

#print "========= gui_job ==========="
#query = "SELECT id, name, proj_id, anaz, status, output, stime, etime FROM gui_job";
#c.execute(query);
#job = c.fetchall();
#print "ID\tTITLE\tPROJ_ID\tANALYZER\tSTATUS\tOUTPUT\tSTART\tEND";
#for item in job:
#    print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]);

#print "========= gui_parameter ==========="
#query = "SELECT id, job_id, anaz, para, val, status FROM gui_parameter WHERE job_id = {}".format(job_pkey[0]);
#print query
#c.execute(query);
#PR = c.fetchall();
#print "ID\tJOB_ID\tANALYZER\tPARAMETER\tVALUE\tSTATUS";
#for item in PR:
#    print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}".format(item[0], item[1], item[2], item[3], item[4], item[5]);
#conn.close();

out_dir = "{}{}".format(OUTPUT_HOME, fName[1]);
# Create output directory
if not (os.path.isdir(out_dir)):
    #print "Creating directory into {}".format(out_dir)
    os.mkdir(out_dir);


# -------- Writing input file for web-link
#print "list of PARAMETERS: "
inFile = '{0}/input{1}.dat'.format(out_dir, para_idx);
fid_in = open(inFile, 'w');
strPara = "Name of Function: {}\n".format(exe_file);
strPara = strPara + "System information \n";
strPara = strPara + "\t- First trajectory contains {0} frames ({1} ps/frame)\n".format(num_frame, num_ps);
strPara = strPara + "\t- There are {0} trajectory file(s) and {1} atoms\n".format(num_files, num_atoms);
strPara = strPara + "Total {} parameters \n".format(int(paras[0][0])+3);
strPara = strPara + "\t- Base path: {}\n".format(base_path);
strPara = strPara + "\t- Structure file: {}\n".format(structure_file);
strPara = strPara + "\t- Trajectory files: \n"
tmp = "";
for trj in trajectoryFile:
    tmp = tmp + "\t\t{}\n".format(trj);
    
strPara = strPara + tmp;

strPara = strPara + "\t- Job specific parameters: \n"
strPara = strPara + "\t\t{0}:{1}\n".format(pInfo[0], paras[0][0]);
tmp = "";
for i in range(len(pInfo)):
    if i > 0:
        tmp = tmp + "\t\t{}:{}\n".format(pInfo[i], paras[i][para_idx]);
strPara = strPara + tmp;
strPara = strPara + "\nPBS: \n{}\n".format(pbs);
fid_in.write(strPara);
fid_in.close();

#print "---- strPara----"
#print strPara

#---------------------< assigned global parameters >---------------------------------
# para_idx = sys.argv[2];                     # parameter index for multiple jobs in a same form
# para_pkeys      = dic["para_pkeys"];        # gui_parameter primary keys obtained from job submitting
# job_pkey        = dic["job_pkey"];          # gui_job primary keys obtained from job submitting
# job_title       = dic["job_title"];         # gui_job title
# prj_pkey        = dic["pkey"];              # gui_project primary key beloning to current job
# prj_title       = dic["ptitle"];            # gui_project title beloning to current job
# SESSION_HOME    = dic["session_home"];      # default session home directory: ~/dJango_home/media/user_id
# OUTPUT_HOME     = dic["output_home"];       # output directory given by user
# PBS_HOME        = dic["pbs_home"];          # directory where PBS script is written (i.e. for using cluster)
# ANALYZER_HOME   = dic["analyzer_home"];     # directory where all analyzers are located (i.e. the location of this file)
# MEDIA_HOME      = dic["media_home"];        # media directory ~/dJango_home/media
# DB_FILE         = dic["dbName"];            # database file name and full location 
# base_path       = dic["base_path"];         # base location of input files
# path_output     = dic["path_output"];       # the location of output directory
# path_python     = dic["path_python"];       # python path to run analyzers
# structure_file  = dic["structure_file"];    # full path of structure file (i.e. PDB, PSF, etc)
# pbs             = dic["pbs"];               # PBS script for using cluster machine
# num_frame	  = dic["num_frame"];         # number of frames in the first trajectory file
# num_atoms	  = dic["num_atoms"];         # number of atomes in the system
# num_files	  = dic["num_files"];         # number of files chosen
# num_ps	  = str(dic["num_ps"]);       # simulation time ps/frame
# trajectoryFile = [];                        # the list of trajectory files

#---------------------< assigned module specific parameters >---------------------------------
num_paras = paras[0][0];			# pInfo[0] : number of parameters
frmInt	  = paras[1][para_idx];		        # pInfo[1] : Frame interval (list)
frmInt    = int(frmInt);
out_file  = paras[2][para_idx];			# pInfo[2] : output file name (list)

#///////////////////////////////////////////////////////////////////////////
# Running actual job
#///////////////////////////////////////////////////////////////////////////
try:
    outFile = '{0}/{1}'.format(out_dir, out_file);
    fid_out = open(outFile, 'w')
    fieldInfo = "# ps/frame\tX-axis\tY-axis\tZ-axis\tAlpha\tBeta\tGamma\tVolumn\n";
    fid_out.write(fieldInfo)
    psf = '{0}{1}'.format(base_path, structure_file);
    cnt = 0;
    timeStamp = [];         # time stamp for trajectory
    sSize = [];
    for idx in range(len(trajectoryFile)):
        # reading trajectory
        dcd = '{0}{1}'.format(base_path, trajectoryFile[idx]);
        u = Universe(psf, dcd);
        
        for ts in u.trajectory:
            cnt = cnt + 1;
            #print "ts.frame = {}".format(cnt);
            if (cnt % frmInt) == 0:
                # get the class MDAnalysis.coordinates.base.Timestep
                # from MDAnalysis.coordinates.DCD.DCDReader
                tmp_time = float(cnt) * float(num_ps) - float(num_ps);
                timeStamp.append(tmp_time);
                outStr = '{0}'.format(tmp_time);
                tmp = [];
                for j in ts.dimensions:
                   outStr = outStr + '\t{0}'.format(j)
                   tmp.append(j);
                outStr = outStr + '\t{0}\n'.format(ts.volume)
                tmp.append(ts.volume);
                sSize.append(tmp);
                #print "Last Line--->"
                #print outStr
                fid_out.write(outStr)

    fid_out.close()

    # -------- Update output table gui_outputs
    # Writing Gnuplot script
    outScr = '{0}/gplot{1}.p'.format(out_dir, para_idx);
    outImg  = '{0}{1}.png'.format(exe_file[:len(exe_file)-3], para_idx);
    imgPath = "{0}/{1}".format(out_dir, outImg);
    fid_out = open(outScr, 'w');
    gScript = """set terminal png enhanced \n""";
    gScript = gScript + "set output '{0}'\n".format(imgPath);
    gScript = gScript + "set multiplot layout 3,1 rowsfirst title 'System size'\n";
    
    npSize = np.array(sSize);
    max_x = npSize[:,0].max();
    min_x = npSize[:,0].min();
    
    max_y = npSize[:,1].max();
    min_y = npSize[:,1].min();
    
    max_z = npSize[:,2].max();
    min_z = npSize[:,2].min();
    
    # For X axis
    num_x_tics = 3.0;
    intx = (max_x - min_x) / num_x_tics;
    # if graph is brocken then remove margins 
    #gScript = gScript + "set tmargin at screen 0.93; set bmargin at screen 0.68\n";
    #gScript = gScript + "set lmargin at screen 0.20; set rmargin at screen 0.85\n";
    gScript = gScript + "set xtics offset 0,0.5; unset xlabel\n";
    if intx >= 0.0001:
        gScript = gScript + """set ytics {0:10.4f},{1:10.4f},{2:10.4f}; unset ylabel\n""".format(min_x, intx, max_x);
    gScript = gScript + "unset ylabel\n";
    #gScript = gScript + """set label 1 'X-axis' at graph 0.01, 0.95 font ',8' \n""";
    gScript = gScript + """plot "{0}" using ($1*0.001):2 title "X-axis" with lines lw 3\n""".format(outFile);

    # For Y axis
    num_y_tics = 3.0;
    inty = (max_y - min_y) / num_y_tics;
    # if graph is brocken then remove margins 
    #gScript = gScript + "set tmargin at screen 0.63; set bmargin at screen 0.38\n";
    #gScript = gScript + "set lmargin at screen 0.20; set rmargin at screen 0.85\n";
    gScript = gScript + "set xtics offset 0,0.5; unset xlabel\n";
    if inty >= 0.0001:
        gScript = gScript + """set ytics {0:10.4f},{1:10.4f},{2:10.4f};\n""".format(min_y, inty, max_y);
    gScript = gScript + "set ylabel 'Size (Angstrom)'\n";
    #gScript = gScript + """set label 1 'Y-axis' at graph 0.01, 0.95 font ',8' \n""";
    gScript = gScript + """plot "{0}" using ($1*0.001):3 title "Y-axis" with lines lw 3\n""".format(outFile);

    # For Z axis
    num_z_tics = 3.0;
    intz = (max_z - min_z) / num_z_tics;
    # if graph is brocken then remove margins 
    #gScript = gScript + "set tmargin at screen 0.33; set bmargin at screen 0.08\n";
    #gScript = gScript + "set lmargin at screen 0.20; set rmargin at screen 0.85\n";
    gScript = gScript + "set xtics offset 0,0.5; set xlabel 'Time (ns)' offset 0,1\n";
    if intz >= 0.0001:
        gScript = gScript + """set ytics {0:10.4f},{1:10.4f},{2:10.4f}; unset ylabel\n""".format(min_z, intz, max_z);
    gScript = gScript + "unset ylabel\n";
    #gScript = gScript + """set label 1 'Z-axis' at graph 0.01, 0.95 font ',8' \n""";
    gScript = gScript + """plot "{0}" using ($1*0.001):4 title "Z-axis" with lines lw 3\n""".format(outFile);
   
    gScript = gScript + "unset multiplot\n";
    gScript = gScript + "set output\n";
    fid_out.write(gScript);
    fid_out.close()

    # Drawing graph with gnuplot
    subprocess.call(["gnuplot", outScr]);
    
    # gzip all reaults
    outZip = "{0}project_{1}_{2}{3}.tar.gz".format(OUTPUT_HOME, prj_pkey, fName[1], para_idx);
    subprocess.call(["tar", "czf", outZip, out_dir]);
    
    # Update values into gui_outputs
    conn = sqlite3.connect(DB_FILE);
    c    = conn.cursor();
    query = """UPDATE gui_outputs SET status = "Complete", img="{0}", txt="{1}", gzip="{2}" WHERE id = {3}""".format(imgPath, outFile, outZip, pk_output);
    c.execute(query);
    conn.commit();
    conn.close();
    #print query
    
    # update gui_parameter & gui_job table when job completed
    etime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
    conn = sqlite3.connect(DB_FILE);
    c    = conn.cursor();
    for i in range(len(para_pkey)):
        query = """UPDATE gui_parameter SET status = "COMPLETE" WHERE id = {0}""".format(para_pkey[i]);
        #print query
        c.execute(query);
        conn.commit();
    
    # update gui_job if every status in gui_parameter are COMPLETE
    query = """SELECT DISTINCT(status) FROM gui_parameter WHERE job_id = {0}""".format(job_pkey[0]);
    c.execute(query);
    ST = c.fetchall();
    #print query;
    #print "number status = {}".format(len(ST));
    #for item in ST:
    #    print "{0}".format(item[0]);
    
    if (len(ST) == 1) and (ST[0][0] == "COMPLETE"):
        etime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
        query = """UPDATE gui_job SET status = "COMPLETE", etime = "{0}" WHERE id = {1}""".format(etime, job_pkey[0]);
        c.execute(query);
        conn.commit();
        
        # making tar file
        outZip = "{0}project_{1}.tar.gz".format(OUTPUT_HOME, prj_pkey[0]);
        subprocess.call(["tar", "czf", outZip, OUTPUT_HOME]);

        # Inserting compressed tar file for all submitted jobs
        #final_title = "[** All JOBs **] {0}".format(job_title);
        #query = """INSERT INTO gui_outputs (job_id, name, img, txt, gzip) VALUES ({0}, "{1}", "{2}", "{3}", "{4}")""".format(job_pkey[0], final_title, imgPath, outFile, outZip);
        #c.execute(query);
        #conn.commit();
        #print query
    conn.close();


#///////////////////////////////////////////////////////////////////////////
# Finalizing  job
# -- Use following codes to make your own function
#///////////////////////////////////////////////////////////////////////////
except:
    # update gui_parameter & gui_job table when job failed 
    etime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
    conn = sqlite3.connect(DB_FILE);
    c    = conn.cursor();
    for i in range(len(para_pkey)):
        query = """UPDATE gui_parameter SET status = "FAILED" WHERE id = {0}""".format(para_pkey[i]);
        c.execute(query);
        conn.commit();
    query = """UPDATE gui_job SET status = "INTERRUPTED" WHERE id = {0}""".format(job_pkey[0]);
    c.execute(query);
    conn.commit();
    
    query = """UPDATE gui_outputs SET status = "Failed" WHERE id = {0}""".format(pk_output);
    c.execute(query);
    conn.commit();
   
    conn.close();




#///////////////////////////////////////////////////////
# print gui_job and gui_parameter table
#///////////////////////////////////////////////////////
stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
conn = sqlite3.connect(DB_FILE);
c    = conn.cursor();

#print "========= gui_job ==========="
query = "SELECT id, name, proj_id, anaz, status, output, stime, etime FROM gui_job";
#print "ID\tTITLE\tPROJ_ID\tANALYZER\tSTATUS\tOUTPUT\tSTART\tEND";
c.execute(query);
job = c.fetchall();
#print "Final idx= {}".format(job[len(job)-1][0]);
#for item in job:
#    print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]);

#print "========= gui_parameter ==========="
query = "SELECT id, job_id, anaz, para, val, status FROM gui_parameter";
#print "ID\tJOB_ID\tANALYZER\tPARAMETER\tVALUE\tSTATUS";
c.execute(query);
PR = c.fetchall();
#print "Final idx= {}".format(PR[len(PR)-1][0]);
#for item in PR:
#    print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}".format(item[0], item[1], item[2], item[3], item[4], item[5]);

conn.close();
