FROM pytorch/pytorch:1.8.0-cuda11.1-cudnn8-runtime

# Ensure terminal output is sent directly to logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ARG T4T_WHL=t4t_headstamp-0.0.1-py3-none-any.whl

# uvicorn/uvloop/pymssql and other requirements
#RUN apk add gcc g++ musl-dev python3-dev libffi-dev openssl-dev make freetds-dev
RUN apt-get -qq update && DEBIAN_FRONTEND=noninteractive apt-get -y install gnupg2
RUN apt-key del 7fa2af80
RUN apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub

# Pillow dependencies
RUN apt-get -qq update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    cmake \
    curl \
    ghostscript \
    git \
#    libegl-dev \
    libffi-dev \
    libfreetype6-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libjpeg-turbo-progs \
    libjpeg8-dev \
    liblcms2-dev \
#    libopengl-dev \
    libopenjp2-7-dev \
    libssl-dev \
    libtiff5-dev \
    libwebp-dev \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxkbcommon-x11-0 \
    netpbm \
    ninja-build \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-setuptools \
    python3-tk \
    sudo \
    tcl8.6-dev \
    tk8.6-dev \
    virtualenv \
    wget \
    xvfb \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
# TODO: separate development from production requirements (and Dockerfiles)
COPY ./predict_api/requirements.txt /requirements.txt
RUN pip install --upgrade pip
ADD ./${T4T_WHL} /${T4T_WHL}
RUN pip install -r /requirements.txt
RUN pip install /${T4T_WHL}

# ADD ./model /model
ADD ./model_snapshot /model_snapshot
ADD ./predict_api /app

WORKDIR /app

EXPOSE 8081

CMD sh run-prediction-api-local.sh