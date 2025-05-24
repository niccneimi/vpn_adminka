FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "django_adminka/manage.py", "runserver", "0.0.0.0:1234"]
