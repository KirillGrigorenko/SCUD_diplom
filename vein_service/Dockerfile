FROM python:3.11-slim
WORKDIR /opt

RUN apt-get update && apt-get install -y git libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

RUN pip install flask numpy tqdm opencv-python-headless
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

RUN git clone https://github.com/KirillGrigorenko/vein_recognition.git /opt/vein_recognition

COPY server.py .

CMD ["python", "server.py"]
