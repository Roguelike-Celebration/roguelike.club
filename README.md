# roguelike.club

Put web stuff in public/

Thing is based on http://v4-alpha.getbootstrap.com/examples/cover/

Edit this!

## Deployment
The website is automatically deployed whenever new commits are pushed to the `master` branch with the following `post-receive` hook set up in Gogs:

```bash
#!/usr/local/bin/bash
while read oldrev newrev ref; do
    if [[ $ref =~ .*/master$ ]]; then
        git --work-tree=/usr/local/www/roguelike.club --git-dir=/home/git/gogs-repositories/roguelike.club/roguelike.club.git checkout -f
        echo 'Deployed branch master to https://roguelike.club/'
    fi
done
```