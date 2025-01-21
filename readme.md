
- docker login amr-registry-pre.caas.intel.com/eip-chatbot
- docker build . -t eip-chatbot
- docker tag eip-chatbot:latest amr-registry.caas.intel.com/eip-chatbot/eip-chatbot:latest
- docker push amr-registry.caas.intel.com/eip-chatbot/eip-chatbot:latest
