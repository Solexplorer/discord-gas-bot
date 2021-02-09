FROM python:3

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "./gas_bot.py", "-s", "ethgasstation" ]
