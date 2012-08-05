function report_activity(hit_code) {
    $.ajax({
        "url": "/api/v1/activity",
        "type": "POST",
        "dataType": "json",
        "data": {"activity": true},

        "success": function(data) {
            alert("success");
        },
        "failure": function() {
            alert("failure");
        },
        "error": function(xhr, textStatus, err) {
            alert("error: " + err);
        }
    })
}

jQuery(document).ready(function() {
    var activity = false;
    $(document).mousemove(function() {
        if (!activity) {
            activity = true;
            var hit_code = $('#hit_code').text();
            report_activity(hit_code)
        }
    })
})
