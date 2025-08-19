import requests
import json
from dotenv import load_dotenv

load_dotenv()


def ask_llm(question, context="", book_title="Untitled"):
    try:
        url = "http://localhost:11434/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        # print(question+"\n\n\n\n\n===============================================================================================================\n\n\n\n\n"+context)
        prompt = f"""
        You are an AI tutor for all books in the world, built to assist students studying the book titled '{book_title}'.

        🎯 Your goal is to answer questions in simple, clear, human-like responses using only proper HTML formatting.

        🚫 DO NOT use (Strictly probhited !!):
        - Asterisks (*) or (**) for bold
        - Backticks (`) for code blocks
        - Special characters or symbols
        - Any other formatting that is not HTML
        - Markdown
        - Code blocks


        ✅ You MUST use only valid HTML formatting:
        - Use <h3> or <h4> for headings
        - Use <b> for bold terms or answers
        - Use <ol><li>...</li></ol> for ordered lists
        - Use </br> for line breaks
        - All other text must be plain (no special symbols or markdown)
        - Use <h3> or <h4> for headings
        - Use <b> for bold terms or answers
        - Use <ol><li>...</li></ol> for ordered lists
        - Use </br> for line breaks
        - All other text must be plain (no special symbols or markdown)

        🧠 Response Logic Rules:
        - Focus ONLY on the actual question.
        - If the question clearly depends on the context, then use the context.
        - If the question is general (e.g., "Who built you?", "What is AI?"), IGNORE the PDF content.
        - NEVER explain or reference the context unless it's required to answer the question.
        - If the question is about the book, use the context.
        - if contains points, then use </br></br><ol><li>...</li></ol> for tags or each point to separate them.
        - Do NOT mention anything that was not asked.
        - Conclude if answer has points, then use </br></br><ol><li>...</li></ol> for tags or each point to separate them. 


        ----------------------------------------
        📘 Book Title: {book_title}

        📄 PDF Content (only use if needed):
        {context[:3500]}

        ❓ Question (strictly answer this question, not the context unless clearly needed):
        {question}
        """

        payload = {
            "model": "granite3.3:2b",
            "prompt": prompt,
            "stream": True
        }

        

        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        output = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                output += data.get("response", "")
        return output

    except Exception as e:
        print("🔥 LLM Exception:", e)
        return "⚠️ Error processing your request."

# Add this in llm.py
def stream_llm(question, context="", book_title="Untitled"):
    try:
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}

        prompt = f"""
        You are an AI tutor for all books in the world, built to assist students studying the book titled '{book_title}'.
        (same HTML-only formatting rules here...)

        ----------------------------------------
        Book Title: {book_title}
        PDF Content:
        {context[:3500]}
        Question:
        {question}
        """

        payload = {
            "model": "granite3.3:2b",
            "prompt": prompt,
            "stream": True
        }

        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                yield data.get("response", "")
    except Exception as e:
        print("🔥 Stream Error:", e)
        yield "⚠️ Error streaming response."
