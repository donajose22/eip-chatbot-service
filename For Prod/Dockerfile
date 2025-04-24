FROM python

ADD requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install --proxy http://proxy-dmz.intel.com:912 -r requirements.txt
ADD langchain_sdk langchain_sdk

ADD main.py main.py
ADD config config
ADD llm llm
ADD routes routes
ADD src src
ADD IntelSHA256RootCA-base64.crt IntelSHA256RootCA-base64.crt
ADD .env .env
ENV APPENV=production

CMD ["python", "main.py"]

# set display port to avoid crash
EXPOSE 5000
ENV DISPLAY=:99