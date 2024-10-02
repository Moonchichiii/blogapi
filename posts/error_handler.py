from rest_framework.views import exception_handler
def custom_exception_handler(exc,context):
    response=exception_handler(exc,context)
    if response is not None:
        if 'detail' in response.data:
            response.data['message']=response.data.pop('detail')
        response.data['type']='error'
    return response
