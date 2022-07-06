var setCheckboxs = document.body.querySelectorAll('.notes_available input');
setCheckboxs.forEach(function(setCheckbox) {
	setCheckbox.onclick = changeAvailability;
});

function changeAvailability(event) {
	var setCheckbox = event.target;
	// console.log(setCheckbox.checked)
	// setCheckbox.checked = !(setCheckbox.checked);
	// console.log(setCheckbox.checked)
	if (setCheckbox.checked) {
		setCheckbox.title = "Available for notes";
	} else {
		setCheckbox.title = "Not available for notes";
	};
	change_set_notes_availability_request(setCheckbox.dataset.id);
};

function change_set_notes_availability_request(id) {
	// Sending and receiving data in JSON format using POST method
	var xhr = new XMLHttpRequest();
	xhr.open("GET", `/change_set_notes_availability/${id}/`, true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function(event) {
		if (xhr.readyState === 4 && xhr.status === 200) {
			var json = JSON.parse(xhr.responseText);
			alert(json["response"]);
			// alert(xhr.responseText);
		};
	};
	// console.log({'type': type, 'id': id, 'color': color});	
	xhr.send();
};