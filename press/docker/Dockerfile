# syntax = docker/dockerfile:experimental
FROM ubuntu:22.04 AS builder

ENV FRAPPE_DOCKER_BUILD True
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

ENV OPENBLAS_NUM_THREADS 1
ENV MKL_NUM_THREADS 1

# Install essential packages
RUN --mount=type=cache,target=/var/cache/apt apt-get update \
  && apt-get install --yes --no-install-suggests --no-install-recommends \
  # Essentials
  build-essential \
  git \
  mariadb-client \
  libmariadb-dev \
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
  # pycups dependencies
  gcc \
  libcups2-dev \
  # s3-attachment dependencies
  libmagic1 \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-essentials`

COPY --chown=root:root supervisord.conf /etc/supervisor/supervisord.conf

# Install Redis from PPA
RUN --mount=type=cache,target=/var/cache/apt curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb jammy main" | tee /etc/apt/sources.list.d/redis.list \
  && apt-get update \
  && apt-get install --yes --no-install-suggests --no-install-recommends \
  redis-server \
  && rm -rf /var/lib/apt/lists/* `#stage-pre-redis`

# Install Python from DeadSnakes PPA
ENV {{ doc.get_dependency_version("python", True) }}
RUN --mount=type=cache,target=/var/cache/apt add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install --yes --no-install-suggests --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    {% if not remove_distutils -%}
    python${PYTHON_VERSION}-distutils \
    {%- endif %}
    python${PYTHON_VERSION}-venv \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-python`

# Install wkhtmltopdf
ENV {{ doc.get_dependency_version("wkhtmltopdf", True) }}


{% if is_arm_build %}
  # ARM setup (0.12.5) & (0.12.6)
  {% if doc.get_dependency_version("wkhtmltopdf") == '0.12.5' %}
  RUN wget https://github.com/Aradhya-Tripathi/wkhtmltopdf/releases/download/0.12.5-arm/wkhtmltox_0.12.5-1.jammy_arm64.deb \
    && dpkg -i wkhtmltox_0.12.5-1.jammy_arm64.deb \
    && rm wkhtmltox_0.12.5-1.jammy_arm64.deb \
    `#stage-pre-wkhtmltopdf`
  {% endif %}

  {% if doc.get_dependency_version("wkhtmltopdf") == '0.12.6' %}
  RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_arm64.deb  \
    && dpkg -i wkhtmltox_0.12.6.1-2.jammy_arm64 \
    && rm wkhtmltox_0.12.6.1-2.jammy_arm64 \
    `#stage-pre-wkhtmltopdf`
  {% endif %}
{% else %}
  # Intel setup
  {% if doc.get_dependency_version("wkhtmltopdf") == '0.12.6' %}
  RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb  \
    && dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && rm wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    `#stage-pre-wkhtmltopdf`
  {% elif doc.get_dependency_version("wkhtmltopdf") == '0.12.5' %}
  RUN wget https://github.com/Aradhya-Tripathi/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.jammy_amd64.deb  \
    && dpkg -i wkhtmltox_0.12.5-1.jammy_amd64.deb \
    && rm wkhtmltox_0.12.5-1.jammy_amd64.deb \
    `#stage-pre-wkhtmltopdf`
  {% endif %}
{% endif %}

{% if doc.is_code_server_enabled %}
RUN curl -fsSL https://code-server.dev/install.sh | sh `#stage-pre-code-server`
{% endif %}

# Install Fonts
RUN git clone --progress --depth 1 https://github.com/frappe/fonts.git /tmp/fonts \
  && rm -rf /etc/fonts && mv /tmp/fonts/etc_fonts /etc/fonts \
  && rm -rf /usr/share/fonts && mv /tmp/fonts/usr_share_fonts /usr/share/fonts \
  && rm -rf /tmp/fonts \
  && fc-cache -fv \
  `#stage-pre-fonts`


# Set max_allowed_packet to 512 MB for mysqldump
RUN echo "[mysqldump]\nmax_allowed_packet              = 512M" > /etc/mysql/conf.d/mysqldump.cnf

# Add frappe user
RUN useradd -ms /bin/bash frappe

# Install Additional Packages
{% for p in doc.additional_packages %}

# Run before install scripts
{% if p.prerequisites %}
RUN --mount=type=cache,target=/var/cache/apt {{ p.prerequisites }} \
  `#stage-pre_before-{{ p.package }}`
{% endif %}

# Install non Ubuntu packages
{% if p.package_manager not in ["apt-get", "apt"] %}
RUN {{ p.package_manager }} install {{ p.package }} \
  `#stage-pre-{{ p.package }}`

# Install Ubuntu packages
{% else %}
RUN --mount=type=cache,target=/var/cache/apt apt-get update \
  && apt-get install --yes --no-install-suggests --no-install-recommends {{ p.package }} \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre-{{ p.package }}`
{% endif %}

# Run after install scripts
{% if p.after_install %}
RUN  --mount=type=cache,target=/var/cache/apt {{ p.after_install }} \
  && rm -rf /var/lib/apt/lists/* \
  `#stage-pre_after-{{ p.package }}`
{% endif %}

{% endfor %}


# symlink mysqldump to mariadb-dump
RUN test -f /usr/bin/mariadb-dump || ln -s /usr/bin/mysqldump /usr/bin/mariadb-dump

# Switch to frappe
USER frappe
WORKDIR /home/frappe


# Install Node using NVM
ENV NVM_DIR /home/frappe/.nvm
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

ENV PATH "$PATH:/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin"

# Install Yarn
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 npm install -g yarn `#stage-pre-yarn`


# Install Bench
ENV PATH "$PATH:/home/frappe/.local/bin"

{% if requires_version_based_get_pip %}
RUN wget https://bootstrap.pypa.io/pip/${PYTHON_VERSION}/get-pip.py && python${PYTHON_VERSION} get-pip.py `#stage-pre-pip`
{% else %}
RUN wget https://bootstrap.pypa.io/get-pip.py && python${PYTHON_VERSION} get-pip.py `#stage-pre-pip`
{% endif %}

ENV {{ doc.get_dependency_version("bench", True) }}
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 python${PYTHON_VERSION} -m pip install --upgrade frappe-bench==${BENCH_VERSION} `#stage-bench-bench`

RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 python${PYTHON_VERSION} -m pip install Jinja2~=3.0.3
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 python${PYTHON_VERSION} -m pip install --upgrade setuptools

RUN git config --global advice.detachedHead false

ENV PYTHONUNBUFFERED 1

# For the sake of completing the step
RUN `#stage-bench-env`

# Set environment variables
{% for v in doc.environment_variables %}
ENV {{v.key}} {{ v.value }}
{% endfor %}

# Install Frappe app
RUN --mount=type=cache,sharing=locked,target=/home/frappe/.cache,uid=1000,gid=1000 --mount=type=bind,source=apps/frappe,target=/home/frappe/context/apps/frappe bench init --python /usr/bin/python${PYTHON_VERSION} --no-backups --frappe-path file:///home/frappe/context/apps/frappe frappe-bench `#stage-apps-frappe`
WORKDIR /home/frappe/frappe-bench

RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 /home/frappe/frappe-bench/env/bin/pip install pycups==2.0.1

# Install Redisearch 2.0 from precompiled binaries
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

  {% if doc.is_code_server_enabled %}
  # Code-server images retain the prepared Git metadata for interactive development.
  COPY --chown=frappe:frappe apps/{{ app.app }}/.git /home/frappe/frappe-bench/apps/{{ app.app }}/.git

  # Code-server images also retain the prepared dashboard source.
  COPY --chown=frappe:frappe apps/{{ app.app }}/dashboard /home/frappe/frappe-bench/apps/{{ app.app }}/dashboard
  {% endif %}

  # Build the prepared submodule source with caching
  RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 \
      {% if not doc.is_code_server_enabled %}
      --mount=type=bind,source=apps/{{ app.app }}/dashboard,target=/home/frappe/frappe-bench/apps/{{ app.app }}/dashboard \
      --mount=type=cache,sharing=locked,target=/home/frappe/frappe-bench/apps/{{ app.app }}/dashboard/node_modules,uid=1000,gid=1000 \
      {% endif %}
      cd /home/frappe/frappe-bench/apps/{{ app.app }}/dashboard \
      && yarn install --frozen-lockfile --non-interactive \
      && NODE_ENV=production yarn run build \
      && bench build --app {{ app.app }} \
      {% if not doc.is_code_server_enabled %}
      && find /home/frappe/frappe-bench/apps/{{ app.app }}/{{ app.app }}/public/dashboard -type f -name '*.map' -delete \
      {% endif %}
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

# Keep only the Node.js dependency closure needed by Frappe realtime.
RUN --mount=type=cache,target=/home/frappe/.cache,uid=1000,gid=1000 \
  mkdir -p /home/frappe/runtime/socketio \
  && node -e 'const fs = require("fs"); const source = require("./apps/frappe/package.json"); const names = ["socket.io", "@redis/client", "superagent", "cookie"]; const dependencies = Object.fromEntries(names.map((name) => [name, source.dependencies[name]])); fs.writeFileSync("/home/frappe/runtime/socketio/package.json", JSON.stringify({ private: true, dependencies }, null, 2))' \
  && cp apps/frappe/yarn.lock /home/frappe/runtime/socketio/yarn.lock \
  && cd /home/frappe/runtime/socketio \
  && yarn install --frozen-lockfile --production --ignore-scripts --non-interactive

# Create custom mounts
{% for m in doc.container_mounts %}
RUN mkdir -p {{ m.destination }} && \
  chown -R frappe:frappe {{ m.destination }} \
  `#stage-mounts-create`
{% endfor %}

ENV FRAPPE_DOCKER_BUILD=
ENV FRAPPE_HARD_LINK_ASSETS True
ENV HISTTIMEFORMAT "%Y-%m-%d %T "

EXPOSE 8000 9000 2200 8088
CMD ["supervisord"]

# Flatten the built filesystem into a separate production runtime image. This
# keeps the full image editable while excluding build-layer history from pulls.
FROM builder AS runtime-files

USER root

RUN install -m 0755 /home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin/node /usr/local/bin/node \
  && mv /home/frappe/frappe-bench/sites/assets /home/frappe/runtime/sites-assets \
  && mkdir -p /home/frappe/frappe-bench/sites/assets \
  && chown -R frappe:frappe /home/frappe/runtime /home/frappe/frappe-bench/sites/assets \
  && find /home/frappe/frappe-bench/apps -type d \( -name node_modules -o -name .next -o -name .turbo -o -name .git \) -prune -exec rm -rf {} + \
  && find /home/frappe/frappe-bench/apps /home/frappe/runtime/sites-assets -type f -name '*.map' -delete \
  && rm -rf /home/frappe/.nvm /home/frappe/.cache /home/frappe/context /root/.cache /tmp/* \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /usr/share/doc/* /usr/share/man/* /usr/share/info/* /tmp/* \
  && fc-cache -f \
  && ldconfig

FROM scratch AS runtime

COPY --from=runtime-files / /

ENV LANG=C.UTF-8 \
  HOME=/home/frappe \
  PATH="/home/frappe/.local/bin:/home/frappe/frappe-bench/env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  NODE_PATH=/home/frappe/runtime/socketio/node_modules \
  PYTHONUNBUFFERED=1 \
  OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 \
  FRAPPE_HARD_LINK_ASSETS=True
{% for v in doc.environment_variables %}
ENV {{v.key}} {{ v.value }}
{% endfor %}

USER frappe
WORKDIR /home/frappe/frappe-bench

EXPOSE 8000 9000
CMD ["/home/frappe/frappe-bench/env/bin/gunicorn", "--chdir", "/home/frappe/frappe-bench/sites", "--bind", "0.0.0.0:8000", "--workers", "6", "--timeout", "120", "--graceful-timeout", "30", "--worker-tmp-dir", "/dev/shm", "frappe.app:application", "--preload", "--max-requests", "5000", "--max-requests-jitter", "1000"]

# Preserve the current image as the default target for Agent-managed benches,
# SSH, code-server, and in-place source updates.
FROM builder AS full

{% for app in doc.apps %}
{% if app.app == "fodista" and not doc.is_code_server_enabled %}
# Keep Fodista dashboard source available for one-off maintenance builds.
COPY --chown=frappe:frappe apps/{{ app.app }}/dashboard /home/frappe/frappe-bench/apps/{{ app.app }}/dashboard
{% endif %}
{% endfor %}
