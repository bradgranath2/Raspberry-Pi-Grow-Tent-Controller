INSTALLATION:

`sudo apt update`
`sudo apt upgrade`
raspi-config:
  -Enable I2C Bus
  -enlarge file system
  
Install Python, python3-rpi.gpio, python3_smbus, python3_opencv, 
Install script dependencies (SQLite3, etc)
Install Apache2
Install PhP
Install Git
`git clone https://github.com/bradgranath2/Raspberry-Pi-Grow-Tent-Controller.git`
`mkdir /var/www/html/grow`
`chown 0777 grow`
copy GrowController.py, favicon.png, and grow.php to /var/www/html/grow/
`mkdir /var/www/html/grow/images`
(mount extra storage on this directory if neccessary)
copy growbox.service to /etc/systemd/system/
`systemctl enable growbox`
`systemctl start growbox`
