- pip install --proxy http://proxy-dmz.intel.com:912 -r requirements.txt


- docker login amr-registry.caas.intel.com/eip-chatbot
- docker build . -t eip-chatbot
- docker tag eip-chatbot:latest amr-registry.caas.intel.com/eip-chatbot/eip-chatbot:latest
- docker push amr-registry.caas.intel.com/eip-chatbot/eip-chatbot:latest
