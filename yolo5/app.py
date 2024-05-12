import time
from pathlib import Path
from flask import Flask, request
from detect import run
import uuid
import yaml
from loguru import logger
import os
import boto3
from pathlib import Path
import pymongo

logger.add("app.log", rotation="500 MB", level="DEBUG")

app = Flask(__name__)

s3 = boto3.client('s3')

images_bucket = os.environ.get('BUCKET_NAME')

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

client = pymongo.MongoClient('mongodb://mongo1:27017/')
db = client['davidhei-database']
collection = db['davidhei-database-collection']


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Generates a UUID for this current prediction HTTP request.
        prediction_id = str(uuid.uuid4())
        logger.info(f'Prediction: {prediction_id}. Start processing.')

        img_name = request.args.get('imgName')
        original_img_path = f'{images_bucket}/{img_name}'

        local_img_path = f'/usr/src/app/data/images/{img_name}'

        s3.download_file(images_bucket, img_name, local_img_path)
        logger.info(f'Downloaded image from S3: {original_img_path}')

        run(
            weights='yolov5s.pt',
            data='data/coco128.yaml',
            source=local_img_path,
            project='static/data',
            name=prediction_id,
            save_txt=True
        )
        logger.info(f'Prediction: {prediction_id}. Prediction completed.')

        predicted_img_path = Path(f'static/data/{prediction_id}/{img_name}')
        s3.upload_file(str(predicted_img_path), images_bucket, f'predicted/{prediction_id}/{img_name}')
        logger.info(f'Uploaded predicted image to S3: {predicted_img_path}')

        pred_summary_path = Path(f'static/data/{prediction_id}/labels/{img_name.split(".")[0]}.txt')
        if pred_summary_path.exists():
            with open(pred_summary_path) as f:
                labels = f.read().splitlines()
                labels = [line.split(' ') for line in labels]
                labels = [{
                    'class': names[int(l[0])],
                    'cx': float(l[1]),
                    'cy': float(l[2]),
                    'width': float(l[3]),
                    'height': float(l[4]),
                } for l in labels]

            logger.info(f'Prediction: {prediction_id}. Prediction summary:\n\n{labels}')

            prediction_summary = {
                'prediction_id': prediction_id,
                'original_img_path': original_img_path,
                'predicted_img_path': predicted_img_path,
                'labels': labels,
                'time': time.time()
            }
            collection.insert_one(prediction_summary)
            logger.info(f'Inserted prediction summary into MongoDB.')

            return prediction_summary
        else:
            logger.error(f'Prediction: {prediction_id}. Prediction result not found.')
            return f'Prediction: {prediction_id}. Prediction result not found', 404

    except Exception as e:
        logger.error(f'Error occurred during prediction: {str(e)}')
        return f'Error occurred during prediction: {str(e)}', 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
