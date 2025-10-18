from langchain_community.llms.ollama import Ollama

model = Ollama(model="llama3.2:3b", temperature=0)

response = model.invoke("Tell me a joke")
print(response)
