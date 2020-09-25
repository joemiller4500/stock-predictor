setup_git() {
  git config --global user.email "travis@travis-ci.org"
  git config --global user.name "Travis CI"
}

commit_website_files() {
  git checkout master
  git add .
  git commit --message "Travis build: $TRAVIS_BUILD_NUMBER"
}

setup_git
commit_website_files
