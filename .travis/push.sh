setup_git() {
  git config --global user.email "travis@travis-ci.org"
  git config --global user.name "Travis CI"
}

commit_website_files() {
  git checkout master
  git add . *.png
  git add . *.csv
  git commit --message "Travis build: $TRAVIS_BUILD_NUMBER"
  git push
}

upload_files() {
  git remote add origin-pages https://${GITHUB_TOKEN}@github.com/joemiller4500/stock-predictor.git > /dev/null 2>&1
  git push --quiet --set-upstream origin-pages gh-pages 
}

setup_git
commit_website_files
# upload_files