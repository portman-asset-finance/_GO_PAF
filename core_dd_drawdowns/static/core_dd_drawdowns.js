$(function() {

    var csrf_token = $("#csrf-token").val();

    $("#applyAll").click(function() {
        $("#removeAll").toggle();
    });

    $("#removeAll").click(function() {

        $("#removeAllConfirmModal").modal({"backdrop":"static"});

    });

    $("#confirmRemoveAll").click(function() {

        $(this).attr("disabled", true);

        $("#cancelRemoveAll").hide();

        $(this).html("<i class='fa fa-pulse fa-spinner'></i>");

        $.ajax({
            method: 'POST',
            url: $(this).attr("data-url"),
            data: {
                csrfmiddlewaretoken: csrf_token,
                filter: $(this).attr("data-filter")
            },
            success: function(res) {
                location.reload();
            },
            error: function(res) {
                alert(JSON.stringify(res));
                $(this).attr("disabled", false);
                $(this).html("Confirm");
                $("#cancelRemoveAll").show();
            }
        });
    });

    $("#cancelRemoveAll").click(function() {

        $("#removeAllConfirmModal").modal("hide");

    });

    var ddIncr = $("#dd-count-incr");

    $(".create-new-batch").click(function() {

        var error = $("#due-date-error");
        error.html("").hide();

        var due_date = $("#batch-due-date").val();
        var call_date = $("#batch-call-date").val();

        if(!due_date) {
            error.html("Please select a due date.").show();
            return;
        }

        var new_date_dt = new Date(); // Today
        var min_date_dt = new_date_dt.setDate(new_date_dt.getDate() + 6);
        var due_date_dt = new Date(due_date);
        var call_date_dt = new Date(call_date) ;


        // if (due_date_dt.getTime() < min_date_dt) {
        //     error.html('Due date must be at least 7 days in the future.').show();
        //     return;
        // }

        if (call_date_dt.getTime() < min_date_dt) {
            error.html('Actual Due date must be at least 7 days in the future.').show();
            return;
        }

        if(due_date) {
            $(this).attr("disabled", true);
            $(".create-new-batch-loading").show();
            $("#cancel-create-new-batch").hide();
            var url = "/core_dd_drawdowns/create/" + due_date;
            if (call_date !== due_date) {
                url += '?call_date=' + call_date ;
            }
            var i = 1;
            ddIncr.html("1");
            setInterval(function() {
                ddIncr.html(++i);
            }, 300);
            location.href = url ;
        }
    });

    $(".remove-drawdown").click(function() {

        $("#confirm-remove-drawdown").modal({'backdrop': 'static'});

        var t= $(this);

        var clicked = false;

        $(".confirm-remove").click(function() {

            alert("Clicked!");

            if(clicked) return ;
            clicked = true ;

            $.ajax({
                url: t.attr('data-url'),
                method: 'POST',
                data: {
                    csrfmiddlewaretoken: csrf_token
                },
                beforeSend: function (xhr) {
                    $("#confirm-remove-drawdown").modal({'backdrop': 'static'});
                },
                success: function (data) {
                    location.href = document.location ;
                },
                error: function (data) {
                    alert(JSON.stringify(data));
                }
            }).done(function() {
                clicked = false;
            });

        });

    });

    $(".dd-batch-history-list").click(function(e) {

        e.preventDefault();

        var url = $(this).attr("href");

        if(typeof(Storage) !== "undefined") {
            if(sessionStorage.batchListReferer) {
                url = sessionStorage.batchListReferer;
            }
        }

        location.href = url ;

    });

    var t = false ;
    var dd_ids = []
    var error = $(".submit-drawdown-error");
    var buttons = $(".submit-drawdown-buttons");
    var loading = $(".submit-drawdown-loading");

    $(".submit-batch").click(function() {

        error.hide();
        loading.hide();

        if (!t) {
            t = $(this) ;
        }

        dd_ids = [];

        $("[data-drawdown-id]").each(function() {
            dd_ids.push($(this).attr('data-drawdown-id'));
        });

        $("#confirm-submit-batch").modal({'backdrop': 'static'});

    });

    var clicked = false;
    $(".confirm-submit").click(function() {

        if(clicked) return ;
        clicked = true ;

        buttons.hide();

        error.hide();

        loading.show();
        buttons.hide();

        $.ajax({
            url: t.attr("data-url"),
            method: 'POST',
            data: {
                ids: JSON.stringify(dd_ids),
                csrfmiddlewaretoken: csrf_token
            },
            success: function(data) {
                clicked = false ;
                if ('error' in data) {
                    error.html(data.error).show();
                    loading.hide();
                    buttons.show();
                    return ;
                }
                if ('changes' in data) {
                    _update_forecast(data.forecast);
                    error.html('There have been a total of ' + data.changes.length +
                        ' changes since the last re-sync. Please double-check the changes below and confirm.').show();
                    loading.hide();
                    buttons.show();
                    return ;
                }
                location.href = '/core_dd_drawdowns/view/' + data.success + '?success=1';
            },
            error: function(data) {
                error.html(JSON.stringify(data)).show();
                loading.hide();
                buttons.show();
                clicked = false;
            }
        });

    });

});