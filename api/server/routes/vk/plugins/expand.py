from core import VKCommunity
from server.plugin.plugin import BasePlugin


class ExpandCommunityPlugin(BasePlugin):
    def __init__(self, community: VKCommunity, **kwargs):
        super().__init__(**kwargs)
        self._community = community

    @classmethod
    def expand(cls, nodes_part, weight_reduction_ratio=0.95, break_point=10, max_nodes=300):
        community = set(nodes_part)
        VKMethods.friends.sync_map(community)
        friends_counter = collections.Counter(
            sum([list(set(VKMethods.friends.sync(user)) - set(community)) for user in community], []))
        community_friends_amount_changes = []
        max_iterations = max_nodes
        count = 0
        curr_weight = 1
        while friends_counter.most_common(1)[0][1] > break_point and max_iterations > 0:
            count += 1
            curr_weight *= weight_reduction_ratio
            max_iterations -= 1
            new_participant, community_friends_amount = friends_counter.most_common(1)[0]
            community_friends_amount_changes.append(community_friends_amount)
            community.add(new_participant)
            del friends_counter[new_participant]
            unique_friends = set(VKMethods.friends.sync(new_participant)) - set(community)
            new_participant_unique_friends = collections.Counter(
                dict(
                    zip(
                        unique_friends,
                        [curr_weight] * len(unique_friends)
                    )

                )
            )
            friends_counter += new_participant_unique_friends
        return cls(community)

    async def response(self) -> dict:
        return {}
