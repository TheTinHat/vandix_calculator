FROM ubuntu:focal

LABEL David Swanlund
ENV PROJ_DIR /usr/local
EXPOSE 8080
RUN apt update -y
RUN apt install -y python3-pip
WORKDIR /app
COPY requirements.txt .
COPY vandix.py .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["vandix.py"]