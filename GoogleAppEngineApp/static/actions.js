'use strict'; 

function rename(name){
	document.getElementById("deck_name").value = name
};

function remove(name){
	document.getElementById("delete_deck").value = name
};

function reps(name){
	document.getElementById("reps_deck").value = name
};

function hide_button(){
	document.getElementById('show-answer').classList.add('hide');
};
