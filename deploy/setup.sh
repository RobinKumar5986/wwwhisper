#!/bin/bash

# Exit if any command fails.
set -e

SCRIPT_DIR="$(cd "$( dirname "$0" )" && pwd)"
WWWHISPER_ROOT_DIR=${SCRIPT_DIR}/..

# User and group to run nginx as (www-data is Debian/Ubuntu
# convention). This user should exists.
NGINX_USER=www-data
# Latest stable release of nginx to download.
NGINX_VERSION="nginx-1.2.2"
# Where in $WWWHISPER_ROOT_DIRy should nginx source be put.
NGINX_SRC_DIR=nginx_src

echo "Installing required system packages"
sudo apt-get install python-virtualenv libssl-dev supervisor

cd ${WWWHISPER_ROOT_DIR}

echo "Initializing virtual environment."
virtualenv virtualenv
source virtualenv/bin/activate

echo "Installing packages required in the virtual environment."
pip install -r ./requirements.txt

# You may want to disable or modify following steps if you already
# have nginx compilled from source. Just modify your build scripts to
# ensure nginx includes modules required by wwwhisper:
#    auth_request: Generic authentication module written by Maxin Dounin.
#    http_ssl_module: Strongly recomended, unless you are protecting
#        access to something very non-sensitive.
#    http_sub_module: Recommended, allows to insert a small iframe in a
#        corner of each protected http page. The iframe contains user's
#        email and a button to sign out.

echo "Downloading and unpacing sources of ${NGINX_VERSION}."
mkdir ${NGINX_SRC_DIR}
cd ${NGINX_SRC_DIR}
wget http://nginx.org/download/${NGINX_VERSION}.tar.gz
tar xvfz ${NGINX_VERSION}.tar.gz
cd ${NGINX_VERSION}

echo "Cloning auth-request module."
git clone https://github.com/PiotrSikora/ngx_http_auth_request_module.git

echo "Configuring nginx with required modules."
# If you want to 
./configure --add-module=./ngx_http_auth_request_module/ \
    --prefix=/usr/local/nginx/ --with-http_ssl_module --with-http_sub_module \
    --user=${NGINX_USER} --group=${NGINX_USER} --sbin-path=/usr/local/sbin

echo "Compiling nginx."
make

echo "Installing nginx."
sudo make install

echo "Installation finished successfully."
echo "To configure wwwhisper for a site execute: "
echo " ./add_site_config.py --site_url http[s]://domain_of_the_site --admin_email your_email"


