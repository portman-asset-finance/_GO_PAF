window.performUnload = true ;

document.body.onbeforeunload = function() {
    if(!window.performUnload) {
        window.performUnload = true ;
        return ;
    }
    sessionStorage.removeItem("GoSageBatchLock");
    $.ajax({
        method: 'POST',
        url: '{% url 'core_sage_export:unlock_batch' sage_batch_ref %}',
        data: {
            session_id: '{{ sage_batch_lock.session_id }}'
        },
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}')
        }
    });
};