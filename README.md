# Dependencies
* sudo apt-get install libffi-dev
* sudo apt-get install python-dev

# Installation
## Create python virtualenv for packages 
* sudo pip install virtualenv
* cd project_folder
* virtualenv venv
* source ./venv/bin/activate
* pip install -r requirements.txt

# How to use
* Modify upload_files.sh to upload new packages
* Modify test-upgrade.sh to use new package files
* Modify test-script.sh to properly test a proxy after upgrade
* bash upload_files.sh PROXY_SERVER
* ./rs upgrade test-upgrade.sh test-script.sh PROXY_SERVER
