FROM nginx:latest

ENV HOME=/opt/repo

RUN apt-get update && apt-get install -y supervisor uwsgi python3 python3-pip procps vim 

COPY ./requirements.txt /tmp/

RUN /usr/bin/pip3 install --requirement /tmp/requirements.txt

COPY . ${HOME}/src


COPY ./deployment/nginx/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /spool/nginx /run/pid && \
    chmod -R 777 /var/log/nginx /var/cache/nginx /etc/nginx /var/run /run /run/pid /spool/nginx && \
    chgrp -R 0 /var/log/nginx /var/cache/nginx /etc/nginx /var/run /run /run/pid /spool/nginx && \
    chmod -R g+rwX /var/log/nginx /var/cache/nginx /etc/nginx /var/run /run /run/pid /spool/nginx && \
    rm /etc/nginx/conf.d/default.conf

COPY ./deployment/nginx/uwsgi.ini /etc/uwsgi/apps-available/uwsgi.ini
RUN ln -s /etc/uwsgi/apps-available/uwsgi.ini /etc/uwsgi/apps-enabled/uwsgi.ini


COPY ./deployment/nginx/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN touch /var/log/supervisor/supervisord.log

EXPOSE 8080:8080

COPY ./deployment/nginx/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN ln -s /usr/local/bin/docker-entrypoint.sh / && \
    chmod 777 /usr/local/bin/docker-entrypoint.sh && \
    chgrp -R 0 /usr/local/bin/docker-entrypoint.sh && \
    chown -R nginx:root /usr/local/bin/docker-entrypoint.sh

WORKDIR ${HOME}
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["supervisord"]