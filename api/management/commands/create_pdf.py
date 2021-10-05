from django.core.management.base import BaseCommand, CommandError
from wkhtmltopdf.views import PDFTemplateResponse
from django.http.request import HttpRequest

class Command(BaseCommand):
    help = 'create pdf'


    def handle(self, *args, **options):
        response = PDFTemplateResponse(
            HttpRequest(), 
            "report_tv7.html", 
            {}, 
            filename = "report.pdf",
            cmd_options = {
                'encoding': 'utf8',
                'quiet': True,
                'orientation': 'landscape',
            },
        )
        with open("/site/report.pdf", "wb") as f:
            f.write(response.rendered_content)        
        print("done")
        