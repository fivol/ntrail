

### Update submodules
```shell
git submodule foreach git pull origin master
```

### Put worker symlink at the root of repo
```shell
ln -s ntrail-worker/worker .
```