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

function getOptionElement(value, text) {
	var option = document.createElement('option');
	option.innerHTML = text;
	option.setAttribute('value', value);
	return option;
};

function getAndInsertNullOptionElement(dropListContainer, itemName) {
	var option = getOptionElement(null, `--- Choose ${itemName} ---`);
	dropListContainer.appendChild(option);
};

function fillDroplist(dropListContainer, containerItems, itemName) {
	cleanNodeContent(dropListContainer);
	if (!dropListContainer.multiple) {
		getAndInsertNullOptionElement(dropListContainer, itemName);
	};
	containerItems.forEach(function(item) {
		var option = getOptionElement(item.id, `${item.position}. ${item[itemName].title}`);
		if (item[itemName].color) {
			option.style = `background-color: ${item[itemName].color}`;
		};
		dropListContainer.appendChild(option);
	});	
};

function checkAndFillList(dropListContainer, containerItems, itemName) {
	if (containerItems.length > 0) {
		fillDroplist(dropListContainer, containerItems, itemName);
		dropListContainer.classList.remove('hidden');
	} else {
		alert(`No one ${itemName}. Choose other ${itemName}!`);
	};
};

function fillTopics(subjectTopics) {
	checkAndFillList(window.topicsList, subjectTopics, 'topic');
};

function fillSets(topicSets) {
	console.log(topicSets)
	checkAndFillList(window.setsList, topicSets, 'set');
};

function changeSubject(event) {
	var subject_id = event.target.value;
	window.topicsList.classList.add('hidden');
	switch (window.destinationModel) {
		case 'playlist':
		case 'topic':
			window.setsList.classList.add('hidden');
		case 'subject':
			hideFinalElements();
	};
	if (subject_id != 'null') {
		downloadJson(`http://${location.host}/api/topics/?subject_id=${subject_id}`, fillTopics);
		if (window.destinationModel == 'subject') {
			window.topicsList.multiple = "multiple";
		};	
	};
};

function changeTopic(event) {
	var topic_id = event.target.value;
	if (topic_id != 'null') {
		downloadJson(`http://${location.host}/api/sets_by_topics_id/?topics_id=${topic_id}`, fillSets);
	} else {
		window.setsList.classList.add('hidden');
		hideFinalElements();
	};
};

function finalElementsEvents(event) {
	if (event.target.value != 'null') {
		showFinalElements();
	} else {
		hideFinalElements();
	};
};

function showFinalElements() {
	if (window.destinationModel != 'playlist') {
		window.deleteCheckBox.classList.remove('hidden');
	};
	window.submitButton.classList.remove('hidden');
};

function hideFinalElements() {
	window.deleteCheckBox.classList.add('hidden');
	window.submitButton.classList.add('hidden');
};

function getListElement(name) {
	var listElement = document.createElement('select');
	listElement.name = name;
	listElement.id = 'select-' + name;
	listElement.title = "Choose " + name;
	listElement.required = true;
	listElement.classList.add("hidden");
	return listElement;
};

function createSelectElements() {
	console.log(window.destinationModel)
	switch (window.destinationModel) {
		case 'subject':
			window.topicsList = getListElement('topic');
			window.topicsList.multiple = "multiple";
			window.topicsList.onchange = finalElementsEvents;
			window.topicContainer.appendChild(window.topicsList);
			break;
		case 'playlist':
		case 'topic':
			window.topicsList = getListElement('topic');
			window.topicsList.onchange = changeTopic;
			window.topicContainer.appendChild(window.topicsList);

			window.setsList	= getListElement('set');
			window.setsList.multiple = "multiple";
			window.setsList.onchange = finalElementsEvents;
			window.setContainer.appendChild(window.setsList);
			break;
	};	
};

var destinationModel = document.getElementById("destination_model").innerHTML;
var subjectList = document.getElementById("select-subject");
subjectList.onchange = changeSubject;
var topicContainer = document.getElementById("topic-container");
var setContainer = document.getElementById("set-container");
createSelectElements();
var deleteCheckBox = document.getElementById("delete_checkbox");
var submitButton = document.getElementById("submit");