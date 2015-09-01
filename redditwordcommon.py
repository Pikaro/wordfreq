# Basic imports

import sys,json,os,urllib,re
from time import time,sleep
from contextlib import closing
import sqlite3
import hashlib

REDDIT_REQUIRED_SLEEP = 2
CONFDIR='/etc/redditwordcount'

DATADIR=CONFDIR+'/data'
FLAIRDIR=DATADIR+'/flairs'
BACKUPDIR=CONFDIR+'/backup'
RESULTDIR=CONFDIR+'/results'

def touch(name):
	with open(name,'a'):
		os.utime(name, None)

def conffile(name):
	name = os.path.join(CONFDIR,name)
	if not os.path.exists(name):
		touch(name)
	return name
def datafile(name):
	name = os.path.join(DATADIR,name)
	if not os.path.exists(name):
		touch(name)
	return name
def flairfile(name):
	name = os.path.join(FLAIRDIR,name)
	if not os.path.exists(name):
		touch(name)
	return name
def backupfile(name):
	name = os.path.join(BACKUPDIR,name)
	if not os.path.exists(name):
		touch(name)
	return name
def resultfile(name):
	name = os.path.join(RESULTDIR,name)
	if not os.path.exists(name):
		touch(name)
	return name

def backup(what):
	os.system('cp '+what+' '+backupfile(what.split('/')[-1]))

def read_json(where,aswhat=dict):
	if not os.path.exists(where):
		touch(where)
	with closing(open(where)) as f:
		return json.load(f)

def write_json(where,what,aswhat=dict,linebreak='\n'):
	what = json.dumps(what, separators=(',',':'))
	bracketlevel=0
	index = 0
	while index < len(what):
		if what[index] == ',' and bracketlevel == 1:
			what = what[:index+1] + linebreak + what[index+1:]
		elif what[index] == '{' or what[index] == '[':
			bracketlevel += 1
		elif what[index] == '}' or what[index] == ']':
			bracketlevel -= 1
		index += 1
	if aswhat is dict:		
		what='{'+linebreak+what[1:-1]+linebreak+'}'
	else:
		what='['+linebreak+what[1:-1]+linebreak+']'

	with closing(open(where,'w')) as f:
		f.write(what)

def read_data(where):
	if not os.path.exists(where):
		touch(where)
	with closing(open(where)) as f:
		return f.read()

def read_structured_data(where):
	return read_data(where).strip().splitlines()

def write_data(where,what):
	with closing(open(where,'w')) as f:
		f.write(what)

# Tries to read a URL with a JSON object behind it x times
def get_json_from_url(url, retries=3, raw=False):
	failed = 0
	while True:
		try:
			if raw:
				return json.load(urllib.urlopen(url))
			else:
				return json.load(urllib.urlopen(url))['data']
		except (IOError, KeyError, ValueError):
			print "  Connection attempt failed."
			failed += 1
			if failed == 3:
				print "Third connection attempt in a row failed, or reddit is down or overloaded right now!"
				exit(1)
			sleep(REDDIT_REQUIRED_SLEEP*3)

wordforms_regex = re.compile("ed$|ing$|s$",re.UNICODE)

def make_mostcommon():
	global mostcommon, mostcommon_regex, wordforms_regex
	mostcommon = [line.strip() for line in read_data(conffile('mostcommon')).splitlines()]
	mostcommon_regex = read_data(conffile('mostcommon_regex')).splitlines()
	mostcommon_regex = [k for k in mostcommon_regex if k]
	mostcommon_regex = '|'.join(mostcommon_regex)
	if mostcommon_regex:
		mostcommon_regex = re.compile(mostcommon_regex)
	else:
		mostcommon_regex = re.compile('THISMATCHESNOTHING')

mostcommon = None
def invalid_word(word):
	if not mostcommon: make_mostcommon()	
	return word in mostcommon or wordforms_regex.sub('',word) in mostcommon or mostcommon_regex.match(word) or len(word)>12

