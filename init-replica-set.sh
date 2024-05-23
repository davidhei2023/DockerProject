#!/bin/bash

echo "Waiting for MongoDB to start..."
sleep 10

echo "Initiating the replica set..."
mongo --host mongo_1:27017 <<EOF
rs.initiate({
  _id: "myReplicaSet",
  members: [
    { _id: 0, host: "mongo_1:27017" },
    { _id: 1, host: "mongo_2:27017" },
    { _id: 2, host: "mongo_3:27017" }
  ]
})
EOF

echo "Replica set initiated."