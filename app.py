from flask import Flask, render_template, request, redirect, session, url_for
import os
from dotenv import load_dotenv
from gtts import gTTS
from flask import send_file
from markupsafe import Markup
from datetime import datetime
from utils.pdf_parser import extract_text_from_pdf
from models.openrouter_llm import ask_llm

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_book_history():
    """Initialize the book history structure in session"""
    if 'book_history' not in session:
        session['book_history'] = {}
    if 'current_book' not in session:
        session['current_book'] = None

def get_current_book_data():
    """Helper to get current book data with validation"""
    if 'current_book' not in session or 'book_history' not in session:
        return None
    return session['book_history'].get(session['current_book'])


# Add this helper function at the top
def init_session():
    """Initialize or reset session variables"""
    session['pdf_path'] = None
    session['book_title'] = None
    session['pdf_text'] = ""
    session['chat_history'] = []
    session['recent_books'] = session.get('recent_books', [])
    session['all_chat_histories'] = session.get('all_chat_histories', {})

# add a session variable to track recent books
def add_to_recent_books(title):
    recent = session.get('recent_books', [])
    if title not in recent:
        recent.insert(0, title)  # Add to top
    if len(recent) > 10:  # Keep only last 10
        recent = recent[:10]
    session['recent_books'] = recent


# Modify the index route to show recent books
@app.route('/', methods=['GET', 'POST'])
def index():
    init_book_history()
    
    if request.method == 'POST':
        file = request.files['pdf']
        if file and file.filename.endswith('.pdf'):
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text immediately
            pdf_text = extract_text_from_pdf(filepath)
            
            # Initialize book data
            book_data = {
                'filename': filename,
                'original_name': file.filename,
                'upload_time': timestamp,
                'last_accessed': timestamp,
                'pdf_text': pdf_text,
                'chat_history': []
            }
            
            # Store in session
            session['book_history'][filename] = book_data
            session['current_book'] = filename
            session.modified = True
            
            return redirect(url_for('chat'))

    return render_template('index.html', book_history=session.get('book_history', {}))

# Updated chat route
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    init_book_history()
    
    book_data = get_current_book_data()
    if not book_data:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_question = request.form.get('question')
        if user_question:
            # Use the book-specific PDF text from book_data instead of session
            answer = ask_llm(
                user_question, 
                book_data['pdf_text'],  # Changed from session['pdf_text']
                book_data['original_name']
            )
            
            # Add to this book's chat history
            book_data['chat_history'].append({
                'question': user_question,
                'answer': answer
            })
            
            # Update session
            session['book_history'][session['current_book']] = book_data
            session.modified = True
    
    return render_template('chat.html',
                         chat_history=book_data['chat_history'],
                         book_history=session['book_history'],
                         current_book=session['current_book'],
                         current_book_data=book_data)



@app.route('/delete_book/<filename>', methods=['GET', 'POST'])
def delete_book(filename):
    if request.method == 'GET':
        # Show confirmation page
        book_data = session['book_history'].get(filename)
        if not book_data:
            return "Book not found", 404
        return render_template('confirm_delete.html', 
                            book_name=book_data['original_name'],
                            filename=filename)
    
    # Handle POST request (actual deletion)
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Delete physical file if exists
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Clean up from session data
        if 'book_history' in session and filename in session['book_history']:
            # If deleting current book, redirect to index
            if session.get('current_book') == filename:
                session.pop('current_book', None)
            
            # Remove from book history
            del session['book_history'][filename]
            
            # Remove from recent books if exists
            if 'recent_books' in session and filename in session['recent_books']:
                session['recent_books'].remove(filename)
            
            session.modified = True
            
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error deleting book: {e}")
        return "Error deleting book", 500

@app.route('/clear_chat/<filename>')
def clear_chat(filename):
    if 'book_history' in session and filename in session['book_history']:
        session['book_history'][filename]['chat_history'] = []
        session.modified = True
    return redirect(url_for('chat'))


#Loading Books
# Updated load_book route
@app.route('/load_book/<filename>')
def load_book(filename):
    init_book_history()
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        # If book not in history, add it
        if filename not in session['book_history']:
            pdf_text = extract_text_from_pdf(filepath)
            session['book_history'][filename] = {
                'filename': filename,
                'original_name': filename,
                'upload_time': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'last_accessed': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'pdf_text': pdf_text,
                'chat_history': []
            }
        
        # Update last accessed time and set as current
        session['book_history'][filename]['last_accessed'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        session['current_book'] = filename
        session.modified = True
        
        return redirect(url_for('chat'))
    return "Book not found", 404

# Switch Book
@app.route("/switch_book/<title>")
def switch_book(title):
    session['book_title'] = title
    # You should load corresponding chat history for this book here
    return redirect("/chat")  # Or whatever your chat route is


@app.route('/mcq') #Verified
def mcq():
    context = session.get('pdf_text', '')
    title = session.get('book_title', 'Untitled')
    questions = ask_llm("""
    I NEED EXACT FORMAT FOR EVERY REQUEST !!!
    Create 10 important useful career and knowledge based multiple choice questions with 4 options each andn final correct answer must be atlast for all attempted answers !! as exact same as like
    EXACT NOTE : Only use the Exact Format for every Request !!:
    
    <h3><bold>1.</bold> What is the ultimate GNU/Linux learning guide discussed in this document?</h3>
    For options, use list tag and mention options A, B, C, D.
    <br>
    <h3><bold>2.</bold> Which book is recommended for mastering the Linux command line?</h3>
    2nd question options and so on upto 10 questions with options A, B, C, D for each question.
    ....
    ....
    <h2>Answers:</h2>
    <br>
    1. A (according to solution of that question)<br>
    2. D (according to solution of that question)<br>
    3. B (according to solution of that question)<br>
    ...
    """, context, title)
    return render_template('mcq.html', questions=questions, title=title)

@app.route('/summarize')
def summarize():
    book_data = get_current_book_data()
    if not book_data:
        return redirect(url_for('index'))
    
    summary = ask_llm(
        f"Summarize the book '{book_data['original_name']}' in a few key points.", 
        book_data['pdf_text'],  # Changed from session['pdf_text']
        book_data['original_name']
    )
    return render_template('summary.html', summary=summary, title=book_data['original_name'])

@app.route('/flashcards')
def flashcards():
    book_data = get_current_book_data()
    if not book_data:
        return redirect(url_for('index'))
    
    cards = ask_llm(
        "Extract 10 key concepts or definitions from this PDF as flashcards (term + explanation)",
        book_data['pdf_text'],  # Changed from session['pdf_text']
        book_data['original_name']
    )
    return render_template('flashcards.html', cards=cards, title=book_data['original_name'])

@app.route('/tts')
def tts():
    book_data = get_current_book_data()
    if not book_data:
        return redirect(url_for('index'))
    
    summary = ask_llm(
        "Give an audio-friendly spoken summary of this PDF.",
        book_data['pdf_text'],  # Changed from session['pdf_text']
        book_data['original_name']
    )
    
    tts = gTTS(text=summary, lang='en')
    tts.save("summary.mp3")
    return send_file("summary.mp3", as_attachment=True)

@app.route('/cleanup_books', methods=['POST'])
def cleanup_books():
    """Clean up books that don't exist in uploads folder"""
    try:
        existing_files = set(os.listdir(app.config['UPLOAD_FOLDER']))
        books_to_remove = []
        
        # Find books that don't exist in uploads folder
        for filename, book_data in session.get('book_history', {}).items():
            if filename not in existing_files:
                books_to_remove.append(filename)
        
        # Remove them from session
        for filename in books_to_remove:
            if filename in session['book_history']:
                del session['book_history'][filename]
            if 'recent_books' in session and filename in session['recent_books']:
                session['recent_books'].remove(filename)
            if session.get('current_book') == filename:
                session.pop('current_book', None)
        
        session.modified = True
        return {'status': 'success', 'removed': books_to_remove}
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return {'status': 'error'}, 500


# @app.route('/summarize')
# def summarize():
#     if 'current_book' not in session or 'book_history' not in session:
#         return redirect(url_for('index'))
    
#     book_data = session['book_history'][session['current_book']]
#     summary = ask_llm(f"Summarize the book '{book_data['original_name']}' in a few key points.", 
#                      session['pdf_text'], book_data['original_name'])
#     return render_template('summary.html', summary=summary, title=book_data['original_name'])

# @app.route('/flashcards')
# def flashcards():
#     if 'current_book' not in session or 'book_history' not in session:
#         return redirect(url_for('index'))
    
#     book_data = session['book_history'][session['current_book']]
#     cards = ask_llm("Extract 10 key concepts or definitions from this PDF as flashcards (term + explanation)", 
#                    session['pdf_text'], book_data['original_name'])
#     return render_template('flashcards.html', cards=cards, title=book_data['original_name'])



# @app.route('/tts')
# def tts():
#     if 'current_book' not in session or 'book_history' not in session:
#         return redirect(url_for('index'))
    
#     book_data = session['book_history'][session['current_book']]
#     summary = ask_llm("Give an audio-friendly spoken summary of this PDF.", 
#                      session['pdf_text'], book_data['original_name'])
    
#     tts = gTTS(text=summary, lang='en')
#     tts.save("summary.mp3")
#     return send_file("summary.mp3", as_attachment=True)


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
