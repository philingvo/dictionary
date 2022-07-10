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

function downloadNativeFormat(event) {
	console.log(set_id)
	downloadJson(`http://${location.host}/api/set_with_elements/?set_id=${window.set_id}`, fillExportingText);
};

function fillExportingText(set_dict) {
	window.set_dict = set_dict;
	refreshExportText();
};

function refreshExportText() {
	window.rawTextField.value = '';
	var export_text = [];	
	var elements = window.set_dict['elements'];
	var elements_count = elements.length;
	for (var w=0;w<elements_count;w++) {
		var eachElement = elements[w];
		var elementText = '';
		var parts_count = eachElement["parts"].length
		for (var p=0;p<parts_count;p++) {
			var partContent = eachElement["parts"][p]["part"].content;
			if (!partContent) {
				partContent = window.noContentText;
			}
			if (partContent.indexOf('\n') >= 0) {console.log('n')}
			if (partContent.indexOf('\r') >= 0) {console.log('r', partContent)}
			partContent = cleanContent(partContent);
			elementText += partContent;
			if (p < parts_count - 1) {
				elementText += window.partSeparator;
			};
		};
		export_text += elementText;
		if (w < elements_count - 1) {
			export_text += window.elementSeparator;
		};
	};
	window.rawTextField.value = export_text;
};

function cleanContent(content) {
	if (window.replaceSeparatorMode) {
		var separators = [window.partSeparator, window.elementSeparator];
		separators.forEach(function(eachSeparator) {
			if (content.indexOf(eachSeparator) >= 0) {
				console.log(content, eachSeparator, content.indexOf(eachSeparator))
				content = content.replaceAll(eachSeparator, '|');
				console.log(content);
			};
		});
	};
	return content;
};

function cleanSeparator(raw_separator) {
	switch (raw_separator){
		case '\\n':
			return '\n';
		case 'tab':
			return '\t';
		default:
			return raw_separator;
	};
};

function defineField(event) {
	var field = event.target;
	if (!field) {
		field = event;
	};
	return field;
};

function getCleanedSeparator(event, separatorName, refresh) {
	var field = defineField(event);
	window[separatorName] = cleanSeparator(field.value);
	if (refresh) {
		refreshExportText();
	};
};

function setWordSeparator(event, refresh=true) {
	getCleanedSeparator(event, 'partSeparator', refresh);
};

function setStringSeparator(event, refresh=true) {
	getCleanedSeparator(event, 'elementSeparator', refresh);
};

function setNoContentText(event, refresh=true) {
	getCleanedSeparator(event, 'noContentText', refresh);
};

function changeReplaceSeparatorMode(event, refresh=true) {
	var field = defineField(event);
	window.replaceSeparatorMode = field.checked;
	if (refresh) {
		refreshExportText();
	};
};

function copyExportingText(event) {
	navigator.clipboard.writeText(window.rawTextField.value)
	.then(() => {
		console.log('Exporting text has been copied');
	})
	.catch(err => {
		console.log('Something went wrong\nCheck your permisson to use the clipboard', err);
	})
	event.target.style = "background-color: orange";
	setTimeout(function(buttonText) {buttonText.style = null},
				1000, event.target);
};

window.onload = downloadNativeFormat;
var set_id = document.getElementById("set_id").value;
var wordSeparatorField = document.getElementById("id_part_separator");
setWordSeparator(wordSeparatorField, false);
wordSeparatorField.onchange = setWordSeparator;
var stringSeparatorField = document.getElementById("id_element_separator");
setStringSeparator(stringSeparatorField, false);
stringSeparatorField.onchange = setStringSeparator;
var noContentTextField = document.getElementById("id_no_content_text");
noContentTextField.onchange = setNoContentText;
setNoContentText(noContentTextField, false);
var replaceSeparatorInContentField = document.getElementById('id_replace_separator_in_content');
changeReplaceSeparatorMode(replaceSeparatorInContentField, false);
replaceSeparatorInContentField.onchange = changeReplaceSeparatorMode;
var rawTextField = document.getElementById("id_raw_text");
rawTextField.readOnly = true;
var copyToClipboardButton = document.getElementById('copy');
copyToClipboardButton.onclick = copyExportingText;