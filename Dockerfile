FROM python:3.11-slim
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
# COPY ./app /code/app
COPY ./ /code/
# CMD ["fastapi", "run", "app/main.py", "--port", "80"]
CMD ["fastapi", "run", "main.py", "--port", "80"]
# CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80"]