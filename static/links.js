function load_recent_urls(divid) {
   $.ajax({
      "url": "/api/v1/dump",
      "type": "GET",
      "dataType": "json",

      "success": function(data) {
         $(divid).html("<tr><th>Code</th><th>Long URL</th><th>Links</th></tr>");

         for (id in data.result) {
            url = data.result[id];

            html = "<tr>";
            html += "<td>" + url.short_code + "</td>";
            html += "<td>" + url.url + "</td>";
            html += "<td>";
            html += "<a href=\"" + url.short_url + "\">Link</a> &nbsp; | &nbsp;";
            html += "<a href=\"" + url.short_url + "+\">Stats</a>";
            html += "</td></tr>\n";
            $(divid).append(html);
         }
      },
      "failure": function() {
         $(resultid).text("FAIL!");
      },
      "error": function(xhr, textStatus, err) {
         $(resultid).text("error: " + err + ", text: " + textStatus);
      }
   });
}

function ajax_shorten(longurl, resultid) {
   $.ajax({
      "url": "/api/v1/shrink",
      "type": "POST",
      "dataType": "json",
      "data": {"url": longurl},

      "success": function(data) {
         $(resultid).html("<a href=\"" + data.short_url + "\">" + data.short_url + "</a>");
         load_recent_urls("#recent");
      },
      "failure": function() {
         $(resultid).text("FAIL!");
      },
      "error": function(xhr, textStatus, err) {
         $(resultid).text("error: " + err + ", text: " + textStatus);
      }
   });
}

jQuery(document).ready(function() {

   $("#shorten_button").click(function(evt) {
      full_url = $("#full_url_input").attr("value");

      if (full_url.length > 0) {
         ajax_shorten(full_url, "#short_url");
      } else {
         /* Files submit normally. */
         return true;
      }

      /* Block the submit button's normal action. */
      return false;
   });

   load_recent_urls("#recent");
})
