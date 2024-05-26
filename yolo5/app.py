import time
from pathlib import Path
from flask import Flask, request, jsonify
from detect import run
import uuid
import yaml
from loguru import logger
import os
import boto3
from pymongo import MongoClient, errors

app = Flask(__name__)
logger.add("app.log", rotation="500 MB", level="DEBUG")

s3 = boto3.client('s3')
images_bucket = os.getenv('BUCKET_NAME')

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

MONGODB_URI = "mongodb://mongo_1:27017/"
DATABASE_NAME = "davidhei-database"
COLLECTION_NAME = "davidhei-database-collection"


@app.route('/predict', methods=['POST'])
def predict():
    prediction_id = str(uuid.uuid4())
    logger.info(f'Prediction: {prediction_id}. Start processing.')

    img_name = request.args.get('imgName')
    if not img_name:
        logger.error("Missing 'imgName' parameter in the request.")
        return jsonify({"error": "Missing 'imgName' parameter"}), 400

    local_img_path = f'/usr/src/app/data/images/{img_name}'
    try:
        s3.download_file(images_bucket, img_name, local_img_path)
        logger.info(f'Downloaded image from S3: {images_bucket}/{img_name}')
    except Exception as e:
        logger.error(f'Error downloading image from S3: {str(e)}')
        return jsonify({"error": "Failed to download image from S3"}), 500

    try:
        run(
            weights='yolov5s.pt',
            data='data/coco128.yaml',
            source=local_img_path,
            project='static/data',
            name=prediction_id,
            save_txt=True
        )
        logger.info(f'Prediction: {prediction_id}. Prediction completed.')
    except Exception as e:
        logger.error(f'Error during prediction: {str(e)}')
        return jsonify({"error": "Prediction failed"}), 500

    try:
        predicted_img_path = f'static/data/{prediction_id}/{img_name}'
        s3_predicted_directory_path = 'predicted'
        predicted_file_name = f'{Path(img_name).stem}-predicted{Path(img_name).suffix}'
        full_name_s3 = f'{s3_predicted_directory_path}/{prediction_id}/{predicted_file_name}'

        s3.upload_file(predicted_img_path, images_bucket, full_name_s3)
        logger.info(f'Uploaded predicted image to S3: {full_name_s3}')
    except Exception as e:
        logger.error(f'Error uploading predicted image to S3: {str(e)}')
        return jsonify({"error": "Failed to upload predicted image to S3"}), 500

    try:
        pred_summary_path = Path(f'static/data/{prediction_id}/labels/{Path(img_name).stem}.txt')
        if not pred_summary_path.exists():
            logger.error(f'Prediction: {prediction_id}. Prediction result not found.')
            return jsonify({"error": "Prediction result not found"}), 404

        with open(pred_summary_path) as f:
            labels = [line.split() for line in f.read().splitlines()]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4])
            } for l in labels]

        prediction_summary = {
            'prediction_id': prediction_id,
            'original_img_path': f'{images_bucket}/{img_name}',
            'labels': labels,
            'time': time.time()
        }

        try:
            client = MongoClient(MONGODB_URI)
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]
            result = collection.insert_one(prediction_summary)
            if result.acknowledged:
                logger.info("Data inserted successfully into MongoDB.")
            else:
                logger.error("Failed to insert data into MongoDB.")
        except errors.PyMongoError as e:
            logger.error(f'Error connecting to MongoDB: {str(e)}')
            return jsonify({"error": "Failed to store prediction in database"}), 500
        finally:
            client.close()

        logger.info(f'Prediction: {prediction_id}. Prediction result stored in MongoDB.')

        return jsonify({"prediction_id": prediction_id, "message": "Prediction completed successfully"})

    except Exception as e:
        logger.error(f'Error occurred during prediction: {str(e)}')
        return jsonify({"error": "Error occurred during prediction"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
