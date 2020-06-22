#!/bin/bash
set -e

# Make sure inputs are correct
if [ $# -lt 1 ]; then
	echo "Usage: $0 IMAGE_FILE [LVRT_DEB_FILE]"
	exit 1
fi
IMAGE_FILE=$1
DEB_FILE=""
DEB_PATH=""
if [ $# -eq 2 ]; then
	DEB_PATH=$2
	DEB_FILE=$(basename $2)
fi

LVRT_PKG=lvrt20-schroot
TMP_DIR=./tmp
mkdir -p $TMP_DIR
MNT_DIR=$TMP_DIR/mnt
mkdir -p $MNT_DIR

OUTPUT_ZIP_FILE=$LVRT_PKG"-"$(basename $IMAGE_FILE)

# Make sure the required tools are installed
function missing_pkgs() {
	echo "One or more required dependencies are missing"
	echo "Install with 'sudo apt install qemu qemu-user-static binfmt-support systemd-container'"
}

if ! which qemu-arm-static > /dev/null; then
	missing_pkgs
	exit 1
fi
if ! which update-binfmts > /dev/null; then
        missing_pkgs
        exit 1
fi
if ! which systemd-nspawn > /dev/null; then
        missing_pkgs
        exit 1
fi

# unpack image
if [[ $IMAGE_FILE == *.zip ]]; then
	echo "Unzipping $IMAGE_FILE"
	unzip $IMAGE_FILE -d $TMP_DIR
	IMAGE_FILE=`ls $TMP_DIR | grep -e \.img$`
elif [[ $IMAGE_FILE == *.xz ]]; then
	echo "Un-xzing $IMAGE_FILE"
	cp $IMAGE_FILE $TMP_DIR/.
	xz -d $TMP_DIR/$(basename $IMAGE_FILE)
	# xz will delete the archive after decompressing
	IMAGE_FILE=`ls $TMP_DIR | grep -e \.img$`
	OUTPUT_ZIP_FILE="${OUTPUT_ZIP_FILE%.*}"".zip"
fi

# mount image
echo "Mounting image..."
LOOP_FILE=`losetup -f -P --show $TMP_DIR/$IMAGE_FILE`
echo $LOOP_FILE
LOOP_PART_FILE=$LOOP_FILE"p2"
if [ -e $LOOP_PART_FILE ]; then
	# rootfs should be in the second partition - in RPi case
	echo $LOOP_PART_FILE
	mount $LOOP_PART_FILE -o rw $MNT_DIR
else
	# there's only 1 partition - probably a BBB
	LOOP_PART_FILE=$LOOP_FILE"p1"
	echo $LOOP_PART_FILE
	mount $LOOP_PART_FILE -o rw $MNT_DIR
fi

# cp arm emulator to image
echo "Adding ARM emaulator to image"
cp /usr/bin/qemu-arm-static $MNT_DIR/usr/bin/.

# comment out ld.so.preload contents
LD_PRELOAD_PATH=$MNT_DIR/etc/ld.so.preload
if [ -e $LD_PRELOAD_PATH ]; then
	echo "Commenting out ld.so.preload"
	sed -i 's/^\([^#]\)/#\1/g' $LD_PRELOAD_PATH
fi

# if resolv.conf exists temporarily move it so that systemd-nspawn
# can use the host system's resolv.conf
RESOLV_PATH=$MNT_DIR/etc/resolv.conf
if [ -f $RESOLV_PATH -o -L $RESOLV_PATH ]; then
	echo "Moving resolv.conf"
	mv $RESOLV_PATH $RESOLV_PATH".hold"
fi

# if using a deb file, copy it into the image
if [ ! -z $DEB_FILE ]; then
	echo "Copying $DEB_FILE to image"
	cp $DEB_PATH $MNT_DIR/home/.
fi

# add makerhub feed
echo "Adding makerhub feed to image"
FEED_STR="deb [trusted=yes] http://feeds.labviewmakerhub.com/debian/ binary/"
echo $FEED_STR > $MNT_DIR/etc/apt/sources.list.d/lvmakerhub.list

# increase image size? maybe unnecessary

# install lvrt-schroot
echo "Updating package cache"
systemd-nspawn -M rpi -D $MNT_DIR apt update
if [ ! -z $DEB_FILE ]; then
        echo "Installing $DEB_FILE to image"
        systemd-nspawn -M rpi --tmpfs=/run/lock -D $MNT_DIR apt install -y /home/$DEB_FILE
else
	echo "Installing $LVRT_PKG to image from feed"
	systemd-nspawn -M rpi --tmpfs=/run/lock -D $MNT_DIR apt install -y $LVRT_PKG
fi

# Do RPi specific stuff (enable UART, I2C, SPI)
# https://www.raspberrypi.org/forums/viewtopic.php?t=21632
# TODO: The raspi-config script needs to access /boot/config.txt and possibly 
#  other syscalls that are not accessible in the container
if [ -x $MNT_DIR/usr/bin/raspi-config ]; then
	echo "Setting Raspberry Pi specific configuration"
	# 0 = true, 1 = false
	systemd-nspawn -M rpi -D $MNT_DIR raspi-config nonint do_ssh 0
	#systemd-nspawn -M rpi -D $MNT_DIR raspi-config nonint do_spi 0
	#systemd-nspawn -M rpi -D $MNT_DIR raspi-config nonint do_i2c 0
	#systemd-nspawn -M rpi -D $MNT_DIR raspi-config nonint do_serial 0
fi


# if using a deb file, remove it afterwards
if [ ! -z $DEB_FILE ]; then
        echo "Removing $DEB_FILE from image"
        rm $MNT_DIR/home/$DEB_FILE
fi

# delete arm emulator
echo "Removing arm emulator"
rm $MNT_DIR/usr/bin/qemu-arm-static

# uncomment ld.preload
if [ -e $LD_PRELOAD_PATH ]; then
	echo "Uncommenting ld.so.preload"
	sed -i 's/^#//g' $MNT_DIR/etc/ld.so.preload
fi

# move back resolv.conf
if [ -f $RESOLV_PATH".hold" -o -L $RESOLV_PATH".hold" ]; then
	echo "Moving resolv.conf back"
	mv $RESOLV_PATH".hold" $RESOLV_PATH
fi

# unmount image file
echo "Unmounting image"
umount $MNT_DIR
losetup -d $LOOP_FILE

# zip it up
echo "Zipping output image file $OUTPUT_ZIP_FILE"
mv $TMP_DIR/$IMAGE_FILE .
zip $OUTPUT_ZIP_FILE $IMAGE_FILE

# cleanup
echo "Cleaning up temporary files"
rm $IMAGE_FILE
rm -rf $TMP_DIR

