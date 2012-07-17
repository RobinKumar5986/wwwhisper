
# User to run wwwhisper as (should not exist).
WWWHISPER_USER=wwwhisper

# User and group to run nginx as (www-data is Debian/Ubuntu
# convention). This user should exists.
NGINX_USER=www-data
# Latest stable release of nginx to download.
NGINX_VERSION="nginx-1.2.2"
# Where in $WWWHISPER_USER home directory should nginx source be put.
NGINX_SRC_DIR=nginx_src

# Exit if any command fails.
set -e
