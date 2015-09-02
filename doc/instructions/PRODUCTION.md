PRODUCTION
==========

Notes for installing STOQS on a production server

STOQS is configured to be installed on your own self-hosted web server or on a 
Platform as a Service (PaaS) provider, such as Heroku. It follows
[The Twelve-Factor App](http://12factor.net/) guidelines with deployment 
settings placed in environment variables.  Unless otherwise noted all commands
should be executed from a regular user account that you will use to manage
the stoqs application, e.g. an account something like USER='stoqsadm'.

### Hosting STOQS on your own Nginx web server:

1. On your server install nginx and configure to start (you may configure nginx
   by editing the /etc/nginx/conf.d/default.conf file):

        sudo yum install nginx
        sudo chkconfig nginx on
        sudo /sbin/service nginx start

2. Clone STOQS to a local writable directory on your server. A good practice
   is to not push any changes from a production server back to the repository,
   therefore our clone can be read-only without any ssh keys configured, e.g.:

        export STOQS_HOME=/opt/stoqsgit
        cd `dirname $STOQS_HOME`
        git clone https://github.com/stoqs/stoqs.git stoqsgit

3. Provision your server: 

    * Start with a system provisioned with a `Vagrant up --provider virtualbox` command
    * Install all the required software using provision.sh as a guide
    * Use a server that already has much of the required software installed
    * There are many other ways, including Docker, for setting up the required services

4. Create a virtualenv using the executable associated with Python 2.7, install 
   the production requirements, and setup environment for server with multiple
   versions of Postgresql installed:
   
        cd $STOQS_HOME 
        /usr/local/bin/virtualenv venv-stoqs
        source venv-stoqs/bin/activate
        ./setup.sh production
        export PATH=/usr/pgsql-9.4/bin:$PATH
        alias psql='psql -p 5433'   # For postgresql server running on port 5433

5. As privileged 'postgres' user create default stoqs database:

        /bin/su postgres
        export PATH=/usr/pgsql-9.4/bin:$PATH
        alias psql='psql -p 5433'   # For postgresql server running on port 5433
        psql -c "CREATE DATABASE stoqs owner=stoqsadm template=template_postgis;"
        psql -c "ALTER DATABASE stoqs SET TIMEZONE='GMT';"

6. As regular 'stoqsadm' user initialize and load the default stoqs database:

        export DATABASE_URL="postgis://<dbuser>:<pw>@<host>:<port>/stoqs"
        stoqs/manage.py makemigrations stoqs --settings=config.settings.local --noinput
        stoqs/manage.py migrate --settings=config.settings.local --noinput --database=default
        wget -q -N -O stoqs/loaders/Monterey25.grd http://stoqs.mbari.org/terrain/Monterey25.grd
        stoqs/loaders/loadTestData.py

7. Copy the file $STOQS_HOME/stoqs/stoqs_nginx.conf to a file that will be
   specific for your system and edit it to and change the server_name
   and location settings for your server.  There are absolute directory paths in 
   this file; make sure they refer to paths on your server, e.g.:

        cp $STOQS_HOME/stoqs/stoqs_nginx.conf $STOQS_HOME/stoqs/stoqs_nginx_kraken.conf
        vi $STOQS_HOME/stoqs/stoqs_nginx_kraken.conf

8. Create a symlink to the above .conf file from the nginx config directory, e.g.:

        sudo ln -s $STOQS_HOME/stoqs/stoqs_nginx_kraken.conf /etc/nginx/conf.d

9. Create the media and static web directories and copy the static files to the 
   production web server location. The $STATIC_ROOT directory must be writable 
   by the user that executes the `collectstatic` command:

        sudo mkdir /usr/share/nginx/html/media
        sudo mkdir /usr/share/nginx/html/static
        sudo chown $USER /usr/share/nginx/html/static
        export STATIC_ROOT=/usr/share/nginx/html/static
        stoqs/manage.py collectstatic

10. Create the $MEDIA_ROOT/sections and $MEDIA_ROOT/parameterparameter
    directories and set permissions for writing by the web process. 
    (They are are the location for graphics produced by the STOQS UI.):

        export MEDIA_ROOT=/usr/share/nginx/html/media
        sudo mkdir $MEDIA_ROOT/sections
        sudo mkdir $MEDIA_ROOT/parameterparameter
        sudo chown -R $USER /usr/share/nginx/html/media
        sudo chmod 733 $MEDIA_ROOT/sections
        sudo chmod 733 $MEDIA_ROOT/parameterparameter

11. Start the stoqs application (replacing <dbuser> <pw> <host> <port> and
    <mapserver_ip_address> with your values, and with all your 
    campaigns/databases separated by commas assigned to STOQS_CAMPAIGNS), e.g.:

        export STATIC_ROOT=/usr/share/nginx/html/static
        export MEDIA_ROOT=/usr/share/nginx/html/media
        export DATABASE_URL="postgis://<dbuser>:<pw>@<host>:<port>/stoqs"
        export MAPSERVER_HOST="<mapserver_ip_address>"
        export STOQS_CAMPAIGNS="stoqs_beds_canyon_events_t,stoqs_may2015"
        export GDAL_DATA=/usr/share/gdal
        cd $STOQS_HOME/stoqs
        uwsgi --socket :8001 --module wsgi:application

12. Test the STOQS user interface at:

        http://<server_name>/


