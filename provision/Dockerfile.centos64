ARG  from
FROM ${from}

ENV  CFLAGS=-w CXXFLAGS=-w

RUN yum install -y \
    diffutils \
    fontconfig-devel \
    freetype-devel \
    gcc \
    gcc-c++ \
    libX11-devel \
    libXext-devel \
    libXrender-devel \
    libjpeg-devel \
    libpng-devel \
    make \
    openssl-devel \
    perl \
    zlib-devel \
    && yum clean all
