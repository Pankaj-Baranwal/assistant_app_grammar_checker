from openai import OpenAI
import csv
import pandas as pd
from tempfile import NamedTemporaryFile
from settings import OPENAI_API_KEY
from helpers import create_assistant,  list_assistants, upload_file, list_vector_stores, delete_file, delete_thread, create_thread, add_message, update_assistant

# constants
ASSISTANT_NAME = "Website Doctor AI"
ASSISTANT_INSTRUCTION = "You are an AI assistant that helps to fix the issues such as grammar, spelling, punctuation, extra spaces and style in the given text. Return only the revised text without any comments or suggestions."
VECTOR_STORE_NAME = "vs_for_website_doctor_new"
V1_PROMPT= "From the given file, fix the issues such as grammar, spelling, punctuation, extra spaces and style. Return only the revised text without any comments or suggestions."
client = OpenAI(api_key=OPENAI_API_KEY)


def trigger_assistant(assistant_id, thread_id):
  """Triggers an assistant to process all the messages in a specified thread and returns the resultant messages."""
  try:
    run = client.beta.threads.runs.create_and_poll(
          thread_id = thread_id,
          assistant_id = assistant_id,
    )
    if run.status == 'completed':
      messages = client.beta.threads.messages.list(
        thread_id=thread_id
      )
    else:
      print(run.status)
    return messages
  except Exception as e:
    raise e

def get_or_create_assistant():
  """Retrieves an assistant by name or creates a new one if it doesn't exist."""
  try:
    assistants_list = list_assistants()
    for agent in assistants_list:
      if agent.name == ASSISTANT_NAME:
        return agent.id

    # if assistant does not exists
    assistant = create_assistant(ASSISTANT_NAME, ASSISTANT_INSTRUCTION)
    return assistant.id
  except Exception as e:
    raise e

def get_or_create_vector_store(vector_store_name):
    """Retrieves a vector store by name or creates a new one if it doesn't exist."""
    try:
        vector_store_list = list_vector_stores()
        for vector_store in vector_store_list:
            if vector_store.name == vector_store_name:
                return vector_store.id
        vector_store = client.beta.vector_stores.create(name=vector_store_name)
        return vector_store.id
    except Exception as e:
        raise e


def add_file_to_vector_store(file_path, vector_store_id):
    """Adds a file to a vector store."""
    try:
        file = upload_file(file_path)
        vector_store_file = client.beta.vector_stores.files.create(
          vector_store_id=vector_store_id,
          file_id=file.id
        )

        print(f"File {file.id} added to vector store {vector_store_id}")
        return file.id
    except Exception as e:
        raise e

def delete_file_from_vector_store(file_id, vector_store_id):
    """Deletes a file from a vector store."""
    try:
        vector_store_file = client.beta.vector_stores.files.delete(
          vector_store_id=vector_store_id,
          file_id=file_id
        )
        print(f"File {file_id} deleted from vector store {vector_store_id}")
        delete_file(file_id)

        return vector_store_file
    except Exception as e:
        raise e

# Main function
def generate_insights(message, assistant_id):
    try:
        thread = create_thread()
        message = add_message(thread, message)

        print(f"\nGenerating the insights...")
        messages = trigger_assistant(assistant_id, thread.id)

        delete_thread(thread.id)

        response = messages.data[0].content[-1].text.value
        return response
    except Exception as e:
        raise e

if __name__ == "__main__":
  try:
      extension = "txt"
      csv_file_path = "malpani_data.csv"
      assistant_id = get_or_create_assistant()
      vector_store_id = get_or_create_vector_store(VECTOR_STORE_NAME)
      df = pd.read_csv(csv_file_path)

      for index, row in df.iterrows():
          data = row['Data']
          with NamedTemporaryFile(suffix=f".{extension}", mode="w") as f:
              f.write(data)
              f.seek(0)
              file_id = add_file_to_vector_store(f.name, vector_store_id)
              update_assistant(assistant_id, vector_store_id)

              response = generate_insights(V1_PROMPT, assistant_id)
              delete_file_from_vector_store(file_id, vector_store_id)   

              # add response to the dataframe
              df.loc[index, 'corrected_data'] = response  


      df.to_csv("corrected_data.csv", index=False) 
  except Exception as e:
      raise e

