from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")  # or paste your key directly here
)

def ask_llm(question, context="", book_title="Untitled"):
    try:
        completion = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": f"You are a helpful AI tutor for the book titled '{book_title}'. Use the provided PDF content below to answer user's questions based only on it."},
                {"role": "user", "content": f"""You are an AI assistant helping a student.

                    Answer the question based strictly on the following PDF content. 
                    Please return your response in **HTML formatted text** using:
                    - Headings (`<h3>`, `<h4>`)
                    - Bold (`<b>`) for important terms or answers
                    - Ordered list (`<ol><li>...</li></ol>`) if it's a list
                    - Use `<br>` for line breaks where needed

                    PDF Content:
                    {context[:3500]}

                    Question:
                    {question}
                    """}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print("🔥 LLM Exception:", e)
        return "⚠️ Error processing your request."
