''' 
Stub for management command.
Caches all users balance at the beginning of the day.
Later this cached balances will be used to determine balance
at every point of time.
Command should be indempotent to multiple runs
'''

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    
    '''Stub for day balance caching command'''

    help = 'Cache active user balances'

    def handle(self, *args, **options):
        pass

