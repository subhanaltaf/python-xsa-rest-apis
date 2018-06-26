/*eslint no-console: 0, no-unused-vars: 0, no-use-before-define: 0, no-redeclare: 0*/
$.ajaxSetup({
    beforeSend: function(xhr,settings) {
      if (settings && settings.hasOwnProperty("type") && settings.type !== "GET"){
          var token = getCSRFToken();
          xhr.setRequestHeader("X-CSRF-Token", token);
      }
    }
});

function getCSRFToken() {
    var token = null;
    $.ajax({
        url: "/",
        type: "GET",
        async: false,
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRF-Token", "Fetch");
        },
        complete: function(xhr) {
            token = xhr.getResponseHeader("X-CSRF-Token");
        }
    });
    return token;
}