FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 80
EXPOSE 36033

CMD [ "python", "./auto_sync.py" ]
