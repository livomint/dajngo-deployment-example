#/usr/bin/env python

#----------------------------------------------------------------------------------------
# Author: Jong Cheol Jeong (korjcjeong@yahoo.com, people.eecs.ku.edu/~jjeong)
# 	  Bioinformatics center, The University of Kansas
#----------------------------------------------------------------------------------------

# for web-interfacer
from django.shortcuts		import render_to_response, get_object_or_404, render
from django.template		import Context, loader, RequestContext
from django.http		import HttpResponseRedirect, HttpResponse, Http404
from django.utils.encoding	import smart_str, smart_unicode
#from django.utils               import simplejson
#from django.core.urlresolvers	import reverse

# for MDAnalysis
import sys
from MDAnalysis import *
from MDAnalysis import core
from MDAnalysis.analysis.align import *
import math
import numpy as np

#from MDAnalysis.tests.datafiles import PSF, DCD, PDB, XTC
#import thread
#import Queue
#from MDAnalysis.tests.datafiles import PSF, DCD, PDB_small, PDB, XTC
#import time
#import threading
#from datetime import datetime
# dJango test
#from django import forms
#from django.core.mail import send_mail


# for server side jobs
import os
import stat
import string
import random
import math
import shutil
from random import randint
from os import path
import subprocess as sub

# for using from object
# https://docs.djangoproject.com/en/dev/topics/forms/?from=olddocs#filefield
#from django import forms
#from django.core.mail import send_mail
#from django.contrib.admin.widgets import FilteredSelectMultiple  
#from django.forms import ModelForm

# importing models
import hashlib
from django.db import connection, transaction
from gui.models import User, Project, Job, Parameter
# --- data modification
#cursor.execute("INSERT INTO table_name (column1, column2, column3) VALUES (value1, value2, value3)")
#cursor.execute("DELETE FROM table_name WHERE column1='xxx'")
#cursor.execute("UPDATE table_name SET column1='update it' WHERE column1='xxx' AND column='yyy'")
#transaction.commit_unless_managed()
# --- Data retrieval
#cursor.execute("SELECT column1, column2 FROM table_name WHERE column3 = %s", zzz)
#row = cursor.fetchone()

#for using Ajax: Json
import json
from django.utils import simplejson
import pickle

# for using sqlite3
import sqlite3

# import others
import re
from datetime import datetime

# download
import os, mimetypes
from django.core.servers.basehttp import FileWrapper

#********************************************
# Define global variables
#********************************************
#
#dbName = settings.DATABASES["default"]["NAME"];
SESSION_TIME_OUT = 9000;
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__));
dbName = "{}/stanalyzer.db".format(PROJECT_ROOT[0:len(PROJECT_ROOT)-4]);
MEDIA_HOME = "{}/media".format(PROJECT_ROOT[0:len(PROJECT_ROOT)-4]);
ANALYZER_HOME = "{}/static/analyzers".format(PROJECT_ROOT[0:len(PROJECT_ROOT)-4]);
#********************************************
# Parsing wrapped lists
# This function is used for parsing parameters and thier information
#********************************************
#------------------------------------
#--- parsing double array
#------------------------------------
def parseWrapList1(strList):
    print "+++ parseWrapList1 +++";
    num_list = len(strList);
    newList = [];
    #print num_list;
    for i in range(num_list):
        #print "Iteration[{}]".format(i);
        strElm = strList[i];
        #print strElm
        lstElm = strElm.split(',');      # split based on comma
        #print lstElm
	newList.append(lstElm);
    return newList;

#------------------------------------
#--- parsing triple array
#------------------------------------
def parseWrapList2(strList):
    print "+++ parseWrapList2 +++";
    num_list = len(strList);
    #print "num_list={}".format(num_list)
    newList = [];
    #print num_list;
    for i in range(num_list):
        #print "Iteration[{}]".format(i);
        strElm = strList[i];
        #print "strElm={}".format(strElm);
	
        lstElm = strElm.split(',');      # split based on comma
        #print "lstElm={}".format(lstElm);
	
	num_para = int(lstElm[0]);
	#print "NUM_PARA={}".format(num_para);
	
	num_Elm  = (len(lstElm) - 1) / num_para;
	#print "NUM_ELE={}".format(num_Elm);
	
	innerList = [];
	innerList.append([num_para]);
	tmp = [];
	for j in range(len(lstElm)):
	    #print 'J='.format(j);
	    if (j > 0):
		tmp.append(lstElm[j]);
		#print "=== ARRAY ==="
		#print tmp

		if (j % num_Elm) == 0:
		    #print "=== ARRAY ==="
		    #print tmp
		    innerList.append(tmp);
		    tmp = [];
	newList.append(innerList);
    return newList;
        

#********************************************
# make n-digit random number 
#********************************************
def rand_N_digits(n):
    print "+++ rand_N_digits +++"
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

#********************************************
# make random string with n letters
#********************************************
def rand_N_letters(n, chars=string.letters + string.digits):
    print "+++ rand_N_letters +++"
    newStr = ''.join(random.choice(chars) for x in range(n));
    return newStr


#********************************************
# Serverside jobs including
# 1) read directories
#********************************************
class serverside:
    def __init__(self, *args):
	print "*** serverside ***"
        if len(args) > 0:
            self.path_trj = str(args[0]);
    # default trajectory file

    def showdir(self, *args):
        try:
            if len(args) > 0:
                #assert os.path.isdir(str(args[0]))
                return os.listdir(str(args[0]));
            else:
                return os.listdir(self.path_trj)
        except:
            return ['n/a']

    def isvalidate(self, *args):
        status = [];
        try:
            tmp = os.path.isdir(self.path_trj);
            if tmp:
                status = ['dir'];
            tmp = os.path.isfile(self.path_trj);
            if tmp:
                status = ['file'];
        except:
            status =[];
        return status;
    
    def mkdir(self, *args):
	status = [];
        try:
            if not os.path.exists(self.path_trj):
		os.makedirs(self.path_trj);
		status = True;
        except:
            status =False;
        return status;
	
    
    def permission_write(self):
        st = os.stat(self.path_trj);
        owner = bool(st.st_mode & stat.S_IWUSR);
        group = bool(st.st_mode & stat.S_IWGRP);
        other = bool(st.st_mode & stat.S_IWOTH);
        return [owner, group, other]

    def permission_exec(self):
        st = os.stat(self.path_trj);
        owner = bool(st.st_mode & stat.S_IXUSR);
        group = bool(st.st_mode & stat.S_IXGRP);
        other = bool(st.st_mode & stat.S_IXOTH);
        return [owner, group, other]

def createChoices(listObj):
    print "+++ createChoices +++"
    # get the list of files
    form_list = [];
    for pos, question in enumerate(listObj):
	tmp = [pos, question]
	form_list.append(tmp)
    return form_list

def eval_path(path):
    print "+++ eval_path +++"
    if path[0] != '/':
        path = '/{0}'.format(path);
    if (path[len(path)-1] != '/'):
        path = "{0}/".format(path);
    return path
        
# calculating angle between p1 and p3 with apex at 1
# p1, p2, and p3 should be numpy array
class geomatric:
    def angle(self, p1, p2, p3): 
	assert (p1.size == p2.size) and (p1.size == p3.size) and (p2.size == p3.size)
	normp1 = math.sqrt(np.sum(p1.__pow__(2)));
	normp3 = math.sqrt(np.sum(p3.__pow__(2)));
	theta  = math.acos(np.sum(p1 * p3)/(normp1 * normp3)) * 180 / math.pi;
	if theta > 90.:
	    theta = 180. - theta
	elif theta < -90.:
	    theta = -1 * (180 + theta)
	return theta;

class simulation:
    # test inputs
    # psf = '/home2/jcjeong/project/stanalyzer1/stanalyzer/trajectory/step5_assembly.psf';
    # dcd = '/home2/jcjeong/project/stanalyzer1/stanalyzer/trajectory/step6_1.dcd';
    
    def __init__(self, psf, trj):
	print "*** simulation ***"
	self.u = Universe(psf, trj);
	
	# total number of frames at each trajectory
	#print "num_frm: "
	self.num_frm = len(self.u.trajectory);
	# time unit per frame
	#print self.num_frm;
	
	#print "num_ps: "
	self.num_ps = np.float16(self.u.trajectory.dt);		# use float16 to fit CHARMM code
	#print self.num_ps;
	
	# total number of atoms
	#print "num_atom"
	self.num_atom  = len(self.u.atoms);
	#print self.num_atom;
	
	# list of segments
	#print "SegList"
	self.CsegList = self.u.segments;
	self.segList = [];
	for i in range(len(self.CsegList)):
	    self.segList.append(self.CsegList[i].name);
	#print self.segList;
	
    def get_segname(self, seg_id):
	return self.segList[int(seg_id)]
    
    def get_seg_residues(self, seg_name):
	selQry = 'segid {0}'.format(seg_name);
	Seg = self.u.selectAtoms(selQry);
	return Seg.residues
	

#********************************************
# Delete files and directories
#********************************************
def delDir(dir_path):
    print "+++ delDir +++"
    if os.path.isdir(dir_path):
	for f in os.listdir(dir_path):
	    file_path = os.path.join(dir_path, f)
	    try:
		if os.path.isfile(file_path):
		    os.remove(file_path);
		    #print "remove {}".format(file_path);
		else:
		    shutil.rmtree(file_path);
	    except Exception, e:
		print e
	shutil.rmtree(dir_path);
	#print "remove {}".format(dir_path);

def delQue(qid):
    print "+++ delQue +++";
    qdel = "qdel {0}".format(qid);
    print qdel;
    os.system(qdel);


#********************************************
# DB retrieval
#********************************************
class getDB:
    row = [];
    def __init__(self, dbName, user):
	print "*** getDB ***"
    	self.dbName = dbName;
        self.user   = user;
    # default trajectory file
    def get_pbs(self, *args):
        conn = sqlite3.connect(self.dbName);
        c = conn.cursor();
        #print "command is {}".format(args[0]);
        if (args[0] == 'get_recent_pbs'):
            query = "SELECT pbs FROM gui_project WHERE user_id='{0}' ORDER BY date DESC limit 1".format(self.user);
            c.execute(query);
            row = c.fetchall();
            pbs = [];
            for i in row:
                pbs.append(i);
            conn.close();
            return pbs

def getUsrLevel (dbName, user_id):
    print "+++ getUsrLevel +++"
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    query = "SELECT level FROM gui_user WHERE uid='{0}'".format(user_id);
    c.execute(query);
    row = c.fetchone();
    level = row[0];
    conn.close();
    return level

def delOutputs (IDs, dbName, delFlg):
    print "+++ delOutputs +++"
    # delete gui_job
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    if isinstance(IDs, list):
	for output_id in IDs:
	    query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE id={0}".format(output_id);
	    c.execute(query);
	    row = c.fetchall();
	    if delFlg == 'true':
		for f in row:
		    # delete queue
		    delQue(f[0])
		    if '/' in f[1]:
			path_img = f[1].split('/');
			path_dir = '/'.join(path_img[:len(path_img)-1])
			delDir(path_dir);
	    else:
		for f in row:
		    delQue(f[0])
		

	    query = "DELETE FROM gui_outputs WHERE id={0}".format(output_id);
	    c.execute(query);
	    conn.commit();
	    #print query;
    else:
	if delFlg == 'true':
	    query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE id={0}".format(IDs);
	    c.execute(query);
	    row = c.fetchall();
	    for f in row:
		delQue(f[0]);
		if '/' in f[1]:
		    path_img = f[1].split('/');
		    path_dir = '/'.join(path_img[:len(path_img)-1])
		    delDir(path_dir);
	else:
	    query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE id={0}".format(IDs);
	    c.execute(query);
	    row = c.fetchall();
	    for f in row:
		delQue(f[0]);

	query = "DELETE FROM gui_outputs WHERE id={0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query;
    conn.close();

def delOutputs_from_jobID (IDs, dbName, delFlg):
    print "+++ delOutputs_from_jobID +++"
    # delete gui_job
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    if isinstance(IDs, list):
	print "--- this runs with LIST"
	for job_id in IDs:
	    if delFlg == 'true':
		query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE job_id={0}".format(job_id);
		c.execute(query);
		row = c.fetchall();
		#print "====== Split word ===="
		for f in row:
		    delQue(f[0])
		    if '/' in f[1]:
			path_img = f[1].split('/');
			path_dir = '/'.join(path_img[:len(path_img)-1])
			delDir(path_dir);
	    else:
		query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE job_id={0}".format(job_id);
		c.execute(query);
		row = c.fetchall();
		for f in row:
		    delQue(f[0])
		
	    query = "DELETE FROM gui_outputs WHERE job_id={0}".format(job_id);
	    c.execute(query);
	    conn.commit();
	    #print query;
    else:
	print "--- this runs with SCHOLAR {0}".format(IDs);
	#print delFlg
	#print "Type is {0}".format(type(delFlg));
	if delFlg == 'true':
	    query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE job_id={0}".format(IDs);
	    #print query
	    c.execute(query);
	    row = c.fetchall();
	    #print row
	    for f in row:
		delQue(f[0])
		print "====== Split word ===="
		if '/' in f[1]:
		    path_img = f[1].split('/');
		    path_dir = '/'.join(path_img[:len(path_img)-1])
		    #print path_dir
		    delDir(path_dir);
		else:
		    print "With no path {0}".format(f[1]);
	else:
	    query = "SELECT qid, img, txt, gzip FROM gui_outputs WHERE job_id={0}".format(IDs);
	    c.execute(query);
	    row = c.fetchall();
	    for f in row:
		delQue(f[0])
	    
	query = "DELETE FROM gui_outputs WHERE job_id={0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query;
    conn.close();

def delJobs (IDs, dbName, delFlg):
    print "+++ delJobs +++"
    # delete gui_job
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    if isinstance(IDs, list):
	for job_id in IDs:
	    #delete gui_parameter, gui_outputs
	    query = "DELETE FROM gui_parameter WHERE job_id={0}".format(job_id);
	    #print query
	    delOutputs_from_jobID(job_id, dbName, delFlg);
	    if delFlg == 'true':
		#deleting job output directory
		query = "SELECT output FROM gui_job WHERE id={0}".format(job_id);
		c.execute(query);
		row = c.fetchall();
		for f in row:
		    if '/' in f[0]:
			delDir(f[0]);
	    
	    query = "DELETE FROM gui_job WHERE id={0}".format(job_id);
	    c.execute(query);
	    conn.commit();
	    #print query
    else:
	#delete gui_parameter, gui_outputs
	query = "DELETE FROM gui_parameter WHERE job_id={0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
	delOutputs_from_jobID(IDs, dbName, delFlg);
	if delFlg == 'true':
	    query = "SELECT output FROM gui_job WHERE id={0}".format(IDs);
	    c.execute(query);
	    row = c.fetchall();
	    for f in row:
		if '/' in f[0]:
		    delDir(f[0]);
	query = "DELETE FROM gui_job WHERE id={0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
    
    conn.close();
    
def delJobs_from_prjID (IDs, dbName, delFlg):
    print "+++ delJobs_from_prjID +++"
    # delete gui_job
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    if isinstance(IDs, list):
	for proj_id in IDs:
	    query = "SELECT id FROM gui_job WHERE proj_id = {0}".format(proj_id);
	    c.execute(query);
	    row = c.fetchall();
	    for item in row:
		job_id = item[0];
		#delete gui_parameter, gui_outputs
		query = "DELETE FROM gui_parameter WHERE job_id={0}".format(job_id);
		c.execute(query);
		conn.commit();
		#print query
		delOutputs_from_jobID(job_id, dbName, delFlg);
		if delFlg == 'true':
		    query = "SELECT output FROM gui_job WHERE id={0}".format(job_id);
		    #print query
		    c.execute(query);
		    row2 = c.fetchall();
		    #print "Print Row2"
		    #print row2
		    for f in row2:
			if '/' in f[0]:
			    delDir(f[0]);

	    # delte gui_job corresponding to proj_id
	    query = "DELETE FROM gui_job WHERE proj_id={0}".format(proj_id);
	    c.execute(query);
	    conn.commit();
	    #print query
    else:
	query = "SELECT id FROM gui_job WHERE proj_id = {0}".format(IDs);
	c.execute(query);
	row = c.fetchall();
	for item in row:
	    job_id = item[0];
	    #delete gui_parameter, gui_outputs
	    query = "DELETE FROM gui_parameter WHERE job_id={0}".format(job_id);
	    c.execute(query);
	    conn.commit();
	    #print query
	    delOutputs_from_jobID(job_id, dbName, delFlg);
	if delFlg == 'true':
	    query = "SELECT output FROM gui_job WHERE id={0}".format(IDs);
	    c.execute(query);
	    row2 = c.fetchall();
	    for f in row2:
		if '/' in f[0]:
		    delDir(f[0]);
	# delte gui_job corresponding to proj_id
	query = "DELETE FROM gui_job WHERE proj_id={0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
    conn.close();

def delProjects (IDs, dbName, delFlg):
    print "+++ delProjects +++"
    delJobs_from_prjID(IDs, dbName, delFlg);
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    if isinstance(IDs, list):
	# delete gui_path_input, gui_path_output, gui_path_python
	for proj_id in IDs:
	    query = "DELETE FROM gui_path_input WHERE proj_id = {0}".format(proj_id);
	    c.execute(query);
	    conn.commit();
	    #print query
	    query = "DELETE FROM gui_path_output WHERE proj_id = {0}".format(proj_id);
	    c.execute(query);
	    conn.commit();
	    #print query
	    query = "DELETE FROM gui_path_python WHERE proj_id = {0}".format(proj_id);
	    c.execute(query);
	    conn.commit();
	    #print query
	    query = "DELETE FROM gui_project WHERE id = {0}".format(proj_id);
	    c.execute(query);
	    conn.commit();
	    #print query
    else:
	query = "DELETE FROM gui_path_input WHERE proj_id = {0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
	query = "DELETE FROM gui_path_output WHERE proj_id = {0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
	query = "DELETE FROM gui_path_python WHERE proj_id = {0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
	query = "DELETE FROM gui_project WHERE id = {0}".format(IDs);
	c.execute(query);
	conn.commit();
	#print query
    conn.close();


#********************************************************
# *  File sort containing both string and numbers
#********************************************************
def getSortedList(myList, rev):
    print "+++ getSortedList +++"
    #i[0]: use key index, x[1]: use file name for comparision
    idx = [i[0] for i in sorted(enumerate(myList), key=lambda x:x[1], reverse=rev)]; 
    #print "** func: idx"
    #print idx
    sList = sorted(myList, reverse=rev);
    #print "** func: sList"
    #print sList
    return [idx, sList];


def extStrings(myList):
    print "+++ extStrings +++"
    # find every number and find maximum number in a certain range
    fixDigit = 7;
    newList = [];
    for strLine in myList:
	subStr = '';
	subInt = '';
	num_cnt = 0;
	for i in strLine:
	    #print "{0}={1}".format(i, ord(i));
	    if (ord(i) > 47) and (ord(i) < 58):
		num_cnt = num_cnt + 1;
		subInt = "{0}{1}".format(subInt, i);
	    else:
		if num_cnt > 0:
		    num_zero = fixDigit - num_cnt;
		    newNum = '0' * num_zero;
		    newNum = "{0}{1}".format(newNum, subInt);
		    subStr = "{0}{1}".format(subStr, newNum);
		    subStr = "{0}{1}".format(subStr, i);
		    subInt = '';
		    num_cnt = 0;
		else:
		    subStr = "{0}{1}".format(subStr, i);
	newList.append(subStr);
    return newList;
def extStrings2(myList):
    print "+++ extStrings +++"
    # find every number and find maximum number in a certain range
    fixDigit = 7;
    newList = [];
    for strLine in myList:
	subStr = '';
	subInt = '';
	num_cnt = 0;
	for i in strLine:
	    #print "*** strLine: {}".format(strLine);
	    #print "ord({0})={1}".format(i, ord(i));
	    if (ord(i) > 47) and (ord(i) < 58):
		num_cnt = num_cnt + 1;
		subInt = "{0}{1}".format(subInt, i);
		#print "subInt : {}".format(subInt);
	    else:
		subStr = "{0}{1}".format(subStr, i);
	
	if num_cnt > 0:
	    num_zero = fixDigit - num_cnt;
	    newNum = '0' * num_zero;
	    newNum = "{0}{1}".format(newNum, subInt);
	    subStr = "{0}{1}".format(subStr, newNum);
	    subStr = "{0}{1}".format(subStr, i);
	    subInt = '';
	    num_cnt = 0;

	#print "subStr: {}".format(subStr);		
	newList.append(subStr);
    return newList;

def sort_str_num(myList, order):
    print "+++ sort_str_num +++"
    #print '{0}-{1}'.format(order, order.upper())

    if (order.upper() == 'DESC'):
	order = True;
    else:
	order = False;
    
    # Sort original list and get the index information
    sListInfo = getSortedList(myList, order);		# False:ascending, True: descending
    sIdx  = sListInfo[0];
    sList = sListInfo[1];
    
    # Extend file name by extending digits with fixed length
    new_sList = extStrings(sList);
    #print new_sList;

    # Sort extended file and get the index of sorted one
    new_sListInfo = getSortedList(new_sList, order);		# False:ascending, True: descending
    new_sIdx = new_sListInfo[0];
    new_sList = new_sListInfo[1];
    
    # Using the index to order original file names
    afterSort = [];
    for i in new_sIdx:
	afterSort.append(sList[i]);
    
    return afterSort;


#********************************************************
# *  Validating path
#********************************************************
def pathValidation(request):
    print "*** pathValidataion ***"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        if (cmd == 'path_validation'):
            path  = request.POST.get('path');
            #print path
            server = serverside(path);
            status = server.isvalidate();
            #print status;
            #print "Status = {}. len={}".format(status, len(status));
            #if len(status) > 0:
            #    print status[0];
                
	    outDic = {
		      'type'           : status,
		}
    
        if (cmd == 'make_dir'):
	    print "==> make_dir ";
            path  = request.POST.get('path');
	    print "call MKDIR ";
	    server = serverside(path);
	    status = server.mkdir();
	    print status;
	    outDic = {
		      'type'           : status,
		}
	    
        return HttpResponse(json.dumps(outDic));

#********************************************************
# *  Validating path
#********************************************************
def info_permission_write(request):
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        if (cmd == 'permission_write'):
            path  = request.POST.get('path');
            #print path
            server = serverside(path);
            status = server.permission_write();
            #print status;                           # status = [owner, group, other]
            #print "Status = {}. len={}".format(status, len(status));
            if len(status) > 0:
                print status[0];
                
        outDic = {
                  'write_info'           : status,
            }
        return HttpResponse(json.dumps(outDic));

def info_permission_exec(request):
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        if (cmd == 'permission_exec'):
            path  = request.POST.get('path');
            #print path
            server = serverside(path);
            status = server.permission_exec();
            #print status;                           # status = [owner, group, other]
            #print "Status = {}. len={}".format(status, len(status));
            if len(status) > 0:
                print status[0];
                
        outDic = {
                  'exec_info'           : status,
            }
        return HttpResponse(json.dumps(outDic));

#********************************************************
# *  GET DB Information
#********************************************************
def getDBinfo(request):
    print "### getDBinfo ###"
    rsec = request.session.get_expiry_age();
    print rsec;
    sstate = '';
    print 'user_id' not in request.session
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
	outDic = {
		    'errMsg'	    : 'Session has been expired!',
	}
	sstate = 'Session has been expired!';
	print sstate
	template = 'gui/login.html';
	return render_to_response(template, outDic, context_instance = RequestContext(request) )

    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        pbs = [];
        if (cmd == 'get_recent_pbs'):
            get_db = getDB(dbName, request.session['user_id']);
            pbs = get_db.get_pbs(cmd);
	if len(pbs) < 1:
	    pbs = "#!/bin/csh\n#PBS -l nodes=1:ppn=1\n#PBS -l mem=500mb\n#PBS -l walltime=72:00:00\n#PBS -l cput=72:00:00\n#PBS -q default\n";
	    
        outDic = {
                  'pbs'           : pbs,
		  'sstate'	  : sstate,
              }
        return HttpResponse(json.dumps(outDic));


def help(request):
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    template = 'gui/help.html';
    outDic = {
	    'pgTitle'	    : 'ST-Analyzer!',
	}
    return render_to_response(template, outDic, context_instance = RequestContext(request) )

def index(request):
    template = 'gui/login.html';
    outDic = {
	    'pgTitle'	    : 'MBanalyzer test page!',
	}
    return render_to_response(template, outDic, context_instance = RequestContext(request) )

def desktop(request):
    template = 'desktop/index.html';
    outDic = {
	    'pgTitle'	    : 'MBanalyzer test page!',
	}
    return render_to_response(template, outDic, context_instance = RequestContext(request) )

#********************************************************
# *  for test purpose
#********************************************************
def test_filter(request):
    template = 'gui/test_filter.htm';
    outDic = {
	    'pgTitle'	    : 'MBanalyzer test page!',
	}
    return render_to_response(template, outDic, context_instance = RequestContext(request) )


#********************************************************
# *  for logout
#********************************************************
def logout(request):
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    # initializing all sessions
    for sesskey in request.session.keys():
        del request.session[sesskey]
    request.session.set_expiry(1);
    outDic = {
		'errMsg'	    : 'You have been loged out!',
    }
    template = 'gui/login.html';
    return render_to_response(template, outDic, context_instance = RequestContext(request) )

#    return HttpResponseRedirect("/gui/")

#********************************************************
# *  for login GUI
#********************************************************
def login(request):
    # initializing all sessions
    for sesskey in request.session.keys():
        del request.session[sesskey];
    
    userid   = request.POST.get('userID');
    pwd      = request.POST.get('pwd');
    userid = userid.strip(' \t\n\r');
    pwd    = pwd.strip(' \t\n\r');
    if (userid == '') or (pwd == ''):
        template = 'gui/login.html';
        Msg      = 'user ID and password should be given!'
    else:
        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        c.execute("select * from gui_user")
        row = c.fetchone();
        #print dbName
        #print row
        
        if not row:
            global user
            user = 'admin';
            pwd   = '12345';
            email = 'admin@stanalyzer.org'
            level = '10'
            hpwd = hashlib.md5(pwd);
            hpwd = hpwd.hexdigest();
            query = "INSERT INTO gui_user (uid, pwd, email, level) VALUES ('{0}', '{1}', '{2}', {3})".format(user, hpwd, email, level)
            #print query
            c.execute(query)
            conn.commit();
            Msg = 'admin has been initialized!'
            template = 'gui/login.html';
        else:
            hpwd = hashlib.md5(pwd);
            hpwd = hpwd.hexdigest();
            query = "SELECT uid, pwd from gui_user WHERE uid='{0}' and pwd='{1}'".format(userid, hpwd);
            #print query
            c.execute(query)
            row = c.fetchone();
            if not row:
                template = 'gui/login.html';
                Msg = 'ID and PWD do not match!';
            else:
                #template = 'gui/stanalyzer.html';
                request.session['user_id'] = userid;
                request.session.set_expiry(SESSION_TIME_OUT);
                #Msg = "{0}={1} and {2}={3}".format(userid, row[0], pwd, row[1]);
                Msg = userid
                conn.close();
                return HttpResponseRedirect("/gui/stanalyzer/")
                #return HttpResponseRedirect("/gui/desktop/")
        conn.close();
    outDic = {
	    'errMsg'	    : Msg,
	}
    return render_to_response(template, outDic, context_instance = RequestContext(request) )


    
    
#********************************************************
# *  for Project View
#********************************************************
def toyView_data(request):
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )


    #request.session.set_expiry(SESSION_TIME_OUT);
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    
    #----------------------------------------
    # INITIALIZING gui_user table
    #----------------------------------------
    c.execute("DELETE FROM gui_user");
    conn.commit();
    
    pwd = "12345";
    hpwd = hashlib.md5(pwd);
    hpwd = hpwd.hexdigest();
    query = """INSERT INTO gui_user (uid, pwd, email, level) \
            VALUES ("admin", "{0}", "admin@stanalyzer.org", 10) """.format(hpwd);
    c.execute(query);
    conn.commit();
    query = """INSERT INTO gui_user (uid, pwd, email, level) \
            VALUES ("jcjeong", "{0}", "jcjeong@stanalyzer.org", 10) """.format(hpwd);
    c.execute(query);
    conn.commit();
    query = """INSERT INTO gui_user (uid, pwd, email, level) \
            VALUES ("guest", "{0}", "guest@stanalyzer.org", 0) """.format(hpwd);
    c.execute(query);
    conn.commit();
    print "gui_user initialized!"
    
    #----------------------------------------
    # INITIALIZING gui_project
    #----------------------------------------
    c.execute("DELETE FROM gui_project");
    conn.commit();
    cdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
    pbs = "#!/bin/csh\n#PBS -l nodes=1:ppn=1\n#PBS -l mem=500mb\n#PBS -l walltime=72:00:00\n#PBS -l cput=72:00:00\n#PBS -q default\n";
    query = """INSERT INTO gui_project (user_id, name, date, pbs) \
            VALUES ("admin", "project toy example1", "{0}", "{1}") """.format(cdate, pbs);
    c.execute(query);
    conn.commit();
    print "gui_project initialized!"
    
    #----------------------------------------
    # INITIALIZING gui_path_input
    #----------------------------------------
    c.execute("DELETE FROM gui_path_input");
    conn.commit();
    path = "/home2/jcjeong/project/stanalyzer2/stanalyzer/trajectory";
    query = """INSERT INTO gui_path_input (proj_id, path) \
            VALUES (1, "{0}") """.format(path);
    c.execute(query);
    conn.commit();
    print "gui_path_input initialized!"

    #----------------------------------------
    # INITIALIZING gui_path_input
    #----------------------------------------
    c.execute("DELETE FROM gui_path_input");
    conn.commit();
    path = "/home2/jcjeong/project/stanalyzer2/stanalyzer/trajectory";
    query = """INSERT INTO gui_path_input (proj_id, path) \
            VALUES (1, "{0}") """.format(path);
    c.execute(query);
    conn.commit();
    print "gui_path_input initialized!"

    #----------------------------------------
    # INITIALIZING gui_path_output
    #----------------------------------------
    c.execute("DELETE FROM gui_path_output");
    conn.commit();
    path = "/home2/jcjeong/tmp";
    query = """INSERT INTO gui_path_output (proj_id, path) \
            VALUES (1, "{0}") """.format(path);
    c.execute(query);
    conn.commit();
    print "gui_path_output initialized!"
    
    #----------------------------------------
    # INITIALIZING gui_path_python
    #----------------------------------------
    c.execute("DELETE FROM gui_path_python");
    conn.commit();
    path = "/home/sunhwan/local/python/bin/python";
    query = """INSERT INTO gui_path_python (proj_id, path) \
            VALUES (1, "{0}") """.format(path);
    c.execute(query);
    conn.commit();
    print "gui_path_python initialized!"
    conn.close();
    
    return HttpResponseRedirect("/")

    
def toyView_prj(request):
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL

    #---------------------------------------------#
    # HANDLING PROJECT TABLE ** START **
    #---------------------------------------------#
    # Initializing variables
    parents = [];
    indent = [];
    parent = [];
    title  = [];
    path1  = [];
    path2  = [];
    path3  = [];
    path4  = [];
    path5  = [];
    pbs    = [];
    date   = [];
    numRec = [];
    
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    c.execute("select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project")
    row = c.fetchall();

    if (not row) or (cmd == 'init'):
        c.execute("DELETE FROM gui_project");
        conn.commit();

        # Reading a file
        fid = open("static/data/init_prj.txt", "r");
        for readLine in fid:
            readLine = readLine.strip(' \t\n\r');
            if (len(readLine) > 0):
                tmp = re.split('\t', readLine);
                query = """INSERT INTO gui_project (user_id, name, path1, path2, path3, path4, path5, pbs, date) \
                         VALUES ( "{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}")""".format( \
                         tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], tmp[6], tmp[7], tmp[8]);
                #print query;
                c.execute(query);
                conn.commit();
        
        fid.close();
        
        # Retriving updated information
        c.execute("select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project")
        row = c.fetchall();
        for item in row:
           #print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\n".format(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9]);
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            title.append(item[2]);
            path1.append(item[3]);
            path2.append(item[4]);
            path3.append(item[5]);
            path4.append(item[6]);
            path5.append(item[7]);
            date.append(item[8]);
            rmCrLf = re.sub(r"\s+", "", item[9]);            
            pbs.append(rmCrLf);
            
        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
        
    elif (cmd == 'delete'):
        #print 'DELETING...';
        c.execute("DELETE FROM gui_project");
        conn.commit();
        
        # display initialized table        
        parents.append(-1);
        indent.append(0);
        parent.append(-1);
        title.append("N/A");
        path1.append("N/A");
        path2.append("N/A");
        path3.append("N/A");
        path4.append("N/A");
        path5.append("N/A");
        pbs.append("N/A");
        date.append("N/A");
        numRec.append(0);           # index starts from 0

    else:
        for item in row:
           #print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\n".format(item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9]);
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            title.append(item[2]);
            path1.append(item[3]);
            path2.append(item[4]);
            path3.append(item[5]);
            path4.append(item[6]);
            path5.append(item[7]);
            date.append(item[8]);
            
            rmCrLf = re.sub(r"\s+", "", item[9]);
            pbs.append(rmCrLf);

        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
    

    outDic = {
            'parents'       : parents,
            'indent'	    : indent,
            'parent'	    : parent,
            'title'	    : title,
            'path1'	    : path1,
            'path2'	    : path2,
            'path3'	    : path3,
            'path4'	    : path4,
            'path5'	    : path5,
            'date'	    : date,
            'pbs'           : pbs,
            'numRec'        : numRec,
        }
    #print c;
    
    conn.close();
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/toyDB_prj.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));

def toyView_usr(request):
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL

    #---------------------------------------------#
    # HANDLING PROJECT TABLE ** START **
    #---------------------------------------------#
    # Initializing variables
    parents = [];
    indent = [];
    parent = [];
    uid  = [];
    pwd  = [];
    email  = [];
    level  = [];
    numRec = [];
    
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    c.execute("select uid, pwd, email, level from gui_user")
    row = c.fetchall();

    if (not row) or (cmd == 'init'):
        c.execute("DELETE FROM gui_user");
        conn.commit();

        # Reading a file
        fid = open("static/data/init_usr.txt", "r");
        for readLine in fid:
            readLine = readLine.strip(' \t\n\r');
            if (len(readLine) > 0):
                tmp = re.split('\t', readLine);
                #print tmp;
                hpwd = hashlib.md5(tmp[1]);
                hpwd = hpwd.hexdigest();
                query = """INSERT INTO gui_user (uid, pwd, email, level) \
                         VALUES ( "{0}", "{1}", "{2}", {3})""".format( \
                         tmp[0], hpwd, tmp[2], tmp[3]);
                #print query;
                c.execute(query);
                conn.commit();
        
        fid.close();
        
        # Retriving updated information
        c.execute("select uid, pwd, email, level from gui_user")
        row = c.fetchall();
        for item in row:
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            uid.append(item[0]);
            pwd.append(item[1]);
            email.append(item[2]);
            level.append(item[3]);

        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
        
    elif (cmd == 'delete'):
        #print 'DELETING...';
        c.execute("DELETE FROM gui_user");
        conn.commit();
        
        # display initialized table        
        parents.append(-1);
        indent.append(0);
        parent.append(-1);
        uid.append("N/A");
        pwd.append("N/A");
        email.append("N/A");
        level.append("N/A");
        numRec.append(0);           # index starts from 0

    else:
        for item in row:
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            uid.append(item[0]);
            pwd.append(item[1]);
            email.append(item[2]);
            level.append(item[3]);

        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
    

    outDic = {
            'parents'       : parents,
            'indent'	    : indent,
            'parent'	    : parent,
            'uid'	    : uid,
            'pwd'	    : pwd,
            'email'	    : email,
            'level'	    : level,
            'numRec'        : numRec,
        }
    #print c;
    
    conn.close();
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/toyDB_usr.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));


def prjView(request):
    # check out authority 
    if 'user_id' not in request.session:
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    conn = sqlite3.connect(dbName);
    c = conn.cursor();

    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        pkey  = request.POST.get('pkey');
        pkey = pkey.strip(' \t\n\r');
        if (cmd == 'delete'):
            query = """DELETE FROM gui_project where user_id = "{0}" AND id = {1}""".format(user_id, pkey);
            #print query;
            c.execute(query);
            conn.commit();

    else:
        cmd = 'http';           # connection with URL
        
    #---------------------------------------------#
    # HANDLING PROJECT TABLE ** START **
    #---------------------------------------------#
    # Initializing variables
    pkey = [];
    parents = [];
    indent = [];
    parent = [];
    title  = [];
    path1  = [];
    path2  = [];
    path3  = [];
    path4  = [];
    path5  = [];
    pbs    = [];
    date   = [];
    numRec = [];
    
    c.execute("select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project")
    row = c.fetchall();

    if (not row):
        # display initialized table
        pkey.append(-1);
        parents.append(-1);
        indent.append(0);
        parent.append(-1);
        title.append("N/A");
        path1.append("N/A");
        path2.append("N/A");
        path3.append("N/A");
        path4.append("N/A");
        path5.append("N/A");
        pbs.append("N/A");
        date.append("N/A");
        numRec.append(0);           # index starts from 0
    else:
        for item in row:
            #print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\n".format(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9]);
            #print "DATE:" +  item[8];
            #print "PBS:" + item[9];
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            pkey.append(item[0]);
            title.append(item[2]);
            path1.append(item[3]);
            path2.append(item[4]);
            path3.append(item[5]);
            path4.append(item[6]);
            path5.append(item[7]);
            date.append(item[8]);
            rmCrLf = re.sub(r"\s+", "", item[9]);
            pbs.append(rmCrLf);
        
        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
    
    outDic = {
            'pkey'          : pkey,
            'parents'       : parents,
            'indent'	    : indent,
            'parent'	    : parent,
            'title'	    : title,
            'path1'	    : path1,
            'path2'	    : path2,
            'path3'	    : path3,
            'path4'	    : path4,
            'path5'	    : path5,
            'pbs'           : pbs,
            'date'	    : date,
            'numRec'        : numRec,
        }
    #print c;
    
    conn.close();
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/projectView.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));

def prjView_new(request):
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    if request.is_ajax() and (request.method == 'POST'):
        #print "OKAY this is NEW submit!!"
        title    = request.POST.get('title');
        pbs      = request.POST.get('pbs');
        rpaths   = request.POST.getlist('rpaths[]');
        #print rpaths
        out_paths  = request.POST.getlist('out_paths[]');
        #print out_paths
        ex_pythons = request.POST.getlist('ex_pythons[]');
        #print ex_pythons
        app_paths  = request.POST.getlist('app_paths[]');
	
        #pbs.replace("\r", r"\r").replace("\n", r"\n");
        #print pbs
        
        #print request.session.session_key; # get session key
        user = request.session.get('user_id');
        cdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
        #cdate = datetime.now().strftime("%A, %d. %B %Y %I:%M%p");
        #print cdate
        
        #fPath = '';
        #vPath = '';
        #print 'learning rpath...'
        #for i in range(len(rpaths)):
        #    fPath = fPath + "path{0}, ".format(i+1);
        #    vPath = vPath + """"{0}", """.format(rpaths[i]);
            
        #query = """INSERT INTO gui_project (user_id, name, {0} date, pbs) \
        #        VALUES ("{1}", "{2}", {3} "{4}", "{5}")""".format(fPath, user, title, vPath, cdate, pbs);
        
        #print dbName
        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        
        # Insert project information into the table
	#print "==== okay insert new value"
        query = """INSERT INTO gui_project (user_id, name, date, pbs) \
                VALUES ("{0}", "{1}", "{2}", "{3}")""".format(user, title, cdate, pbs);
        #print query
        c.execute(query);
        conn.commit();
        
        # Retriving the primary key of project
        query = """SELECT id FROM gui_project WHERE user_id = "{0}" AND date = "{1}" """.format(user, cdate);
        c.execute(query);
        prj_id = c.fetchone();      # primary key = prj_id[0]
        
        #print "PRIMARY KEY IS: {}".format(prj_id[0]);
        
        # Insert input, output, and python path
        for i in range(len(rpaths)):
            query = """INSERT INTO gui_path_input (proj_id, path) \
                       VALUES ({0}, "{1}")""".format(prj_id[0], rpaths[i]);
            #print query;
            c.execute(query);
            conn.commit();

        for i in range(len(out_paths)):
            query = """INSERT INTO gui_path_output (proj_id, path) \
                       VALUES ({0}, "{1}")""".format(prj_id[0], out_paths[i]);
            #print query
            c.execute(query);
            conn.commit();

        for i in range(len(ex_pythons)):
            query = """INSERT INTO gui_path_python (proj_id, path) \
                       VALUES ({0}, "{1}")""".format(prj_id[0], ex_pythons[i]);
            print query
            c.execute(query);
            conn.commit();

        for i in range(len(app_paths)):
            query = """INSERT INTO gui_path_app (proj_id, path) \
                       VALUES ({0}, "{1}")""".format(prj_id[0], app_paths[i]);
            #print query
            c.execute(query);
            conn.commit();

        # Display tables;
        """
        query = "SELECT id, user_id, name, date, pbs FROM gui_project";
        c.execute(query);
        row = c.fetchall();
        print query
        for item in row:
            print item;
            
        query = "SELECT id, proj_id, path FROM gui_path_input";
        c.execute(query);
        row = c.fetchall();
        print query
        for item in row:
            print item;

        query = "SELECT id, proj_id, path FROM gui_path_output";
        c.execute(query);
        row = c.fetchall();
        print query
        for item in row:
            print item;

        query = "SELECT id, proj_id, path FROM gui_path_python";
        c.execute(query);
        row = c.fetchall();
        print query
        for item in row:
            print item;
	    
        query = "SELECT id, proj_id, path FROM gui_path_app";
        c.execute(query);
        row = c.fetchall();
        print query
        for item in row:
            print item;

        """
        conn.close();
        
    else:
        title       = "";
        pbs         = "";
        rpaths      = "";
        out_paths   = "";
        ex_pythons  = "";
	app_paths   = "";
            
        
    outDic = {
            'title'	    : title,
            'pbs'	    : pbs,
            'rpaths'	    : rpaths,
            'out_paths'     : out_paths,
            'ex_pythons'    : ex_pythons,
	    'app_paths'	    : app_paths,
        }
        
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/projectView_new.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));
    
def prjView_update(request):
    print "### prjView_update ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    if request.is_ajax() and (request.method == 'POST'):
        cmd     =  request.POST.get('cmd');
        pkey     = request.POST.get('pkey');
        title    = request.POST.get('title');
        pbs      = request.POST.get('pbs');
        rpaths   = request.POST.getlist('rpaths[]');
        out_paths  = request.POST.getlist('out_paths[]');
        ex_pythons = request.POST.getlist('ex_pythons[]');
        app_paths  = request.POST.getlist('app_paths[]');
	
        user = request.session.get('user_id');
        cdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S");

        if cmd == 'reload':            
            #print dbName
            conn = sqlite3.connect(dbName);
            c = conn.cursor();
            
            # Update project information
            query = """UPDATE gui_project SET name="{0}", date="{1}", pbs="{2}" \
                    WHERE id={3} AND user_id="{4}" """.format(title, cdate, pbs, pkey, user);
            #print query
            c.execute(query);
            conn.commit();
            
            # Deleting associated tables - this makes easier to update it
            query = "DELETE FROM gui_path_input WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
            
            # Insert input, output, and python path
            for i in range(len(rpaths)):
                query = """INSERT INTO gui_path_input (proj_id, path) \
                           VALUES ({0}, "{1}")""".format(pkey, rpaths[i]);
                #print query
                c.execute(query);
                conn.commit();
    
            # Deleting associated tables - this makes easier to update it
            query = "DELETE FROM gui_path_output WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
    
            for i in range(len(out_paths)):
                query = """INSERT INTO gui_path_output (proj_id, path) \
                           VALUES ({0}, "{1}")""".format(pkey, out_paths[i]);
                #print query
                c.execute(query);
                conn.commit();
    
            # Deleting associated tables - this makes easier to update it
            query = "DELETE FROM gui_path_python WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
    
            for i in range(len(ex_pythons)):
                query = """INSERT INTO gui_path_python (proj_id, path) \
                           VALUES ({0}, "{1}")""".format(pkey, ex_pythons[i]);
                #print query
                c.execute(query);
                conn.commit();

        # Deleting associated tables - this makes easier to update it
            query = "DELETE FROM gui_path_app WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
    
            for i in range(len(app_paths)):
                query = """INSERT INTO gui_path_app (proj_id, path) \
                           VALUES ({0}, "{1}")""".format(pkey, app_paths[i]);
                #print query
                c.execute(query);
                conn.commit();
    
    else:
        pkey        = "";
        title       = "";
        pbs         = "";
        rpaths      = "";
        out_paths   = "";
        ex_pythons  = "";
        app_paths   = "";
            
        
    outDic = {
            'pkey'          : pkey,
            'title'	    : title,
            'pbs'	    : pbs,
            'rpaths'	    : rpaths,
            'out_paths'     : out_paths,
            'ex_pythons'    : ex_pythons,
	    'app_paths'     : app_paths,
        }
        
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/projectView_new.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));
        

def prjView_delete(request):
    # check out authority
    print "### prjView_delete ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);        # session will be closed in 10 minutes
    if request.is_ajax() and (request.method == 'POST'):
        cmd     =  request.POST.get('cmd');
        pkey     = request.POST.get('pkey');
        
        user = request.session.get('user_id');
        cdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S");

        if cmd == 'prjDelete':            
            #print dbName
            conn = sqlite3.connect(dbName);
            c = conn.cursor();
            
            # DELETING project information
            query = "DELETE FROM gui_project WHERE id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();

            query = "DELETE FROM gui_job WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();

            query = "DELETE FROM gui_path_input WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();

            query = "DELETE FROM gui_path_output WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();

            query = "DELETE FROM gui_path_python WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
	    
            query = "DELETE FROM gui_path_app WHERE proj_id={0}".format(pkey);
            #print query
            c.execute(query);
            conn.commit();
            
            conn.close();
    else:
        pkey        = "";
            
        
    outDic = {
            'pkey'          : pkey,
        }
        
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/projectView_new.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));
        
    

def jobView(request):
    # check out authority
    print "### jobView ###";
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    
    #request.session.set_expiry(SESSION_TIME_OUT);
    template = 'gui/jobView.html';
    outDic = {
        'cmd': 'init',
    }
    return render_to_response(template, outDic, context_instance = RequestContext(request));

def jobView_jqGrid_para(request):
    # check out authority
    print "### jobView_jqGrid_para ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    
    #request.session.set_expiry(SESSION_TIME_OUT);
    job_id = request.GET.get('job_id');

    if request.GET.get("sidx"):
        sidx = request.GET["sidx"];
        sord = request.GET["sord"];
        cpage   = request.GET["page"];
        cpage   = int(cpage);
        maxrow  = request.GET["rows"];
        maxrow  = int(maxrow);    
        
    if cpage == 1:
        st_index = 0;
        ed_index = maxrow;
    else:
        st_index = maxrow * cpage - maxrow;
        ed_index = maxrow * cpage;
        
        
    if (request.GET["_search"] == 'true'):
        sfilter = request.GET["filters"];
        search_dic =json.loads(sfilter);      # convert string to dictionary
        search_rules = search_dic["rules"][0];
        search_field = search_rules["field"];
        search_data = search_rules["data"];
        query = """select id, anaz, para, val, status from gui_parameter where job_id = {0} AND {1} like "%{2}%" order by {3} {4} limit {5}, {6}""".format(job_id, search_field, search_data, sidx, sord, st_index, ed_index);
        #print query
    else:   
        query = "select id, anaz, para, val, status from gui_parameter where job_id = {0} order by {1} {2}".format(job_id, sidx, sord);
        #print query

    #query = "select id, job_id, anaz, para, val, status from gui_parameter where job_id = {0} order by {1} {2}".format(job_id, sidx, sord);
    #query = "select id, anaz, para, val, status from gui_parameter where job_id = {0} order by {1} {2}".format(job_id, sidx, sord);
    #print query;
    conn = sqlite3.connect(dbName);
    c = conn.cursor();    
    c.execute(query);
    row = c.fetchall();
    conn.close();
    
    rows = [];
    row_cnt = 0;
    if st_index == 0:    
	for item in row:
	    row_cnt = row_cnt + 1;
	    tmp = { "id": str(row_cnt), "cell": item}
	    rows.append(tmp);
    else:
	for item in row:
	    row_cnt = row_cnt + 1;
	    if (row_cnt > st_index):
		tmp = { "id": str(row_cnt), "cell": item}
		rows.append(tmp);

    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
        tpages = 1;
    
    total_pages = tpages;

    outDic = {
            'total'	: total_pages,
            'page'      : cpage,
            'records'   : row_cnt,
            'rows'      : rows,            
        }
    return HttpResponse(json.dumps(outDic));

    
def jobView_jqGrid_job(request):
    # check out authority
    print "jobView_jqGrid_job"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    
    #request.session.set_expiry(SESSION_TIME_OUT);
    prj_id = request.GET.get('prj_id');
    
    if request.GET.get("sidx"):
        sidx = request.GET["sidx"];
        sord = request.GET["sord"];
        cpage   = request.GET["page"];
        cpage   = int(cpage);
        maxrow  = request.GET["rows"];
        maxrow  = int(maxrow);    
        
    if cpage == 1:
        st_index = 0;
        ed_index = maxrow;
    else:
        st_index = maxrow * cpage - maxrow;
        ed_index = maxrow * cpage;

    if (request.GET["_search"] == 'true'):
        sfilter = request.GET["filters"];
        search_dic =json.loads(sfilter);      # convert string to dictionary
        search_rules = search_dic["rules"][0];
        search_field = search_rules["field"];
        search_data = search_rules["data"];
        query = """select id, name, anaz, status, output, stime, etime from gui_job where proj_id = {0} AND {1} like "%{2}%" order by {3} {4} limit {5}, {6}""".format(prj_id, search_field, search_data, sidx, sord, st_index, ed_index);
        #print query
    else:   
        query = "select id, name, anaz, status, output, stime, etime from gui_job where proj_id = {0} order by {1} {2}".format(prj_id, sidx, sord);
        #print query

    #query = "select id, proj_id, name, anaz, status, output, stime, etime from gui_job where proj_id = {0} order by {1} {2}".format(prj_id, sidx, sord);
    #print query;
    conn = sqlite3.connect(dbName);
    c = conn.cursor();    
    c.execute(query);
    row = c.fetchall();
    conn.close();
    
    rows = [];
    row_cnt = 0;
    
    if st_index == 0:
	for item in row:
	    row_cnt = row_cnt + 1;
	    tmp = { "id": str(row_cnt), "cell": item}
	    rows.append(tmp);
    else:
	for item in row:
	    row_cnt = row_cnt + 1;
	    if (row_cnt > st_index):
		tmp = { "id": str(row_cnt), "cell": item}
		rows.append(tmp);
	
        
    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
        tpages = 1;
    
    total_pages = tpages;

    outDic = {
            'total'	: total_pages,
            'page'      : cpage,
            'records'   : row_cnt,
            'rows'      : rows,            
        }
    return HttpResponse(json.dumps(outDic));

    

def jobView_jqGrid_prj(request):
    # check out authority
    print "### jobView_jqGrid_prj ###"
    rsec = request.session.get_expiry_age();
    print 'user_id' not in request.session

    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
	print "works this !!!!"
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
	print template
        return render_to_response(template, outDic, context_instance = RequestContext(request))

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    #print request.GET
	
    if request.GET.get("sidx"):
	sidx    = request.GET["sidx"];
	sord    = request.GET["sord"];
	cpage   = request.GET["page"];
	cpage   = int(cpage);
	maxrow  = request.GET["rows"];
	maxrow  = int(maxrow);    
	
    if cpage == 1:
	st_index = 0;
	ed_index = maxrow;
    else:
	st_index = maxrow * cpage - maxrow;
	ed_index = maxrow * cpage;
    
    #if request.is_ajax() and (request.method == 'POST'):
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    
    if (request.GET["_search"] == 'true'):
	sfilter = request.GET["filters"];
	search_dic =json.loads(sfilter);      # convert string to dictionary
	search_rules = search_dic["rules"][0];
	search_field = search_rules["field"];
	search_data = search_rules["data"];
	query = """select id, user_id, name, date, pbs from gui_project where user_id = "{0}" AND {1} like "%{2}%" order by {3} {4} limit {5}, {6}""".format(user_id, search_field, search_data, sidx, sord, st_index, ed_index);
	#print query
    else:   
	query = "select id, user_id, name, date, pbs from gui_project where user_id = '{0}' order by {1} {2}".format(user_id, sidx, sord);
	#print query
    
    c.execute(query);
    row = c.fetchall();
    conn.close();

    rows = [];
    row_cnt = 0;
    if st_index == 0:
	for item in row:
	    row_cnt = row_cnt + 1;
	    tmp = { "id": str(row_cnt), "cell": item}
	    rows.append(tmp);
    else:
	for item in row:
	    row_cnt = row_cnt + 1;
	    if (row_cnt > st_index):
		tmp = { "id": str(row_cnt), "cell": item}
		rows.append(tmp);
    
    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
	tpages = 1;
    
    total_pages = tpages;

    outDic = {
	    'total'	: total_pages,
	    'page'      : cpage,
	    'records'   : row_cnt,
	    'rows'      : rows,            
	}
    return HttpResponse(json.dumps(outDic));

def resultView_jqGrid_results(request):
    #print "OKAY i am In RESUT VIEW"
    # check out authority
    print "### resultView_jqGrid_results ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    
    #request.session.set_expiry(SESSION_TIME_OUT);
    prj_id = request.GET.get('prj_id');
    
    if request.GET.get("sidx"):
        sidx = request.GET["sidx"];
        sord = request.GET["sord"];
        cpage   = request.GET["page"];
        cpage   = int(cpage);
        maxrow  = request.GET["rows"];
        maxrow  = int(maxrow);    
        
    if cpage == 1:
        st_index = 0;
        ed_index = maxrow;
    else:
        st_index = maxrow * cpage - maxrow;
        ed_index = maxrow * cpage;

    if (request.GET["_search"] == 'true'):
	#print "--- search true at resultView ----"
        sfilter = request.GET["filters"];
        search_dic =json.loads(sfilter);      # convert string to dictionary
        search_rules = search_dic["rules"][0];
        search_field = search_rules["field"];
        search_data = search_rules["data"];
	# select all job ID corresponding to 'prj_id'
        query = """select id from gui_job where proj_id = {0} order by {1} {2}""".format(prj_id, sidx, sord);
	#print query
	conn = sqlite3.connect(dbName);
	c = conn.cursor();    
	c.execute(query);
	tmp = c.fetchall();
	JOBs = [];
	for job_id in tmp:
	    query = """select id, job_id, name, status, qid, img, txt, gzip from gui_outputs where job_id = {0} AND {1} like "%{2}%" order by {3} {4}""".format(job_id[0], search_field, search_data, sidx, sord);
	    #print query
	    c.execute(query);
	    row = c.fetchall();
	    JOBs.append(row);
	conn.close();
	#print JOBs
	conn.close();
	
    else:
	#print "--- search FALSE at resultView ----"
	JOBs = [];
	query = """select id from gui_job where proj_id = {0} order by {1} {2}""".format(prj_id, sidx, sord);
	#print query
	conn = sqlite3.connect(dbName);
	c = conn.cursor();    
	c.execute(query);
	tmp = c.fetchall();	# retrieve all related jobs corresponding to the current project 
	for job_id in tmp:
	    query = """select id, job_id, name, status, qid, img, txt, gzip from gui_outputs where job_id = {0} order by {1} {2}""".format(job_id[0], sidx, sord);
	    #print query
	    c.execute(query);
	    row = c.fetchall();
	    #print row
	    JOBs.append(row);
	conn.close();
	#print row
	#print "============== UPPER ROW, BELOW JOBs ===============";
	#print JOBs

    rows = [];
    row_cnt = 0;
    if st_index == 0:
	for row in JOBs:
	    for item in row:
		#item_arr = [ i for i in item ];
		row_cnt = row_cnt + 1;
		tmp = { "id": str(row_cnt), "cell": item}
		#print tmp;
		rows.append(tmp);
    else:
	for row in JOBs:
	    for item in row:
		row_cnt = row_cnt + 1;
		if (row_cnt > st_index):
		    tmp = { "id": str(row_cnt), "cell": item}
		    rows.append(tmp);
    
        
    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
        tpages = 1;
    
    total_pages = tpages;

    outDic = {
            'total'	: total_pages,
            'page'      : cpage,
            'records'   : row_cnt,
            'rows'      : rows,            
        }
    return HttpResponse(json.dumps(outDic));

    

def resultView_jqGrid_del_results(request):
    # check out authority
    print "### resultView_jqGrid_del_results ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
    if cmd == 'del_user':
        #print "OKAY I am in del_user"
        # Extract my level
        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        query = "select level from gui_user where uid='{0}'".format(user_id);
        c.execute(query);
        my_level = c.fetchone();
        my_level = int(my_level[0]);
        delUsers = request.POST.getlist('uid[]');
        fUsers = [];                                 # the list of users failed for deletion 
        for t_user in delUsers:
            query = "select level from gui_user where uid='{0}'".format(t_user);
            c.execute(query);
            user_level = c.fetchone();
            user_level = int(user_level[0]);
            if (my_level > user_level) or (user_id == t_user):
                query = "delete from gui_user where uid='{}'".format(t_user);
                #print query
                c.execute(query);
                conn.commit();
            else:
                #print t_user
                fUsers.append(t_user);
        conn.close();
        outDic = {
            'fUsers'    : fUsers,
        }
    return HttpResponse(json.dumps(outDic));

    
def userView(request):
    # check out authority
    print "### userView ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL

    #---------------------------------------------#
    # HANDLING PROJECT TABLE ** START **
    #---------------------------------------------#
    # Initializing variables
    parents = [];
    indent = [];
    parent = [];
    uid  = [];
    pwd  = [];
    email  = [];
    level  = [];
    numRec = [];
    
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    c.execute("select uid, pwd, email, level from gui_user")
    row = c.fetchall();

    if (not row):
        # display initialized table        
        parents.append(-1);
        indent.append(0);
        parent.append(-1);
        uid.append("N/A");
        pwd.append("N/A");
        email.append("N/A");
        level.append("N/A");
        numRec.append(0);           # index starts from 0
    else:
        for item in row:
            parents.append(-1);
            indent.append(0);
            parent.append(-1);
            uid.append(item[0]);
            pwd.append(item[1]);
            email.append(item[2]);
            level.append(item[3]);

        for i in range(len(row) ):
            numRec.append(i);
        #print "Number of Items in DB = {}".format(len(row));
    

    outDic = {
            'parents'       : parents,
            'indent'	    : indent,
            'parent'	    : parent,
            'uid'	    : uid,
            'pwd'	    : pwd,
            'email'	    : email,
            'level'	    : level,
            'numRec'        : numRec,
        }
    #print c;
    
    conn.close();
    if request.is_ajax() and (request.method == 'POST'):
       return HttpResponse(json.dumps(outDic));
    else:
        template = 'gui/user.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));

def usrView_jqGrid_create_user(request):
    print "### usrView_jqGrid_create_user ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    if cmd == 'get_level':
        level = getUsrLevel(dbName, user_id);
        outDic = {
            'user' : user_id,
            'level': level,
        }
    
    if cmd == 'newUser':
        new_user    = request.POST.get('user');
        new_pwd     = request.POST.get('pwd');
        hpwd = hashlib.md5(new_pwd);
        hpwd = hpwd.hexdigest();
        new_email   = request.POST.get('email');
        new_level   = request.POST.get('level');
        
        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        query = "INSERT INTO gui_user (uid, pwd, email, level) VALUES ('{0}', '{1}', '{2}', {3})".format(new_user, hpwd, new_email, new_level)
        c.execute(query);
        conn.commit();
        conn.close();
        outDic = {
            'user'	: new_user,
            'pwd'	: hpwd,
            'email'	: new_email,
            'level'	: new_level,
        }
        
    if cmd == 'editUser':
        #print "I am in EditUSER"
        edit_user    = request.POST.get('user');
        edit_pwd     = request.POST.get('pwd');
        hpwd = hashlib.md5(edit_pwd);
        hpwd = hpwd.hexdigest();
        edit_email   = request.POST.get('email');
        edit_level   = request.POST.get('level');

        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        query = "UPDATE gui_user SET uid='{0}', pwd='{1}', email='{2}', level={3} WHERE uid='{4}' ".format(edit_user, hpwd, edit_email, edit_level, edit_user);
        #print query
        c.execute(query);
        conn.commit();
        conn.close();
        outDic = {
            'user'	: edit_user,
            'pwd'	: hpwd,
            'email'	: edit_email,
            'level'	: edit_level,
        }
        
    return HttpResponse(json.dumps(outDic));


def usrView_jqGrid_del_user(request):
    # check out authority
    print "### usrView_jqGrid_del_user ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
    if cmd == 'del_user':
        #print "OKAY I am in del_user"
        # Extract my level
        conn = sqlite3.connect(dbName);
        c = conn.cursor();
        query = "select level from gui_user where uid='{0}'".format(user_id);
        c.execute(query);
        my_level = c.fetchone();
        my_level = int(my_level[0]);
        delUsers = request.POST.getlist('uid[]');
        fUsers = [];                                 # the list of users failed for deletion 
        for t_user in delUsers:
            query = "select level from gui_user where uid='{0}'".format(t_user);
            c.execute(query);
            user_level = c.fetchone();
            user_level = int(user_level[0]);
            if (my_level > user_level) or (user_id == t_user):
                query = "delete from gui_user where uid='{}'".format(t_user);
                #print query
                c.execute(query);
                conn.commit();
            else:
                #print t_user
                fUsers.append(t_user);
        conn.close();
        outDic = {
            'fUsers'    : fUsers,
        }
    return HttpResponse(json.dumps(outDic));



def usrView_jqGrid_usr(request):
    # check out authority
    print "### usrView_jqGrid_usr ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
	sstate = 'Session has been expired!';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    else:
	sstate = '';
	
    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    #print request.GET
        
    if request.GET.get("sidx"):
        sidx    = request.GET["sidx"];
        sord    = request.GET["sord"];
        cpage   = request.GET["page"];
        cpage   = int(cpage);
        maxrow  = request.GET["rows"];
        maxrow  = int(maxrow);    
        
    if cpage == 1:
        st_index = 0;
        ed_index = maxrow;
    else:
        st_index = maxrow * cpage - maxrow;
        ed_index = maxrow * cpage;
    
    #if request.is_ajax() and (request.method == 'POST'):
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    
    if (request.GET["_search"] == 'true'):
        sfilter = request.GET["filters"];
        search_dic =json.loads(sfilter);      # convert string to dictionary
        search_rules = search_dic["rules"][0];
        search_field = search_rules["field"];
        search_data = search_rules["data"];
        query = """select uid, email, level from gui_user where {0} like "%{1}%" order by {2} {3}""".format(search_field, search_data, sidx, sord);
        #print query
    else:   
        query = "select uid, email, level from gui_user order by {0} {1}".format(sidx, sord);
        #print query
    
    c.execute(query);
    row = c.fetchall();
    conn.close();

    rows = [];
    row_cnt = 0;
    if st_index == 0:
	for item in row:
	    row_cnt = row_cnt + 1;
	    tmp = { "id": str(row_cnt), "cell": item}
	    rows.append(tmp);
    else:
	for item in row:
	    row_cnt = row_cnt + 1;
	    if (row_cnt > st_index):
		tmp = { "id": str(row_cnt), "cell": item}
		rows.append(tmp);
	
    
    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
        tpages = 1;
    
    total_pages = tpages;
    #print rows
    outDic = {
            'total'	: total_pages,
            'page'      : cpage,
            'records'   : row_cnt,
            'rows'      : rows,
	    'sstate'	: sstate, 
        }
    return HttpResponse(json.dumps(outDic));

def stanalyzer(request):
    print "### stanalyzer ###"
    # check out authority
    rsec = request.session.get_expiry_age();
    print type(rsec)
    print "{} is remained until expired!".format(rsec);
    rdate = request.session.get_expiry_date();
    print "Date expired: {0}".format(rdate);
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
	outDic = {
		    'errMsg'	    : 'Session has been expired!',
		}
	template = 'gui/login.html';
	sstate = 'Session has been expired!';
	return render_to_response(template, outDic, context_instance = RequestContext(request) )
    else:
	sstate = '';
	
    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    
    if request.is_ajax() and (request.method == 'POST'):
	#print "This is AJAX!"
	cmd   = request.POST.get('cmd');
	
        #print "Okay you requested CMD as {}".format(cmd);
        if (cmd == 'path'):
	    print "\tCMD: path";
            pkey  = request.POST.get('pkey');
            pkey = pkey.strip(' \t\n\r');

            #query = "select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project where id = {0}".format(pkey);
            query = "select id, user_id, name, date, pbs from gui_project where user_id = '{0}' AND id = {1}".format(user_id, pkey);
            c.execute(query);
            prj = c.fetchall();
            
            query = "select id, proj_id, path from gui_path_input where proj_id = {0}".format(pkey);
            c.execute(query);
            path_in = c.fetchall();
            
            query = "select id, proj_id, path from gui_path_output where proj_id = {0}".format(pkey);
            c.execute(query);
            path_out = c.fetchall();

            query = "select id, proj_id, path from gui_path_python where proj_id = {0}".format(pkey);
            c.execute(query);
            path_py = c.fetchall();

            query = "select id, proj_id, path from gui_path_app where proj_id = {0}".format(pkey);
            c.execute(query);
            path_app = c.fetchall();
	    
        elif (cmd =='reload'):
	    print "\tCMD: reload";
            #print "This is  AJAX with relaod!!!!!!"
            #c.execute("select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project order by date desc")
            # find most recent one
            query = "select id, user_id, name, date, pbs from gui_project where user_id = '{0}' order by date desc".format(user_id);
            c.execute(query);
            prj = c.fetchall();
            pkey = prj[0][0];
            
            query = "select id, proj_id, path from gui_path_input where proj_id = {0}".format(pkey);
            c.execute(query);
            path_in = c.fetchall();
            
            query = "select id, proj_id, path from gui_path_output where proj_id = {0}".format(pkey);
            c.execute(query);
            path_out = c.fetchall();
    
            query = "select id, proj_id, path from gui_path_python where proj_id = {0}".format(pkey);
            c.execute(query);
            path_py = c.fetchall();
	    
            query = "select id, proj_id, path from gui_path_app where proj_id = {0}".format(pkey);
            c.execute(query);
            path_app = c.fetchall();
	    
        elif (cmd == 'prjDelete'):
            #print "CMD: prjDelte"
            query = "select id, user_id, name, date, pbs from gui_project where user_id = '{0}' order by date desc".format(user_id);
            c.execute(query);
            prj = c.fetchall();
            if len(prj) < 1 :
                pkey = ['-1'];
                path_in  = ['N/A'];
                path_out = ['N/A'];
                path_py  = ['N/A'];
            else:
                pkey = prj[0][0];
            
                query = "select id, proj_id, path from gui_path_input where proj_id = {0}".format(pkey);
                c.execute(query);
                path_in = c.fetchall();
                
                query = "select id, proj_id, path from gui_path_output where proj_id = {0}".format(pkey);
                c.execute(query);
                path_out = c.fetchall();
        
                query = "select id, proj_id, path from gui_path_python where proj_id = {0}".format(pkey);
                c.execute(query);
                path_py = c.fetchall();

                query = "select id, proj_id, path from gui_path_app where proj_id = {0}".format(pkey);
                c.execute(query);
                path_app = c.fetchall();
            
    else:
        #print "This is NOT AJAX!!!!!!"
        #c.execute("select id, user_id, name, path1, path2, path3, path4, path5, date, pbs from gui_project order by date desc")
        # find most recent one
        query = "select id, user_id, name, date, pbs from gui_project where user_id = '{0}' order by date desc".format(user_id);
        c.execute(query);
        prj = c.fetchall();
        if len(prj) < 1 :
            pkey = ['-1'];
            path_in  = ['N/A'];
            path_out = ['N/A'];
            path_py  = ['N/A'];
        else:
            pkey = prj[0][0];
        
            query = "select id, proj_id, path from gui_path_input where proj_id = {0}".format(pkey);
            c.execute(query);
            path_in = c.fetchall();
            
            query = "select id, proj_id, path from gui_path_output where proj_id = {0}".format(pkey);
            c.execute(query);
            path_out = c.fetchall();
    
            query = "select id, proj_id, path from gui_path_python where proj_id = {0}".format(pkey);
            c.execute(query);
            path_py = c.fetchall();

            query = "select id, proj_id, path from gui_path_app where proj_id = {0}".format(pkey);
            c.execute(query);
            path_app = c.fetchall();

    #print "length ROW: {}".format(len(row));
    #for item in row:
    #    print "id:{0}\nuser_id:{1}\nTitle:{2}\npath1:{3}\npath2:{4}\npath3:{5}\npath4:{6}\npath5:{7}\ndate:{8}\npbs:{9}\n".format(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9]);

    # Initializing variables
    pkey = [];
    user = [];
    title  = [];
    ptitle= zip(pkey, title); # merge two lists together
    
    path_inputs_id = [];
    path_inputs_proj_id = [];
    path_inputs_path = [];
    
    path_outputs_id = [];
    path_outputs_proj_id = [];
    path_outputs_path = [];

    path_pythons_id = [];
    path_pythons_proj_id = [];
    path_pythons_path = [];
    
    path_apps_id = [];
    path_apps_proj_id = [];
    path_apps_path = [];
    
    pbs    = [];
    date   = [];
    numRec = [];
    fList  = [];    # file list in the base directory
    if (not prj):
        # display initialized table
        pkey.append("");
        user.append("");
        title.append("");
        path_inputs_id.append("");
        path_inputs_proj_id.append("");
        path_inputs_path.append("");
	
        path_outputs_id.append("");
        path_outputs_proj_id.append("");
        path_outputs_path.append("");
	
        path_pythons_id.append("");
        path_pythons_proj_id.append("");
        path_pythons_path.append("");
	
        path_apps_id.append("");
        path_apps_proj_id.append("");
        path_apps_path.append("");
	
        pbs.append("");
        date.append("");
        numRec.append("");           # index starts from 0
        fList.append("");
    else:
        # print "ROW = {0}".format(len(row));
        # for project
        for item in prj:
            pkey.append(item[0]);
            user.append(item[1]);
            title.append(item[2]);
            date.append(item[3]);
            pbs.append(item[4]);
            
        for item in path_in:
            path_inputs_id.append(item[0]);
            path_inputs_proj_id.append(item[1]);
            path_inputs_path.append(item[2]);
            
        for item in path_out:
            path_outputs_id.append(item[0]);
            path_outputs_proj_id.append(item[1]);
            path_outputs_path.append(item[2]);
            
        for item in path_py:
            path_pythons_id.append(item[0]);
            path_pythons_proj_id.append(item[1]);
            path_pythons_path.append(item[2]);

        for item in path_app:
            path_apps_id.append(item[0]);
            path_apps_proj_id.append(item[1]);
            path_apps_path.append(item[2]);

        #print "Number of Items in DB = {}".format(len(row));
        for i in range(len(prj)):
            numRec.append(i);

        server = serverside(path_inputs_path[0]);
        fList = server.showdir();
	
	fList = sort_str_num(fList, 'asc');
	
        """
        status =  server.isvalidate();
        #print "Status for {} = {}".format(path1[0], status);
        if not status:
            fList = server.showdir();
        else:
            fList = [];
        """ 
        ptitle = zip(pkey, title);
    outDic = {
            'PROJECT_ROOT'          : PROJECT_ROOT,
            'dbName'                : dbName,
            'MEDIA_HOME'            : MEDIA_HOME,
            'ANALYZER_HOME'         : ANALYZER_HOME,
            'user'                  : request.session['user_id'],
            'pkey'                  : pkey,
            'title'	            : title,
            'ptitle'                : ptitle,
            'path_inputs_id'        : path_inputs_id,
            'path_inputs_proj_id'   : path_inputs_proj_id,
            'path_inputs_path'      : path_inputs_path,
            'path_outputs_id'       : path_outputs_id,
            'path_outputs_proj_id'  : path_outputs_proj_id,
            'path_outputs_path'     : path_outputs_path,
            'path_pythons_id'       : path_pythons_id,
            'path_pythons_proj_id'  : path_pythons_proj_id,
            'path_pythons_path'     : path_pythons_path,
	    'path_apps_id'          : path_apps_id,
            'path_apps_proj_id'     : path_apps_proj_id,
            'path_apps_path'        : path_apps_path,
            'pbs'                   : pbs,
            'date'	            : date,
            'numRec'                : numRec,
            'fList'                 : fList,
	    'sstate'		    : sstate,
        }

 
    conn.close();

    if request.is_ajax() and (request.method == 'POST'):
        return HttpResponse(json.dumps(outDic));
    else:
        #template = 'gui/stanalyzer.html';
        template = 'desktop/index.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request));



def stanalyzer_info(request):
    print "### stanalyzer_info ###"
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT); 
    fList = 'File not found!';
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        
        # ----------------------------------------
        # Get list of files based on the directory
        # ----------------------------------------
        if (cmd == 'get_flist'):
            # get file list for the given path
            path = request.POST.get('path');
            path = eval_path(path);
            #if (path[len(path)-1] != '/'):
            #    path = path + '/';
            #else:
                #print "passed!";
                #print "path={}, End with [{}]".format(path, path[len(path)-1]);
            server = serverside(path);
            fList = server.showdir();
	    
	    fList = sort_str_num(fList, 'asc');
	    
	    
            outDic = {
                    'fList' : fList,
                }

        # ---------------------------------------------
        # Processing information requried for job submitting
        # ---------------------------------------------
        if (cmd == 'get_structure'):
            pkey    = request.POST.get('pkey');
            title   = request.POST.get('title');
            bpath   = request.POST.get('bpath');
            stfile  = request.POST.get('stfile');
	    pdbfile  = request.POST.get('pdbfile');
            trjFile = request.POST.getlist('trjFile[]');
    
            # --- removing white spaces ---
            pkey = pkey.strip(' \t\n\r');
            title = title.strip(' \t\n\r');
            bpath = bpath.strip(' \t\n\r');
            stfile = stfile.strip(' \t\n\r');
	    pdbfile = pdbfile.strip(' \t\n\r');

            psf = '{0}/{1}'.format(bpath, stfile);
	    pdb = '{0}/{1}'.format(bpath, pdbfile);
            trj = '{0}/{1}'.format(bpath, trjFile[0]);
            
            #print psf
            #print trj
            # call MDsimulation 
            objSim = simulation(psf, trj);
            
            # get frame, atom, and segment information            
            num_frm  = objSim.num_frm;
            num_atom = objSim.num_atom;
	    num_ps   = str(objSim.num_ps);			# dt in picoseconds - convert floating to string (float type can be confused by Django)
            segList  = objSim.segList;
            
            # assume the first segments are chosen
            CresList = objSim.get_seg_residues(segList[0]);
            #print '--- CresList ---'
            #print CresList
            
            resList = [];
            resID   = [];
            for i in range(len(CresList)):
                resList.append(CresList.residues[i].name);
                resID.append(CresList.residues[i].id);
            
            #print '------resList-------'
            #print resList
            
	    num_files = len(trjFile);
	    
            outDic = {
                'bpath'	    : bpath,
                'trjFile'   : trjFile,
                'stfile'    : stfile,
		'pdbfile'   : pdbfile,
                'num_frm'   : num_frm,
                'num_atom'  : num_atom,
		'num_ps'    : num_ps,
		'num_files' : num_files,
                'segList'   : segList,
                'resList'   : resList,
                'resID'	    : resID,
            }

        # ---------------------------------------------
        # Get segment information
        # ---------------------------------------------
        if (cmd == 'get_segment'):
	    print "-> get_segment"
            segid      = request.POST.get('segID');
            bpath      = request.POST.get('bpath');
            stfile     = request.POST.get('stfile');
	    pdbfile    = request.POST.get('pdbfile');
            trjFile    = request.POST.getlist('trjFile[]');

            # --- removing white spaces ---
            segid   = segid.strip(' \t\n\r');
            bpath   = bpath.strip(' \t\n\r');
            stfile  = stfile.strip(' \t\n\r');
            pdbfile = pdbfile.strip(' \t\n\r');
            
            # ---- checkout path: make sure end with '/'
            bpath = eval_path(bpath);

            #print segid
            #print bpath
            #print stfile
            #print trjFile[0]
            
            psf = '{0}/{1}'.format(bpath, stfile);
	    pdb = '{0}/{1}'.format(bpath, pdbfile);
            trj = '{0}/{1}'.format(bpath, trjFile[0]);
            #print psf
            #print trj
            # call MDanalysis
            objSim = simulation(psf, trj);
            #print 'Object created'
            seg_name = objSim.get_segname(segid);
            #print seg_name
            CresInfo   = objSim.get_seg_residues(seg_name);
            resList = [];
            resID =[];
            for i in range(len(CresInfo)):
                resList.append(CresInfo[i].name);
                resID.append(CresInfo[i].id);
                
            #print '---resList---'
            #print resList
            #print '---resID---'
            #print resID
            
            outDic = {
                'resList' : resList,
                'resID'   : resID,
            }

        return HttpResponse(json.dumps(outDic));
    else:
        return HttpResponseRedirect("/gui/")





def stanalyzer_sendJob(request):
    print "### stanalyzer_sendJob ###"
    #print request.session
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    data = request.POST;
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
        
        # ----------------------------------------
        # Writing Job script and send it
        # ----------------------------------------
        if (cmd == 'sendJob'):
            job_title   = request.POST.get('job_title');
            pkey        = request.POST.get('pkey');
            ptitle      = request.POST.get('ptitle');
            machine     = request.POST.get('machine');
            func_name   = request.POST.getlist('funcName[]');
            Paras       = request.POST.getlist('Paras[]');
            ParaInfo    = request.POST.getlist('ParaInfo[]');
            bpath       = request.POST.get('bpath');
            stfile      = request.POST.get('stfile');
	    pdbfile     = request.POST.get('pdbfile');
            path_output = request.POST.get('path_output');
            path_python = request.POST.get('path_python');
            trjFile     = request.POST.getlist('trjFile[]');
            pbs         = request.POST.get('pbs');
	    num_frame	= request.POST.get('num_frame');
	    num_atoms	= request.POST.get('num_atoms');
	    num_files	= request.POST.get('num_files');
	    num_ps	= request.POST.get('num_ps');


	    #print "*** TRJ FILES ****";
	
            # --- removing white spaces ---
            bpath  = bpath.strip(' \t\n\r');
            stfile = stfile.strip(' \t\n\r');
	    pdbfile = pdbfile.strip(' \t\n\r');
            path_output = path_output.strip(' \t\n\r');
            path_python = path_python.strip(' \t\n\r');
            
            # ---- checkout path: make sure end with '/'
            bpath = eval_path(bpath);
            path_output = eval_path(path_output);
            
	    #print "######## Before Wrap ##############"
	    #print Paras
	    #print ParaInfo
	    
            #--- parsing List ----
            Paras = parseWrapList2(Paras);
            ParaInfo = parseWrapList1(ParaInfo);
            
	    #print "######## after Wrap ##############"
	    #print Paras
	    #print ParaInfo
            #PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__));

            #--- Get unique session ID
            user = request.session['user_id'];
            date = datetime.now().strftime("%Y%m%d%H%M%S%f");
            rndStr = rand_N_letters(6);
            
            #-------------------------------------------
            # creating SESSION_HOME directory
            #-------------------------------------------
            #print "creating directory"
            #print __file__
            
            SESSION_HOME = "{}/media/{}".format(PROJECT_ROOT[0:len(PROJECT_ROOT)-4],user);
            OUTPUT_HOME  = eval_path(SESSION_HOME);
            if (path_output == OUTPUT_HOME):
                #print SESSION_HOME
                if not (os.path.isdir(SESSION_HOME)):
                    #print "Creating directory into {}".format(SESSION_HOME)
                    os.mkdir(SESSION_HOME);
                    
                SESSION_HOME = "{}/{}{}".format(SESSION_HOME, date, rndStr);
                if not (os.path.isdir(SESSION_HOME)):
                    #print "Creating directory into {}".format(SESSION_HOME)
                    os.mkdir(SESSION_HOME);
                else:
                    while not (os.path.isdir(SESSION_HOME)):
                        rndStr = rand_N_letters(6);
                        SESSION_HOME = "{}/{}{}".format(SESSION_HOME, date, rndStr);
                        if not (os.path.isdir(SESSION_HOME)):
                            #print "Creating directory into {}".format(SESSION_HOME)
                            os.mkdir(SESSION_HOME);
                            break;
                OUTPUT_HOME = eval_path(SESSION_HOME);
            else:
                OUTPUT_HOME = path_output;
            
	    #print OUTPUT_HOME
	    
            PBS_HOME = "{}pbs".format(OUTPUT_HOME);
            if not (os.path.isdir(PBS_HOME)):
                #print "creating PBS_HOME: {}".format(PBS_HOME);
                os.mkdir(PBS_HOME);

            SH_HOME  = "{}sh".format(OUTPUT_HOME);
            if not (os.path.isdir(SH_HOME)):
                #print "creating SH_HOME: {}".format(SH_HOME);
                os.mkdir(SH_HOME);
            
            # Wriring variables into binary format
            file_out = "{}para".format(OUTPUT_HOME);
            
            # ---------------------------- Writing PBS
	    #print "Writing PBS....";
            #print "PBS: {}".format(pbs);
            for ifunc in func_name:
		func_idx = func_name.index(ifunc);
		print "func_idx: {}".format(func_idx);
		for cnt_frm in range(len(Paras[func_idx][1])):
		    print "cnt_frm: {}".format(cnt_frm);
		    tmp = "{0}/{1}{2}.pbs".format(PBS_HOME, ifunc, cnt_frm);
		    fid_i = open(tmp, 'w');
		    fid_i.write(pbs);
		    
		    job_name = "#PBS -N {0}{1}\n".format(ifunc[0:5], cnt_frm);
		    fid_i.write(job_name);
		    
		    err_file = "#PBS -e {0}/{1}{2}.err\n".format(PBS_HOME, ifunc, cnt_frm);
		    fid_i.write(err_file);
		    
		    log_file = "#PBS -o {0}/{1}{2}.log\n".format(PBS_HOME, ifunc, cnt_frm);
		    fid_i.write(log_file);
    
		    move_workdir = "cd {}\n".format(ANALYZER_HOME);
		    fid_i.write(move_workdir);
		    
		    run_job = "{0} {1}.py {2} {3}\n".format(path_python, ifunc, file_out, cnt_frm);
		    fid_i.write(run_job);
		    fid_i.close();
                
            # ---------------------------- Writing SHELL SCRIPT
	    print "Writing Shell script....";
            for ifunc in func_name:
		func_idx = func_name.index(ifunc);
		print "func_idx: {}".format(func_idx);
		for cnt_frm in range(len(Paras[func_idx][1])):
		    print "cnt_frm: {}".format(cnt_frm);
		    tmp = "{0}/{1}{2}.sh".format(SH_HOME, ifunc, cnt_frm);
		    fid_i = open(tmp, 'w');
		    
		    def_shell = "#!/bin/bash\n";
		    fid_i.write(def_shell);
    
		    move_workdir = "cd {}\n".format(ANALYZER_HOME);
		    fid_i.write(move_workdir);
		    
		    run_job = "{0} {1}.py {2} {3}\n".format(path_python, ifunc, file_out, cnt_frm);
		    fid_i.write(run_job);
		    fid_i.close();
		    
		    # change script permission to 755
		    os.chmod(tmp, 0755);
            
            
            #print "# ---------------------------- Insert job into a table ---------------------------------"
            #print "HERE works"
            conn = sqlite3.connect(dbName);
            c = conn.cursor();
            
            funcNames = ",".join(func_name);
            stime     = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
            query = """INSERT INTO gui_job (name, proj_id, anaz, status, output, stime, etime) \
                    VALUES ("{0}", {1}, "{2}", "{3}", "{4}", "{5}", "{6}")""".format(job_title, pkey, funcNames, 'SENT', OUTPUT_HOME, stime, 'N/A');
            print query
            c.execute(query);
            conn.commit();
            #print "Job table updated!"
            
            #print "# ---------------------------- Insert parameter into a table ---------------------------------"
            #print "Paras: {}".format(Paras);
            #print "func_name: {}".format(func_name);
            #print "ParaInfo: {}".format(ParaInfo);
            #calculating the most recent Job primary key
            query = """SELECT id FROM gui_job WHERE proj_id = {0} AND stime = "{1}" """.format(pkey, stime);
            #print query
            c.execute(query);
            job_pkey = c.fetchone();
            para_pkeys = [];
            #print job_pkey[0];
            for i in range(len(func_name)):
		print "--------- # of Func name: {}/{}".format(i, len(func_name));
                para_pkey = [];
                for j in range(len(Paras[i])):
		    #print "--------- # of Paras: {}/{}".format(j, len(Paras[i]));
		    for k in range(len(Paras[i][j])):
			#print "--------- # of Paras2: {}/{}".format(k, len(Paras[i][j]));
			query = """INSERT INTO gui_parameter (job_id, anaz, para, val, status) \
				VALUES ({0}, "{1}", "{2}", "{3}", "{4}")""".format(job_pkey[0], func_name[i], ParaInfo[i][j], Paras[i][j][k], 'SENT');
			#print query;
			c.execute(query);
			conn.commit();
                query = """SELECT id FROM gui_parameter WHERE job_id = {0} AND anaz = "{1}" """.format(job_pkey[0], func_name[i]);
                #print query
                c.execute(query);
                tmp_para_pkey = c.fetchall();
                for item in tmp_para_pkey:
                    para_pkey.append(item[0]);
                para_pkeys.append(para_pkey);
                #print "parameter table updated!"
                    
            #print "# ---------------------------- Display tables ---------------------------------"
            #print "Items in gui_job"
            query = "SELECT * from gui_job";
            c.execute(query);
            row = c.fetchall();
            #for item in row:
            #    print item;
                
            #print "Items in gui_parameter"
            query = "SELECT * from gui_parameter";
            c.execute(query);
            row = c.fetchall();
            #for item in row:
            #    print item;

            conn.close();


            #-------------------------------------------
            # Writring input arguments into a file
            #-------------------------------------------
            cdic ={
                'para_pkeys'	    : para_pkeys,
                'job_pkey'          : job_pkey,
                'job_title'         : job_title,
                'pkey'              : pkey,
                'ptitle'            : ptitle,
                'dbName'            : dbName,
                'pbs'               : pbs,
                'date'              : date,
                'session_home'      : SESSION_HOME,
                'output_home'       : OUTPUT_HOME,
                'pbs_home'          : PBS_HOME,
                'media_home'        : MEDIA_HOME,
                'analyzer_home'     : ANALYZER_HOME,
                'base_path'         : bpath,
                'path_output'       : path_output,
                'path_python'       : path_python,
                'structure_file'    : stfile,
		'pdb_file'	    : pdbfile,
                'trajectory'        : trjFile,
                'Paras'             : Paras,
                'funcName'          : func_name,
                'paraInfo'          : ParaInfo,
		'num_frame'	    : num_frame,
		'num_atoms'	    : num_atoms,
		'num_files'	    : num_files,
		'num_ps'	    : num_ps,
            }
            
            #print "works {}".format(PBS_HOME)
            # save dictionary into a file
            #file_out = "{}para".format(OUTPUT_HOME)
            #print "Writing binary file {}".format(file_out);
            fid_out = open(file_out, 'wb');
            pickle.dump(cdic, fid_out);
            fid_out.close();
            
            # ---------------------------- Submit Jobs
            if (machine == 'PBS'):
                print "Run code at {}".format(machine);
                for ifunc in func_name:
		    func_idx = func_name.index(ifunc);
		    for cnt_frm in range(len(Paras[func_idx][1])):
			# Run Script
			fpbs = "{0}/{1}{2}.pbs".format(PBS_HOME, ifunc, cnt_frm);
			print fpbs
			#print "Okay I am sending job to Queue!";
			q_id = sub.check_output(["qsub", fpbs]);
			#print q_id
			Q = q_id.split('.');
			#print "Okay queue id is {}".format(Q[0]);
			# Insert values into gui_outputs
			conn = sqlite3.connect(dbName);
			c    = conn.cursor();
			#uq_func = "{0}{1}".format(ifunc, cnt_frm);
			uq_func = "{0}{1}_{2}".format(ifunc, cnt_frm, Paras[func_idx][2][cnt_frm]);
			print "*** details of function name *****"
			print uq_func
			
			query = """INSERT INTO gui_outputs (job_id, name, status, qid, img, txt, gzip) VALUES ({0}, "{1}", "Queue", {2}, "N/A", "N/A", "N/A")""".format(job_pkey[0], uq_func, Q[0]);
			c.execute(query);
			conn.commit();
			conn.close();
		
		    
            elif (machine == 'Interactive'):
                print "Run code at {}".format(machine);
                for ifunc in func_name:
		    func_idx = func_name.index(ifunc);
		    for cnt_frm in range(len(Paras[func_idx][1])):
			#print "****** func_idx *******"
			#print Paras[func_idx];
			# Insert values into gui_outputs
			uq_func = "{0}{1}".format(ifunc, cnt_frm);
			q_id = 0;			# interactive mode set q_id as 0
			conn = sqlite3.connect(dbName);
			c    = conn.cursor();
			uq_func = "{0}{1}_{2}".format(ifunc, cnt_frm, Paras[func_idx][2][cnt_frm]);
			print "*** details of function name *****"
			print uq_func
			query = """INSERT INTO gui_outputs (job_id, name, status, qid, img, txt, gzip) VALUES ({0}, "{1}", "Sent", {2}, "N/A", "N/A", "N/A")""".format(job_pkey[0], uq_func, q_id);
			#print query
			c.execute(query);
			conn.commit();
			conn.close();
			# Run script
			cmd = "{0}/{1}{2}.sh".format(SH_HOME, ifunc, cnt_frm);
			os.system(cmd);
	    
            return HttpResponse(json.dumps(cdic));


def showImage(request):
    print "### showImage ####";
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    data = request.POST;
    
    if request.is_ajax() and (request.method == 'POST'):
	abs_path = request.POST.get('abs_path');
	print abs_path;
	rel_path = '/static/../../../../tmp/box/box0.png';
	cdioutDic = {
	    'abs_path': abs_path,
	    'rel_path': rel_path,
	}
	return HttpResponse(json.dumps(cdic));
    

def download_path(request, path):
    print "### download_path ####";
    #print path;
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    
    # link the file
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path ) # not FileField instance
    response['Content-Disposition'] = 'attachment; filename={0}'.format(smart_str( os.path.basename( path ) ));

    return response
    
    
    
def makeDownload(request):
    # check out authority
    print "### makeDownload ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    
    #request.session.set_expiry(SESSION_TIME_OUT);
    output_id 	= request.GET.get('id');
    dfield = request.GET.get('dformat');
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    query = """select {0} from gui_outputs where id = {1}""".format(dfield, output_id);
    #print query;
    c.execute(query);
    row = c.fetchone();
    #print "the path of [{0}] in output_id ({1}) is {2}".format(dfield, output_id, row[0]);
    path = row[0];
    
    # link the file
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path ) # not FileField instance
    response['Content-Disposition'] = 'attachment; filename={0}'.format(smart_str( os.path.basename( path ) ));

    return response

def mediaLink(request, file_name):
    print "### mediaLink ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #print "=== I am in mediaLink ==="
    path = '/{}'.format(file_name);
    #print path
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path ) # not FileField instance
    response['Content-Disposition'] = 'attachment; filename={0}'.format(smart_str( os.path.basename( path ) ));

    return response

def wysFileManager(request):
    print "### wysFileManager ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #print request
    c ={
            'output'        : 'okay updated!'
	}
    return HttpResponse(json.dumps(outDic));

def resultView_DBmanager(request):
    print "### resultView_DBmanager ###";
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
    if cmd == 'delete':
        print "OKAY I am in delete DB manager (Result View)"
	table 	= request.POST.get('table');
	tmpIDs	= request.POST.get('IDs');
	flag_del= request.POST.get('del');
	
	# parsing IDs
	tmpIDs = tmpIDs.strip(' \t\n\r');
	listIDs = tmpIDs.split(',');
	print "Let's see what I have got from IDs:"
	print listIDs
	
	IDs = [];
	for num in listIDs:
	    num = num.strip(' \t\n\r');		# remove white space
	    if len(num) > 0:			# remove empty list
		if '-' in num:
		    print "FOUND conataining '-': {}".format(num);
		    tmp = num.split('-');
		    num1 = int(tmp[0]);
		    num2 = int(tmp[1]);
		    if num1 < num2:
			tmp2 = range(num1,num2+1);
		    else:
			tmp2 = range(num2,num1+1);
		    for i in tmp2:
			IDs.append(i);
		else:
		    tmp2 = int(num);
		    IDs.append(tmp2);
	IDs = set(IDs);				# make sure having unique IDs
	IDs = list(IDs);
	
	# deleting gui_project
	if table == 'gui_user':
	    conn = sqlite3.connect(dbName);
	    c = conn.cursor();
	    print "** DELETE FROM {} **".format(table);
	    for i in IDs:
		query = """DELETE FROM {0} where uid = "{1}" """.format(table, i);
		c.execute(query);
		conn.commit();
	    conn.close();

	elif table == 'gui_project':
	    print "** DELETE gui_project **";
	    delProjects(IDs, dbName, flag_del);

	elif table == 'gui_job':
	    print "** DELETE gui_project **";
	    delJobs(IDs, dbName, flag_del);
	    
	elif table == 'gui_outputs':
	    print "** DELETE gui_outputs **";
	    delOutputs(IDs, dbName, flag_del);
	    
	elif table == 'gui_queue':
	    print "** DELETE Queue **";
	    for qid in IDs:
		#print "{} is deleting...\n".format(qid);
		delQue(qid);

	else:
	    conn = sqlite3.connect(dbName);
	    c = conn.cursor();
	    print "** DELETE FROM {} **".format(table);
	    for i in IDs:
		query = "DELETE FROM {0} where id = {1} ".format(table, i);
		c.execute(query);
		conn.commit();
	    conn.close();

        outDic = {
            'fUsers'    : IDs,
        }
    return HttpResponse(json.dumps(outDic));



def dummy_test(request):
    print "### dummy_test ###";
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
    if cmd == 'array_test':
        print "[DUMMY TEST] >> [array_test]"
	outFile = request.POST.getlist('outFile[]');
	segID	= request.POST.getlist('segID[]');
	for f in outFile:
	    print f;
	
	for s in segID:
	    print s;
	    
        outDic = {
            'segID'     : segID,
	    'outFile'	: outFile,
        }
    return HttpResponse(json.dumps(outDic));


def fileSort(request):
    print "### fileSort ###";
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
    if cmd == 'sort_file':
	fList1 = request.POST.getlist('fList1[]');
	fList2 = request.POST.getlist('fList2[]');
	
	print "CALL: sort_str_num()"
	fList1 = sort_str_num(fList1, 'asc');
	fList2 = sort_str_num(fList2, 'asc');

        outDic = {
            'fList1'     : fList1,
	    'fList2'     : fList2,
        }
    if cmd == 'pick_file':
	print "** pick_file **"
	fList  = request.POST.getlist('fList[]');
	stFile=[];
	stFile1 = request.POST.get('stFile');
	stFile.append(stFile1);
	
	edFile = [];
	edFile1 = request.POST.get('edFile');
	edFile.append(edFile1);
	
	# extend file names
	extList = extStrings(fList);
	ext_stFile = extStrings(stFile);
	print "=== ext_stFile ===="
	print ext_stFile[0];
	ext_edFile = extStrings(edFile);
	print "=== ext_edFile ===="
	print ext_edFile[0]
	#
	# get sorted list and index
	listInfo = getSortedList(extList, False);
	sortIdx  = listInfo[0];
	sortList = listInfo[1];
	print sortList
	
	msg = [];
	if ext_stFile[0] in sortList:
	    stIdx = sortList.index(ext_stFile[0]);
	else:
	    stIdx = len(fList)+1;
	    msg.append(stFile);
	    
	if ext_edFile[0] in sortList:
	    edIdx = sortList.index(ext_edFile[0]);
	else:
	    edIdx = len(fList)+1;
	    msg.append(edFile);
	
	sList = [];			# selected list
	rList = [];			# remained list
	
	for i in range(len(fList)):
	    if (i < stIdx) or (i > edIdx):
		rList.append(fList[i]);
	    else:
		sList.append(fList[i]);
	
	outDic = {
	    'sList' 	: sList,
	    'rList'	: rList,
	    'msg'	: msg,
	}
	
    return HttpResponse(json.dumps(outDic));



def viewTable(request, table_name):
    print "### viewTable ###"
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    #print request.GET
        
    if request.GET.get("sidx"):
        sidx    = request.GET["sidx"];
        sord    = request.GET["sord"];
        cpage   = request.GET["page"];
        cpage   = int(cpage);
        maxrow  = request.GET["rows"];
        maxrow  = int(maxrow);    
        
    if cpage == 1:
        st_index = 0;
        ed_index = maxrow;
    else:
        st_index = maxrow * cpage - maxrow;
        ed_index = maxrow * cpage;
    
    #if request.is_ajax() and (request.method == 'POST'):
    print "dbName: {}".format(dbName);
    
    conn = sqlite3.connect(dbName);
    c = conn.cursor();
    
    if (request.GET["_search"] == 'true'):
        sfilter = request.GET["filters"];
        search_dic =json.loads(sfilter);      # convert string to dictionary
        search_rules = search_dic["rules"][0];
        search_field = search_rules["field"];
        search_data = search_rules["data"];
        query = """select * from {0} where {1} like "%{2}%" order by {3} {4}""".format(table_name, search_field, search_data, sidx, sord);
        #print query
    else:   
        query = "select * from {0} order by {1} {2}".format(table_name, sidx, sord);
        #print query
    
    c.execute(query);
    row = c.fetchall();
    conn.close();

    rows = [];
    row_cnt = 0;
    if st_index == 0:
	for item in row:
	    row_cnt = row_cnt + 1;
	    tmp = { "id": str(row_cnt), "cell": item}
	    rows.append(tmp);
    else:
	for item in row:
	    row_cnt = row_cnt + 1;
	    if (row_cnt > st_index):
		tmp = { "id": str(row_cnt), "cell": item}
		rows.append(tmp);
    
    # calculating total number of pages
    tpages = int(math.ceil(float(row_cnt) / float(maxrow)));
    #print "tpages: {}".format(tpages);
    if tpages < 1:
        tpages = 1;
    
    total_pages = tpages;

    outDic = {
            'total'	: total_pages,
            'page'      : cpage,
            'records'   : row_cnt,
            'rows'      : rows,            
        }
    return HttpResponse(json.dumps(outDic));
    
def showTables(request):
    print "### showTables ###";
    # check out authority 
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
        }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )
    else:
	outDic = {
	    'msg' : 'show me table!',
	}
        template = 'gui/tableView.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )



def verifyQuery(request):
    """
    #Testing queries
    # segid PROA and name H* and (prop z >= 5)
    #
    """
    print "### verifyQuery ###";
    # check out authority
    """
    rsec = request.session.get_expiry_age();
    if ('user_id' not in request.session) or (SESSION_TIME_OUT < rsec) or (rsec <= 0):
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
                }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request) )

    #request.session.set_expiry(SESSION_TIME_OUT);
    user_id = request.session['user_id'];
    """
    if request.is_ajax() and (request.method == 'POST'):
        cmd   = request.POST.get('cmd');
    else:
        cmd = 'http';           # connection with URL
        outDic = {
                    'errMsg'	    : 'Session has been expired!',
            }
        template = 'gui/login.html';
        return render_to_response(template, outDic, context_instance = RequestContext(request))
    
	# turning on periodic boundary conditions
	MDAnalysis.core.flags['use_periodic_selections'] = True;
	MDAnalysis.core.flags['use_KDTree_routines'] = False;

    if cmd == 'getStructure':
	print "getStructure!!!"
	query 	    = request.POST.get('query');
	pdbfile     = request.POST.get('pdbfile');
	bpath       = request.POST.get('bpath');
	stfile      = request.POST.get('stfile');
	pdbfile     = request.POST.get('pdbfile');
	trjFile    = request.POST.getlist('trjFile[]');
	
	bpath = bpath.strip(' \t\n\r');
	stfile = stfile.strip(' \t\n\r');
	pdbfile = pdbfile.strip(' \t\n\r');
	trjfile = trjFile[0].strip(' \t\n\r');
	
	stfile = "{0}/{1}".format(bpath, stfile);
	pdbfile = "{0}/{1}".format(bpath, pdbfile);
	trjfile = "{0}/{1}".format(bpath, trjfile);
	
	print "PDB name = '{}'".format(pdbfile);
	
	if (pdbfile[len(pdbfile)-3:] != "pdb"):
	    print "PDB is missing, so now using {}".format(trjfile);
	    pdbfile = trjfile

	#print query
	print stfile
	print pdbfile
	print trjfile
	
	# verifying query
	#print "reading pdb file..."
	u = MDAnalysis.Universe(stfile, trjfile);
	#print "Structure is loaded"
	
	# centering atoms
	MEMB = u.selectAtoms(query);
	u.atoms.translate(-MEMB.centerOfMass());
	
	ucell = u.trajectory[0];
	size_x = "{}".format(ucell.dimensions[0]);
	size_y = "{}".format(ucell.dimensions[1]);
	size_z = "{}".format(ucell.dimensions[2]);
	print "#### size_x, size_y, size_z ####"
	print size_x
	print size_y
	print size_z

	#print "selecting atoms..."
	selAtoms = u.selectAtoms(query);
	#print "DONE!" 
	
	# residue information
	num_residue = selAtoms.numberOfResidues();
	res_names   = selAtoms.resnames();
	uq_resname  = list(set(res_names));
	#print "uq_resname is Okay!"
	
	res_index   = selAtoms.resids();
	uq_resid    = list(set(res_index));
	uq_resid    = np.array(uq_resid).tolist(); # convert numpy int64 to int ==> this cause JSON problems. 
	
	#print "uq_resid is Okay!"
	# integers are converted into int64
	# it can cause problems, so convert it to noraml Python datatype
	#tmpList = [];
	#for i in uq_resid:
	#    tmpList.append(np.asscalar(i))
	#uq_resid = tmpList;
	
	num_atoms   = selAtoms.numberOfAtoms();
	names       = selAtoms.names();
	uq_name     = list(set(names));
	#print "uq_name is Okay!"
	
	segids	    = selAtoms.segids();
	uq_segid    = list(set(segids));
	#print "uq_segid is Okay!"
	
	# extracting types
	types = [];
	for t in selAtoms:
	    types.append(t.type);
	uq_type = list(set(types));
	#print "uq_type is Okay!"
	
	# extracting coordinates
	CRDs = selAtoms.coordinates();
	#crd_min = '{}'.format(round(float(CRDs.min())));
	crd_min = round(float(CRDs.min()));
	#crd_max = '{}'.format(round(float(CRDs.max())));
	crd_max = round(float(CRDs.max()));
	
	outDic = {
		'uq_resname'	: uq_resname,
		'uq_resid'	: uq_resid,
		'uq_name'	: uq_name,
		'uq_segid'	: uq_segid,
		'uq_type'	: uq_type,
		'crd_min'	: crd_min,
		'crd_max'	: crd_max,
		'num_atoms'	: num_atoms,
		'size_x'	: size_x,
		'size_y'	: size_y,
		'size_z'	: size_z,
	    }
	#print outDic
	return HttpResponse(json.dumps(outDic));

    if cmd == 'verify':
	print "Verify!!!"
	query 	    = request.POST.get('query');
	pdbfile     = request.POST.get('pdbfile');
	bpath       = request.POST.get('bpath');
	stfile      = request.POST.get('stfile');
	pdbfile     = request.POST.get('pdbfile');
	trjFile    = request.POST.getlist('trjFile[]');
	
	query = query.strip(' \t\n\r');
	bpath = bpath.strip(' \t\n\r');
	stfile = stfile.strip(' \t\n\r');
	pdbfile = pdbfile.strip(' \t\n\r');
	trjfile = trjFile[0].strip(' \t\n\r');
	
	stfile = "{0}/{1}".format(bpath, stfile);
	pdbfile = "{0}/{1}".format(bpath, pdbfile);
	trjfile = "{0}/{1}".format(bpath, trjfile);

	print "PDB name = '{}'".format(pdbfile);
	
	if (pdbfile[len(pdbfile)-3:] != "pdb"):
	    print "PDB is missing, so now using {}".format(trjfile);
	    pdbfile = trjfile
	
	#print query
	#print stfile
	#print pdbfile
	#print trjFile
	
	# verifying query
	#print "reading psf and pdb file..."
	u = Universe(stfile, pdbfile);
	#print "Structure is loaded"
	
	#print "selecting atoms..."
	selAtoms = u.selectAtoms(query);
	#print "DONE!" 
	
	# residue information
	num_residue = selAtoms.numberOfResidues();
	#print "num_residue...{}".format(num_residue);
	
	res_names   = selAtoms.resnames();
	#print "res_names...{}".format(res_names);
	
	uq_res      = list(set(res_names));
	#print "uq_res...{}".format(uq_res);
	
	res_index   = selAtoms.resids();
	#print "res_index...{}".format(res_index)
	
	num_atoms   = selAtoms.numberOfAtoms();
	#print "num_atoms..{}".format(num_atoms);
	
	names       = selAtoms.names();
	#print "names...{}".format(names);
	
	uq_names    = list(set(names));
	#print "uq_names..{}".format(uq_names);
	
	# coordinate information
	CRDs = selAtoms.coordinates();
	#print "CRDs..{}".format(CRDs);
	
	# type information
	selInfo = "\n# Total Number of selected residues: {}\n".format(num_residue);
	selInfo = "{0}# Selected unique residues: \n".format(selInfo);
	#print selInfo
	
	tmp = "";
	tmp_cnt = 0;
	for res in uq_res:
	    tmp_cnt = tmp_cnt + 1;
	    if (tmp_cnt % 5 == 0):
		tmp = "{0}{1}\n".format(tmp, res);
	    else:
		tmp = "{0}{1}\t".format(tmp, res);
	selInfo = "{0}{1}\n".format(selInfo, tmp);
	selInfo = "{0}\n# Total Number of selected atoms: {1}\n".format(selInfo, num_atoms);
	selInfo = "{0}# Selected unique atoms: \n".format(selInfo);
	tmp = "";
	tmp_cnt = 0;
	for atom in uq_names:
	    tmp_cnt = tmp_cnt + 1;
	    if (tmp_cnt % 5 == 0):
		tmp = "{0}{1}\n".format(tmp, atom);
	    else:
		tmp = "{0}{1}\t".format(tmp, atom);
	selInfo = "{0}{1}\n".format(selInfo, tmp);
	#print selInfo
	#print uq_names;
	
	selInfo = "{0}\n#SEG_ID\tRES_ID\tRES_NAME\tNAME\tTYPE\tX-axis\tY-axis\tZ-axis\n".format(selInfo);
	types = [];
	cnt = 0;
	for t in selAtoms:
	    segid = t.segid;
	    resid = t.resid;
	    resname = t.resname;
	    name = t.name;
	    x = CRDs[cnt][0];
	    y = CRDs[cnt][1];
	    z = CRDs[cnt][2];
	    cnt = cnt + 1;
	    typ = t.type;
	    types.append(typ);
	    selInfo = "{0}{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\r\n".format(selInfo, segid, resid, resname, name, typ, x, y, z);
	uq_types = list(set(types));
	tmp = "# Selected unique types: \n";
	tmp_cnt = 0;
	for tps in uq_types:
	    tmp_cnt = tmp_cnt + 1;
	    if (tmp_cnt % 5 == 0):
		tmp = "{0}\n".format(tmp);
	    else:
		tmp = "{0}{1}\t".format(tmp, tps);
	selInfo = "#Total Number of selected types:{0}\n{1}{2}".format(len(types), tmp, selInfo);
	
	
	outDic = {
		'selInfo'	: selInfo,
		'num_residue'	: num_residue,
		'res_names'	: res_names,
		'resid'		: res_index,
		'num_atoms'	: num_atoms,
		'names'		: names,
		'uq_names'	: uq_names,
	    }
	return HttpResponse(json.dumps(outDic));
	
