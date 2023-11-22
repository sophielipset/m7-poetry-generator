var synthesis = window.speechSynthesis; 

function sayText(helloWorld) {
    console.log(text)
    if ('speechSynthesis' in window) { 
        if (helloWorld) { 
            var text = "Hello, world!";
        } 
        else {
            var lines = document.querySelectorAll(".generated-poem");
        }
        var poem = ''
        lines.forEach((line) => {
            var utterance = new SpeechSynthesisUtterance(line.innerHTML);
            synthesis.speak(utterance);  
            poem += line.innerHTML
        });
        storePoem(poem)
        var utterance = new SpeechSynthesisUtterance(text);
        var voices = synthesis.getVoices();
        utterance.voice = voices[0];
        console.log({
            name: utterance.voice.name,
            lang: utterance.voice.lang
        })
        synthesis.speak(utterance);  
    } else {
        console.log("Speech synthesis is not supported.")
    }
}

function logVoices() { 
    var voices = synthesis.getVoices();
    voices.forEach(function (voice) { 
        console.log({
            name: voice.name,
            lang: voice.lang
        })
    })
}

function storePoem(poem) {
    console.log('storing poem')
    const title = document.querySelector('#poem-title').innerHTML;
    localStorage.setItem(
        title,
        poem
    );
}

function displayLocalStorage() {
    // retrieve all keys from localStorage
    const keys = Object.keys(localStorage);

    // create HTML structure to display poem data 
    const localStorageDiv = document.getElementById('localStorageData');
    const ul = document.createElement('ul');

    // iterate through keys and create list items to display title-line pairs
    keys.forEach(title => {
    const lines = localStorage.getItem(title);
    const li = document.createElement('li');
    li.textContent = `${title}: ${lines}`;
    ul.appendChild(li);
    });

    // append the list to the div element
    localStorageDiv.appendChild(ul);
}
