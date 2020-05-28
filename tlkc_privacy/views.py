import shutil

from django.shortcuts import render
from django.conf import settings
import os
from os import path
from datetime import datetime
from p_tlkc_privacy.privacyPreserving import privacyPreserving
from django.http import HttpResponseRedirect, HttpResponse
from wsgiref.util import FileWrapper
from pm4py.objects.log.importer.xes import factory as xes_importer_factory


def tlkc_main(request):
    if request.method == 'POST':
        event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
        event_log_name = os.path.join(event_logs_path, settings.EVENT_LOG_NAME)

        if 'applyButton' in request.POST:
            temp_path = os.path.join(settings.MEDIA_ROOT, "temp")

            if settings.EVENT_LOG_NAME == ':notset:':
                return HttpResponseRedirect(request.path_info)

            values = setValues(request)

            if len(values['sens_att_list']) == 0 and float(values['confidence_bound']) !=1:
                outputs = get_output_list("TLKC")
                msg_text = 'A sensitive attribute have to be selected when confidence bounding is less than 1!'
                return render(request, 'tlkc_main.html',
                              {'log_name': settings.EVENT_LOG_NAME, 'values': values, 'outputs': outputs, 'sensitive':  values['sens_att_list'],
                               'message': msg_text})

            privacy_aware_log_path = os.path.join(temp_path, "TLKC")

            L = []
            C = []
            K = []
            K2 = []
            T = []

            T.append(values['time_accuracy'])

            L.append(int(values['bk_power']))
            K.append(int(values['k_anonymity']))

            C.append(float(values['confidence_bound']))
            K2.append(float(values['frq_threshold']))

            cont =[]
            pp = privacyPreserving(event_log_name, settings.EVENT_LOG_NAME[:-4])
            pp.apply(T, L, K, C, K2, values['sens_att_list'], cont, values['bk_type'],privacy_aware_log_path )

            outputs = get_output_list("TLKC")

            xes_log = xes_importer_factory.apply(event_log_name)
            sensitives = get_attributes(xes_log)

            return render(request, 'tlkc_main.html',
                          {'log_name': settings.EVENT_LOG_NAME, 'values': values, 'outputs': outputs,
                           'sensitvie': sensitives})

        elif 'downloadButton' in request.POST:
            if "output_list" not in request.POST:
                return HttpResponseRedirect(request.path_info)

            temp_path = os.path.join(settings.MEDIA_ROOT, "temp")
            filename = request.POST["output_list"]
            file_dir = os.path.join(temp_path,"TLKC", filename)

            try:
                wrapper = FileWrapper(open(file_dir, 'rb'))
                response = HttpResponse(wrapper, content_type='application/force-download')
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_dir)
                return response
            except Exception as e:
                return None

        elif 'addButton' in request.POST:

            if "output_list" not in request.POST:
                return HttpResponseRedirect(request.path_info)

            filename = request.POST["output_list"]

            temp_name = os.path.join(settings.MEDIA_ROOT, "temp", "TLKC", filename)
            event_name = os.path.join(settings.MEDIA_ROOT, "event_logs", filename)
            shutil.move(temp_name, event_name)

            outputs = get_output_list("TLKC")

            values = setValues(request)

            xes_log = xes_importer_factory.apply(event_log_name)
            sensitives = get_attributes(xes_log)

            return render(request, 'tlkc_main.html',
                          {'log_name': settings.EVENT_LOG_NAME, 'values': values, 'outputs': outputs,
                           'sensitvie': sensitives})

        elif "deleteButton" in request.POST:

            if "output_list" not in request.POST:
                return HttpResponseRedirect(request.path_info)

            filename = request.POST["output_list"]
            temp_path = os.path.join(settings.MEDIA_ROOT, "temp")
            file_dir = os.path.join(temp_path, "TLKC", filename)

            sensitives = []
            if settings.EVENT_LOG_NAME != ":notset:":
                xes_log = xes_importer_factory.apply(event_log_name)
                sensitives = get_attributes(xes_log)

            os.remove(file_dir)

            outputs = get_output_list("TLKC")
            values = setValues(request)

            return render(request, 'tlkc_main.html',
                          {'log_name': settings.EVENT_LOG_NAME, 'values': values, 'outputs': outputs,
                           'sensitvie': sensitives})


    else:

        values = {}
        values['bk_power'] = 2
        values['k_anonymity'] = 10
        values['confidence_bound'] = 0.5
        values['frq_threshold'] = 0.5

        outputs = get_output_list("TLKC")
        sensitives = []

        if settings.EVENT_LOG_NAME != ':notset:':
            event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
            file_dir = os.path.join(event_logs_path, settings.EVENT_LOG_NAME)
            xes_log = xes_importer_factory.apply(file_dir)

            sensitives = get_attributes(xes_log)

        return render(request, 'tlkc_main.html', {'log_name': settings.EVENT_LOG_NAME, 'values':values, 'outputs':outputs, 'sensitvie':sensitives})


def setValues(request):
    values = {}
    values['time_accuracy'] = request.POST['time_accuracy']
    values['bk_type'] = request.POST['bk_type']
    values['bk_power'] = request.POST['bk_power']
    values['k_anonymity'] = request.POST['k_anonymity']
    values['confidence_bound'] = request.POST['confidence_bound']
    values['frq_threshold'] = request.POST['frq_threshold']
    if 'sens_att_list' in request.POST:
        values['sens_att_list'] = request.POST.getlist('sens_att_list')
    else:
        values['sens_att_list'] = []
    return values


def get_output_list(directoty):
    temp_path = os.path.join(settings.MEDIA_ROOT, "temp")
    output_path = os.path.join(temp_path, directoty)
    outputs = [f for f in os.listdir(output_path) if
                           os.path.isfile(os.path.join(output_path, f))]
    return outputs

def get_attributes(xes_log):
    sensitives = []
    case_attribs = []
    for case_index, case in enumerate(xes_log):
        for key in case.attributes.keys():
            if key not in case_attribs:
                case_attribs.append(key)

    event_attribs = []
    for case_index, case in enumerate(xes_log):
        for event_index, event in enumerate(case):
            for key in event.keys():
                if key not in event_attribs:
                    event_attribs.append(key)

    sensitives = case_attribs + event_attribs
    # sensitives = case_attribs
    print("in function")
    print(sensitives)
    return sensitives