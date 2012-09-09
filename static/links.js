function load_recent_urls(divid) {
   $.ajax({
      "url": "/api/v1/dump",
      "type": "GET",
      "dataType": "json",

      "success": function(data) {
         $(divid).html("<tr><thead><th>Code</th><th>Long URL</th><th>Hits</th><th>Links</th></tr></thead>");

         for (id in data.result) {
            url = data.result[id];

            var MAX_WIDTH = 80;
            long_url = url.url.substring(0, MAX_WIDTH);
            if (url.url.length > MAX_WIDTH) {
               long_url += '...';
            }

            html = "<tr>";
            html += "<td>" + url.short_code + "</td>";
            html += "<td>" + long_url + "</td>";
            html += "<td>" + url.hits + "</td>";
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
         $(resultid).val(data.short_url);
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
