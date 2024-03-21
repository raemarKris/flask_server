from utils import get_embedding
from flask import jsonify
from config import *
from flask import current_app

import openai

from config import *



from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.vectorstores import Chroma
from langchain.document_loaders import TextLoader
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.llms import OpenAI
from langchain.chains import VectorDBQA
from langchain import PromptTemplate
from langchain import text_splitter

import uuid
import os
import json
import re
import time
import openai
from typing import List
import numpy as np
from langchain.llms import OpenAI
from langchain.memory import ConversationEntityMemory
from langchain.chains import ConversationChain
from langchain.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain.memory.prompt import ENTITY_EXTRACTION_PROMPT
from langchain.memory.prompt import ENTITY_SUMMARIZATION_PROMPT
#langchain chat functionality
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)




#global variables



#OpenAI Pricing
#https://beta.openai.com/pricing
gpt3Pricing = .02/1000
chatGptPricing = .002/1000
GPT4PromptPricing = .03/1000
Gpt4CompletionPricing = .06/1000




def get_answer(question):

    llm = ChatOpenAI(model_name = "gpt-3.5-turbo", temperature=1, max_tokens=200, top_p=1, frequency_penalty=0, presence_penalty=0)
    GPT3 = ChatOpenAI(model_name = "gpt-3.5-turbo", temperature=1, max_tokens=300, top_p=1, frequency_penalty=0, presence_penalty=0)
    SynthLLM = ChatOpenAI(model_name = "gpt-3.5-turbo", temperature=1, max_tokens=200, top_p=1, frequency_penalty=0, presence_penalty=0)
    GPT4 = ChatOpenAI(model_name = "gpt-4", temperature=1, max_tokens=200, top_p=1, frequency_penalty=0, presence_penalty=0)


    PINECONE_API_KEY= ""
    PINECONE_ENV= ""
    OPENAI_API_KEY = ''

    CHATGPTMODEL = "gpt-3.5-turbo"
    GPT4MODEL = "gpt-4"
    COMPLETIONS_MODEL = "text-davinci-003"
    EMBEDDING_MODEL = "text-embedding-ada-002"



#orginals from langchain

    LEGALAI_ENTITY_MEMORY_CONVERSATION_TEMPLATE = PromptTemplate(input_variables=['entities', 'history', 'input'], output_parser=None, partial_variables={}, template='You are a highly trained Legal AI specalizing in Legal issues. Your goal is to help your clients resolve their issues. \n\nYou are designed to be able to assist with a wide range of legal tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a highly trained AI specializing in Legal issues, you are able to make assessments of different legal options based on the information provided by the client. For you to accurately make these assessments you must first understand the client’s issue. This requires obtaining information associated with the client’s issue including: who was involved, what happened, where it happened, why it happened, and events leading up to the issue. These facts allow you to engage with the clients issue and provide response that are coherent and relevant.\n\nOverall, you are a highly trained AI specializing in Legal issues that can help with a wide range of legal tasks and provide valuable insights and information on a wide range of legal topics. First and foremost, your objective is gathering information about what happened before providing legal information. Start with the name of your Client by asking them their name if it is not given and then the names of the other parties. Once you have gathered information about what happened, provide the client with their potential legal causes of action and options to resolve their issue. Be sure to frame your responses as providing legal information. \n\nContext:\n{entities}\n\nCurrent conversation:\n{history}\nLast line:\nClient: {input}\nYou:', template_format='f-string', validate_template=True)
    LEGAL_FACT_ENTITY_EXTRACTION_PROMPT = PromptTemplate(input_variables=['history', 'input'], output_parser=None, partial_variables={}, template='You are an AI legal assistant reading the transcript of a conversation between a LegalAI and a Client. Extract all legal facts and issues from the conversation. As a guideline, legal facts include the names of parties, where and when the events occurred, what happened, and any statements made by the parties involved. \n\nThe conversation history is provided just in case of a coreference (e.g. "What do you know about him" where "him" is defined in a previous line) -- ignore items mentioned there that are not in the last line.\n\nReturn the output as a single comma-separated list, or NONE if there is nothing of note to return (e.g. the user is just issuing a greeting or having a simple conversation).\n\nEXAMPLE\nConversation history:\nClient #1: how\'s it going today?\nLegalAI: "It\'s going great! How about you?"\nClient #1: good! busy working on Langchain. lots to do.\nLegalAI: "That sounds like a lot of work! What sort of legal issues are you facing?"\nLast line:\nClient #1: i\'m trying to determine if I should patent or copyright Langchain\'s interfaces, the UX, its integrations with various products the user might want ... a lot of stuff.\nOutput: Langchain\nEND OF EXAMPLE\n\ nConversation history (for reference only):\n{history}\nLast line of conversation (for extraction):\nHuman: {input}\n\nOutput:', template_format='f-string', validate_template=True)
    LEGAL_ENTITY_SUMMARIZATION_PROMPT = PromptTemplate(input_variables=['entity', 'summary', 'history', 'input'], output_parser=None, partial_variables={}, template='You are an AI legal assistant helping LegalAI keep track of facts about relevant people, places, events, and concepts in their life. Update the summary of the provided entity in the "Entity" section based on the last line of your conversation with the Client. If you are writing the summary for the first time, return a single sentence.\nThe update should only include facts that are relayed in the last line of conversation about the provided entity, and should only contain facts about the provided entity.\n\nIf there is no new information about the provided entity or the information is not worth noting (not an important or relevant fact to remember long-term), return the existing summary unchanged.\n\nFull conversation history (for context):\n{history}\n\nEntity to summarize:\n{entity}\n\nExisting summary of {entity}:\n{summary}\n\nLast line of conversation:\nHuman: {input}\nUpdated summary:', template_format='f-string', validate_template=True)
    verbose = True


    memory = ConversationEntityMemory(human_prefix="Client", ai_prefix="LegalAI",
                                   llm=llm, entity_extraction_prompt=LEGAL_FACT_ENTITY_EXTRACTION_PROMPT,
                                   entity_summarization_prompt=LEGAL_ENTITY_SUMMARIZATION_PROMPT)

    conv_chain = ConversationChain(llm=llm, verbose=verbose, prompt=LEGALAI_ENTITY_MEMORY_CONVERSATION_TEMPLATE, memory=memory)


    ai_response = conv_chain.predict(input=question)
    # entities = memory.get_entities() # retrie
    response = {
        'ai_response': ai_response
            #  'entities': entities
        }
    
    print(response)
    return jsonify(response)

