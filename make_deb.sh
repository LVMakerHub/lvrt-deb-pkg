#! /bin/bash

set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 IMAGE_TAR_FILE"
  exit 1
fi

PKG_NAME=lvrt-schroot
PKG_VER=14.1
PKG_REV=4
PKG_DIR=$PKG_NAME\_$PKG_VER-$PKG_REV

SYSTEMD_SERVICE_DIR=$PKG_DIR/etc/systemd/system/multi-user.target.wants
CHROOT_DIR=$PKG_DIR/srv/chroot/labview

# Add schroot session creation script
mkdir -p $PKG_DIR/usr/sbin
cp src/schroot-lv-start.sh $PKG_DIR/usr/sbin/.

# Add systemd service file to start schroot
mkdir -p $SYSTEMD_SERVICE_DIR
cp src/labview.service $SYSTEMD_SERVICE_DIR/.

# Add systemd service file to start emulated sys web server
cp src/nisysserver.service $SYSTEMD_SERVICE_DIR/.

# Add NI Sys Web Server emulator script
cp src/NISysServer.py $PKG_DIR/usr/sbin/.

# Create schroot configuration
cp -r src/schroot $PKG_DIR/etc/

# Change permissions
sudo chown -R root:root $PKG_DIR/*

# Create chroot dir
mkdir -p $CHROOT_DIR
if [[ $1 == *tar.bz2 ]]; then
	tar xjf $1 -C $CHROOT_DIR
elif [[ $1 == *tar.gz ]]; then
	tar xzf $1 -C $CHROOT_DIR
fi

# Do a little customization to the chroot
mkdir $CHROOT_DIR/root
rm -r $CHROOT_DIR/home/root

# Create control file and maintainer scripts
mkdir $PKG_DIR/DEBIAN
cp src/control $PKG_DIR/DEBIAN/.
cp src/post* $PKG_DIR/DEBIAN/.
cp src/pre* $PKG_DIR/DEBIAN/.

# Create the package
dpkg-deb --build $PKG_DIR

#cleanup
sudo rm -rf $PKG_DIR
