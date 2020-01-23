#!/bin/bash 

py="${HOME}/py/bin/python"
pip="${HOME}/py/bin/pip"
cythonize="${HOME}/py/bin/cythonize"

CRED_PATH="${HOME}/svg/pysrc"
CRED_FNAME="credentials"
CRED_USERNAME="duanuys"
CRED_PASSWORD="Dawie2018"
PY_VERSION="3"
echo $CRED_PATH, $CRED_FNAME
# write native python func that checks credentials
printf "%s\n" \
  "def check_credentials(name, password):" \
  "    if name != '${CRED_USERNAME}':" \
  "        return False" \
  "    if password != '${CRED_PASSWORD}':" \
  "        return False" \
  "    return True" \
  > $CRED_PATH/$CRED_FNAME.pyx
  
  # use cython to convert to *.c
 $cythonize $CRED_PATH/$CRED_FNAME.pyx -$PY_VERSION -i
 
  # now clean up files that we don't need.
  rm $CRED_PATH/$CRED_FNAME.pyx
  rm $CRED_PATH/$CRED_FNAME.c