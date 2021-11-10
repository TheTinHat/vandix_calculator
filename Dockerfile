FROM ubuntu:focal

LABEL David Swanlund
RUN apt update -y
RUN apt install -y python3-pip
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt


ENTRYPOINT ["python3"]
CMD ["vandix.py"]