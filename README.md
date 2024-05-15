INSTALLATION:

Install Python
Install script dependencies (SQLite3, etc)
Install Apache2
Install PhP

`mkdir /var/www/html/grow`
`chown 0777 grow`
copy GrowController.py, favicon.png, and grow.php to /var/www/html/grow/
`mkdir /var/www/html/grow/images`
(mount extra storage on this directory if neccessary)
copy growbox.service to /etc/systemd/system/
`systemctl enable growbox`
`systemctl start growbox`
