FROM mongo:5

COPY initiate-replica.sh /docker-entrypoint-initdb.d/initiate-replica.sh

RUN chmod +x /docker-entrypoint-initdb.d/initiate-replica.sh

CMD ["bash","/docker-entrypoint-initdb.d/initiate-replica.sh"]