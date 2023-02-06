FROM python:3.9-alpine

WORKDIR /code

COPY ./req.txt /code/req.txt

RUN pip3 install --no-cache-dir --upgrade -r /code/req.txt

RUN touch a.txt

COPY ./sport.py /code/sport.py

CMD ["uvicorn", "sport:app", "--host", "0.0.0.0", "--port", "80"]
