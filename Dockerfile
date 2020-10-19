FROM ubuntu:latest
VOLUME /golem/work /golem/output /golem/resource
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -qq -y install handbrake handbrake-cli
WORKDIR /golem/work
