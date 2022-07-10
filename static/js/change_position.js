function falseFunction() {
	return false;
};

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
		};
	};
};

function sendChangePositionCommand() {
	console.log(window.startPosition, window.endPosition)
	if (window.startPosition != window.endPosition) {

		var url = window.changePositionUrl;
		console.log(window.totalLen)
		if (totalLen > 7) {
			var url = `${url}/${window.containerId}`
		};
		url = `/${url}/${window.startPosition}/${window.endPosition}/`;
		console.log(window.endPosition)

		console.log(url, window.startPosition)
		var xhr = new XMLHttpRequest();
		xhr.open("GET", url, true);
		xhr.onreadystatechange = function(event) {
			console.log(xhr.readyState, xhr.status)
			if (xhr.readyState === 4 && xhr.status === 200) {
				location.reload();

			} else if (xhr.readyState === 4) {
				alert("Can't set new position");
			};
		};
		xhr.send();
	};
};

function changeMouseFunctions(buttonFunction, linksFunction) {
	console.log('changeMouseFunctions');
	window.changePositionButtons.forEach(function(eachButton) {
		eachButton.onclick = buttonFunction;
	});
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

var addNewItemIntoEnd = document.getElementById("add_new_item_into_end");
if (addNewItemIntoEnd) {
	var hrefList = addNewItemIntoEnd.href.split('/');
	var length = hrefList.length;
	var addNewItemIntoEndLink = hrefList[3];	
	if (length > 6) {
		var containerId = hrefList[4];
	};
	var totalLen = length + 1;
};

var addNewItemIntoEndDiv = document.getElementById("change_position_url");
var changePositionUrl = addNewItemIntoEndDiv.innerHTML;

var table = document.body.getElementsByTagName("table")[0];

if (table) {
	var cellsInRow = window.table.children[0].children[0].children.length;
	var lastRow = table.querySelector("[data-position='end']");
	lastRow.children[0].colSpan = cellsInRow;
	var links = window.table.getElementsByTagName("a");
	var changePositionButtons = document.body.querySelectorAll('.change_position_button');
	changeMouseFunctions(startChangingPosition);
	var cancelButton = document.getElementById("cancel_adding");
	if (cancelButton) {
		cancelButton.onclick = cancel;
	};
};