FROM docker.io/ubuntu:20.04
RUN apt-get update && apt-get install \
  -y --no-install-recommends python3 python3-virtualenv

### setup python environment
ENV APP_ROOT=/opt
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:${APP_ROOT}/.local/bin:${APP_ROOT}:${PATH} HOME=${APP_ROOT}

### copy source code and helper scripts
COPY bin/ ${APP_ROOT}

### fix permissions
RUN chmod -R u+x ${APP_ROOT} && \
    chgrp -R 0 ${APP_ROOT} && \
    chmod -R g=u ${APP_ROOT} /etc/passwd

### make sure container is not running as root
USER 1001
WORKDIR ${APP_ROOT}

### install application dependencies
RUN pip install --no-cache-dir -r requirements.txt

### run helper-script and application
ENTRYPOINT [ "uid_entrypoint" ]
CMD kopf run podscaler.py --verbose
