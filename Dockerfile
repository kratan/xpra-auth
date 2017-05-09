FROM ubuntu:16.04
LABEL maintainer "Andreas Kratzer <andreas.kratzer@kit.edu>"

ENV NVIDIA_VER=375.39
ENV NVIDIA_INSTALL=http://us.download.nvidia.com/XFree86/Linux-x86_64/${NVIDIA_VER}/NVIDIA-Linux-x86_64-${NVIDIA_VER}.run

ENV CUDA_VERSION 8.0.61

ENV PYCUDA_VER=2016.1.2
ENV PYCUDA_INSTALL=http://git.tiker.net/trees/pycuda.git

# Install main Stuff
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections \
	&& apt-get update \
	&& apt-get install --no-install-recommends -y \
	binutils \
        module-init-tools \
	gnupg2 \
	build-essential \
	curl \
	pkg-config \
	ca-certificates \
	python-netifaces \
	wget \
	supervisor \
	python-software-properties \
	software-properties-common \
	python-pip \
	libboost-all-dev \
	build-essential \
	python-dev \
	python-setuptools \
	libboost-python-dev \
	libboost-thread-dev \
	nginx

#Add nvidia driver to current image
RUN curl -o /tmp/NVIDIA-Linux-x86_64-${NVIDIA_DRIVER}.run ${NVIDIA_INSTALL} \
	&& sh /tmp/NVIDIA-Linux-x86_64-${NVIDIA_DRIVER}.run -a -N --ui=none --no-kernel-module

LABEL com.nvidia.volumes.needed="nvidia_driver"

RUN NVIDIA_GPGKEY_SUM=d1be581509378368edeec8c1eb2958702feedf3bc3d17011adbf24efacce4ab5 \
	&& NVIDIA_GPGKEY_FPR=ae09fe4bbd223a84b2ccfce3f60f4b3d7fa2af80 \
	&& apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub \
	&& apt-key adv --export --no-emit-version -a $NVIDIA_GPGKEY_FPR | tail -n +5 > cudasign.pub \
	&& echo "$NVIDIA_GPGKEY_SUM  cudasign.pub" | sha256sum -c --strict - && rm cudasign.pub \
	&& echo "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64 /" > /etc/apt/sources.list.d/cuda.list

LABEL com.nvidia.cuda.version="${CUDA_VERSION}"

ENV CUDA_PKG_VERSION 8-0=$CUDA_VERSION-1
RUN apt-get update && apt-get install -y --no-install-recommends \
	cuda-core-$CUDA_PKG_VERSION \
        cuda-misc-headers-$CUDA_PKG_VERSION \
        cuda-command-line-tools-$CUDA_PKG_VERSION \
        cuda-nvrtc-dev-$CUDA_PKG_VERSION \
        cuda-nvml-dev-$CUDA_PKG_VERSION \
        cuda-nvgraph-dev-$CUDA_PKG_VERSION \
        cuda-cusolver-dev-$CUDA_PKG_VERSION \
        cuda-cublas-dev-$CUDA_PKG_VERSION \
        cuda-cufft-dev-$CUDA_PKG_VERSION \
        cuda-curand-dev-$CUDA_PKG_VERSION \
        cuda-cusparse-dev-$CUDA_PKG_VERSION \
        cuda-npp-dev-$CUDA_PKG_VERSION \
        cuda-cudart-dev-$CUDA_PKG_VERSION \
        cuda-driver-dev-$CUDA_PKG_VERSION \
	&& ln -s cuda-8.0 /usr/local/cuda \
	&& rm -rf /var/lib/apt/lists/*

RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf \
	&& ldconfig

RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf \
	&& echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH /usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64

#Get xpra latest
RUN curl https://winswitch.org/gpg.asc | apt-key add - \
	&& echo "deb http://winswitch.org/beta/ xenial main" > /etc/apt/sources.list.d/winswitch.list \
	&& echo "deb http://winswitch.org/ xenial main" >> /etc/apt/sources.list.d/winswitch.list \
	&& apt-get update \
	&& apt-get upgrade --no-install-recommends -y --allow-unauthenticated xpra


# copy over our requirements.txt file
COPY requirements.txt /tmp/

#install required python packages
RUN pip install --upgrade pip && pip install --upgrade -r /tmp/requirements.txt


# Create the directory needed to run the dbus daemon and Xpra
RUN mkdir /var/run/dbus && mkdir /var/run/xpra \
	&& chown -R root:xpra /var/run/xpra && chmod 0775 -R /var/run/xpra

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Copy the modified Nginx conf
ADD nginx.conf /etc/nginx/sites-enabled/xpra-auth.conf

#set Rights, make Dirs
RUN mkdir -p /etc/nginx/certs/private \
	&& mkdir -p /etc/nginx/certs/public \
	&& chmod 0710 -R /etc/nginx/certs/private \
	&& chmod 0755 -R /etc/nginx/certs/public \
	&& rm -Rf /etc/nginx/sites-enabled/default


# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
ADD uwsgi.ini /etc/uwsgi/

# Copy Supervisord conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#COPY setup.sh /setup.sh
RUN useradd -g xpra -ms /bin/bash xpra

RUN mkdir -p /xprafile && chmod 0777 -R /xprafile && mkdir -p /app && chmod 0777 -R /app
VOLUME /xprafile

#cleanup
RUN apt-get clean -y \
	&& apt-get autoclean -y \
	&& apt-get autoremove -y \
	&& rm -rf /usr/share/locale/*  \
	&& rm -rf /var/cache/debconf/*-old \
	&& rm -rf /var/lib/apt/lists/* \
	&& rm -rf /usr/share/doc/* \
	rm -rf /tmp/*

WORKDIR /app

#nginx rest
EXPOSE 4443

#xpra proxy
EXPOSE 443

CMD ["/usr/bin/supervisord"]
