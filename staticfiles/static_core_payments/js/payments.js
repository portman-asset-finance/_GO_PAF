$(function () {

  /* Functions */

  loadForm = function (e, t, c) {

    var btn = $(this);
    if(t) btn = $(t);

    var modalSelector = btn.attr("data-modal-target");

    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $(modalSelector).modal({"backdrop":"static"});
      },
      success: function (data) {
          console.log(modalSelector);
        $(modalSelector + " .modal-content").html(data.html_record_form);
      },
      error: function(data) {
        alert(JSON.stringify(data));
      }
    });
  };

$(".js-modal-record_payment").click(loadForm);

});