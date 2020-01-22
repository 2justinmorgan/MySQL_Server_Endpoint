#!/usr/bin/env python3
import sys, subprocess, inspect, copy, re, json

sql_script = "/var/www/jlm_app/jlm_app/sql.sh"

def usage():
	proc = subprocess.Popen(sql_script,stderr=subprocess.PIPE)
	sql_script_usage = proc.communicate()[1].decode("ascii")
	sql_script_name = sql_script.split(',')[-1]
	msg = sql_script_usage.replace(sql_script_name,__file__)
	sys.stderr.write(msg)

def check_args(argv, argc):
	if argc <= 1:
		usage()
		exit(1)
	# for printing to console (uses stderr)
	if "print" == argv[-1]:
		return [argv[:-1],True]
	return [argv,False]

def my_assert(a, b):
	if a != b:
		msg = ""+str(a)+"\n !=\n"+str(b)+"\n"
		line_rec = inspect.currentframe().f_back.f_lineno
		ret_msg = __file__+": ERR line: "+str(line_rec)+"\n"+msg
		sys.stderr.write('\n------------------------\n')
		sys.stderr.write(ret_msg)
		sys.stderr.write('------------------------\n\n')

def exec_sql_script(f_name, sql_script_argv):
	sql_script_argv_str = ' '.join(sql_script_argv)

	proc = subprocess.Popen(
		[sql_script,sql_script_argv_str],
		stdout=subprocess.PIPE)
	output = proc.stdout.read().decode("ascii")

	return output

# clean_line accepts a messy and spaced-out line/str to then return
# a clean line/str that is comma separated (coordinates are optional)
def clean_line(line):
	items = []

	cleaner_line = ' '.join(line.split())
	for item in cleaner_line.split(','):
		item = item.strip()
		if "NULL" in item:
			continue
		items.append(' '+item.strip(','))

	return ','.join(items)[1:] # to ignore leading whitespace

my_assert(
	clean_line("italy,   calibri,				fresno, 10.3345	-32.9001 \n"),
	"italy, calibri, fresno, 10.3345 -32.9001")
my_assert(
	clean_line("america,	home state,	  home	ville town,	NULL	NULL\n"),
	"america, home state, home ville town")

# create_lines accepts the output from the sql script, which is messy
# and spaced-out, to return an array of comma-separated lines/strs
def create_lines(output):
	lines = []

	for line in output.split('\n'):
		lines.append(clean_line(line))
	lines.pop()

	#lines = list(chain.from_iterable(repeat(i, c) for i, c in Counter(lines)))

	return lines

my_assert(
	create_lines(""),
	[])
my_assert(
	create_lines("cnt,	reg,	cty,	NULL	NULL\n cnt,	reg,	cty,  2.11	-1.5\n"),
	["cnt, reg, cty","cnt, reg, cty, 2.11 -1.5"])	

# invalid_str returns true if any of the strings in 'lst' are equal to 
# or a substring of 'string'
def invalid_str(string, lst):
	for s in lst:
		if s in string:
			return True
	return False

my_assert(invalid_str("ppl",["pear","water melon","juice","orange"]),False)
my_assert(invalid_str(" region , \n",["country","region","city"]),True)

# get_line returns a one line csv "str", derived from the list of
# lines of a section, 'lines', and returns the csv "str" tokenization
def get_csv_list(lines):
	sections = ["country","region","city"]
	csv_list = []

	for line in lines: # remove sql select column title/header
		line = line.replace(',','').strip()
		if re.search('[a-zA-Z]',line) and not invalid_str(line, sections):
			csv_list.append(line.replace('\n',''))

	return csv_list # index -1 to ignore the last added comma

my_assert(
	get_csv_list(["  "," city \n"," san diego  ","san  luis obispo  "]),
	["san diego","san  luis obispo"])
my_assert(
	get_csv_list(["\n \n"," regio n \n","  fresno \n"]),
	["regio n","fresno"])

# get_distinctions will return an array of 3 csv-strings: the sql
# script's output for distinct Country, Region, and City
def get_distinctions(output):
	distinctions = ['Country','Region','City']
	distinctionsObj = {}
	i = 0

	# sections are County, Region, City
	for section in output:
		#section_lines = section.split(',')
		section_lines = section.split('\n')

		# line is a csv "str" tokenized to a csv_list
		line = get_csv_list(section_lines)
		distinctionsObj[distinctions[i]] = line
		i += 1
	
	return distinctionsObj

my_assert(
	get_distinctions([
		"country \n,\namerica,\ndominican republic, \n italy,\n\n",
		"\n region ,\n , \n calibri,\ntexas\n \n \n",
		"\n\n bakersfield, \nbenitos , \n san  diego\n"]),
	{'Country': ['america','dominican republic','italy'],
	'Region': ['calibri','texas'],
	'City': ['bakersfield','benitos','san  diego']})

my_assert(
	get_distinctions([
		"\n  country\n, \namerica,\nunited kingdom,\n australia,\n",
		" \n  \nregion\n,\n  california,\n",
		"\n, \n,city\n,  san luis obispo, \n"]),
	{'Country': ['america','united kingdom','australia'],
	'Region': ['california'],
	'City': ['san luis obispo']})

# meant for "add" queries. See notes inside this function
def make_check_object(output):
	# NOTE: this is super hacky right now. Queries will soon 
	# be done with ORM. But the returned obj is meant for "add" queries
	if "is already in the database" in output:
		return {"existsInDatabase": "true"}
	else:
		return {"existsInDatabase": "false"}
	
def make_object(output):

	if '-|-' not in output:
		return make_check_object(output)

	split_output = output.split('-|-')
	csv_output = split_output[0]
	my_object = {}

	csv_lines = []

	for line in create_lines(csv_output)[1:-1]:
		csv_lines.append(line)

	distinctions = get_distinctions(split_output[1:])

	my_object["results"] = csv_lines
	my_object["filterOptions"] = distinctions

	return my_object

# NOTE: using stderr to not conflict with json stdout printing
def format_print(my_object):
	sys.stderr.write("\n---------------------------\n")
	sys.stderr.write("RESULTS:\n")
	for location in my_object["results"]:
		sys.stderr.write(location+'\n')
	
	sys.stderr.write('\n')
	for filterType in my_object["filterOptions"]:
		sys.stderr.write(filterType+':\n')

		filterTypeLst = my_object["filterOptions"][filterType]
		for filterOption in filterTypeLst:
			sys.stderr.write('  '+filterOption+'\n')
	sys.stderr.write("---------------------------\n\n")

def main():
	args = check_args(sys.argv, len(sys.argv))
	sql_argv = args[0][1:]
	to_print = args[1] # boolean
	
	sql_script_output = exec_sql_script(sql_script,sql_argv)

	my_object = make_object(sql_script_output)

	# NOTE: this prints to stdout
	print(json.dumps(my_object))

	# prints object for CLI (enter 'p' after command)
	# NOTE: this prints to stderr
	if to_print:
		format_print(my_object)
	
main()



