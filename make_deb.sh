#! /bin/bash

set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 IMAGE_TAR_FILE"
  exit 1
fi
DFLT_IMGFILE="build/tmp/deploy/images/generic-armv7a/core-image-minimal-chroot-generic-armv7a.tar.gz"
IMAGE_TAR="$1"
if [ -d "$IMAGE_TAR" -a -f "$IMAGE_TAR/$DFLT_IMGFILE" ]; then
	IMAGE_TAR="$IMAGE_TAR/$DFLT_IMGFILE"
fi
if [ ! -f "$IMAGE_TAR" ]; then
	echo "$0: $IMAGE_TAR does not exist"
	exit 1
fi

PKG_NAME=lvrt25-schroot
PKG_VER=25.1.0
PKG_REV=2
PKG_DIR=$PKG_NAME\_$PKG_VER-$PKG_REV
REPO_DIR=debian

SYSTEMD_SERVICE_DIR=$PKG_DIR/etc/systemd/system
SYSTEMD_SERVICE_MUT_DIR=$SYSTEMD_SERVICE_DIR/multi-user.target.wants
CHROOT_DIR=$PKG_DIR/srv/chroot/labview

sudo rm -rf $PKG_DIR

# Add schroot session creation script
mkdir -p $PKG_DIR/usr/sbin
cp src/schroot-lv-start.sh $PKG_DIR/usr/sbin/.

# Add systemd service file to start schroot
mkdir -p $SYSTEMD_SERVICE_DIR
mkdir -p $SYSTEMD_SERVICE_MUT_DIR
cp src/labview.service $SYSTEMD_SERVICE_DIR/
rm -f $SYSTEMD_SERVICE_MUT_DIR/labview.service
ln -sf /etc/systemd/system/labview.service $SYSTEMD_SERVICE_MUT_DIR/labview.service

# Add systemd service file to start emulated sys web server
cp src/nisysserver.service $SYSTEMD_SERVICE_DIR/
rm -f $SYSTEMD_SERVICE_MUT_DIR/nisysserver.service
ln -sf /etc/systemd/system/nisysserver.service $SYSTEMD_SERVICE_MUT_DIR/nisysserver.service

cp src/linxioserver-tcp.service $SYSTEMD_SERVICE_DIR/
cp src/linxioserver-serial.service $SYSTEMD_SERVICE_DIR/

# Add NI Sys Web Server emulator script
cp src/NISysServer.py $PKG_DIR/usr/sbin/
chmod 755 $PKG_DIR/usr/sbin/NISysServer.py

# Create schroot configuration
cp -r src/schroot $PKG_DIR/etc/

# Add license info and man pages
mkdir -p $PKG_DIR/usr/share/doc/labview
cp src/LICENSE $PKG_DIR/usr/share/doc/labview/.
mkdir -p $PKG_DIR/usr/share/man/man5
cp src/labview.5 $PKG_DIR/usr/share/man/man5/.
gzip $PKG_DIR/usr/share/man/man5/labview.5
cp src/lvrt.5 $PKG_DIR/usr/share/man/man5/.
gzip $PKG_DIR/usr/share/man/man5/lvrt.5

# Change permissions
sudo chown -R root:root $PKG_DIR/*

# Create chroot dir
mkdir -p $CHROOT_DIR
if [[ "$IMAGE_TAR" == *tar.bz2 ]]; then
	tar xjf "$IMAGE_TAR" -C $CHROOT_DIR
elif [[ "$IMAGE_TAR" == *tar.gz ]]; then
	tar xzf "$IMAGE_TAR" -C $CHROOT_DIR
else
	echo "$0: Error: Can't extract file $IMAGE_TAR"
	exit 1
fi

# Do a little customization to the chroot
mkdir $CHROOT_DIR/root
rm -r $CHROOT_DIR/home/root

function create_package() {
	# Create control file and maintainer scripts
	mkdir $PKG_DIR/DEBIAN
	sed -e 's/VERSION/'$PKG_VER-$PKG_REV'/' -e 's/NAME/'$PKG_NAME'/'  -e 's/ARCH/'$1'/' src/control > $PKG_DIR/DEBIAN/control
	cp src/post* $PKG_DIR/DEBIAN/.
	cp src/pre* $PKG_DIR/DEBIAN/.

	# Create the package
	PACKAGE_FILE="${PKG_NAME}_${PKG_VER}-${PKG_REV}_$1.deb"
	dpkg-deb -Zgzip --build $PKG_DIR "$PACKAGE_FILE"

	# Cleanup
	rm -rf $PKG_DIR/DEBIAN
}

# Create packages for both 32-bit and 64-bit architectures
create_package "armhf"
create_package "arm64"

# Create the repo
mkdir -p $REPO_DIR/binary
cp $PKG_DIR_*.deb $REPO_DIR/binary/.
cd $REPO_DIR
sudo dpkg-scanpackages -m binary /dev/null > binary/Packages
sudo chown $USER binary/Packages
cd binary
rm -f Packages.gz
gzip Packages

#cleanup
sudo rm -rf $PKG_DIR
