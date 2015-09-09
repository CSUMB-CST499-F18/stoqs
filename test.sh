#!/bin/bash
# Do database operations to create default database and create fixture for testing
# Designed for re-running on development system - ignore errors in Vagrant and Travis-ci
# Pass the stoqsadm password as an argument on first execution in order to create the
# stoqsadm user; it must match what's in DATABASE_URL.  Must also set MAPSERVER_HOST.
# Make sure none of these are set: STATIC_FILES, STATIC_URL, MEDIA_FILES, MEDIA_URL.

psql -c "CREATE USER stoqsadm WITH PASSWORD '$1';" -U postgres
psql -c "DROP DATABASE stoqs;" -U postgres
psql -c "CREATE DATABASE stoqs owner=stoqsadm template=template_postgis;" -U postgres
psql -c "ALTER DATABASE stoqs SET TIMEZONE='GMT';" -U postgres

# DATABASE_URL environment variable must be set outside of this script
stoqs/manage.py makemigrations stoqs --settings=config.settings.ci --noinput
stoqs/manage.py migrate --settings=config.settings.ci --noinput --database=default
psql -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO stoqsadm;" -U postgres -d stoqs

# Assume starting in project home (stoqsgit) directory, get bathymetry, and load data
cd stoqs
wget -q -N -O loaders/Monterey25.grd http://stoqs.mbari.org/terrain/Monterey25.grd
coverage run --include="loaders/__in*,loaders/DAP*,loaders/Samp*" loaders/loadTestData.py

# Label some data in the test database
coverage run -a --include="contrib/analysis/classify.py" contrib/analysis/classify.py \
  --createLabels --groupName Plankton --database default  --platform dorado \
  --inputs bbp700 fl700_uncorr --discriminator salinity --labels diatom dino1 dino2 sediment \
  --mins 33.33 33.65 33.70 33.75 --maxes 33.65 33.70 33.75 33.93 -v

# Run tests using the continuous integration setting
# test_stoqs database created and dropped by role of the shell account using Test framework's DB names
./manage.py dumpdata --settings=config.settings.ci stoqs > stoqs/fixtures/stoqs_test_data.json
echo "Unit tests..."
coverage run -a --source=utils,stoqs manage.py test stoqs.tests.unit_tests --settings=config.settings.ci
unit_tests_status=$?

# Run the development server in the background for the functional tests
coverage run -a --source=utils,stoqs manage.py runserver --noreload \
    --settings=config.settings.ci > /tmp/functional_tests_server.log 2>&1 &
pid=$!
echo "Functional test with development server running as pid = $pid ..."
./manage.py test stoqs.tests.functional_tests --settings=config.settings.ci
ps -ef | grep $pid
echo "Trying to kill with TERM signal..."
/usr/bin/kill -s TERM $pid
ps -ef | grep $pid
##cat /tmp/functional_tests_server.log
tools/removeTmpFiles.sh > /dev/null 2>&1

# Report results of unit and functional tests
coverage report -m
cd ..
exit $unit_tests_status
