FROM tomcat:8-jre7

RUN rm -fr /usr/local/tomcat/webapps/*

ADD setenv.sh /usr/local/tomcat/bin/setenv.sh

ADD target/zmon-controller-1.0.1-SNAPSHOT.war /usr/local/tomcat/webapps/ROOT.war
