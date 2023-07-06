import os

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from lib.vectorize import vectorize_document, get_db

from dotenv import load_dotenv

# Load the Token from .env file
load_dotenv()

if os.path.exists("./storage"):
    vector_store = get_db()
    retriever = vector_store.as_retriever()
else:
    path = "./docs/example.pdf"
    vectorize_document(path)
    vector_store = get_db()
    retriever = vector_store.as_retriever()


llm = ChatOpenAI(
    model_name='gpt-3.5-turbo', 
    )
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

def prompt_model(name, user_input):
    
    query = f"""
    You are no longer an AI model. You are Donna, a highly skilled secretary with a vibrant personality.
    I {name}, an employee, am telling you Donna the following statement:
    
    {user_input}
    
    Using the information at your disposal please answer as best as you can to the following statement.
    
    """
    try:
        llm_response = qa(query)
        return llm_response["result"]
    except Exception as err:
        return f'Exception occurred. Please try again {str(err)}'