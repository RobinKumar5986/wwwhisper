#!/bin/bash

SCRIPT_DIR="$(cd "$( dirname "$0" )" && pwd)"

source ${SCRIPT_DIR}/config.sh

echo "Installing required packages."
sudo apt-get install git python-virtualenv libssl-dev supervisor

echo "Adding the user ${WWWHISPER_USER}, member of a group ${NGINX_USER}."
sudo adduser --system --ingroup ${NGINX_USER} ${WWWHISPER_USER}

echo "Executing configuration steps as the user ${WWWHISPER_USER}."
sudo -H -g ${NGINX_USER} -u ${WWWHISPER_USER} ${SCRIPT_DIR}/deploy_sudoed.sh

cd "/home/${WWWHISPER_USER}/${NGINX_SRC_DIR}/${NGINX_VERSION}";

echo "Installing nginx."
#sudo make install

echo "Installation finished successfully."
echo "Becoming ${WWWHISPER_USER}."
echo "To configure wwwhisper for a site execute: "
echo " ./add_site_config.py --site_url http[s]://domain_of_the_site --admin_email your_email"
cd "/home/${WWWHISPER_USER}"
sudo su --shell /bin/bash wwwhisper

