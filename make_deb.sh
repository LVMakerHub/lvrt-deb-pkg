#! /bin/bash

set -e

if [ $# -ne 1 ]; then
  echo "Invalid argument"
  exit 1
fi

PKG_NAME=lvrt-schroot
PKG_VER=14.1
PKG_REV=2
PKG_DIR=$PKG_NAME\_$PKG_VER-$PKG_REV

SYSTEMD_SERVICE_DIR=$PKG_DIR/etc/systemd/system/multi-user.target.wants
CHROOT_DIR=$PKG_DIR/srv/chroot/labview

# Add systemd service file to start schroot
mkdir -p $SYSTEMD_SERVICE_DIR
cp src/labview.service $SYSTEMD_SERVICE_DIR/.

# Create schroot configuration
cp -r src/schroot $PKG_DIR/etc/

# Change permissions
sudo chown -R root:root $PKG_DIR/*

# Create chroot dir
mkdir -p $CHROOT_DIR
tar xjf $1 -C $CHROOT_DIR

# Do a little customization to the chroot
mkdir $CHROOT_DIR/root
rm -r $CHROOT_DIR/home/root

# Create control file
mkdir $PKG_DIR/DEBIAN
cp src/control $PKG_DIR/DEBIAN/.

# Create the package
dpkg-deb --build $PKG_DIR

#cleanup
sudo rm -rf $PKG_DIR


