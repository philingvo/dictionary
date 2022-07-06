String.prototype.capitalize = function() {
	return this.charAt(0).toUpperCase() + this.slice(1);
};

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

function changeSetForNotes(event) {
	var setId = event.target.value;
	// console.log(set_id)
	if (window.currentSetId != setId) {
		if (setId != 'null') {
			window.currentSetId = setId;			
			downloadJson(`http://${location.host}/api/part_types/?set_id=${setId}`, buildFields);
		} else {
			window.pageTitle.innerHTML = "Notes";
			cleanNodeContent(elementForm);
			window.saveButton.classList.add('hidden');
			window.currentSetId = null;
		};
	};
};

function buildFields(downloadData) {
	var setTitle = downloadData["set_properties"]["title"];
	var setLanguage = downloadData["set_properties"]["type"]["language"]["code"]
	var setType = downloadData["set_properties"]["type"]["name"];
	window.pageTitle.innerHTML = `Notes for ${setTitle} (Set type: (${setLanguage.toUpperCase()}) ${setType})`;
	window.downloadData = downloadData;
	cleanNodeContent(elementForm);
	window.elementForm.appendChild(createNoteHeader());	
	downloadData['parts_types'].forEach(function(eachPartType) {
		eachPartType.type.name = eachPartType.type.name.capitalize();
		window.elementForm.appendChild(createPartForm(eachPartType));
	});
	window.saveButton.classList.remove('hidden');
};

function createNoteHeader() {
	var elementHeaderContainer = createElement('element_header_container');
	var elementHeader = createElement('element_header');
	[['set_title', `Set: ${window.downloadData["set_properties"]["title"]}`, `/show_set_elements/${window.currentSetId}/`],
	['set_type', `Type: ${window.downloadData["set_properties"]["type"]["name"]}`, `/update_set_type/${window.downloadData["set_properties"]["type"]["id"]}/`]].forEach(function(eachHeaderData) {
		var headerElement = createElement(eachHeaderData[0], eachHeaderData[1], 'a');
		headerElement.href = eachHeaderData[2];
		elementHeader.appendChild(headerElement);
	});
	elementHeader.appendChild(createElement('abstract_button', false, 'div', appearAbstractField, "Abstract"));
	elementHeaderContainer.appendChild(elementHeader);
	
	var inputBody = createElement('input_body');
	var abstractField = createInputField(false, false, `Type abstract for an element here`, 'hidden')
	abstractField.classList.add('abstract');
	inputBody.appendChild(abstractField);
	elementHeaderContainer.appendChild(inputBody);
	return elementHeaderContainer;
};

function appearAbstractField(event) {
	event.target.parentNode.nextSibling.children[0].classList.toggle('hidden');
};

function createElement(className=false, text=false, tag='div', onclickFunction=false, title=false) {
	var element = document.createElement(tag);
	if (className) {
		element.classList.add(className);
	};
	if (text) {
		element.innerHTML = text;
	};
	if (onclickFunction) {
		element.onclick = onclickFunction;
	};
	if (title) {
		element.title = title;
	};
	return element;
};

function createPartHeader(partTypeData) {
	var partHeader = createElement('part_header');
	[['part_position', partTypeData.position],
	['part_name', partTypeData.type.name],
	['part_format', partTypeData.type.format.name],
	['part_language', partTypeData.type.language.original_name]].forEach(
		function(eachHeaderData) {
			partHeader.appendChild(createElement(eachHeaderData[0], eachHeaderData[1]));
	});
	partHeader.appendChild(createElement('comment_button', false, 'div', appearCommentField, "Comment"));
	return partHeader;
};

function createInputField(position=false, type=false, placeholderText, className=false) {
	var inputElement = createElement(className, false, 'textarea');
	if (position) {
		inputElement.dataset.position = position;
	};
	if (type) {
		inputElement.dataset.type = type;
	};
	inputElement.placeholder = placeholderText;
	autosize(inputElement);
	return inputElement;
};

function createContentField(partTypeData) {
	var contentField;
	switch (partTypeData.type.format.name) {
		case 'text':
		contentField = createInputField(partTypeData.position,
										'content',
										`Type ${partTypeData.type.name} text here`);
		break;
		case 'url':
		contentField = createInputField(partTypeData.position,
										'content',
										`Insert ${partTypeData.type.name} here`);
		break;
	};
	return contentField;
};

function createInputBody(partTypeData) {
	var inputBody = createElement('input_body');
	[createContentField(partTypeData),	
	createInputField(partTypeData.position, 'comment', `Type comment for ${partTypeData.type.name} here`, 'hidden')].forEach(
		function(eachElement) {
			inputBody.appendChild(eachElement);
	});
	return inputBody;
};

function appearCommentField(event) {
	event.target.parentNode.nextSibling.children[1].classList.toggle('hidden');
};

function createPartForm(partTypeData) {
	var partForm = document.createElement('div');
	partForm.classList.add('part_form');
	[createPartHeader(partTypeData),
	createInputBody(partTypeData)].forEach(
		function(eachNode) {
			partForm.appendChild(eachNode);
		})	
	return partForm;
};

function checkContent(contentExists, content) {
	console.log(contentExists || (content != ''))
	return contentExists || (content != '');
};

function eraseContentFields(contentFields) {
	contentFields.forEach(function(eachField) {
		eachField.value = '';
	});
};

function getData() {
	var data = {'set': window.currentSetId,
				'parts': []}
	var contentFields = [];
	var contentExists = false;
	var abstractField = document.querySelector('.abstract');
	contentFields.push(abstractField);
	contentExists = checkContent(contentExists, abstractField.value);
	data['abstract'] = abstractField.value;
	downloadData['parts_types'].forEach(function(partType) {
		var allFieldsForPart = document.querySelectorAll(`textarea[data-position="${partType.position}"]`);
		var dataFields = [];
		allFieldsForPart.forEach(function(eachField) {
			dataFields.push({'type': eachField.dataset.type,
							'data': eachField.value});
			contentExists = checkContent(contentExists, eachField.value);
			contentFields.push(eachField);
		});
		var dataPart = {'position': partType.position,
						'fields': dataFields};
		data['parts'].push(dataPart);
	});
	// console.log(contentExists)
	if (contentExists) {
		eraseContentFields(contentFields);
		return data;
	} else {
		alert('No data');
		return false;
	};
};

function sendNote(type, id, color) {
	if (window.currentSetId != null) {
		var xhr = new XMLHttpRequest();
		xhr.open("POST", window.csrf_token.action, true);
		xhr.setRequestHeader("X-CSRFToken", window.csrf_token.querySelector('input').value);
		xhr.setRequestHeader("Content-Type", "application/json");
		xhr.onreadystatechange = function(event) {
			if (xhr.readyState === 4 && xhr.status === 200) {
				var json = JSON.parse(xhr.responseText);
				alert(json["response"]);
			};
		};
		var data = getData();
		if (data) {		
			xhr.send(JSON.stringify(data));
		} else {
			alert('No any data to save');
		};
	};
};

function setPreviousSet(event) {		
	changeSetForNotes({target: window.notesAvailableSetsList});
};

var currentSetId = null;
var notesAvailableSetsList = document.getElementById("select-set");
notesAvailableSetsList.onchange = changeSetForNotes;
window.onload = setPreviousSet;
var elementForm = document.getElementById("element_form");
var saveButton = document.getElementById("save_button");
var pageTitle = document.getElementsByTagName("title")[0];
// pageTitle.innerHTML = 'Notes'
saveButton.onclick = sendNote;
document.addEventListener('keydown', function(event) {
	if (["Enter", "NumpadEnter"].indexOf(event.code) >= 0 && event.ctrlKey) {
		sendNote();
	};
});
var csrf_token = document.getElementById("csrf_token");