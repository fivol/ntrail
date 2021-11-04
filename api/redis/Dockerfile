FROM redis
COPY redis.conf /usr/local/etc/redis/redis.conf
COPY sysctl.conf /etc/sysctl.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]