import time
import weaviate
from integration.integration_util import TestFailedException

schema = {
    "classes": [
        {
            "class": "Label",
            "description": "a label describing a message",
            "properties": [
                {
                    "name": "name",
                    "description": "The name of this label",
                    "dataType": ["string"],
                },
                {
                    "name": "description",
                    "description": "The description of this label",
                    "dataType": ["text"],
                }
            ]
        },
        {
            "class": "Message",
            "description": "a message from written by a person",
            "properties": [
                {
                    "name": "content",
                    "description": "The content of the message",
                    "dataType": ["text"],
                },
                {
                    "name": "labeled",
                    "description": "The label assigned to this message",
                    "dataType": ["Label"],
                }
            ]
        }
    ]
}

query = """
{
  Get {
      Message {
        content
        _additional {
            id
        }
        labeled {
          ... on Label {
            name
            description
          }
        }
      }
    }
}
"""


def contextual(client: weaviate.Client):
    print("Test classification")
    client.schema.create(schema)

    # Create labels
    client.data_object.create(
        {
            "name": "positive",
            "description": "A positive, good, happy or supporting message."
        },
        "Label"
    )
    client.data_object.create(
        {
            "name": "negative",
            "description": "A negative, bad, sad or disrupting message."
        },
        "Label"
    )

    client.data_object.create(
        {
            "content": "ALERT: So now we find out that the entire opponent “hit squad” illegally wiped their phones clean just prior to the investigation of them, all using the same really dumb reason for this “accident”, just like other people smashing her phones with a hammer, & DELETING THEIR EMAILS!"
        },
        "Message"
    )
    client.data_object.create(
        {
            "content": "I'm so happy, proud and excited to be a part of this community for the rest of my days."
        },
        "Message"
    )
    client.data_object.create(
        {
            "content": "thank you for reminding the world of our cause"
        },
        "Message"
    )

    time.sleep(2.0)
    client.classification.schedule()\
        .with_type("text2vec-contextionary-contextual")\
        .with_class_name("Message")\
        .with_based_on_properties(["content"])\
        .with_classify_properties(["labeled"])\
        .with_wait_for_completion()\
        .do()

    result = client.query.raw(query)
    labeled_messages = result["data"]["Get"]["Message"]
    for message in labeled_messages:
        if message["labeled"] is None:
            raise TestFailedException("Message is not labeled after classification!")


if __name__ == "__main__":
    client = weaviate.Client("http://localhost:8080")
    contextual(client)
