FROM python:3.13-alpine
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
RUN pip install https://storage.googleapis.com/tensorflow/versions/2.20.0/tensorflow_cpu-2.20.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
COPY . /code
CMD ["fastapi", "run", "main.py", "--port", "80"]
