def collect_archive(self, count=200):
    assert isinstance(count, int)
    features = self.get_features()
    if not features:
        return []
    names = list(features.keys())
    archive = DB.get_features_values(self.class_name(),
                                     names=names, count=count)
    return {
        name: (value, sorted(archive.get(name, [])))
        for name, value in features.items()
    }