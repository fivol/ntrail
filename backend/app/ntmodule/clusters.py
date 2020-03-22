class Clusters:
    def __init__(self, objects):
        self.objects = objects

    def represent(self):
        pools = self.objects.pools()
        pools = list(filter(lambda x: x.size > 1, pools))
        pools_nodes = set(sum([pool.nodes for pool in pools], []))
        all_nodes = self.objects.nodes
        single_nodes = [node for node in all_nodes if node not in pools_nodes]
        pools.append(self.objects.__class__(single_nodes, target='loners'))

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
