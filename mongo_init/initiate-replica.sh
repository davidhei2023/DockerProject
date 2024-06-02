#!/bin/bash

check_mongo_ready() {
  container=$1
  until docker exec $container mongo --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
    echo "Waiting for $container to be ready..."
    sleep 2
  done
}

check_mongo_ready mongo_1
check_mongo_ready mongo_2
check_mongo_ready mongo_3

echo "Initiating replica set..."
mongosh --eval "rs.initiate({
  _id: 'myReplicaSet',
  members: [
    { _id: 0, host: 'mongo_1:27017' },
    { _id: 1, host: 'mongo_2:27017' },
    { _id: 2, host: 'mongo_3:27017' }
  ]
})"

tail -f /dev/null
