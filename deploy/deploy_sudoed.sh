#!/bin/bash

SCRIPT_DIR="$(cd "$( dirname "$0" )" && pwd)"

source ${SCRIPT_DIR}/config.sh

cd ${HOME}

echo "Cloning wwwhisper project to $(pwd)."
git clone https://github.com/wrr/wwwhisper.git .

echo "Initializing virtual environment."
virtualenv virtualenv
source virtualenv/bin/activate

echo "Installing packages required in the virtual environment."
pip install -r ./requirements.txt

# 1. Nginx setup.
#  wwwhisper requires following nginx modules:
#    auth_request: Generic authentication module written by Maxin Dounin.

#    http_ssl_module: Strongly recomended, unless you are protecting
#    access to something very non-sensitive.

#    http_sub_module: Recommended, allows to insert a small iframe in a
#    corner of each protected http page. The iframe contains user's
#    email and a button to sign out.

echo "Downloading and unpacing sources of ${NGINX_VERSION}."
mkdir ${NGINX_SRC_DIR}
cd ${NGINX_SRC_DIR}
wget http://nginx.org/download/${NGINX_VERSION}.tar.gz
tar xvfz ${NGINX_VERSION}.tar.gz
cd ${NGINX_VERSION}

echo "Cloning auth-request module."
git clone https://github.com/PiotrSikora/ngx_http_auth_request_module.git

echo "Configuring nginx with required modules."
./configure --add-module=./ngx_http_auth_request_module/ \
    --prefix=/usr//local/nginx/ --with-http_ssl_module --with-http_sub_module \
    --user=www-data --group=www-data --sbin-path=/usr/local/sbin

echo "Compiling nginx."
make
