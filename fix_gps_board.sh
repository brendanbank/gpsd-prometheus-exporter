#!/bin/bash

# Thanks to https://lang-ship.com/reference/Arduino/libraries/RTC_RV-3028-C7_Arduino_Library/class_r_v3028.html#a9cbc9a009d4e5dbfeb29e366140be42b
# And the folks at https://github.com/raspberrypi/linux/issues/2912

# Raspberry Pi GPS/RTC Expansion Board https://store.uputronics.com/index.php?route=product/product&path=60_64&product_id=81

function wait_for_EEBusy_done {
   busy=$((0x80))
   while (( busy == 0x80 ))
   do
      status=$( i2cget -y 1 0x52 0x0E )
      busy=$((status & 0x80))
   done
}

rmmod rtc_rv3028

wait_for_EEBusy_done

# disable auto refresh
register=$( i2cget -y 1 0x52 0x0F )
writeback=$((register | 0x08))
i2cset -y 1 0x52 0x0F $writeback

# enable BSM in level switching mode
register=$( i2cget -y 1 0x52 0x37 )
writeback=$((register | 0x0C))
i2cset -y 1 0x52 0x37 $writeback

# update EEPROM
i2cset -y 1 0x52 0x27 0x00
i2cset -y 1 0x52 0x27 0x11

wait_for_EEBusy_done

# reenable auto refresh
register=$( i2cget -y 1 0x52 0x0F )
writeback=$((register & ~0x08))
i2cset -y 1 0x52 0x0F $writeback

wait_for_EEBusy_done

modprobe rtc_rv3028

