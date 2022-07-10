function cleanNodeContent(parentNode) {
	while (parentNode.firstChild) {
		parentNode.removeChild(parentNode.firstChild);
	};
};

function downloadJson(requestPath, callFunction) {
	var xhr = new XMLHttpRequest();
	xhr.open('GET', requestPath);
	xhr.onload = function(evt) {
		var rawData = evt.target.response;
		var jsonData = JSON.parse(rawData);
		callFunction(jsonData);
	};
	xhr.send();
};

function fillElements(setElements) {
	cleanNodeContent(window.elementsList);	
	if (setElements.elements.length > 0) {
		setElements.elements.forEach(function(element) {
			var parts = [];
			element.parts.forEach(function(part) {
				parts.push(part.part.content);
			});
			var parts_text = parts.join(' - ');
			var option = document.createElement('option');
			option.innerHTML = `${element.position}. ${parts_text}`;
			option.setAttribute('value', element.position);
			window.elementsList.appendChild(option);
		});
	} else {
		alert('No one element in this set. Choose other set!')
	};
};

function changeSet(event) {
	var set_id = event.target.value;
	console.log(set_id)
	if (set_id != 'null') {
		downloadJson(`http://${location.host}/api/set_with_elements/?set_id=${set_id}`, fillElements);
		window.elementsList.classList.remove('hidden');
		window.submitButton.classList.remove('hidden');
	} else {
		window.elementsList.classList.add('hidden');
		window.submitButton.classList.add('hidden');
	};
};

var setsList = document.getElementById("select-set");
setsList.onchange = changeSet;
var elementsList = document.getElementById("select-element");
elementsList.onchange = null;
var submitButton = document.getElementById("submit");