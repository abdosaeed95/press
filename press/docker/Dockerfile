# syntax = docker/dockerfile:experimental
FROM ubuntu:22.04

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Make Python/pip installs quieter & leaner
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install essential packages (runtime + common tools)
RUN --mount=type=cache,target=/var/cache/apt apt-get update \
  && apt-get install --yes --no-install-suggests --no-install-recommends \
  # Essentials
  build-essential \
  git \
  mariadb-client \
  libmariadb3 \
  pkg-config \
  pv \
  ntp \
  wget \
  curl \
  supervisor \
  file \
  # Dependencies for SSH access
  openssh-server \
  nano \
  vim \
  less \
  htop \
  iputils-ping \
  telnet \
  # Dependencies for adding Python PPA
  software-properties-common \
  gnupg \
  # weasyprint dependencies
  libpango-1.0-0 \
  libharfbuzz0b \
  libpangoft2-1.0-0 \
  libpangocairo-1.0-0 \
  # wkhtmltopdf dependencies
  ca-certificates \
  fontconfig \
  libfreetype6 \
  libjpeg-turbo8 \
  libpng16-16 \
  libx11-6 \
  libxcb1 \
  libxext6 \
  libxrender1 \
  xfonts-75dpi \
  xfonts-base \
  # s3-attachment dependencies
  libmagic1 \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-essentials`

COPY --chown=root:root supervisord.conf /etc/supervisor/supervisord.conf

# Install Redis from packages.redis.io (Ubuntu 22.04 = jammy)
RUN --mount=type=cache,target=/var/cache/apt \
  curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb jammy main" > /etc/apt/sources.list.d/redis.list \
  && apt-get update \
  && apt-get install --yes --no-install-recommends redis-server \
  && rm -rf /var/lib/apt/lists/* `#stage-pre-redis`

# Install Python from DeadSnakes PPA
ENV {{ doc.get_dependency_version("python", True) }}
RUN --mount=type=cache,target=/var/cache/apt add-apt-repository -y ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install --yes --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    {% if not remove_distutils -%}
    python${PYTHON_VERSION}-distutils \
    {%- endif %}
    python${PYTHON_VERSION}-venv \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-python`

# Install wkhtmltopdf
# Install wkhtmltopdf
ENV {{ doc.get_dependency_version("wkhtmltopdf", True) }}

{% if is_arm_build %}
  # ARM (Ubuntu 22.04 jammy)
  {% if doc.get_dependency_version("wkhtmltopdf") in ['0.12.6', '0.12.6.1', '0.12.6.1-2'] %}
  RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_arm64.deb \
    && apt-get update && apt-get install -y --no-install-recommends \
       xfonts-75dpi xfonts-base \
    && dpkg -i wkhtmltox_0.12.6.1-2.jammy_arm64.deb \
    && rm wkhtmltox_0.12.6.1-2.jammy_arm64.deb \
    `#stage-pre-wkhtmltopdf (jammy arm64)`
  {% elif doc.get_dependency_version("wkhtmltopdf") == '0.12.4' %}
  RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar -xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && sudo mv wkhtmltox/bin/wkhtmlto* /usr/local/bin/ \
    && rm -rf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz wkhtmltox \
    `#stage-pre-wkhtmltopdf (generic 0.12.4)`
  {% else %}
  RUN echo "wkhtmltopdf {{ doc.get_dependency_version('wkhtmltopdf') }} isn't supported on Ubuntu 22.04. Use 0.12.6.1-2." && exit 1
  {% endif %}
{% else %}
  # Intel/amd64 (Ubuntu 22.04 jammy)
  {% if doc.get_dependency_version("wkhtmltopdf") in ['0.12.6', '0.12.6.1', '0.12.6.1-2'] %}
  RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && apt-get update && apt-get install -y --no-install-recommends \
       xfonts-75dpi xfonts-base \
    && dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && rm wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    `#stage-pre-wkhtmltopdf (jammy amd64)`
  {% elif doc.get_dependency_version("wkhtmltopdf") == '0.12.4' %}
  RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar -xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && mv wkhtmltox/bin/wkhtmlto* /usr/local/bin/ \
    && rm -rf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz wkhtmltox \
    `#stage-pre-wkhtmltopdf (generic 0.12.4)`
  {% else %}
  RUN echo "wkhtmltopdf {{ doc.get_dependency_version('wkhtmltopdf') }} isn't supported on Ubuntu 22.04. Use 0.12.6.1-2." && exit 1
  {% endif %}
{% endif %}


{% if doc.is_code_server_enabled %}
RUN curl -fsSL https://code-server.dev/install.sh | sh `#stage-pre-code-server`
{% endif %}

# Fonts
RUN git clone --progress --depth 1 https://github.com/frappe/fonts.git /tmp/fonts \
  && rm -rf /etc/fonts && mv /tmp/fonts/etc_fonts /etc/fonts \
  && rm -rf /usr/share/fonts && mv /tmp/fonts/usr_share_fonts /usr/share/fonts \
  && rm -rf /tmp/fonts \
  && fc-cache -fv \
  `#stage-pre-fonts`

# Set max_allowed_packet to 512 MB for mysqldump
RUN echo "[mysqldump]\nmax_allowed_packet = 512M" > /etc/mysql/conf.d/mysqldump.cnf

# Add frappe user
RUN useradd -ms /bin/bash frappe

# ---------- Additional Packages (templated) ----------
{% for p in doc.additional_packages %}

# Run before install scripts
{% if p.prerequisites %}
RUN --mount=type=cache,target=/var/cache/apt {{ p.prerequisites }} \
  `#stage-pre_before-{{ p.package }}`
{% endif %}

# Install non-Ubuntu packages
{% if p.package_manager not in ["apt-get", "apt"] %}
RUN {{ p.package_manager }} install {{ p.package }} \
  `#stage-pre-{{ p.package }}`

# Install Ubuntu packages
{% else %}
RUN --mount=type=cache,target=/var/cache/apt apt-get update \
  && apt-get install --yes --no-install-recommends {{ p.package }} \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-{{ p.package }}`
{% endif %}

# Run after install scripts
{% if p.after_install %}
RUN --mount=type=cache,target=/var/cache/apt {{ p.after_install }} \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre_after-{{ p.package }}`
{% endif %}

{% endfor %}
# ----------------------------------------------------

# symlink mysqldump to mariadb-dump
RUN ln -s /usr/bin/mysqldump /usr/bin/mariadb-dump || true

# Switch to frappe
USER frappe
WORKDIR /home/frappe

# Install Node using NVM (use bash shell for nvm)
SHELL ["/bin/bash", "-lc"]
ENV NVM_DIR=/home/frappe/.nvm
ENV {{ doc.get_dependency_version("nvm", True) }}
ENV {{ doc.get_dependency_version("node", True) }}

RUN wget https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh \
  && bash install.sh \
  && . "/home/frappe/.nvm/nvm.sh" \
  && nvm install ${NODE_VERSION} \
  && nvm use v${NODE_VERSION} \
  && nvm alias default v${NODE_VERSION} \
  && rm install.sh \
  && nvm cache clear \
  `#stage-pre-node`

ENV PATH="$PATH:/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin"

# Install Yarn (you can switch to corepack if desired)
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 npm install -g yarn `#stage-pre-yarn`

# Back to default shell
SHELL ["/bin/sh", "-c"]

# Install Bench + pip tooling
ENV PATH="$PATH:/home/frappe/.local/bin"

{% if requires_version_based_get_pip %}
RUN wget https://bootstrap.pypa.io/pip/${PYTHON_VERSION}/get-pip.py && python${PYTHON_VERSION} get-pip.py `#stage-pre-pip`
{% else %}
RUN wget https://bootstrap.pypa.io/get-pip.py && python${PYTHON_VERSION} get-pip.py `#stage-pre-pip`
{% endif %}

ENV {{ doc.get_dependency_version("bench", True) }}
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 \
    python${PYTHON_VERSION} -m pip install --upgrade \
      "frappe-bench==${BENCH_VERSION}" \
      "Jinja2~=3.0.3" \
      "setuptools" \
    `#stage-bench-and-pip`

RUN git config --global advice.detachedHead false
ENV PYTHONUNBUFFERED=1

# For the sake of completing the step
RUN `#stage-bench-env`

# Set environment variables (templated)
{% for v in doc.environment_variables %}
ENV {{ v.key }} {{ v.value }}
{% endfor %}

RUN git config --global --add safe.directory /home/frappe/context/apps/frappe/.git

# Install Frappe app (init bench)
RUN --mount=type=cache,sharing=locked,target=/home/frappe/.cache,uid=1000,gid=1000 \
    --mount=type=bind,source=apps/frappe,target=/home/frappe/context/apps/frappe \
    bench init --python /usr/bin/python${PYTHON_VERSION} --no-backups --frappe-path file:///home/frappe/context/apps/frappe frappe-bench \
    `#stage-apps-frappe`

WORKDIR /home/frappe/frappe-bench

# ---------- Build pycups with temporary dev deps, then purge ----------
USER root
RUN --mount=type=cache,target=/var/cache/apt apt-get update \
    && apt-get install -y --no-install-recommends gcc libcups2-dev \
    && su - frappe -c "/home/frappe/frappe-bench/env/bin/pip install --no-cache-dir pycups==2.0.1" \
    && apt-get purge -y gcc libcups2-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    `#stage-pycups-buildclean`
USER frappe
# ---------------------------------------------------------------------

# Install Redisearch 2.0 from precompiled binaries (your assets)
COPY --chown=frappe:frappe redis /home/frappe/frappe-bench/redis
COPY --chown=frappe:frappe .vimrc /home/frappe/.vimrc
COPY --chown=frappe:frappe common_site_config.json /home/frappe/frappe-bench/sites/common_site_config.json

# Install other apps
{% for app in doc.apps %}
{% if app.app != "frappe" %}

RUN git config --global --add safe.directory /home/frappe/context/apps/{{ app.app }}/.git

  {% if app.app == "fodista" %}
  RUN --mount=type=cache,sharing=locked,target=/home/frappe/.cache,uid=1000,gid=1000 \
      --mount=type=bind,source=apps/{{ app.app }},target=/home/frappe/context/apps/{{ app.app }} \
      bench get-app file:///home/frappe/context/apps/{{ app.app }} --skip-assets \
      {% if app.use_cached %}
      --cache-key {{ app.hash }} {% if doc.compress_app_cache %}--compress-artifacts{% endif %} \
      {% endif %} \
      `#stage-apps-{{ app.app }}`

  # Copy .git after get-app to retain history
  COPY --chown=frappe:frappe apps/{{ app.app }}/.git /home/frappe/frappe-bench/apps/{{ app.app }}/.git

  # Submodule update and build with caching
  RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 \
      --mount=type=cache,target=/home/frappe/frappe-bench/apps/{{ app.app }}/node_modules,uid=1000,gid=1000 \
      git -C /home/frappe/frappe-bench/apps/{{ app.app }} submodule update --init --recursive \
      && cd /home/frappe/frappe-bench/apps/{{ app.app }}/dashboard \
      && yarn install \
      && NODE_ENV=production yarn run build \
      && bench build --app {{ app.app }} \
      `#stage-apps-Build-{{ app.app }}`
  {% else %}

  RUN --mount=type=cache,sharing=locked,target=/home/frappe/.cache,uid=1000,gid=1000 \
      --mount=type=bind,source=apps/{{ app.app }},target=/home/frappe/context/apps/{{ app.app }} \
      bench get-app file:///home/frappe/context/apps/{{ app.app }} \
      {% if app.use_cached %}
      --cache-key {{ app.hash }} {% if doc.compress_app_cache %}--compress-artifacts{% endif %} \
      {% endif %} \
      `#stage-apps-{{ app.app }}`
  {% endif %}

{% endif %}
{% endfor %}

# Pull app updates from mounted repository
{% for app in doc.apps %}
{% if app.pullable_release %}
RUN --mount=type=bind,source=app_updates/{{ app.app }},target=/home/frappe/context/app_updates/{{ app.app }} \
  cd /home/frappe/frappe-bench/apps/{{ app.app }} \
  && git reset --hard \
  && git remote add -f app_update /home/frappe/context/app_updates/{{ app.app }} \
  && git fetch --depth 1 app_update {{ app.pullable_hash }} \
  && git checkout {{ app.pullable_hash }} \
  && git remote remove app_update \
  `#stage-pull-{{ app.app }}`
{% endif %}
{% endfor %}

COPY --chown=frappe:frappe config /home/frappe/frappe-bench/config
COPY --chown=frappe:frappe apps.txt /home/frappe/frappe-bench/sites/apps.txt

# Create custom mounts
{% for m in doc.container_mounts %}
RUN mkdir -p {{ m.destination }} \
  && chown -R frappe:frappe {{ m.destination }} \
  `#stage-mounts-create`
{% endfor %}

ENV FRAPPE_HARD_LINK_ASSETS=True
ENV HISTTIMEFORMAT="%Y-%m-%d %T "

# Optional: purge heavy build toolchain now that assets are built
USER root
RUN --mount=type=cache,target=/var/cache/apt apt-get purge -y build-essential \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*
USER frappe


EXPOSE 8000 9000 2200 8088
CMD ["supervisord"]
