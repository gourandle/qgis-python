FROM debian:9.9
RUN apt-get update
RUN apt-get install -y python3.5
RUN apt-get install -y apt-transport-https
RUN apt-get install -y vim wget
RUN apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
RUN wget -O - https://qgis.org/downloads/qgis-2019.gpg.key | gpg --import
RUN gpg --export --armor 51F523511C7028C3 | apt-key add -
RUN add-apt-repository "deb https://qgis.org/debian-ltr stretch main"
RUN apt-get update
RUN apt-get install -y qgis qgis-server python3-qgis
RUN apt-get install fontconfig
# RUN qgis path : /usr
# RUN qgis plugin python path : /usr/share/qgis
RUN mkdir -p /var/opt/distribution-map/example
COPY "interpolation.py" "interpolation.py"
COPY "init.sh" "init.sh"
# CMD ["/usr/bin/python", "interpolation.py"]
CMD ["./init.sh"]
