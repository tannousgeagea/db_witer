#!/bin/bash
set -e

/bin/bash -c "python3 /home/$user/src/waste_db_writer/manage.py makemigrations"
/bin/bash -c "python3 /home/$user/src/waste_db_writer/manage.py migrate"
/bin/bash -c "python3 /home/$user/src/waste_db_writer/manage.py create_superuser"

sudo -E supervisord -n -c /etc/supervisord.conf