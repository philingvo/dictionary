var elementID = location.hash;

if (elementID) {
	if (elementID.indexOf('?') > 0) {
		elementID = elementID.slice(1, elementID.indexOf('?'))
	} else {
		elementID = elementID.slice(1)
	};
	var elementPosition = document.getElementById(elementID);
	elementPosition.parentNode.classList.add('start_element');	
	console.log(elementPosition.parentNode, elementPosition.parentNode.scrollHeight);
	var elementPosition = document.getElementById(elementID);
	var headerElement = document.getElementById("header");
	var y = headerElement.clientHeight;
	setTimeout(function() {
		elementPosition.scrollIntoView(true)
		window.scrollBy({"left": 0, "top": -1*y});
	}, 1);
	setTimeout(function() {
		elementPosition.parentNode.classList.remove('start_element');
	}, 5000);
};