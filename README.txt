
HR Interview Answer Evaluator
=============================

This web application allows users to answer common HR interview questions and evaluates their responses using a Word2Vec-based similarity model. It also tracks average scores and displays model answers.

Features
--------
- Select from a list of common HR interview questions
- Submit your answer and receive a similarity score
- View a toggleable model answer for comparison
- Track your average score across unique responses
- Session-based answer history
- Clean UI with Bootstrap 5

Tech Stack
----------
- Frontend: HTML, CSS, Bootstrap 5
- Backend: Flask (Python)
- NLP: Gensim Word2Vec (GoogleNews-vectors-negative300)
- Session Management: Flask session
- Containerization: Docker (optional)

Installation (Local)
--------------------
1. Clone this repository:
   git clone https://github.com/yourusername/hr-interview-evaluator.git
   cd hr-interview-evaluator

2. Install dependencies:
   pip install -r requirements.txt

3. Download Word2Vec Model:
   - Download `GoogleNews-vectors-negative300.bin.gz` from https://code.google.com/archive/p/word2vec/
   - Unzip it and place it in the project root directory.

4. Run the Flask app:
   python app.py

5. Open the app in your browser:
   http://localhost:5000

Running with Docker (Optional)
------------------------------
1. Build the Docker image:
   docker build -t hr-evaluator .

2. Run the container:
   docker run -p 5000:5000 hr-evaluator

3. Visit:
   http://localhost:5000

Project Structure
-----------------
hr-interview-evaluator/
├── templates/
│   └── index.html
├── static/
│   └── style.css (optional)
├── app.py
├── Dockerfile
├── requirements.txt
├── README.txt
└── GoogleNews-vectors-negative300.bin

To Do / Future Enhancements
---------------------------
- Add login functionality for persistent history
- Display performance trends
- Support multi-language responses
- Export answer history and scores

Credits
-------
- Gensim Word2Vec: https://radimrehurek.com/gensim/
- Flask: https://flask.palletsprojects.com/
- Bootstrap: https://getbootstrap.com/
