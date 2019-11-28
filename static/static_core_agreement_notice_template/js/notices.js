$(function () {

  /* Functions */

  var loadForm = function () {


    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-notice").modal({backdrop:'static'});
      },
      success: function (data) {
          $("#modal-notice .modal-content").html(data.html_form);
      }
    });
  };

  var saveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#notice-table tbody").html(data.html_notice_list);
          $("#modal-notice").modal("hide");
        }
        else {
          $("#modal-notice .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };

  /* Binding */

  // Create notice
  $(".js-create-notice").click(loadForm);
  $("#modal-notice").on("submit", ".js-notice-create-form", saveForm);

  // Update notice
  // $("#notice-table").on("click", ".js-update-notice", loadForm);
  $("#modal-notice").on("submit", ".js-notice-update-form", saveForm);

   $(".js-update-notice").on("click", loadForm);

  // Delete notice
  $("#notice-table").on("click", ".js-delete-notice", loadForm);
  $("#modal-notice").on("submit", ".js-notice-delete-form", saveForm);

});