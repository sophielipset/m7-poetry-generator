from flask import Flask, render_template, request, url_for, flash, redirect
from poetry_generator import PoetryGenerator

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY='cJQch11oyg34tKkZdvL4jw'
)

@app.route('/')
def index():
    """
    Route to index.html file
    """
    return render_template('index.html')

@app.route('/generator', methods=['GET'])
def generator():
    """
    Route to generator.html file
    """
    return render_template('generator.html')

@app.route('/generator', methods=['POST'])
def scrape_poems():
    """
    Build PoetryGenerator and run a genetic algorithm for 5 generations. 
    Return generator.html template with poem lines and title and the authors
    used to build the poetry. 
    """
    if request.method == 'POST':
        input_text = request.form['insp-text']
        num_lines = request.form['num-lines']
        if not input_text or not num_lines:
            flash('Value is required!')
            return render_template('generator.html')
        else:
            num_lines = int(num_lines)
            generator_ = PoetryGenerator()
            generator_.run_genetic_algo(5, input_text, num_lines)
            poem = generator_.get_top_poem()
            authors = generator_.get_authors()
        return render_template('generator.html', poem=poem.get_lines(), title=poem.title, authors=authors)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
