function editComment(event) {
	var buttonElement = event.target;
	var textElement = buttonElement.parentNode.children[0];
	var text = textElement.innerHTML; //.firstChild
	var type = event.target.dataset.type;
	var id = event.target.dataset.id;
	// console.log(event.target.dataset.type, event.target.dataset.id)
	switch (type) {
			case 'element':
			var name = 'abstract';
			break;
			case 'part':
			var name = 'comment';
			break;
		};
	var emptyText = `No ${name} yet`;
	if (text == emptyText) {
		text = '';
	};

	var previousText = textElement.innerHTML;
	var textToSend = false;
	var newText = prompt("Insert text", text);
	// console.log(newText, previousText)
	if (newText && previousText != newText) {
		// console.log(textElement)
		textElement.classList.remove("faded");
		textElement.innerHTML = newText;
		// console.log(textElement)
		var textToSend = newText;
	} else if (newText == '' && previousText != emptyText) {
		textElement.classList.add("faded");
		textElement.innerHTML = emptyText;
		var textToSend = null;
		// console.log(textToSend);
	};	
	if (textToSend != false) {
		// console.log(type, id, textToSend)
		comment_request(type, id, textToSend);
	};
};

function comment_request(type, id, textToSend) {
	// Sending and receiving data in JSON format using POST method
	var xhr = new XMLHttpRequest();
	// xhr.open("POST", 'http://192.168.0.100:12345', true);
	xhr.open("POST", window.csrf_token_comment_element.action, true);
	xhr.setRequestHeader("X-CSRFToken", window.csrf_token_comment_element.querySelector('input').value);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function(event) {
		if (xhr.readyState === 4 && xhr.status === 200) {
			var json = JSON.parse(xhr.responseText);
			alert(json["response"]);
			// alert(xhr.responseText);
		};
	};
	var data = JSON.stringify({'type': type,
								'id': id,
								'text': textToSend});
	xhr.send(data);	
};

var editButtons = document.body.querySelectorAll('.edit_button.edit_active');
editButtons.forEach(function(editButton) {
	editButton.onclick = editComment;
	// console.log(editButton)
});

window.csrf_token_comment_element = document.getElementById("csrf_token_comment");