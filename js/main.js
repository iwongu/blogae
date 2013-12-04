$(document).ready(function() {
    $('#search-form').
	submit(function(e) {
	    window.location = "/s/" + $('#search-term').val() + "/";
	    e.preventDefault();
	});

    $('#month-select').
        change(function(e) {
            window.location = e.target.selectedOptions[0].value;
        });
});
