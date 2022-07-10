function createPallet() {
	var palletContainer = document.createElement('div');
	palletContainer.id = 'pallet';
	var colors = ['white',
				'maroon',
				'crimson',
				'red',
				'orange',
				'gold',
				'olive',
				'yellow',
				'green',
				'lime',
				'blue',
				'teal',
				'cyan',
				'purple',
				'magenta',
				'pink',
				'gray',
				'silver']
	colors.forEach(function(eachColor){
		palletElement = document.createElement('div');
		palletElement.classList.add('pallet_element')
		palletElement.style["background-color"] = eachColor;
		palletElement.onclick = assignColor;
		palletContainer.appendChild(palletElement);
	});
	var deleteColorButton = document.createElement('div');
	deleteColorButton.classList.add('pallet_element', 'without_color');
	deleteColorButton.onclick = assignColor;
	palletContainer.appendChild(deleteColorButton);

	return palletContainer;
};

function showPallet(event) {
	var thisItemColorButton = event.target;
	if (thisItemColorButton != window.itemColorButton) {
		window.itemColorButton = event.target;
		window.itemColorButton.parentNode.appendChild(window.pallet);
	} else {
		closePallet(thisItemColorButton);
	};
};

function closePallet(thisItemColorButton) {
	thisItemColorButton.parentNode.removeChild(window.pallet);
	window.itemColorButton = null;
};

function assignColor(event) {
	if (window.itemColorButton) {
		var palletElement = event.target;
		var color = palletElement.style["background-color"]
		if (palletElement.classList.contains("without_color")) {
			window.itemColorButton.classList.add("without_color");
			color = null;
		} else if (window.itemColorButton.classList.contains("without_color")) {
			window.itemColorButton.classList.remove("without_color");
		};
		var previousColor = window.itemColorButton.style["background-color"];
		if (previousColor != color && !(previousColor == '' && color == null)) {
			window.itemColorButton.style["background-color"] = color;
			var borderColor = color;
			if (color == 'white') {
				borderColor = null;
			};
			window.itemColorButton.style["border-color"] = borderColor;
			color_request(window.itemColorButton.dataset.type, window.itemColorButton.dataset.id, color);
		};
		closePallet(itemColorButton);
	};
};

function color_request(type, id, color) {
	// Sending and receiving data in JSON format using POST method
	var xhr = new XMLHttpRequest();
	xhr.open("POST", window.csrf_token_element_color.action, true);
	xhr.setRequestHeader("X-CSRFToken", window.csrf_token_element_color.querySelector('input').value);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function(event) {
		if (xhr.readyState === 4 && xhr.status === 200) {
			var json = JSON.parse(xhr.responseText);
			alert(json["response"]);
		};
	};
	var data = JSON.stringify({'type': type,
								'id': id,
								'color': color});
	xhr.send(data);
};

var itemColorsButtons = document.body.querySelectorAll('.item_color span');
itemColorsButtons.forEach(function(eachColorButton) {
	eachColorButton.onclick = showPallet;
});
window.csrf_token_element_color = document.getElementById("csrf_token_color");
window.pallet = createPallet();