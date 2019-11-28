$(function() {

    var getDT = "";
    var createUrl = "";

    var $manualPaymentInfo = $(".id-manual-payment-information") ;

    // Get DD history
    $("[data-manage-ddi]").click(function() {
        getDDlist(this);
    });

    $("#dd-new-modal").on("click", "[data-manage-ddi]", function() {
        getDDlist(this);
    });

     function getDDlist(t) {

        createUrl = $(t).attr("data-create-url");

        $.ajax({
            url: $(t).attr("data-url"),
            dataType: 'json',
            beforeSend: function(xhr) {
                getDT = new Date();
                $manualPaymentInfo.html("") ;
                $("#dd-list-modal").modal({"backdrop": "static"});
            },
            success: function(data) {
                if (data.is_manual) $manualPaymentInfo.html("<span class='badge badge-success'>Manual</span>");
                $("#dd-list-modal .table").html(data.html);
            },
            error: function(data) {
                alert(JSON.stringify(data));
            }
        })

    }

    // Create DD form
    $(".js-create-dd-form").click(function() {

        $.ajax({
            url: createUrl,
            dataType: 'json',
            beforeSend() {
                $("#dd-list-modal").modal("hide");
                $("#dd-new-modal .modal-body").html("");
                $("#dd-new-modal").modal({"backdrop": "static"});
            },
            success: function(data) {
                $("#dd-new-modal .modal-body").html(data.html_form);
            },
            error: function(data) {

            }
        });

    });

    // Submit DD form
    $("#dd-new-modal").submit(function() {

        var form = $("#id-create-dd-form");

        var submitButton = $("#id-create-dd-form button");

        submitButton.attr('disabled', true);
        submitButton.html("<i class='fa fa-pulse fa-spinner'></i></i>");

        $.ajax({
            url: createUrl,
            method: 'POST',
            data: form.serialize(),
            dataType: "json",
            success: function(data) {
                $("#dd-new-modal .modal-body").html(data.html_form);
            },
            error: function(data) {
                alert(JSON.stringify(data));

            }
        });


        return false;

    });

});