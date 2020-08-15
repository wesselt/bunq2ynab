import boto3

from lib.errors import ParameterNotFoundError
from lib.log import log


class ParameterStore:
    """Class used for modeling Parameters
    """

    def __init__(self):
        self.client = boto3.client('ssm')

    def fetch_parameter(self, name, with_decryption=False):
        """Gets a Parameter from Parameter Store (Returns the Value)
        """
        try:
            log.debug('Fetching Parameter %s', name)
            response = self.client.get_parameter(
                Name=name,
                WithDecryption=with_decryption
            )
            return response['Parameter']['Value']
        except self.client.exceptions.ParameterNotFound:
            errmsg = 'Parameter {0} Not Found'.format(name)
            log.critical(errmsg)
            raise ParameterNotFoundError(
                errmsg
            )

    def put_parameter(self, name, value):
        """Puts a Parameter into Parameter Store
        """
        try:
            current_value = self.fetch_parameter(name)
            assert current_value == value
            log.debug(
                'No need to update parameter %s with value %s since they are the same', name, value)
        except (ParameterNotFoundError, AssertionError):
            log.debug('Putting SSM Parameter %s with value %s', name, value)
            self.client.put_parameter(
                Name=name,
                Value=value,
                Type='String',
                Overwrite=True
            )


parameter_store = ParameterStore()
