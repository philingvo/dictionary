function falseFunction() {
	return false;
};

// https://learn.javascript.ru/searching-elements-dom
function definePosition(element) {
	if (!element.dataset.position) {
		element = element.parentElement;
	};
	return element.dataset.position;
};

function findPositionElement(element) {
	if (element.tagName != 'TABLE') {
		while (element.tagName != 'TR') {
			element = element.parentElement;
		};
		if (element.classList.contains("table_header")) {
			return false;
		} else {
			return element;
		}
	} else {
		return false;
	};
};

function focusElement(event) {
	var element = findPositionElement(event.target);
	console.log(element)
	if (element && definePosition(element) != 0) {
		if (element.classList.contains("focused_element")) {
			element.classList.remove("focused_element");
		} else {
			element.classList.add("focused_element");
		};
	};
};

function startChangingPosition(event) {
	window.startElement = event.target.parentElement.parentElement;
	window.startPosition = definePosition(startElement);
	if (window.startPosition > 0) {

		changeMouseFunctions(null, preventDefaultLinks);
		window.table.onmouseover = window.table.onmouseout = focusElement;
		window.table.onmouseup = finishChangingPosition;
		toggleCancelButtonAppearance();

		focusElement(event);
		startElement.classList.add('start_element');
		console.log('START POSITION', startPosition)	
	};
};

function finishChangingPosition(event) {
	var element = findPositionElement(event.target);
	if (element) {
		console.log(element)
		window.endPosition = definePosition(element);
		console.log(window.endPosition)
		if (window.endPosition != 0) {
			// console.log(window.endPosition)
			window.table.onmouseover = window.table.onmouseout = window.table.onmouseup = null;
			element.classList.add("end_element");
			console.log('END POSITION', window.endPosition);
			element.classList.toggle("focused_element");

			window.startElement.classList.remove('start_element');
			
			setTimeout(function(element) {
							element.classList.remove("end_element");
							sendChangePositionCommand();
						},
						1000, element);
			toggleCancelButtonAppearance();
			setTimeout(changeMouseFunctions, 1, startChangingPosition, null);
			// changeMouseFunctions(startChangingPosition);
		};
	};
};

function sendChangePositionCommand() {
	console.log(window.startPosition, window.endPosition)
	if (window.startPosition != window.endPosition) {

		// window.change_position_url_list[totalLen-3] = window.startPosition;
		// window.change_position_url_list[totalLen-2] = window.endPosition;
		// var url = window.change_position_url_list.join('/');

		var url = window.changePositionUrl;
		console.log(window.totalLen)
		if (totalLen > 7) {
			var url = `${url}/${window.containerId}`
		};
		url = `/${url}/${window.startPosition}/${window.endPosition}/`;
		console.log(window.endPosition)

		// var url = location.origin + `/${window.change_position_url}/${window.startPosition}/${window.endPosition}/`
		console.log(url, window.startPosition)
		var xhr = new XMLHttpRequest();
		// xhr.open("POST", 'http://192.168.0.100:12345', true);
		xhr.open("GET", url, true);
		xhr.onreadystatechange = function(event) {
			console.log(xhr.readyState, xhr.status)
			if (xhr.readyState === 4 && xhr.status === 200) {
				location.reload();
				// var json = JSON.parse(xhr.responseText);
				// alert(json["response"]);
				// alert(xhr.responseText);
			} else if (xhr.readyState === 4) {
				alert("Can't set new position");
			};
		};
		xhr.send();
	};
};

function changeMouseFunctions(buttonFunction, linksFunction) {
	console.log('changeMouseFunctions');
	// console.log(window.changePositionButtons);
	window.changePositionButtons.forEach(function(eachButton) {
		// eachButton.onmousedown = functionName;
		// console.log(eachButton.dataset.position, eachButton.onclick);
		eachButton.onclick = buttonFunction;
		// console.log(eachButton.onclick);
	});
	// console.log('changeButton2');
	if (window.links) {
		for (var i = 0; i < window.links.length; i++) {
			window.links[i].onclick = linksFunction;
		};
	};
};

function preventDefaultLinks(event) {
	event.preventDefault();
};

document.addEventListener('keydown', function(event) {
	switch (event.code) {
		case "Escape":
			cancel();
		break;
	}
});

function cancel() {
	if (window.table.onmouseover != null) {
		console.log('Escape');
		toggleCancelButtonAppearance();
		window.table.onmouseover = window.table.onmouseout = window.table.onmouseup = null;
		changeMouseFunctions(startChangingPosition, null);
		if (window.startElement) {
			window.startElement.classList.remove('start_element');
		};
		window.rows = document.body.getElementsByTagName("tr");
		for (var i = 0; i < window.rows.length; i++) {
			window.rows[i].classList.remove("focused_element");
		};
	};
};

function toggleCancelButtonAppearance() {
	window.cancelButton.classList.toggle("hidden");
	console.log(window.cancelButton.classList);
};

// document.onmousedown = startChangingPosition;
// document.onmouseup = startChangingPosition;

var addNewItemIntoEnd = document.getElementById("add_new_item_into_end");
if (addNewItemIntoEnd) {
	var hrefList = addNewItemIntoEnd.href.split('/');
	var length = hrefList.length;
	var addNewItemIntoEndLink = hrefList[3];	
	// console.log(hrefList)
	if (length > 6) {
		var containerId = hrefList[4];
	};
	// console.log(177, containerId)
	var totalLen = length + 1;
	// console.log(179, totalLen);
};

var addNewItemIntoEndDiv = document.getElementById("change_position_url");
var changePositionUrl = addNewItemIntoEndDiv.innerHTML;
// console.log(changePositionUrl);

// if (document.querySelectorAll(".position_up").length > 0) {
// 	console.log("!!!!!!!!!!!!!!");
// 	var change_position_url_list = document.querySelectorAll(".position_up")[0].children[0].href.split('/');
// 	// var totalLen = change_position_url_list.length;
// 	// var containerId = change_position_url_list[totalLen-4];
// 	// console.log(containerId, totalLen);	
// 	// console.log(change_position_url_list);
// };

var table = document.body.getElementsByTagName("table")[0];
// console.log(table)
if (table) {
	var cellsInRow = window.table.children[0].children[0].children.length;
	var lastRow = table.querySelector("[data-position='end']");
	lastRow.children[0].colSpan = cellsInRow;
	var links = window.table.getElementsByTagName("a");
	var changePositionButtons = document.body.querySelectorAll('.change_position_button');
	// console.log(window.links);
	// console.log(window.changePositionButtons)
	changeMouseFunctions(startChangingPosition);
	var cancelButton = document.getElementById("cancel_adding");
	if (cancelButton) {
		cancelButton.onclick = cancel;
	};
};
// changePositionButtons.forEach(function(eachButton) {
// 	eachButton.onclick = startChangingPosition;
// });