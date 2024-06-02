#!/bin/bash
sleep 1
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

