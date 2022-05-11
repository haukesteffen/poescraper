FROM tensorflow/tensorflow
WORKDIR /app
RUN apt install --no-install-recommends -y libpq-dev
COPY requirements.txt requirements.txt
RUN pip3 --no-cache-dir install -r requirements.txt
COPY . .
CMD ["python3", "trainer.py"]
