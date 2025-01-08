import logging
import logging
from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient

import os

import azure.functions as func

app = func.FunctionApp()


# Get values from environment variables
CONTAINER_REGISTRY_URL = os.getenv("CONTAINER_REGISTRY_URL")
NUMBER_OF_IMAGES_TO_KEEP = os.getenv("NUMBER_OF_IMAGES_TO_KEEP", 3)
SCHEDULE = os.getenv("SCHEDULE", "* * * 1 * *")

@app.timer_trigger(schedule=SCHEDULE, arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed.')
    assert NUMBER_OF_IMAGES_TO_KEEP > 2
    # Call the untagging function
    untag_old_images(CONTAINER_REGISTRY_URL)


def untag_old_images(container_registry_url: str):
    try:
        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()
        client = ContainerRegistryClient(endpoint=container_registry_url, credential=credential)

        logging.info(f"Connecting to container registry: {container_registry_url}")

        for repo in client.list_repository_names():
            # List all tags in the repository
            tags = client.list_tag_properties(repo)
            # Sort tags by timestamp (newest first)
            sorted_tags = sorted(
                tags, 
                key=lambda tag: tag.last_updated_on, 
                reverse=True
            )

            # Keep the last three tags and remove the rest
            tags_to_delete = sorted_tags[NUMBER_OF_IMAGES_TO_KEEP:]
            for tag in tags_to_delete:
                try:
                    logging.info(f"Deleting tag: {tag.name}") 
                    client.delete_tag(repo, tag.name)
                except Exception as e:
                    logging.warning(e)

            logging.info("Successfully untagged old images.")

    except Exception as e:
        logging.error(f"Error while untagging old images: {e}")