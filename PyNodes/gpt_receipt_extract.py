import os
import base64
import json
import argparse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key= api_key)
gpt_model = os.getenv("GPT_RECEIPT_EXTRACT_MODEL")

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_receipt_text(image_path: str) -> str:
  base64_image = encode_image(image_path)

  response = client.chat.completions.create(
    model=gpt_model,
    temperature=0.2,
    messages=[
      {
        "role": "user",
        "content": [
          {
              "type": "text", 
              "text": '''Read the following receipt image and return it's text as clean JSON under the following schema:
              {
                "type": "object",
                "properties": {
                  "store_name": {
                    "type": "string",
                    "description": "The brand name of the store where the purchase was made."
                  },
                  "store_branch": {
                    "type": "string",
                    "description": "The name of particular branch where the purchase was made."
                  },
                  "store_addr": {
                    "type": "string",
                    "description": "The address of the store."
                  },
                  "store_location": {
                    "type": "string",
                    "description": "The city, place or area were the store is."
                  },
                  "entity_id": {
                    "type": "string",
                    "description": "The tax or business identification number of the store."
                  },
                  "phone": {
                    "type": "string",
                    "description": "The contact phone number of the store."
                  },
                  "date": {
                    "type": "string",
                    "description": "The date of the transaction."
                  },
                  "time": {
                    "type": "string",
                    "description": "The time of the transaction."
                  },
                  "subtotal": {
                    "type": "string",
                    "description": "The subtotal amount of the purchase."
                  },
                  "svc": {
                    "type": "string",
                    "description": "Service charges if applicable."
                  },
                  "tax": {
                    "type": "string",
                    "description": "The tax amount."
                  },
                  "total": {
                    "type": "string",
                    "description": "The total amount paid."
                  },
                  "tips": {
                    "type": "string",
                    "description": "The tips amount if any."
                  },
                  "total_discount": {
                    "type": "string",
                    "description": "Total discount applied to the transaction."
                  },
                  "line_items": {
                    "type": "array",
                    "description": "List of items purchased.",
                    "items": {
                      "type": "object",
                      "properties": {
                        "item_key": {
                          "type": "string",
                          "description": "Unique identifier for the item."
                        },
                        "item_name": {
                          "type": "string",
                          "description": "Text description of the item."
                        },
                        "item_value": {
                          "type": "string",
                          "description": "Price of a single unit of the item."
                        },
                        "item_quantity": {
                          "type": "string",
                          "description": "Quantity of the item purchased."
                        },
                        "item_total": {
                          "type": "string",
                          "description": "Total amount charged for this purchase's item."
                        },
                      }
                    }
                  },
                  "line_discounts": {
                    "type": "array",
                    "description": "List of discounts applied to specific items.",
                    "items": {
                      "type": "object",
                      "properties": {
                        "discount_key": {
                          "type": "string",
                          "description": "Item identifier to which the discount is applied."
                        },
                        "discount_name": {
                          "type": "string",
                          "description": "Text of the discount."
                        },
                        "discount_value": {
                          "type": "string",
                          "description": "Monetary value of the discount."
                        }
                      }
                    }
                  }
                }
              }
              '''},
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
            }
          },
        ],
      }
    ]
  )

  result: str = response.choices[0].message.content
  return result.removeprefix("```json").removesuffix("```").strip()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Convert a receipt image into receipt JSON.")
  parser.add_argument('--image_path', type=str, help='The path to the image file')
  parser.add_argument('--output_directory', type=str, help='The directory to save the processed JSON')
  args = parser.parse_args()

  image_name = os.path.splitext(os.path.basename(args.image_path))[0]

  result = get_receipt_text(args.image_path)

  with open(os.getenv("GPT_RECEIPT_EXTRACT_RAW_OUTPUT","output_raw.json"), 'w') as file:
      file.write(result)

  with open(os.path.join(args.output_directory, f"{image_name}.json"), 'w') as json_file:
      data = json.loads(result)
      json.dump(data, json_file, indent=4)
