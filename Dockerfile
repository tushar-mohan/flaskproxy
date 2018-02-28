FROM ubuntu

RUN apt-get update && \
    apt-get install -y tzdata python-pip && \
    rm -rf /var/lib/apt/lists && \
    pip install --upgrade pip 

WORKDIR /opt/flaskproxy

COPY ./requirements.txt /opt/flaskproxy/requirements.txt
RUN pip install -r /opt/flaskproxy/requirements.txt
COPY . /opt/flaskproxy/
