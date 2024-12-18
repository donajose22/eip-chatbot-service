FROM python:3.12

ADD requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install --proxy http://proxy-dmz.intel.com:912 -r requirements.txt
ADD .venv/Lib/site-packages/langchain_sdk langchain_sdk
# RUN pip install --proxy http://proxy-dmz.intel.com:912 https://af01p-fm.devtools.intel.com/artifactory/igpt_forge_gaas_python_sdk-fm-local/api/storage/langchain_sdk-0.1.2/0.1.2/langchain_sdk-0.1.2-py3-none-any.whl

ADD main.py main.py
ADD config config
ADD llm llm
ADD routes routes
ADD src src
ADD IntelSHA256RootCA-base64.crt IntelSHA256RootCA-base64.crt
ADD .env .env
ENV APP_ENV=development
# ENV HTTP_PROXY=http://proxy-dmz.intel.com:912
# ENV HTTPS_PROXY=http://proxy-dmz.intel.com:912

CMD ["python", "main.py"]

# RUN waitress-serve --port 8080 main:app
# set display port to avoid crash
EXPOSE 5000
ENV DISPLAY=:99