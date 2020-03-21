class Clusters:
    def __init__(self, objects):
        self.objects = objects

    def represent(self):
        pools = self.objects.pools()
        pools = list(filter(lambda x: x.size > 1, pools))

        return {
            'clusters': {
                'items':
                    [self.objects.main_cluster_data()] +
                    [
                        pool.main_cluster_data(self.objects.hash)
                        for pool in pools
                    ],
                'mainID': self.objects.hash
            }
        }
