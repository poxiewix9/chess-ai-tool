import openai
import logfire
from komodo.chessbuddy.config.env import Settings

openai.api_key = Settings.OPENAI_API_KEY

@logfire.instrument(record_return=True)
def format_with_openai(question, result, max_result_chars=10000):
    if isinstance(result, str) and len(result) > max_result_chars:
        truncated_result = result[:max_result_chars] + "\n\n[Result truncated due to length]"
    else:
        truncated_result = result
    client = openai.OpenAI()
    logfire.instrument_openai(client)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Format the following tool result into a detailed, complete, and user-friendly answer to the user's question. "
                    "List all available fields and their values from the tool result. "
                    "Do not summarize, omit, or refer the user elsewhere; include all raw details in your response. "
                    "Output will be displayed on streamlit, format images and tables with markdown. "
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\nResult: {truncated_result}\n\n"
                           f"Format this result as a detailed, readable response for the user."
            }
        ],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
