String.prototype.capitalize = function() {
	return this.charAt(0).toUpperCase() + this.slice(1);
};

function getQueryVariable(variable) {
	// console.log(window.location)
	// var query = window.location.search.substring(1);
	// if (!query) {
	// 	query = window.location.hash.slice(window.location.hash.indexOf('?'));
	// };
	// console.log(window.query)
	var vars = window.query.split('&');
	for (var i = 0; i < vars.length; i++) {
		var pair = vars[i].split('=');
		if (decodeURIComponent(pair[0]) == variable) {
			return decodeURIComponent(pair[1]);
		};
	};
	// console.log('Query variable %s not found', variable);
};

function getArrowElement() {
	var arrowElement = document.createElement('span');
	arrowElement.classList.add('arrow_element');
	arrowElement.innerHTML = '>';
	return arrowElement;
};

function getLinkElement(container_name, container_object_title=false, container_id=false) {
	var linkElement = document.createElement('a');
	// console.log(container_name, container_object_title, container_id);
	linkElement.innerHTML = container_name.capitalize();
	if (container_object_title) {
		linkElement.innerHTML += `: ${container_object_title}`;
	};
	// console.log(container_name, window.container_name)
	if (container_name.toLowerCase() != window.container_name.toLowerCase()) {
		linkElement.href = `/${window.containers_names[container_name.toLowerCase()]}/`;
		if (container_id) {
			linkElement.href += `${container_id}/` + getQueryStringForPathLink(container_name,
																				container_object_title,
																				container_id);
		};
	};
	return linkElement;
};

function addQueryStringsToContentItemLinks(container_name, container_object_title, container_id, queryStringsPairPosition) {
	var itemClass = 'content_item_text';
	if (window.container_name.toLowerCase() == 'set') {
		itemClass = 'details';
	};
	var itemLinks = document.querySelectorAll(`.${itemClass} a`);
	console.log(54, itemClass)
	console.log(55, itemLinks)
	for (var i=0;i<itemLinks.length;i++) {
		itemLinks[i].href += createQueryString(container_name, container_object_title, container_id, queryStringsPairPosition);
	};
};

function createQueryString(container_name, container_object_title, container_id, position=0) {
	// if (container_name.toLowerCase() == window.firstContainerName) {
	// console.log(window.containersData.length == 0)
	// console.log(position)
	if (position > 0) {
		var symbol = '&';
	} else {	
		var symbol = '?';
	};
	return `${symbol}${container_name.toLowerCase()}=${container_object_title}${window.separationSymbol}${container_id}`;
};

function cleanQueryString() {
	// console.log(window.location)
	window.query = window.location.search.substring(1);
	if (!query) {
		window.query = window.location.hash.slice(window.location.hash.indexOf('?'));
	};
};

function handleQueryString() {
	cleanQueryString();
	window.containersData = [];
	Object.keys(window.containers_names).forEach(function(container_name) {
		// console.log(container_name)
		var containerData = getQueryVariable(container_name);
		// console.log(containerData)
		if (containerData) {
			containerData = containerData.split(window.separationSymbol);
			containerData.push(container_name);
			window.containersData.push(containerData);
		};
	});
};

function createPathLinks() {
	for (var i=0;i<containersData.length;i++) {
	// window.containersData.forEach(function(containerData) {
		var containerData = containersData[i];
		window.linkPath.appendChild(getLinkElement(containerData[2], containerData[0], containerData[1]));		
		linkPath.appendChild(getArrowElement());
		addQueryStringsToContentItemLinks(containerData[2], containerData[0], containerData[1], i);
	};
};

function getQueryStringForPathLink(container_name, container_object_title, container_id) {
	var queryString = ''
	for (var i=0;i<window.containersData.length;i++) {
		if (Object.keys(containers_names).indexOf(containersData[i][2]) < Object.keys(containers_names).indexOf(container_name)) {
		// if (containersData[i][2] != container_name) {
			// console.log(containersData[i])
			queryString += createQueryString(containersData[i][2], containersData[i][0], containersData[i][1], i);
		};
	};
	return queryString; 
};

var containers_names = {'subjects': 'show_subjects',
						'subject': 'show_subject_topics',
						'topic': 'show_topic_sets',
						'set': 'show_set_elements',
						'element': 'show_element_parts'};

var firstContainerName = 'subject';
var separationSymbol = '@';

var linkPath = document.getElementById('links_path');
var container_name = document.getElementById("container_name").innerHTML;
var container_id = document.getElementById('container_id').innerHTML;
// console.log(container_id, container_name)
// if (container_id) {


// console.log(Object.keys(containers_names).indexOf(container_name.toLowerCase()), Object.keys(containers_names).indexOf('subject'))
// if (window.containersData.length > 0 && Object.keys(containers_names).indexOf(container_name.toLowerCase()) > Object.keys(containers_names).indexOf('subject')) {

if (container_id) {
	handleQueryString();
	var container_object_title = document.getElementById("container_object_title").innerHTML;

	if (window.containersData.length > 0 && Object.keys(containers_names).indexOf(container_name.toLowerCase()) > Object.keys(containers_names).indexOf('subject')) {
		linkPath.appendChild(getLinkElement('subjects'));
		linkPath.appendChild(getArrowElement());
		createPathLinks();
		linkPath.appendChild(getLinkElement(container_name, container_object_title));
	};	
	var queryStringsPairPosition = window.containersData.length;
	addQueryStringsToContentItemLinks(container_name, container_object_title, container_id, queryStringsPairPosition);
// } else if (Object.keys(containers_names).indexOf(container_name.toLowerCase()) == Object.keys(containers_names).indexOf('subject')) {
// 	linkPath.appendChild(getLinkElement('subjects'));
};