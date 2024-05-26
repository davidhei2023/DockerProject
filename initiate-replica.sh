#!/bin/bash

# Start MongoDB in the background
mongod --replSet myReplicaSet --bind_ip_all &

# Wait for MongoDB to fully start
sleep 10

echo "Initiating replica set..."
mongosh --eval "rs.initiate({
  _id: 'myReplicaSet',
  members: [
    { _id: 0, host: 'mongo_1:27017' },
    { _id: 1, host: 'mongo_2:27017' },
    { _id: 2, host: 'mongo_3:27017' }
  ]
})"

# Keep the container running by tailing the MongoDB log
tail -f /dev/null
