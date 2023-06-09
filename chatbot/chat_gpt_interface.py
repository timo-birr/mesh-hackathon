import csv

from gpt_index import SimpleDirectoryReader, LLMPredictor, PromptHelper, GPTSimpleVectorIndex
from langchain.chat_models import ChatOpenAI
import gradio as gr
import os
import openai

data_dir = "data_processed"
index_filename = "index.json"
key_filename = "key"
model = "gpt-3.5-turbo-0301"
url_mapping_path = os.path.join("mappings", "product_id_url.csv")

max_input_size = 65536
num_outputs = 4096 * 4
max_chunk_overlap = 30
chunk_size_limit = 50

preparation = {"role": "system", "content": "Verändere den folgenden Text, sodass statt der Angabe der ID ein "
                                            "html hyperlink zu https://www.fischer.de/de-de/produkte/ID "
                                            "auf den Produktnamen genannt wird, der in einem neuem Tab geöffnet wird. "
                                            "Gib auschließlich den veränderten Text zurückund kürze den Text nicht "
                                            "mehr als nötig"}

# this is needed to access the openai api
with open(key_filename, 'r') as file:
    key_string = file.read()

os.environ["OPENAI_API_KEY"] = key_string


def construct_index(directory_path, llm_predictor):
    """
    Creates the index to access the data of fischer that is stored in directory_path
    Additionally writes the created index to directory path
    Warning this may take a long time ( > 1hour and costs about 3 dollars), also check your openai api rate limits
    :param directory_path: path to the directory with all preprocessed text files that contain the product info
    :param llm_predictor: the predictor to create the embedding for
    :return: the resulting index
    """
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk(os.path.join(directory_path, index_filename))

    return index

def has_non_digits(input_str):
    """
    Checks if the input string contains characters other than digits.
    Returns True if input_str contains non-digit characters, False otherwise.
    """
    if input_str == "":
        return True
    for char in input_str:
        if not char.isdigit():
            return True
    return False


def load_index(directory_path):
    """
    Convinience Method to load Index from disk
    :param directory_path: the path to the file where the index is stored (index.json)
    :return: the loaded index
    """
    return GPTSimpleVectorIndex.load_from_disk(directory_path)


class ChatBot:

    def __init__(self, index, llm):
        self.index = index
        # self.id_bot = id_bot
        self.llm = llm
        self.image_dict = {}

        # open the CSV file and read the data into the dictionary
        # safe this dict so it is easy to map products to preview images later
        with open(url_mapping_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                product_id, url = row
                self.image_dict[product_id] = url

    def prepare_input(self, input_text):
        # there needs to be context for the model in order for it to know exactly what to do
        result = "Beantworte die Frage mit einer Liste von Produkten der Firma Fischer ohne Zusatzinformationen. " + \
                 input_text + ". Was ist deren ID?"
        return result

    def insert_images(self, output_text):
        lines = output_text.split("<br>")
        output = ""
        for l in lines:
            start = l.find('/produkte/') + len('/produkte/')
            end = l.find('"', start)
            # extract the id value from the string
            id = l[start:end]
            if has_non_digits(id):
                print(f"invalid id {id}")
                continue
            id = str(int(id))
            if not id in self.image_dict.keys():
                print(f"invalid id {id}")
                continue
            source = self.image_dict[id]
            image = f"<img src = \"{source}\">"
            output += l + image + "<br>"
        return f"<div style = \"height: 600px; overflow-y: auto;\" >{output}</div >"

    def prepare_output_ai(self, ouput_text):
        response = openai.ChatCompletion.create(
            model=model,
            messages=[preparation, {"role": "user", "content": ouput_text}],
            temperature=0,
        )
        return response["choices"][0]["message"]["content"].replace("\n", "<br>")

    def chat(self, input_text):
        input_text = self.prepare_input(input_text)
        # if the input query is not precise enough the model needs to query to much data which leads to the
        # model crashing
        # this is not optimal handling but the fastest to implement
        try:
            response = self.index.query(input_text, similarity_top_k=15, response_mode="compact")
            response = self.prepare_output_ai(response.response)
            response = self.insert_images(response)
        except:
            response = "Bitte gib mehr Kontext"
        # if no valid id could be found the query was perhaps not precise enough
        if response == "":
            response = "Bitte gib mehr Kontext"
        return response


def main():
    print("Starting")
    llm = LLMPredictor(ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    index_path = os.path.join(data_dir, index_filename)

    # only create index if it does not already exist
    if not os.path.isfile(index_path):
        print("Indexing")
        construct_index(data_dir, llm)
        print("done")

    index = GPTSimpleVectorIndex.load_from_disk(index_path)
    chatbot = ChatBot(index, llm)

    iface = gr.Interface(fn=chatbot.chat,
                         inputs=gr.components.Textbox(lines=7, label="Was willst du bauen?"),
                         outputs=gr.outputs.HTML(),
                         title="ToolTutor")

    iface.launch(share=False)


if __name__ == "__main__":
    main()
