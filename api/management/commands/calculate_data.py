from django.core.management.base import BaseCommand, CommandError
from heatcontrol.api.models import MeteringPointData

class Command(BaseCommand):
    help = 'calculate metering point data'

    def handle(self, *args, **options):
        for mpdata in MeteringPointData.objects.filter(deleted = False):
            mpdata.calculate_data()
        print("done")
        