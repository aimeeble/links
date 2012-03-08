
function ajax_shorten(longurl, resultid) {
   $.ajax({
      "url": document.location.href,
      "type": "POST",
      "dataType": "json",
      "data": {"full_url": longurl},

      "success": function(data) {
         $(resultid).text(data.short_url);
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
         alert("img");
         return true;
      }

      /* Block the submit button's normal action. */
      return false;
   });
})
