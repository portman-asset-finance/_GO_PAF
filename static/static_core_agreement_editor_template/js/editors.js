
var loadForm = null;

$(function () {

  /* Functions */

  loadForm = function (e, t, c) {
    
    var btn = $(this);
    if(t) btn = $(t);

    var editorSelector = btn.attr("data-modal-target") || "#modal-editor";

    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      success: function (data) {
        if ('redirect' in data) {
          location.reload();
        } else {
          $(editorSelector).modal({"backdrop":"static"});
          $(editorSelector + " .modal-content").html(data.html_form);
        }
      },
      error: function(data) {
        alert(JSON.stringify(data));
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
          $("#editor-table tbody").html(data.html_editor_list);
          $("#modal-editor").modal("hide");
        }
        else if ('redirect' in data) {
          location.reload();
        }
        else {
          $("#modal-editor .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };

  /* Binding */

  // Create editor
  $(".js-create-editor").click(loadForm);
  $("#modal-editor").on("submit", ".js-editor-create-form", saveForm);

  // Update editor
  // $("#editor-table").on("click", ".js-update-editor", loadForm);
  $("#modal-editor").on("submit", ".js-editor-update-form", saveForm);

  $("#modal-editor").on("click", ".change-dates-btn", loadForm);

  $(".js-update-editor").on("click", loadForm);

  // Delete editor
  $("#editor-table").on("click", ".js-delete-editor", loadForm);
  $("#modal-editor").on("submit", ".js-editor-delete-form", saveForm);

});