function report_activity(hit_code) {
    $.ajax({
        "url": "/api/v1/activity",
        "type": "POST",
        "dataType": "json",
        "data": {
            "hit_code": hit_code,
            "type": "mouse",
        },

        "success": function(data) {
        },
        "failure": function() {
        },
        "error": function(xhr, textStatus, err) {
        }
    })
}

jQuery(document).ready(function() {
    var activity = false;
    $(document).on('mousemove touchstart', function() {
        if (!activity) {
            activity = true;
            var hit_code = $('#hit_code').text();
            report_activity(hit_code)
        }
    })
})
