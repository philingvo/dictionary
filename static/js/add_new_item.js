function startAddNewItem(event) {
	changeMouseFunctions(null, preventDefaultLinks);
	window.table.onmouseover = window.table.onmouseout = focusElement;
	window.table.onmouseup = putAddNewItemCommand;
	toggleCancelButtonAppearance();
};

function putAddNewItemCommand(event) {
	var element = findPositionElement(event.target);
	console.log(window.addNewItemButton.onclick)
	if (element) {
		window.table.onmouseover = window.table.onmouseout = window.table.onmouseup = null;
		element.classList.add("end_element");
		window.endPosition = definePosition(element);
		console.log('END POSITION', endPosition);
		element.classList.toggle("focused_element");
		
		setTimeout(function(element) {
						element.classList.remove("end_element");
						createNewItem();
					}, 1000, element);
		toggleCancelButtonAppearance();
		setTimeout(changeMouseFunctions, 1, startChangingPosition, null);
	};
};

function createNewItem() {
	
	var url = window.addNewItemIntoEndLink;
	if (totalLen > 7) {
		var url = `${url}/${window.containerId}`;
	};
	url = `/${url}/${window.endPosition}/`;
	console.log(url);
	var xhr = new XMLHttpRequest();

	xhr.open("GET", url, true);
	xhr.onreadystatechange = function(event) {
		console.log(xhr.readyState, xhr.status)

		if (xhr.readyState === 2 && xhr.status === 200) {
			location.href = xhr.responseURL;
		} else if (xhr.readyState === 4 && xhr.status == 0) {
			alert("Mistake has been occured during creating the new element");
		};
	};
	xhr.send();
};

var addNewItemButton = document.getElementById("add_new_item");

if (addNewItemButton) {	
	addNewItemButton.onclick = startAddNewItem;
};