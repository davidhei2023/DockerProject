#!/bin/bash

set -e

# Set environment variables
cat <<EOF > /home/ubuntu/PolybotService/.env
MONGO_IMAGE=mongo:5
POLYBOT_IMG_NAME=davidhei/davidhei-repostory-1:polybot-app-${GITHUB_RUN_NUMBER}
YOLO5_IMG_NAME=davidhei/davidhei-repostory-1:yolo5-image-v0.2.2-${GITHUB_RUN_NUMBER}
BUCKET_NAME=davidhei-ohio-s3bucket
AWS_DEFAULT_REGION=us-east-2
TELEGRAM_APP_URL=https://27fd-18-224-71-210.ngrok-free.app
TELEGRAM_TOKEN=7161211112:AAEEWsM2Pj-08738K-Vhmr6s8vE3yBhK8LU
S3_BUCKET_NAME=davidhei-ohio-s3bucket
YOLO5_URL=http://yolo5_app:8081
EOF

# Create the replica set initiation script
cat <<EOF > /home/ubuntu/PolybotService/initiate-replica.sh
#!/bin/bash

# Start MongoDB with replica set configuration
mongod --replSet myReplicaSet --bind_ip_all &

# Wait for MongoDB to fully start
sleep 10

# Initialize the replica set
mongo <<EOF
rs.initiate()
rs.add("mongo_2:27017")
rs.add("mongo_3:27017")
rs.status()
EOF
EOF

chmod +x /home/ubuntu/PolybotService/initiate-replica.sh

# Create the docker-compose.yaml file
cat <<EOF > /home/ubuntu/PolybotService/docker-compose.yaml
version: '3.8'

services:
  mongo_1:
    container_name: mongo_1
    image: mongo:\${MONGO_IMAGE}
    ports:
      - "27017:27017"
    volumes:
      - mongo_1_data:/data/db
      - ./initiate-replica.sh:/docker-entrypoint-initdb.d/initiate-replica.sh
    env_file:
      - .env
    networks:
      - mongoCluster
    command: bash /docker-entrypoint-initdb.d/initiate-replica.sh

  mongo_2:
    container_name: mongo_2
    image: mongo:\${MONGO_IMAGE}
    ports:
      - "27018:27017"
    volumes:
      - mongo_2_data:/data/db
    env_file:
      - .env
    networks:
      - mongoCluster
    command: mongod --replSet myReplicaSet --bind_ip_all

  mongo_3:
    container_name: mongo_3
    image: mongo:\${MONGO_IMAGE}
    ports:
      - "27019:27017"
    volumes:
      - mongo_3_data:/data/db
    env_file:
      - .env
    networks:
      - mongoCluster
    command: mongod --replSet myReplicaSet --bind_ip_all

  polybot:
    container_name: polybot
    image: \${POLYBOT_IMG_NAME}
    ports:
      - "8443:8443"
    volumes:
      - ~/.aws/credentials:/root/.aws/credentials:ro
    env_file:
      - .env
    networks:
      - mongoCluster
    depends_on:
      - mongo_1
      - mongo_2
      - mongo_3

  yolo5_app:
    container_name: yolo5_app
    image: \${YOLO5_IMG_NAME}
    ports:
      - "8081:8081"
    volumes:
      - ~/.aws/credentials:/root/.aws/credentials:ro
    env_file:
      - .env
    networks:
      - mongoCluster
    depends_on:
      - mongo_1
      - mongo_2
      - mongo_3

networks:
  mongoCluster:
    driver: bridge

volumes:
  mongo_1_data:
    driver: local
  mongo_2_data:
    driver: local
  mongo_3_data:
    driver: local
EOF

# Bring down any existing containers
docker-compose down

# Bring up the services
docker-compose up -d
