from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import CallbackLog
from .functions import process_callback

import json


@csrf_exempt
def callback(request):

    get_data = {}
    for key, value in request.GET.items():
        get_data[key] = value

    post_data = {}
    for key, value in request.POST.items():
        post_data[key] = value

    meta_data = {}
    for key, value in request.META.items():
        meta_data[key] = value

    body_data_to_insert = request.body
    try:
        body_data_to_insert = json.dumps(json.loads(body_data_to_insert))
    except:
        pass

    callback_object = CallbackLog(http_method=request.method, get_data=get_data,
                                  post_data=post_data, body_data=body_data_to_insert, meta_data=meta_data)

    try:
        process_callback(json.loads(request.body))
    except Exception as e:
        callback_object.error = str(e)

    callback_object.processed = True
    callback_object.save()

    return JsonResponse({'success': True})
