# Pull base image.
FROM ubuntu:latest

VOLUME /golem/work /golem/output /golem/resource
ENV DEBIAN_FRONTEND=noninteractive

# Define software versions.
ARG HANDBRAKE_VERSION=1.3.1
ARG HANDBRAKE_URL=https://download.handbrake.fr/releases/${HANDBRAKE_VERSION}/HandBrake-${HANDBRAKE_VERSION}-source.tar.bz2

# Set to 'max' to keep debug symbols.
ARG HANDBRAKE_DEBUG_MODE=none

# Define working directory.
WORKDIR /tmp

# Compile HandBrake
RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get install -y \
 autoconf \
  automake \
  autopoint \
  appstream \
  build-essential \
  cmake \
  git \
  libass-dev \
  libbz2-dev \
  libfontconfig1-dev \
  libfreetype6-dev \
  libfribidi-dev \
  libharfbuzz-dev \
  libjansson-dev \
  liblzma-dev \
  libmp3lame-dev \
  libnuma-dev \
  libogg-dev \
  libopus-dev \
  libsamplerate-dev \
  libspeex-dev \
  libtheora-dev \
  libtool \
  libtool-bin \
  libturbojpeg0-dev \
  libvorbis-dev \
  libx264-dev \
  libxml2-dev \
  libvpx-dev \
  m4 \
  make \
  meson \
  nasm \
  ninja-build \
  patch \
  pkg-config \
  tar \
  zlib1g-dev \
  clang \
  gstreamer1.0-libav \
  intltool \
  libappindicator-dev \
  libdbus-glib-1-dev \
  libglib2.0-dev \
  libgstreamer1.0-dev \
  libgtk-3-dev \
  libnotify-dev \
  libwebkit2gtk-4.0-dev
    # Download sources.
 RUN    mkdir HandBrake && \
        curl -# -L ${HANDBRAKE_URL} | tar xj --strip 1 -C HandBrake; 

    # Import custom presets
 RUN curl https://raw.githubusercontent.com/KasperSvendsenGit/golem-video/master/handbrake_presets/preset_builtin.list -o ./HandBrake/preset/preset_builtin.list
 RUN curl https://raw.githubusercontent.com/KasperSvendsenGit/golem-video/master/handbrake_presets/preset_custom.json -o ./HandBrake/preset/preset_custom.json

    # Compile.
 RUN   cd HandBrake && \
                ./configure --prefix=/usr \
                --debug=$HANDBRAKE_DEBUG_MODE \
                --disable-gtk-update-checks \
                --enable-fdk-aac \
                --enable-x265 \
                --enable-qsv \
                --launch-jobs=$(nproc) \
                --launch \
                && \
    /tmp/run_cmd -i 600 -m "HandBrake still compiling..." make --directory=build install && \
    if [ "${HANDBRAKE_DEBUG_MODE}" = "none" ]; then \
        strip /usr/bin/ghb \
              /usr/bin/HandBrakeCLI; \
    fi && \
    cd .. 
    # Cleanup.
    #del-pkg build-dependencies && \
    #rm -rf /tmp/* /tmp/.[!.]*

RUN \
    APP_ICON_URL=https://raw.githubusercontent.com/KasperSvendsenGit/golem-video/master/handbrake-icon.png && \
    install_app_icon.sh "$APP_ICON_URL"

# Metadata.
LABEL \
      org.label-schema.name="handbrake" \
      org.label-schema.description="Docker container for HandBrake on golem.network" \
      org.label-schema.version="unknown" \
      org.label-schema.vcs-url="https://github.com/KasperSvendsenGit/golem-video" \
      org.label-schema.schema-version="1.0"
