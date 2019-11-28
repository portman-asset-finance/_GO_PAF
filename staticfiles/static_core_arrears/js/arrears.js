$(function () {

  /* Functions */
  var loadForm = function () {
    var arrear_update = $(this);
    $.ajax({
      url: arrear_update.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#arrear-modal").modal({backdrop:'static'})
      },
      success: function (data) {
        $("#arrear-modal .modal-content").html(data.html_arrears_form)
      }
    });
  };

  /* Functions */
  var viewForm = function () {
    var arrear_view = $(this);
    $.ajax({
      url: arrear_view.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#arrear-modal").modal({backdrop:'static'})
      },
      success: function (data) {
        $("#arrear-modal .modal-content").html(data.html_arrears_form)
      }
    });
  };

  var saveForm = function () {
    $('#btn-update-arrear').prop('disabled', true);
    var form = $(this);
    var return_target = form.attr("data-url");
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#arrear-modal").modal("hide");
          $('.modal-backdrop').remove();
          location.href = return_target;
        }
        else {
          $("#arrear-modal .modal-content").html(data.html_arrears_form);
          $('#btn-update-arrear').prop('disabled', false);
        }
      }
    });
    return false;
  };

  var saveCancellation = function () {
    $('#btn-cancel-allocation').prop('disabled', true);
    var form = $(this);
    var return_target = form.attr("data-url");
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#arrear-modal").modal("hide");
          $('.modal-backdrop').remove();
          location.href = return_target;
        }
        else {
          $("#arrear-modal .modal-content").html(data.html_arrears_form);
          $('#btn-cancel-allocation').prop('disabled', false);
        }
      }
    });
    return false;
  };

  /* Binding */

  // Update book
  $("#arrear-table").on("click", ".js-update-arrear", loadForm);
  $("#arrear-modal").on("submit", ".js-arrear-update-form", saveForm);
  $("#arrear-table").on("click", ".js-view-collection", viewForm);
  $("#arrear-modal").on("submit", ".js-cancel-allocation-form", saveCancellation);

});