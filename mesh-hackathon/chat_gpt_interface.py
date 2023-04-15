from gpt_index import SimpleDirectoryReader, LLMPredictor, PromptHelper, GPTSimpleVectorIndex
from langchain.chat_models import ChatOpenAI
import gradio as gr
import sys
import os
import deepl
data_dir = "data_processed"
index_filename = "index.json"
key_filename = "key"

max_input_size = 4096
num_outputs = 512
max_chunk_overlap = 20
chunk_size_limit = 600

with open(key_filename, 'r') as file:
    key_string = file.read()

os.environ["OPENAI_API_KEY"] = key_string


def construct_index(directory_path, llm_predictor):

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    """UnstructuredReader = download_loader("UnstructuredReader", refresh_cache=True)
    loader = UnstructuredReader()
    all_docs = []
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if os.path.isfile(filepath):
            docs = loader.load_data(file=filepath, split_documents=False)
            for d in docs:
                d.extra_info = {"id": filename.replace(".txt", "")}
            all_docs.extend(docs)"""
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk(os.path.join(directory_path, index_filename))

    return index


def load_index(directory_path):
    return GPTSimpleVectorIndex.load_from_disk(directory_path)


class ChatBot:

    def __init__(self, index, llm):
        self.index = index
        self.llm = llm


    def chat(self, input_text):

        #translator = deepl.Translator(auth_key)
        #result = translator.translate_text(text, target_lang=target_language)
        #translated_text = result.text
        response = self.index.query(input_text, response_mode="compact")
        return response.response


def main():
    print("Starting")
    llm = LLMPredictor(ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    index_path = os.path.join(data_dir, index_filename)

    if not os.path.isfile(index_path):
        print("Indexing")
        construct_index(data_dir, llm)
        print("done")

    index = GPTSimpleVectorIndex.load_from_disk(index_path)
    chatbot = ChatBot(index, llm)

    iface = gr.Interface(fn=chatbot.chat,
                         inputs=gr.components.Textbox(lines=7, label="Enter your text"),
                         outputs="text",
                         title="Custom-trained AI Chatbot")

    iface.launch(share=False)


if __name__ == "__main__":
    main()