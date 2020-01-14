#INSTALLATION

upgrade to stretch debian

https://qgis.org/en/site/forusers/alldownloads.html#debian-ubuntu

sudo apt-add-repository https://qgis.org/debian


wget -O - https://qgis.org/downloads/qgis-2017.gpg.key | gpg --import
gpg --fingerprint CAEB3DC3BDF7FB45


gpg --export --armor CAEB3DC3BDF7FB45 | sudo apt-key add -

sudo apt-get install qgis-server python3-qgis

qgis path : /usr
qgis plugin python path : /usr/share/qgis
