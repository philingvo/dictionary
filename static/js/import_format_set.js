function changeSubject(event) {
	var subject_id = event.target.value;
	window.topicsList.classList.add('hidden');
	hideFinalElements();
	if (subject_id) {
		downloadJson(`http://${location.host}/api/topics/?subject_id=${subject_id}`, fillTopics);
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

function fillTopics(subjectTopics) {
	checkAndFillList(window.topicsList, subjectTopics, 'topic');
	if (history.state && history.state.topic) {
		// console.log(history.state.topic)
		// console.log(window.topicsList)
		window.topicsList.childNodes.forEach(function(eachOption) {
			if (eachOption.value == history.state.topic) {
				eachOption.selected = true;
				changeTopic({target: window.topicsList});
			};
		});
	};
};

function checkAndFillList(dropListContainer, containerItems, itemName) {
	if (containerItems.length > 0) {
		fillDroplist(dropListContainer, containerItems, itemName);
		dropListContainer.classList.remove('hidden');
	} else {
		alert(`No one ${itemName}. Choose other ${itemName}!`);
		cleanNodeContent(dropListContainer);
		hideFinalElements();
	};
};

function fillDroplist(dropListContainer, containerItems, itemName) {
	cleanNodeContent(dropListContainer);
	getAndInsertNullOptionElement(dropListContainer, itemName);
	containerItems.forEach(function(item) {
		var option = getOptionElement(item.id, `${item.position}. ${item[itemName].title}`);
		if (item[itemName].color) {
			option.style = `background-color: ${item[itemName].color};`;
		};
		dropListContainer.appendChild(option);
	});
};

function cleanNodeContent(parentNode) {
	while (parentNode.firstChild) {
		parentNode.removeChild(parentNode.firstChild);
	};
};

function getAndInsertNullOptionElement(dropListContainer, itemName) {
	var option = getOptionElement('', `--- Choose ${itemName} ---`);
	dropListContainer.appendChild(option);
};

function getOptionElement(value, text) {
	var option = document.createElement('option');
	option.innerHTML = text;
	option.setAttribute('value', value);
	return option;
};

function createSelectElements() {
	window.topicsList = getListElement('topic');
	window.topicsList.onchange = changeTopic;
	window.topicContainer.appendChild(window.topicsList);
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

function changeTopic(event) {
	var topic_id = event.target.value;
	history.pushState({topic: topic_id}, `?topic=${topic_id}`);
	if (topic_id) {
		showFinalElements();
		// downloadJson(`http://${location.host}/api/sets_by_topics_id/?topics_id=${topic_id}`, showFinalElements);
	} else {
		hideFinalElements();
	};
};

function showFinalElements() {
	if (window.uploadfileField) {
		window.submitButton.classList.remove('hidden');
		window.uploadfileField.classList.remove('hidden');
	};
};

function hideFinalElements() {
	if (window.uploadfileField) {
		window.submitButton.classList.add('hidden');
		window.uploadfileField.classList.add('hidden');
	};
};

function setPreviousTopic(event) {
	changeSubject({target: window.subjectList});
};

var subjectList = document.getElementById("select-subject");
subjectList.onchange = changeSubject;
var topicContainer = document.getElementById("topic-container");
createSelectElements();
window.onload = setPreviousTopic;
var submitButton = document.getElementById("submit");
var uploadfileField = document.getElementById("set_file");