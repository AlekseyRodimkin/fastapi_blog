FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY docker .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]
