from openai import OpenAI
from settings import OPENAI_API_KEY

client = OpenAI(
    api_key=OPENAI_API_KEY    
)


# assistant helpers
def create_assistant(assistant_name,
                     instruction,
                     model="gpt-4-turbo"):
    """Create an OpenAI assistant with the given name and instruction"""
    try:
        assistant = client.beta.assistants.create(
            name=assistant_name,
            instructions=instruction,
            model=model,
            tools=[{"type": "file_search"}]
        )

        return assistant
    except Exception as e:
        raise e


def update_assistant(assistant_id, vector_store_id):
    """Update an OpenAI assistant with the given vector store"""
    try:
        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
          tools=[{"type": "file_search"}],
          tool_resources={
              "file_search": {
                "vector_store_ids": [vector_store_id]
                }
          },
        )
        return assistant
    except Exception as e:
        raise e


def list_assistants():
    """List all OpenAI assistants"""
    try:
        assistants = client.beta.assistants.list()
        return assistants.data
    except Exception as e:
        raise e

# Thread helpers
def create_thread():
    """Create a new thread in the assistant"""
    try:
        new_thread = client.beta.threads.create()
        print(f"Thread {new_thread.id} created successfully ")
        return new_thread
    except Exception as e:
        raise e


def delete_thread(thread_id):
    """Delete a thread with the given thread_id"""
    try:
        response = client.beta.threads.delete(thread_id=thread_id)
        if response.deleted:
            print(f"\nThread {thread_id} deleted successfully")
            return response
        print(f"\nThread {thread_id} could not be deleted")
    except Exception as e:
        raise e

# File handling helpers
def upload_file(file_path):
    """Upload a file to the OpenAI API"""
    try:
        file = client.files.create(
            file=open(file_path, "rb"),
            purpose='assistants'
        )
        print(f"File {file.id} uploaded successfully")
        return file
    except Exception as e:
        raise e


def delete_file(file_id):
    """Delete a file with the given file_id"""
    try:
        response = client.files.delete(file_id=file_id)
        if response.deleted:
            print(f"\nFile {file_id} deleted successfully")
            return response
        print(f"\nFile {file_id} could not be deleted")
    except Exception as e:
        raise e

# Extras
def list_vector_stores():
    """List all vector stores"""
    try:
        vector_stores = client.beta.vector_stores.list()
        return vector_stores.data
    except Exception as e:
        raise e

def add_message(thread, user_message):
    """Adds a message from the user to a specified thread."""
    try:
        message = client.beta.threads.messages.create(thread_id=thread.id,
                                                    role="user",
                                                    content=user_message)
        return message
    except Exception as e:
        raise e

