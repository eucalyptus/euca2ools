FROM alpine:3.5

# Install Required Packages
RUN apk add --update \
  python-dev \
  py-pip \
  py-setuptools \
  ca-certificates \
  gcc \
  musl-dev \
  linux-headers \
  yaml-dev \
  libxslt-dev \
  libxml2-dev \
  zlib-dev

RUN pip install --upgrade pip setuptools

# Build euca2ools
ADD . /root

RUN cd ~/ \
  && python setup.py install

# Remove unneeded files
RUN apk del gcc musl-dev linux-headers \
  && rm -rf ~/* \
  && rm -rf /var/cache/apk/*

CMD ['ash']
