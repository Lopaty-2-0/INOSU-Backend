FROM python:3.12-slim

WORKDIR /INOSU

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "python wait_for_redis.py && gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app"]
