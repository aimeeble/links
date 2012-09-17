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

function progress_done(text) {
   $('#progress_bar').parent().removeClass('progress-striped active');
   $('#progress_bar').text(text);
}

function ajax_shorten(longurl) {
   $.ajax({
      "url": "/api/v1/shrink",
      "type": "POST",
      "dataType": "json",
      "data": {"url": longurl},

      "success": function(data) {
         progress_done(data.short_url);
         load_recent_urls("#recent");
      },
      "failure": function() {
         progress_done("FAIL!");
      },
      "error": function(xhr, textStatus, err) {
         progress_done("error: " + err + ", text: " + textStatus);
      }
   });
}

function ajax_progress(evt) {
   if (evt.lengthComputable) {
      pct = Math.round(evt.loaded * 100 / evt.total)
      $('#progress_bar').width(pct + '%');
   } else {
      $('#progress_bar').width('100%');
      $('#progress_bar').text('Loading...');
   }
}

function ajax_upload() {
   formData = new FormData();
   input = document.getElementById('imgfile_input');
   formData.append('file', input.files[0]);

   $.ajax({
      "url": "/api/v1/post",
      "type": "POST",
      "dataType": "json",
      "contentType": false,
      "cache": false,
      "processData": false,
      "data": formData,

      "xhr": function() {
         myXhr = $.ajaxSettings.xhr();
         myXhr.upload.addEventListener('progress', ajax_progress, false);
         return myXhr;
      },
      "beforeSend": function(xhr, settings) {
         $('#progress_bar').text('');
         $('#progress_bar').parent().addClass('progress-striped active');
      },
      "success": function(data) {
         progress_done(data.short_url);
         load_recent_urls("#recent");
      },
      "failure": function() {
         progress_done("FAIL!");
      },
      "error": function(xhr, textStatus, err) {
         progress_done("error: " + err + ", text: " + textStatus);
      }
   });
}

jQuery(document).ready(function() {

   $("#shorten_button").click(function(evt) {
      full_url = $("#full_url_input").attr("value");

      if (full_url.length > 0) {
         ajax_shorten(full_url);
      }

      /* Block the submit button's normal action. */
      return false;
   });

   $("#upload_button").click(function(evt) {
      ajax_upload();

      /* Block the submit button's normal action. */
      return false;
   });

   $('#short_url').bind("ajaxProgress", function (xhr, progressEvt) {
      console.log('global...');
      if (progressEvt.lengthComputable) {
         pct = Math.round(progressEvt.loaded * 100 / progressEvt.total)
         console.log('Loaded: ' + pct + '%');
      } else {
         console.log('Loading...');
      }
   });

   load_recent_urls("#recent");
})
