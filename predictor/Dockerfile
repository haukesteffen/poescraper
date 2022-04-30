FROM tensorflow/tensorflow
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 --no-cache-dir install -r requirements.txt
COPY . .
CMD ["python3", "predictor.py"]
