#!/bin/bash

outfile="/var/www/jlm_app/jlm_app/data.csv"
outfile_format="fields terminated by ',' lines terminated by '\n'"

function usage() {
	>&2 echo "Usage: $0 <function>,[country],[region],[city],[url],[lng],[lat]"
}

# check args/usage
if [ $# -le 0 ]
then
	usage
	exit 1
fi	

IFS=',' read -ra INPUT <<< $@
task=${INPUT[0]}
country='"'${INPUT[1]}',"'
region='"'${INPUT[2]}',"'
city='"'${INPUT[3]}',"'
url='"'${INPUT[4]}'"'
lng=${INPUT[5]}
lat=${INPUT[6]}

# valid tasks
tasks=(check all all* add remove coordinates quantity)

separator="select '-|-' as '';"

# for sql conditionals
cty='city = '$city
reg='region = '$region
cnt='country = '$country

login='mysql -u root -p"dbup101"'

case "$task" in
	# returns all locations that match specified metrics "$city",
	# "$region", and/or "$country". Empty returns are possible
	"all")
		format='country, region, city, lng, lat'
		conditionals=""

		# this is a quick/lazy way to utilize the "dynamic-ness"
		# of many possible sql queries
		if [[ $city != '","' ]]
		then
			conditionals="city = $city and"
		fi
		if [[ $region != '","' ]]
		then
			temp=$conditionals
			conditionals="$temp region = $region and"
		fi
		if [[ $country != '","' ]]
		then
			temp=$conditionals
			conditionals="$conditionals country = $country"
		else
			conditionals="${conditionals[@]::-3}"
		fi

		mysql -u root --batch -p"dbup101" << EOF
		use jlm_app;
		select distinct country, region, city, lng, lat 
		from locations where $conditionals
		order by country asc, region asc, city asc;
		$separator
		select distinct country from locations
		where $conditionals order by country asc; 
		$separator
		select distinct region from locations
		where $conditionals order by region asc; 
		$separator
		select distinct city from locations
		where $conditionals order by city asc; 
EOF
		;;
	# returns all locations in the database
	"all*")
		format='country, region, city, lng, lat'
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		select distinct $format from locations
		order by country asc, region asc, city asc;
		$separator
		select distinct country from locations
		order by country asc;
		$separator
		select distinct region from locations
		order by region asc;
		$separator
		select distinct city from locations
		order by city asc;
EOF
		;;
	# checks if the specified location exists in the DB
	"check")
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		select country, region, city from locations
		where $cty and $reg and $cnt;
EOF
		;;
	# adds the specific location of the city name "$city"
	"add")
		ARGS="${country//\"}${region//\"}${city//\"}"

		# checks if location exists in DB, only adds if it DNE 
		if [[ "$($0 check,$ARGS)" == "" ]] # ("" == DNE)
		then
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		insert into locations (city,region,country,url)
		values ($city, $region, $country, $url);
EOF
		else
		echo Location \" $ARGS \" is already in the database!
		fi
		;;
	# removes all occurences of location, should be only 1
	"remove")
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		delete from locations where $cty and $reg and $cnt;
EOF
		;;
	# adds the lng and lat of specified location, does nothing
	# if the specified location DNE
	"coordinates")
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		update locations
		set lng = $lng, lat = $lat
		where $cty and $reg and $cnt;
EOF
		;;		
	# returns the total number of locations in the DB
	"quantity")
		mysql -u root -p"dbup101" << EOF
		use jlm_app;
		select count(*) from locations;
EOF
		;;
	# outputs to locations.csv, i.e. "region: maine" outputs all 
	# locations with a region of "maine" to locations.csv
	#"outfile")
	#	cty=
	*)
		usage
		>&2 echo "$0:"
		>&2 echo "  \"$task\" is an invalid function"
		>&2 echo "  valid functions are [ ${tasks[@]} ]"
		;;
		
esac
