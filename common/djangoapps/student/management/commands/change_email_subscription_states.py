"""Management command to update user's email subscription state in bulk on Braze."""
import csv
import logging

from django.core.management.base import BaseCommand, CommandError

from lms.djangoapps.utils import get_braze_client

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
SUBSCRIPTION_STATES = ["subscribed", "unsubscribed", "opted_in"]
CHUNK_SIZE = 50


class Command(BaseCommand):
    """
    Management command to update user's email subscription state in bulk on Braze.
    """

    help = """
    Change the email subscription status for all given users on braze.

    Example:

    Change email subscription status for multiple users on braze.
        $ ... change_email_subscription_states -p <csv_file_path>
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-p', '--csv_path',
            metavar='csv_path',
            dest='csv_path',
            required=False,
            help='Path to CSV file.')

        parser.add_argument(
            '-s', '--subscription_state',
            required=False,
            help='Subscription state value')

    def _chunked_iterable(self, iterable):
        """
        Yield successive CHUNK_SIZE sized chunks from iterable.
        """
        for i in range(0, len(iterable), CHUNK_SIZE):
            yield iterable[i:i + CHUNK_SIZE]

    def _chunk_list(self, emails_list):
        """
        Chunk a list into sub-lists of length CHUNK_SIZE.
        """
        return list(self._chunked_iterable(emails_list))

    def handle(self, *args, **options):
        emails = []
        csv_file_path = options['csv_path']
        subscription_state = options['subscription_state']

        if subscription_state not in SUBSCRIPTION_STATES:
            raise CommandError(f"Error: The given subscription state '{subscription_state}' is not valid.")

        try:
            with open(csv_file_path, 'r') as csv_file:
                reader = list(csv.DictReader(csv_file))
                emails = [row.get('email') for row in reader]
        except FileNotFoundError as exc:
            raise CommandError(f"Error: File not found because of {exc}")  # lint-amnesty, pylint: disable=raise-missing-from
        except csv.Error as exc:
            logger.exception(f"CSV error: {exc}")
        else:
            logger.info("CSV file read successfully.")

        chunks = self._chunk_list(emails)

        try:
            braze_client = get_braze_client()
            if braze_client:
                for i, chunk in enumerate(chunks):
                    braze_client.change_email_subscription_state(
                        email=chunk,
                        subscription_state=subscription_state
                    )
                    logger.info(f"Successfully {subscription_state} for chunk-{i + 1} consist of {len(chunk)} emails")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception(f"Unable to update email status on Braze due to : {exc}")
