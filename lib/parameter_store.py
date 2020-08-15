from lib.log import log


class ParameterStore:
    """Class used for modeling Parameters
    """

    def __init__(self):
        self.client = None


    def load(self):
        import boto3
        self.client = boto3.client('ssm')


    def fetch_parameter(self, name):
        """Gets a Parameter from Parameter Store (Returns the Value)
        """
        if not self.client:
            self.load()
        log.debug('Fetching Parameter %s', name)
        response = self.client.get_parameter(
            Name=name, WithDecryption=True)
        return response['Parameter']['Value']


    def put_parameter(self, name, value):
        """Puts a Parameter into Parameter Store
        """
        if not self.client:
            self.load()
        current_value = self.fetch_parameter(name)
        if current_value == value:
            log.debug('No need to update parameter %', name)
            return
        log.debug('Putting SSM Parameter %s', name)
        self.client.put_parameter(Name=name, Value=value, Overwrite=True)


parameter_store = ParameterStore()
