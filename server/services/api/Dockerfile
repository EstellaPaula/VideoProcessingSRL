FROM python:3.8

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get install -y netcat
RUN pip3 install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip3 install -r requirements.txt

# copy source code
COPY . /usr/src/app/

EXPOSE 5000

CMD ["python", "-u", "main.py"]