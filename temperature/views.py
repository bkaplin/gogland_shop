import json
import re

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from temperature.forms import CalculateAverageForm


class CalculateAverage(TemplateView):
    template_name = 'temperature/calculate_average.html'
    form_class = CalculateAverageForm

    def get_context_data(self, **kwargs):
        context = super(CalculateAverage, self).get_context_data(**kwargs)

        context['form'] = self.form_class

        return context

    def post(self, request, **kwargs):
        res, errors = self.process_data(request.POST.get('data'))

        return HttpResponse(json.dumps({'success': True, 'result': res, 'errors': errors}), status=200, content_type='application/json')

    @staticmethod
    def process_data(data):
        started, ended = False, False
        pochva, bydka = [], []
        pochva_min, pochva_max = [], []
        bydka_min, bydka_max = [], []
        errors = None

        for line in data.split('\n'):
            if re.match(r'\(\(\d{2},21', line):
                if not started:
                    started = True
                    continue
                else:
                    ended = True

            if started and not ended:
                vars = line.split(',')
                if re.match(r'=04,', line):
                    t = vars[2]
                    t_min = vars[4]
                    t_max = vars[5]
                    try:
                        real_t = int(t) / 10.0
                        real_t_min = int(t_min) / 10.0
                        real_t_max = int(t_max) / 10.0
                    except:
                        errors = f'Error: неверное значение в строчке {line}'
                        break

                    pochva.append(real_t)
                    pochva_min.append(real_t_min)
                    pochva_max.append(real_t_max)

                elif re.match(r'=05,', line):
                    t = vars[1]
                    t_min = vars[4]
                    t_max = vars[5]
                    try:
                        real_t = int(t) / 10.0
                        real_t_min = int(t_min) / 10.0
                        real_t_max = int(t_max) / 10.0
                    except:
                        errors = f'Error: неверное значение в строчке {line}'
                        break

                    bydka.append(real_t)
                    bydka_min.append(real_t_min)
                    bydka_max.append(real_t_max)

        if not errors:
            len_pochva = len(pochva) or 1
            len_bydka = len(bydka) or 1
            res = {
                'pochva': {
                    'average': round(sum(pochva) / len_pochva, 1),
                    'min': min(pochva_min[:4]) if pochva_min else -999,
                    'max': max(pochva_max[4:]) if pochva_max else 999,
                },
                'bydka': {
                    'average': round(sum(bydka) / len_bydka, 1),
                    'min': min(bydka_min[:4]) if bydka_min else -999,
                    'max': max(bydka_max[4:]) if bydka_max else 999,
                }
            }
        else:
            res = None

        return res, errors
