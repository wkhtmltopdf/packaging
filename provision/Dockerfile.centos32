ARG  from
FROM ${from}

ENV  CFLAGS=-w CXXFLAGS=-w

RUN sed -i 's/\$arch/i686/g' /etc/yum.repos.d/* && \
    sed -i 's/\$basearch/i386/g' /etc/yum.repos.d/*

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
