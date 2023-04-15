import csv

from gpt_index import SimpleDirectoryReader, LLMPredictor, PromptHelper, GPTSimpleVectorIndex
from langchain.chat_models import ChatOpenAI
import gradio as gr
import sys
import os
import openai
import deepl
data_dir = "data_processed"
index_filename = "index.json"
key_filename = "key"
id_index = "index.json"
model = "gpt-3.5-turbo-0301"


max_input_size = 65536
num_outputs = 4096 * 4
max_chunk_overlap = 30
chunk_size_limit = 50

preparation = {"role": "system", "content": "Verändere den folgenden Text, sodass statt der Angabe der ID ein "
                                                         "html hyperlink zu https://www.fischer.de/de-de/produkte/ID "
                                                         "auf den Produktnamen genannt wird, der in einem neuem Tab geöffnet wird. "
                                            "Gib auschließlich den veränderten Text zurück."}


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
        # self.id_bot = id_bot
        self.llm = llm
        self.image_dict = {}

        # open the CSV file and read the data into the dictionary
        with open('product_id_url.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                product_id, url = row
                self.image_dict[product_id] = url
        self.context = []

    def prepare_input(self, input_text):
        result = "Beantworte die Frage mit einer Liste von Produkten ohne Zusatzinformationen. " + input_text + ". Was ist deren ID?"
        print(result)
        return result

    def insert_images(self, output_text):
        lines = output_text.split("<br>")
        output = ""
        for l in lines:
            start = l.find('/produkte/') + len('/produkte/')
            end = l.find('"', start)
            # extract the id value from the string
            id = str(int(l[start:end]))
            if not id in self.image_dict.keys():
                print(f"invalid id {id}")
                continue
            source = self.image_dict[id]
            image = f"<img src = \"{source}\">"
            output += l + image + "<br>"
        return f"<div style = \"height: 200px; overflow-y: auto;\" >{output}</div >"

    def prepare_output(self, output_text):
        output_string = output_text
        output_string = output_string.replace("ID:", "")
        last_index = 0
        while "(" in output_string[last_index:]:
            start_index = output_string.find("(", last_index)
            end_index = output_string.find(")", last_index)
            last_index = end_index + 2
            if end_index > start_index:
                value = output_string[start_index + 1:end_index]
                previous_len = len(value)
                value = value.replace(" ", "")
                url = f"<a href='https://www.fischer.de/de-de/produkte/{value}' target='_blank'> Link</a>"
                last_index += (len(url) - previous_len)
                output_string = output_string[:start_index] + "(" + url + output_string[end_index:]
        output_string = output_string.replace("\n", "<br>")
        return output_string

    def prepare_output_ai(self, ouput_text):
        response = openai.ChatCompletion.create(
            model=model,
            messages=[preparation, {"role": "user", "content": ouput_text}],
            temperature=0,
        )
        return response["choices"][0]["message"]["content"].replace("\n", "<br>")

    def chat(self, input_text):

        #translator = deepl.Translator(auth_key)
        #result = translator.translate_text(text, target_lang=target_language)
        #translated_text = result.text
        self.context.append("Nutzer: " + input_text)
        input_text = self.prepare_input(input_text)
        response = self.index.query(input_text,similarity_top_k=15,response_mode="compact")
        response = self.prepare_output_ai(response.response)
        print(response)
        response = self.insert_images(response)
        print(response)
        self.context.append("Assistent: " + response)
        return response


def main():
    print("Starting")
    llm = LLMPredictor(ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    index_path = os.path.join(data_dir, index_filename)


    if not os.path.isfile(index_path):
        print("Indexing")
        construct_index(data_dir, llm)
        print("done")

    """"if not os.path.isfile(os.path.join("mappings", id_index)):
        print("Indexing")
        construct_index("mappings", llm)
        print("done")"""""

    index = GPTSimpleVectorIndex.load_from_disk(index_path)
    #id_bot = GPTSimpleVectorIndex.load_from_disk(os.path.join("mappings", id_index))
    chatbot = ChatBot(index, llm)

    iface = gr.Interface(fn=chatbot.chat,
                         inputs=gr.components.Textbox(lines=7, label="Was willst du bauen?"),
                         outputs=gr.outputs.HTML(),
                         title="ToolTutor",
                         output_text_max_length=50000)

    iface.launch(share=False)

def test():
    test = "-Test (ID: 205) \n - BLA (ID: 42) \n -xkd (ID: 50)"
    bot = ChatBot(None, None)
    print(bot.prepare_output(test))


if __name__ == "__main__":
    main()
    #test()