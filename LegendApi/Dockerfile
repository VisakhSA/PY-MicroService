FROM python:3.9-alpine

WORKDIR /code

COPY ./req.txt /code/req.txt

RUN pip3 install --no-cache-dir --upgrade -r /code/req.txt

RUN touch a.txt

COPY ./legend.py /code/legend.py

CMD ["uvicorn", "legend:app", "--host", "0.0.0.0", "--port", "81"]
