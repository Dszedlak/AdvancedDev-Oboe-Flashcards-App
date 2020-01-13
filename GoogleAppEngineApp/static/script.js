'use strict'; 

window.addEventListener('load', function () {
	document.getElementById('sign-out').onclick = function () {
		firebase.auth().signOut();
	};
	var uiConfig = {
		signInSuccessUrl: '/',
		signInOptions: [
			firebase.auth.GoogleAuthProvider.PROVIDER_ID,
			firebase.auth.EmailAuthProvider.PROVIDER_ID,
		],
		tosUrl: '<your-tos-url>'
	};

	firebase.auth().onAuthStateChanged(function (user) {
		if (user) {
			user.getIdToken().then(function (token) {
				document.cookie = "token=" + token;
			});
			location.href = "/";
		} 
		else {
			var ui = new firebaseui.auth.AuthUI(firebase.auth());
			ui.start('#firebaseui-auth-container', uiConfig);
			document.cookie = "token=";
		}
	}, function (error) {
		console.log(error);
		alert('Unable to log in: ' + error)
	});
});                     