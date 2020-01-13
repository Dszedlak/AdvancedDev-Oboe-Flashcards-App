'use strict'; 
window.addEventListener('load', function () {
	document.getElementById('sign-out').onclick = function () {
		firebase.auth().signOut().then(function(){		
		document.cookie = "token=";
		window.location.replace('/login');
		});
	};
});                     