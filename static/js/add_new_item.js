function startAddNewItem(event) {
	// console.log('start add');
	changeMouseFunctions(null, preventDefaultLinks);
	window.table.onmouseover = window.table.onmouseout = focusElement;
	window.table.onmouseup = putAddNewItemCommand;
	toggleCancelButtonAppearance();
	// console.log(window.table.onmouseover, window.table.onmouseout, window.table.onmouseup)
};

//https://www.de-online.ru/news/180_nemeckikh_glagolov_glagolov_kotorye_dolzhen_znat_kazhdyj/2011-02-15-26
//https://online-teacher.ru/blog/nem-glagoli
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
		// changeMouseFunctions(startChangingPosition, null);
		// setCancelButtonFunction();
		// console.log(window.addNewItemButton.onclick)
		// window.addNewItemButton.onclick = startAddNewItem;
		// console.log(window.addNewItemButton.onclick);
	};
};

function createNewItem() {
	// var url = `${location.origin}/add_new_element_into_set/${window.containerId}/${window.endPosition}/`;	
	// var url = `${location.origin}/${window.addNewItemIntoEndLink}/${window.containerId}/${window.endPosition}/`;

	var url = window.addNewItemIntoEndLink;
	if (totalLen > 7) {
		var url = `${url}/${window.containerId}`;
	};
	url = `/${url}/${window.endPosition}/`;
	console.log(url);
	var xhr = new XMLHttpRequest();
	// xhr.open("POST", 'http://192.168.0.100:12345', true);
	xhr.open("GET", url, true);
	xhr.onreadystatechange = function(event) {
		console.log(xhr.readyState, xhr.status)
		// console.log(xhr)
		if (xhr.readyState === 2 && xhr.status === 200) {
			location.href = xhr.responseURL;
			// console.log(xhr.responseURL);
			// location.reload();
			// var json = JSON.parse(xhr.responseText);
			// alert(json["response"]);
			// alert(xhr.responseText);
		} else if (xhr.readyState === 4 && xhr.status == 0) {
			alert("Mistake has been occured during creating the new element");
		};
	};
	xhr.send();
};

var addNewItemButton = document.getElementById("add_new_item");
// if (!window.table) {
// 	addNewItemButton.classList.add("hidden");
// };
if (addNewItemButton) {	
	addNewItemButton.onclick = startAddNewItem;
};
// var addNewItemIntoEnd = document.getElementById("add_new_item_into_end");
// addNewItemIntoEnd.href = `/add_new_element_into_set/${window.containerId}/end/`;