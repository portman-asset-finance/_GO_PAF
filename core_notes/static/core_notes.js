
var customer = false ;
var confirmed = false ;
var typeChanged, profileChanged, brokerChanged = false ;
var typeValue, profileValue, brokerValue ;

$(function() {

    /*
    $("#id-postcode-search").keypress(function(e) {
        if(e.which === 13) {
            postcoder($(this).val());
        }
    });
    */

    var clicked = false;
    $("#postcode-search").click(function() {
        runPostcodeSearch() ;
    });

    $("#input-contact-modal .modal-content").on("click", "#postcode-search", function() {
        runPostcodeSearch();
    });

    function runPostcodeSearch() {

        if(clicked) return;
        clicked = true;
        var postcode = $("#id-postcode-search").val();

        postcoder(postcode, function() {
            clicked = false;
            $("#id-postcode").val(postcode);
        });

    }

    /* var validationSelectors = $("[data-validate='true']");

    validationSelectors.on("keyup", function() {
        removeValidationMessage(this);
    }) ;
    validationSelectors.on("change", function () {
        removeValidationMessage(this);
    }) ;

    function removeValidationMessage(t) {
        if($(t).val()) {
            $(t).removeClass('error');
            $(t).closest('.form-group').find('.invalid-feedback').html('');
        }
    }
    */

    var switch_label = $("#customer-switch-label") ;
    var company_name_err = $("#company-name-err");

    var eacElement = $("#company_name") ;

    $("#customer-switch").click(function() {

        if($(this).is(":checked")) {

            // New customer
            switch_label.html("New customer") ;
            $("#customer-number-display").html("").hide() ;
            $("#new_company_name").val(eacElement.val()).show().attr("disabled", false);
            eacElement.hide().attr("disabled", true);

        } else {

            // Existing Customer
            switch_label.html("Existing Customer");
            eacElement.show().attr("disabled", false);
            $("#new_company_name").hide().attr("disabled", true);

            $("#company_name").val("");
            $("#new_company_name").val("");

        }

        $("#id-customer-number").val("") ;
        $("#id-address-line-1").val("") ;
        $("#id-address-line-2").val("") ;
        $("#id-address-line-3").val("") ;
        $("#id-address-line-4").val("") ;
        $("#id-address-line-5").val("") ;
        $("#id-customer-number").val("")  ;
        $("#id-postcode").val("") ;
        $("#id-customer-contact-name").val("") ;
        $("#id-customer-phone").val("") ;
        $("#id-customer-email").val("");
        $("#id-customer-mobile").val("") ;

    });

    $("#confirm-changes-ok").click(function() {
        confirmed = true ;
        $("#form_tab1").trigger("submit");
    });

    typeValue = $("#id-agreement-type-value");
    profileValue = $("#id-profile-type-value");
    brokerValue = $("#id-broker-type-value");

    var agreementStage = $("#id-agreement-stage").val();

    $("#id-agreement-type").change(function() {
        if(parseInt(agreementStage) > 1) {
            typeChanged = $(this).val() !== typeValue.val();
        }
    });

    $("#id-profile-type").change(function() {
        if(parseInt(agreementStage) > 1) {
            profileChanged = $(this).val() !== profileValue.val();
        }
    });

    $("#id-broker-type").change(function() {
        if(parseInt(agreementStage) > 1) {
            brokerChanged = $(this).val() !== brokerValue.val();
        }
    });

    $("#form_tab1").submit(function(e) {

        var customer_number = $("#id-customer-number").val();

        company_name_err.hide() ;

        var existing = true ;

        if($("#customer-switch").is(":checked")) existing = false ;

        // if(existing && !customer_number) {
        //     e.preventDefault() ;
            // company_name_err.html("Please select a valid company").show() ;
        // }

        if(customer_number && !confirmed) {

            e.preventDefault();
            if (!customer) {
                getCustomer(customer_number, function () {
                    if (checkCustomerChanges()) {
                        confirmed = true;
                        $("#form_tab1").trigger("submit");
                    }
                });
                return ;
            }

            if(checkCustomerChanges()) {
                confirmed = true;
                $(this).trigger("submit");
            }

        }

    });

});


function checkCustomerChanges() {

    var changes = 0 ;
    var changes_html = "<ul>" ;

    var company_name = $("#company_name").val();
    if(company_name !== customer.customercompany && customer.customercompany !== null) {
        changes++;
        changes_html += "<li>Company name from '" + customer.customercompany + "' to '" + company_name + "'</li>";

    }

    var address1 = $("#id-address-line-1").val();
    if(address1 !== customer.customeraddress1 && customer.customeraddress1 !== null) {
        changes++;
        changes_html += "<li>Address line 1 from '" + customer.customeraddress1 + "' to '" + address1 + "'</li>" ;
    }

    var address2 = $("#id-address-line-2").val();
    if(address2 !== customer.customeraddress2 && customer.customeraddress2 !== null) {
        changes++;
        changes_html += "<li>Address line 2 from '" + customer.customeraddress2 + "' to '" + address2 + "'</li>" ;
    }

    var postcode = $("#id-postcode").val();
    if(postcode !== customer.customerpostcode && customer.customerpostcode !== null) {
        changes++;
        changes_html += "<li>Postcode from '" + customer.customerpostcode + "' to '" + postcode +"'</li>" ;
    }

    var contact = $("#id-customer-contact-name").val();
    if(contact !== customer.customercontact && customer.customercontact !== null) {
        changes++;
        changes_html += "<li>Contact name from '" + customer.customercontact + "' to '" + contact + "'</li>";
    }

    var email = $("#id-customer-email").val();
    if(email !== customer.customeremail && customer.customeremail !== null) {
        changes++ ;
        changes_html += "<li>Email from '" + customer.customeremail + "' to '" + email + "'</li>" ;
    }

    var phone = $("#id-customer-phone").val();
    if(phone !== customer.customerphonenumber && customer.customerphonenumber !== null) {
        changes++ ;
        changes_html += "<li>Phone number from '" + customer.customerphonenumber + "' to '" + phone + "'</li>"
    }

    var mobile = $("#id-customer-mobile").val();
    if(mobile !== customer.customermobilenumber && customer.customermobilenumber !== null) {
        changes++ ;
        changes_html += "<li>Mobile number from '" + customer.customermobilenumber + "' to '" + mobile + "'</li>" ;
    }

    changes_html += "</ul>" ;

    if(changes) {
        $("#customer-changes-area").show();
        $("#customer_changes").val(changes);
    } else {
        $("#customer-changes-area").hide();
    }

    if(typeChanged||profileChanged||brokerChanged) {

        var agreement_changes_html = "<ul>";

        if(typeChanged) {
            agreement_changes_html += "<li>Agreement type</li>";
        }
        if(profileChanged) {
            agreement_changes_html += "<li>Profile type</li>";
        }
        if(brokerChanged) {
            agreement_changes_html += "<li>Broker type";
        }

        agreement_changes_html += "</ul>";

        $("#agreement-changes-area").show();
        $("#agreement-changes").html(agreement_changes_html);

        changes = true ;

    } else {
        $("#agreement_changes-area").hide();
    }

    if(changes) {

        $("#customer-changes").html(changes_html);
        $("#confirm-changes").modal("show");

        return false ;

    }

    return true ;

}

function postcoder(p, c) {

    $("#address-select").html("") ;
    $("#address-search-results").hide() ;

    var postcodes ;

    $.ajax({
        url: "https://api.getAddress.io/find/" + p + "?api-key=7aC6nUQ6DEC9t9E3oRSxvQ18620",
        dataType: "json",
        success: function(data) {

            var count = 0;
            postcodes = data;

            $("#address-select").append($("<option>", {
                value: '',
                text: 'Please Select'
            }));

            $.each(data.addresses, function(i, item) {

                count = i + 1;
                var address = "";
                var lines = data.addresses[i].split(",");
                for(var i = 0; i < lines.length; i++) {
                    if(lines[i] && lines[i] !== " ") {
                        address = address + lines[i] + ",";
                    }
                }
                address = address.replace(/,$/, '');

                $("#address-select").append($("<option>", {
                    value: address,
                    text: address
               }));

            });

            $("#address-select").change(function() {

                var lines = $(this).val().split(",");
                for(var i = 0; i < lines.length; i++) {
                    $("#id-address-line-" + Math.floor(i + 1)).val(lines[i]).trigger("change");
                }

                $("#id-postcode").val(p).trigger("change") ;

            });

            if(count) {
               $("#address-search-results").show();
            }

            if(c && typeof c === "function") c();

        },
        error: function(data) {

            var systemFailure = false ;

            if(data) {
                if('responseText' in data) {
                    try {
                        var response = JSON.parse(data.responseText);
                        if('Message' in response) {
                            systemFailure = response.Message ;
                        }
                    } catch(err) {
                    }
                }
            }

            if(systemFailure) {
                if(systemFailure=='Not Found'){
                    $("#postcode-error-message-text").html('<b>Postcode is Invalid</b>')
                }
                if(systemFailure=='Bad Request'){
                    $("#postcode-error-message-text").html('<b>Postcode has been entered incorrectly</b>')
                }
                // $("#postcode-error-message-text").html('<b>Request Failed:</b> ' + systemFailure) ;
                $("#postcode-error-message").modal();
            } else {
                $("#postcode-error").modal();
            }

            if(c && typeof c === "function") c() ;
        }
    })

}

function getCustomer(customer_no, _cb) {

    $.ajax({
        url: '/core_agreement_crud/customer/' + customer_no,
        success: function(res) {

            $("#id-profile-type").trigger("change");

            customer = res.data ;
            if(_cb && typeof _cb === "function") {
                return _cb() ;
            }
            $("#company_name").val(res.data.customercompany);
            $("#id-customer-number").val(customer_no) ;
            $("#customer-number-display").html(customer_no + ":").show() ;
            $("#id-address-line-1").val(res.data.customeraddress1) ;
            $("#id-address-line-2").val(res.data.customeraddress2) ;
            $("#id-address-line-3").val(res.data.customeraddress3) ;
            $("#id-address-line-4").val(res.data.customeraddress4) ;
            $("#id-address-line-5").val(res.data.customeraddress5) ;
            $("#id-customer-number").val(res.data.customernumber)  ;
            $("#id-postcode").val(res.data.customerpostcode) ;
            $("#id-customer-contact-name").val(res.data.customercontact) ;
            $("#id-customer-phone").val(res.data.customerphonenumber) ;
            $("#id-customer-email").val(res.data.customeremail);
            $("#id-customer-mobile").val(res.data.customermobilenumber) ;
        },
        error: function() {

        }
    });

}

function isCurrency(e) {

    e = e ? e : window.event ;

    var charCode = e.which ? e.which : e.keyCode ;

    if(charCode > 31 && (charCode < 48 || charCode > 57)) {
        if(charCode !== 46) {
            return false ;
        }
    }

    return true ;

}

function isNumber(e) {

    e = e ? e : window.event ;

    var charCode = e.which ? e.which : e.keyCode ;

    if(charCode > 31 && (charCode < 48 || charCode > 57)) {
        return false ;
    }

    return true ;

}
