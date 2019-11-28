$(function(){

    $('.switchbutton').click(function() {
        processSwitch($(this));
        inputManagement();
    });

    $("#btn-collect-all").click(function(){

        $('#arrears_total_collected').val(addCommas(0.00));
        $('#arrears_total_adjustment').val(addCommas(0.00));
        $('.switchdiv').show();

        let cur_total_arrears = initNaN(parseFloat($('#arrears_total_arrears').val().replace(',','')));
        let cur_unallocated_receipts = initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value')));
        let calc_total_collected = 0;
        let calc_unallocated_receipts = 0;

        if ( cur_total_arrears > cur_unallocated_receipts) {
            calc_total_collected = cur_unallocated_receipts;
            calc_unallocated_receipts = 0;
        } else {
            calc_total_collected = cur_total_arrears;
            calc_unallocated_receipts = (cur_unallocated_receipts - cur_total_arrears );
        }

        $('#widget_unallocated_arrears_total').html(addCommas(calc_unallocated_receipts.toFixed(2)));
        $('#arrears_total_collected').val(addCommas(calc_total_collected.toFixed(2)));

        allocateCollection();
        updateDetailTotals();
        updateSummaryTotals();
        updateUnallocatedReceipts();
        $('.switchbutton').each(function() {
            processSwitchOff($(this))
        });
        inputManagement();
    });

    $("#btn-refresh-all").click(function(){
        $('#arrears_total_collected').val(addCommas((0.00).toFixed(2)));
        $('#arrears_total_adjustment').val(addCommas((0.00).toFixed(2)));
        $('.switchdiv').show();
        updateUnallocatedReceipts();
        allocateCollection();
        updateDetailTotals();
        updateSummaryTotals();
        $('.switchbutton').each(function() {
            processSwitchOff($(this))
        });
        inputManagement();
    });

    $('#arrears_total_collected').change(function() {
        $('.switchdiv').show();
        // updateUnallocatedReceipts();
        allocateCollection();
        updateDetailTotals();
        updateSummaryTotals();
        updateUnallocatedReceipts();
        $('.switchbutton').each(function() {
            processSwitchOff($(this))
        });
        inputManagement();
    });

    $('.check-for-change').change(function() {
        updateDetailElement($(this));
        updateSummaryTotals();
        updateUnallocatedReceipts();
        inputManagement();
    });

    updateDetailTotals();
    updateSummaryTotals();
    // updateUnallocatedReceipts();
    inputManagement();
});

function paymentSectionActive() {

    $('#btn-update-arrear').prop('disabled', true);
    $('#record-payment-receipt').prop('disabled', true);
    $('#btn-dismiss-collection-modal').prop('disabled', true);
    $('#btn-dismiss-modal').prop('disabled', true);
    $('#enter-card-details').prop('disabled', true);
    $('#arrears_total_collected').prop('readonly', true);
    $('.switchbutton').prop('disabled', true);
    $('#btn-collect-all').hide();
    $('#btn-refresh-all').hide();

}

function paymentSectionInactive() {

    $('#btn-update-arrear').prop('disabled', false);
    $('#record-payment-receipt').prop('disabled', false);
    $('#btn-dismiss-collection-modal').prop('disabled', false);
    $('#btn-dismiss-modal').prop('disabled', false);
    $('#enter-card-details').prop('disabled', false);
    // $('#arrears_total_collected').prop('readonly', false);
    $('.switchbutton').prop('disabled', false);
    $('#btn-collect-all').show();
    $('#btn-refresh-all').show();
    updateUnallocatedReceipts();
    inputManagement();
}

function inputManagement() {

    if ((initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value'))) === 0) ) {
        // $('#btn-update-arrear').prop('disabled', true);
        $('#arrears_total_collected').prop('readonly', true);
        // $('.switchbutton').prop('disabled', true);
        $('#btn-collect-all').hide();
        // $('#btn-refresh-all').hide();

        if (initNaN(parseFloat($('#arrears_total_balance').val().replace(',','')) !==
                (initNaN(parseFloat($('#arrears_total_arrears').val().replace(',','')))))) {
            $('#btn-update-arrear').prop('disabled', false);
            $('#btn-refresh-all').show();
        } else {
            $('#btn-update-arrear').prop('disabled', true);
            $('#btn-refresh-all').hide();
        }

    } else {

        $('#btn-update-arrear').prop('disabled', false);
        $('#arrears_total_collected').prop('readonly', false);
        $('.switchbutton').prop('disabled', false);
        $('#btn-collect-all').show();
        $('#btn-refresh-all').show();

        if (initNaN(parseFloat($('#arrears_total_balance').val().replace(',','')) !==
                (initNaN(parseFloat($('#arrears_total_arrears').val().replace(',','')))))) {
            $('#btn-update-arrear').prop('disabled', false);
            $('#btn-refresh-all').show();
        } else {
            $('#btn-update-arrear').prop('disabled', true);
            $('#btn-refresh-all').hide();
        }
    }
}

function updateDetailElement(thisObj) {

    let arrear_val_prefix = 'arrear_val_';
    let collected_val_prefix = 'collected_val_';
    let adjustment_val_prefix = 'adjustment_val_';
    let balance_val_prefix = 'balance_val_';
    let arrear_cur_prefix = 'arrear_cur_';
    let collected_cur_prefix = 'collected_cur_';
    let adjustment_cur_prefix = 'adjustment_cur_';
    let balance_cur_prefix = 'balance_cur_';
    let switch_prefix = 'switchdiv';

    let switch_number = thisObj.attr('id');
    let switch_index = switch_number[switch_number.length -1];

    let arrear_val_id = arrear_val_prefix.concat(switch_index);
    let collected_val_id = collected_val_prefix.concat(switch_index);
    let adjustment_val_id = adjustment_val_prefix.concat(switch_index);
    let balance_val_id = balance_val_prefix.concat(switch_index);
    let switch_id = switch_prefix.concat(switch_index);

    let arrear_val = initNaN(parseFloat($('#'+arrear_val_id).val().replace(',','')));
    let collected_val = initNaN(parseFloat($('#'+collected_val_id).val().replace(',','')));
    let adjustment_val = initNaN(parseFloat($('#'+adjustment_val_id).val().replace(',','')));
    let balance_val = initNaN(parseFloat($('#'+balance_val_id).val().replace(',','')));
    let unallocated_receipt_val = initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value')));

    if ((collected_val + adjustment_val) > arrear_val) {
        if (collected_val > arrear_val) {
            adjustment_val = 0;
            collected_val = arrear_val;
        } else {
            collected_val = arrear_val;
            adjustment_val = arrear_val - collected_val;
        }
    }

    if (collected_val > unallocated_receipt_val) {
        collected_val = unallocated_receipt_val;
    }

    balance_val = arrear_val - (collected_val + adjustment_val);

    $('#'+collected_val_id).val(addCommas(collected_val.toFixed(2)));
    $('#'+adjustment_val_id).val(addCommas(adjustment_val.toFixed(2)));
    $('#'+balance_val_id).val(addCommas(balance_val.toFixed(2)));

    if (arrear_val !== balance_val) {
        $('#'+switch_id).hide();
    } else {
        $('#'+switch_id).show();
    }

}

function updateUnallocatedReceipts() {

    let new_widget_unallocated_receipt_value = 0;
    let new_widget_arrears_total_value = 0;
    let new_arrears_total_collected = 0;

    if (initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')))
        <= initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value')))) {

        new_widget_unallocated_receipt_value = initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value')))
                                        - initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')));

        new_widget_arrears_total_value = initNaN(parseFloat($('#widget_agreement_arrears_total').data('value')))
                                        - initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')))
                                        - initNaN(parseFloat($('#arrears_total_adjustment').val().replace(',','')));

        new_arrears_total_collected = initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')));

    } else {

        new_widget_unallocated_receipt_value = 0;

        new_widget_arrears_total_value = initNaN(parseFloat($('#widget_agreement_arrears_total').data('value')))
                                        - initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')))
                                        - initNaN(parseFloat($('#arrears_total_adjustment').val().replace(',','')));

        new_arrears_total_collected = initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value')));

    }

    $('#widget_agreement_arrears_total').html(addCommas(new_widget_arrears_total_value.toFixed(2)));
    $('#widget_unallocated_arrears_total').html(addCommas(new_widget_unallocated_receipt_value.toFixed(2)));
    $('#arrears_total_collected').val(addCommas(new_arrears_total_collected.toFixed(2)));
}

function processSwitchOff(thisObj) {

    let arrear_val_prefix = 'arrear_val_';
    let collected_val_prefix = 'collected_val_';
    let adjustment_val_prefix = 'adjustment_val_';
    let balance_val_prefix = 'balance_val_';
    let arrear_cur_prefix = 'arrear_cur_';
    let collected_cur_prefix = 'collected_cur_';
    let adjustment_cur_prefix = 'adjustment_cur_';
    let balance_cur_prefix = 'balance_cur_';

    let switch_number = thisObj.attr('id');
    let switch_index = switch_number[switch_number.length -1];

    let arrear_val_id = arrear_val_prefix.concat(switch_index);
    let collected_val_id = collected_val_prefix.concat(switch_index);
    let adjustment_val_id = adjustment_val_prefix.concat(switch_index);
    let balance_val_id = balance_val_prefix.concat(switch_index);
    let arrear_cur_id = arrear_cur_prefix.concat(switch_index);
    let collected_cur_id = collected_cur_prefix.concat(switch_index);
    let adjustment_cur_id = adjustment_cur_prefix.concat(switch_index);
    let balance_cur_id = balance_cur_prefix.concat(switch_index);

    $('#'+arrear_val_id).removeClass('arrears-active-border-color arrears-active-font-color');
    $('#'+collected_val_id).removeClass('collected-active-border-color collected-active-font-color');
    $('#'+adjustment_val_id).removeClass('adjustment-active-border-color adjustment-active-font-color');
    $('#'+balance_val_id).removeClass('balance-active-border-color balance-active-font-color');
    $('#'+arrear_cur_id).removeClass('arrears-active-border-color arrears-active-font-color');
    $('#'+collected_cur_id).removeClass('collected-active-border-color collected-active-font-color');
    $('#'+adjustment_cur_id).removeClass('adjustment-active-border-color adjustment-active-font-color');
    $('#'+balance_cur_id).removeClass('balance-active-border-color balance-active-font-color');
    $('#'+collected_val_id).attr('readonly', true);
    $('#'+adjustment_val_id).attr('readonly', true);
    thisObj.prop('checked', false);
    thisObj.attr('checked', false);
}

function processSwitchOn(thisObj) {

    let arrear_val_prefix = 'arrear_val_';
    let collected_val_prefix = 'collected_val_';
    let adjustment_val_prefix = 'adjustment_val_';
    let balance_val_prefix = 'balance_val_';
    let arrear_cur_prefix = 'arrear_cur_';
    let collected_cur_prefix = 'collected_cur_';
    let adjustment_cur_prefix = 'adjustment_cur_';
    let balance_cur_prefix = 'balance_cur_';

    let switch_number = thisObj.attr('id');
    let switch_index = switch_number[switch_number.length -1];

    let arrear_val_id = arrear_val_prefix.concat(switch_index);
    let collected_val_id = collected_val_prefix.concat(switch_index);
    let adjustment_val_id = adjustment_val_prefix.concat(switch_index);
    let balance_val_id = balance_val_prefix.concat(switch_index);
    let arrear_cur_id = arrear_cur_prefix.concat(switch_index);
    let collected_cur_id = collected_cur_prefix.concat(switch_index);
    let adjustment_cur_id = adjustment_cur_prefix.concat(switch_index);
    let balance_cur_id = balance_cur_prefix.concat(switch_index);

    $('#'+arrear_val_id).addClass('arrears-active-border-color arrears-active-font-color');
    $('#'+adjustment_val_id).addClass('adjustment-active-border-color adjustment-active-font-color');
    $('#'+balance_val_id).addClass('balance-active-border-color balance-active-font-color');
    $('#'+arrear_cur_id).addClass('arrears-active-border-color arrears-active-font-color');
    $('#'+adjustment_cur_id).addClass('adjustment-active-border-color adjustment-active-font-color');
    $('#'+balance_cur_id).addClass('balance-active-border-color balance-active-font-color');
    $('#'+adjustment_val_id).attr('readonly', false);

    if ((initNaN(parseFloat($('#widget_unallocated_arrears_total').data('value'))) !== 0) ) {
        $('#'+collected_val_id).addClass('collected-active-border-color collected-active-font-color');
        $('#'+collected_cur_id).addClass('collected-active-border-color collected-active-font-color');
        $('#'+collected_val_id).attr('readonly', false);
    }

    thisObj.attr('checked', true);
    thisObj.prop('checked', true);
}

function processSwitch(thisObj) {
    if (thisObj.attr('checked')){
            processSwitchOff(thisObj)
        }
    else
        {
            processSwitchOn(thisObj)
        }
}

function allocateCollection() {

    let wip_arrears_total_collected = initNaN(parseFloat($('#arrears_total_collected').val().replace(',','')));
    let wip_detail_arrear_1 = initNaN(parseFloat($('#arrear_val_1').val().replace(',','')));
    let wip_detail_arrear_2 = initNaN(parseFloat($('#arrear_val_2').val().replace(',','')));
    let wip_detail_arrear_3 = initNaN(parseFloat($('#arrear_val_3').val().replace(',','')));
    let wip_detail_arrear_4 = initNaN(parseFloat($('#arrear_val_4').val().replace(',','')));
    let wip_detail_arrear_5 = initNaN(parseFloat($('#arrear_val_5').val().replace(',','')));
    let wip_detail_arrear_6 = initNaN(parseFloat($('#arrear_val_6').val().replace(',','')));
    let wip_detail_collected_1 = initNaN(parseFloat($('#collected_val_1').val().replace(',','')));
    let wip_detail_collected_2 = initNaN(parseFloat($('#collected_val_2').val().replace(',','')));
    let wip_detail_collected_3 = initNaN(parseFloat($('#collected_val_3').val().replace(',','')));
    let wip_detail_collected_4 = initNaN(parseFloat($('#collected_val_4').val().replace(',','')));
    let wip_detail_collected_5 = initNaN(parseFloat($('#collected_val_5').val().replace(',','')));
    let wip_detail_collected_6 = initNaN(parseFloat($('#collected_val_6').val().replace(',','')));

    if (wip_arrears_total_collected >= wip_detail_arrear_1) {
        wip_detail_collected_1 = wip_detail_arrear_1;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_1;
    } else {
        wip_detail_collected_1 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }
    if (wip_arrears_total_collected >= wip_detail_arrear_2) {
        wip_detail_collected_2 = wip_detail_arrear_2;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_2;
    } else {
        wip_detail_collected_2 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }
    if (wip_arrears_total_collected >= wip_detail_arrear_3) {
        wip_detail_collected_3 = wip_detail_arrear_3;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_3;
    } else {
        wip_detail_collected_3 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }
    if (wip_arrears_total_collected >= wip_detail_arrear_4) {
        wip_detail_collected_4 = wip_detail_arrear_4;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_4;
    } else {
        wip_detail_collected_4 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }
    if (wip_arrears_total_collected >= wip_detail_arrear_5) {
        wip_detail_collected_5 = wip_detail_arrear_5;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_5;
    } else {
        wip_detail_collected_5 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }
    if (wip_arrears_total_collected >= wip_detail_arrear_6) {
        wip_detail_collected_6 = wip_detail_arrear_6;
        wip_arrears_total_collected = wip_arrears_total_collected - wip_detail_collected_6;
    } else {
        wip_detail_collected_6 = wip_arrears_total_collected;
        wip_arrears_total_collected = 0;
    }

    $('#collected_val_1').val(addCommas(wip_detail_collected_1.toFixed(2)));
    $('#collected_val_2').val(addCommas(wip_detail_collected_2.toFixed(2)));
    $('#collected_val_3').val(addCommas(wip_detail_collected_3.toFixed(2)));
    $('#collected_val_4').val(addCommas(wip_detail_collected_4.toFixed(2)));
    $('#collected_val_5').val(addCommas(wip_detail_collected_5.toFixed(2)));
    $('#collected_val_6').val(addCommas(wip_detail_collected_6.toFixed(2)));
    $('#adjustment_val_1').val((0).toFixed(2));
    $('#adjustment_val_2').val((0).toFixed(2));
    $('#adjustment_val_3').val((0).toFixed(2));
    $('#adjustment_val_4').val((0).toFixed(2));
    $('#adjustment_val_5').val((0).toFixed(2));
    $('#adjustment_val_6').val((0).toFixed(2));
    }

function updateDetailTotals() {

    let balance_val_1 = (initNaN(parseFloat($('#arrear_val_1').val().replace(',',''))) -
                         initNaN(parseFloat($('#collected_val_1').val().replace(',',''))) -
                         initNaN(parseFloat($('#adjustment_val_1').val().replace(',','')))).toFixed(2) ;

    let balance_val_2 = (initNaN(parseFloat($('#arrear_val_2').val().replace(',',''))) -
                         initNaN(parseFloat($('#collected_val_2').val().replace(',',''))) -
                         initNaN(parseFloat($('#adjustment_val_2').val().replace(',','')))).toFixed(2) ;

    let balance_val_3 = (initNaN(parseFloat($('#arrear_val_3').val().replace(',',''))) -
                         initNaN(parseFloat($('#collected_val_3').val().replace(',',''))) -
                         initNaN(parseFloat($('#adjustment_val_3').val().replace(',','')))).toFixed(2) ;

    let balance_val_4 = (initNaN(parseFloat($('#arrear_val_4').val().replace(',',''))) -
                         initNaN(parseFloat($('#collected_val_4').val().replace(',',''))) -
                         initNaN(parseFloat($('#adjustment_val_4').val().replace(',','')))).toFixed(2) ;

    let balance_val_5= (initNaN(parseFloat($('#arrear_val_5').val().replace(',',''))) -
                        initNaN(parseFloat($('#collected_val_5').val().replace(',',''))) -
                        initNaN(parseFloat($('#adjustment_val_5').val().replace(',','')))).toFixed(2) ;

    let balance_val_6 = (initNaN(parseFloat($('#arrear_val_6').val().replace(',',''))) -
                         initNaN(parseFloat($('#collected_val_6').val().replace(',',''))) -
                         initNaN(parseFloat($('#adjustment_val_6').val().replace(',','')))).toFixed(2) ;

    $('#balance_val_1').val(addCommas(balance_val_1));
    $('#balance_val_2').val(addCommas(balance_val_2));
    $('#balance_val_3').val(addCommas(balance_val_3));
    $('#balance_val_4').val(addCommas(balance_val_4));
    $('#balance_val_5').val(addCommas(balance_val_5));
    $('#balance_val_6').val(addCommas(balance_val_6));
}

function updateSummaryTotals(){

    let arrears_total_arrears = (initNaN(parseFloat($('#arrear_val_1').val().replace(',',''))) +
                                 initNaN(parseFloat($('#arrear_val_2').val().replace(',',''))) +
                                 initNaN(parseFloat($('#arrear_val_3').val().replace(',',''))) +
                                 initNaN(parseFloat($('#arrear_val_4').val().replace(',',''))) +
                                 initNaN(parseFloat($('#arrear_val_5').val().replace(',',''))) +
                                 initNaN(parseFloat($('#arrear_val_6').val().replace(',','')))).toFixed(2) ;

    let arrears_total_collected = (initNaN(parseFloat($('#collected_val_1').val().replace(',',''))) +
                                   initNaN(parseFloat($('#collected_val_2').val().replace(',',''))) +
                                   initNaN(parseFloat($('#collected_val_3').val().replace(',',''))) +
                                   initNaN(parseFloat($('#collected_val_4').val().replace(',',''))) +
                                   initNaN(parseFloat($('#collected_val_5').val().replace(',',''))) +
                                   initNaN(parseFloat($('#collected_val_6').val().replace(',','')))).toFixed(2) ;

    let arrears_total_adjustment = (initNaN(parseFloat($('#adjustment_val_1').val().replace(',',''))) +
                                    initNaN(parseFloat($('#adjustment_val_2').val().replace(',',''))) +
                                    initNaN(parseFloat($('#adjustment_val_3').val().replace(',',''))) +
                                    initNaN(parseFloat($('#adjustment_val_4').val().replace(',',''))) +
                                    initNaN(parseFloat($('#adjustment_val_5').val().replace(',',''))) +
                                    initNaN(parseFloat($('#adjustment_val_6').val().replace(',','')))).toFixed(2) ;

    let arrears_total_balance = (initNaN(parseFloat($('#balance_val_1').val().replace(',',''))) +
                                 initNaN(parseFloat($('#balance_val_2').val().replace(',',''))) +
                                 initNaN(parseFloat($('#balance_val_3').val().replace(',',''))) +
                                 initNaN(parseFloat($('#balance_val_4').val().replace(',',''))) +
                                 initNaN(parseFloat($('#balance_val_5').val().replace(',',''))) +
                                 initNaN(parseFloat($('#balance_val_6').val().replace(',','')))).toFixed(2) ;

    $('#arrears_total_arrears').val(addCommas(arrears_total_arrears));
    $('#arrears_total_collected').val(addCommas(arrears_total_collected));
    $('#arrears_total_adjustment').val(addCommas(arrears_total_adjustment));
    $('#arrears_total_balance').val(addCommas(arrears_total_balance));
}

function initNaN(parm_value) {

        wip_value = parm_value;
        if (isNaN(wip_value)) {
            wip_value = parseFloat('0');
        }
    return wip_value;
}

function addCommas(nStr) {
    nStr += '';
    let x = nStr.split('.');
    let x1 = x[0];
    let x2 = x.length > 1 ? '.' + x[1] : '';
    let rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
        x1 = x1.replace(rgx, '$1' + ',' + '$2');
    }
    return x1 + x2;
}

function formatCurrency(t) {
    // Input type MUST be text
    // t = this
    // t.value = parseFloat(t.value).replace(',','').toFixed(2);
    t.value = initNaN(parseFloat(t.value.replace(',',''))).toFixed(2);
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