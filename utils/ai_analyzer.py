import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def detect_document_type(text):
    """
    Use AI to detect document type and structure based on content.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the following document content and detect its type and structure. "
                    "Consider elements like headers, sections, formatting patterns, and content style. "
                    "Respond in JSON format with the following structure: "
                    "{'document_type': string, 'structure': array of section types, 'confidence': float}"
                },
                {"role": "user", "content": text[:2000]}  # Send first 2000 chars for analysis
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Failed to detect document type: {str(e)}")

def analyze_document(text):
    try:
        # First detect document type
        doc_type_info = detect_document_type(text)

        # Then perform full analysis
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the following document and provide: "
                    "1. A concise summary\n"
                    "2. Key insights\n"
                    "3. Main topics\n"
                    "4. Important entities\n"
                    "Respond in JSON format."
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        analysis = json.loads(response.choices[0].message.content)
        # Merge document type information with analysis
        analysis.update({
            "document_type": doc_type_info["document_type"],
            "structure": doc_type_info["structure"],
            "type_confidence": doc_type_info["confidence"]
        })
        return analysis
    except Exception as e:
        raise Exception(f"Failed to analyze document: {str(e)}")

def extract_key_points(text):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Extract the key points from the following text. "
                    "Provide them in a clear, bulleted format in JSON."
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Failed to extract key points: {str(e)}")