FROM python:3.7

RUN apt-get update -y
WORKDIR /opt/app
COPY ./ .
RUN pip install -r requirements.txt --no-cache-dir
EXPOSE 1536
CMD ["python", "__main__.py"]