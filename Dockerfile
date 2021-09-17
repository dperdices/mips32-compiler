FROM ubuntu:20.04
LABEL version="0.1" maintainer="Daniel Perdices <daniel.perdices@uam.es>"
RUN apt-get update && apt-get install -y binutils-mips-linux-gnu python3 python3-pip
RUN mkdir cwd
WORKDIR cwd
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN adduser nonroot
USER nonroot
ADD . .
CMD gunicorn --bind 0.0.0.0:$PORT wsgi