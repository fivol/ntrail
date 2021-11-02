from core.module.cross_connections import CrossConnections, NodeImportance


class Clusters:
    def __init__(self, objects):
        self.objects = objects

    def represent(self):
        pools = self.objects.pools()
        pools = list(filter(lambda x: x.size > 1, pools))
        pools_nodes = set(sum([pool.ids for pool in pools], []))
        all_nodes = self.objects.ids
        single_nodes = [node for node in all_nodes if node not in pools_nodes]
        single_nodes_obj = self.objects.__class__(single_nodes, target='loners')

        inter_clusters_obj = CrossConnections(self.objects)
        inter_nodes_obj = NodeImportance(self.objects)

        clusters = pools + [single_nodes_obj, inter_clusters_obj, inter_nodes_obj]

        return {
            'clusters': {
                'items':
                    [self.objects.main_cluster_data()] +
                    [
                        cluster.main_cluster_data(self.objects.hash)
                        for cluster in clusters
                    ],
                'mainID': self.objects.hash
            }
        }
