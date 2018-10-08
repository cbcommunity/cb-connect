# Administrative scripts

There is one script here: `usermanager` which automates the process of creating
users in the Cb Response and Cb Protection servers based on a CSV file with
email and password columns (see the example `userlist.csv` file in this directory)

To use this script:

	python usermanager --profile devday-admin bulkadd -f ~/useraccounts.csv 
	python usermanager --profile devday-admin print -f ~/useraccounts.csv 

