#!/usr/bin/env bash

if [ `hostname` != madmax ]; then
    echo You must be logged into 'madmax' to publish.
    exit
fi

PUBLISH_DIR=/var/www/fitnr.com
BUILD_DIR=build
BACKUP_FILE=fitnr.com-`date +%F-%N`.tgz

# Remove any subversion directories
find $BUILD_DIR -name *svn* -type d | xargs rm -rf

# Fixup permissions for files and directories
find $BUILD_DIR -type d | xargs chmod 750
find $BUILD_DIR -type f | xargs chmod 640

tar zcf $BACKUP_FILE $PUBLISH_DIR
rm -rf $PUBLISH_DIR
cp -a $BUILD_DIR $PUBLISH_DIR

chown -Rf louis:www-data $PUBLISH_DIR
