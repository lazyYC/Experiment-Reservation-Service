let inputIdCounter = 0;

const addButton = document.getElementById('add');
const inputContainer = document.getElementById('time');

addButton.addEventListener('click', () => {
  const inputAndButtonContainer = document.createElement('div');
  inputAndButtonContainer.classList.add('input-and-button-container');

  const input = document.createElement('input');
  const button = document.createElement('button');
  input.id = `input-${inputIdCounter}`;
  input.name = `time-${inputIdCounter}`;
  input.setAttribute('class', `time-input`);

  button.innerHTML = 'Delete';
  button.setAttribute('class', `btn btn-secondary`);
  button.setAttribute('data-input-id', input.id);

  inputAndButtonContainer.appendChild(input);
  inputAndButtonContainer.appendChild(button);
  inputContainer.appendChild(inputAndButtonContainer);

  addButton.parentNode.removeChild(addButton);
  if (inputIdCounter != 11) {
    inputContainer.appendChild(addButton);
  }

  inputIdCounter++;
});

inputContainer.addEventListener('click', (event) => {
  if (event.target.tagName === 'BUTTON') {
    const inputId = event.target.getAttribute('data-input-id');
    const input = document.getElementById(inputId);
    input.parentNode.remove();
  }
});