# Goscana
Github Actions to perform static analysis of Go code

Inspired by [this project](https://github.com/grandcolline/golang-github-actions)
I wanted to participate in implementation of Github Actions to scan Go code.

First I thought to fork the above project and make some improvements -
update a Docker image and add ability to update PR comments if they already exist.

But finally I decided to switch from Bash scripting to Python
and add one more action to run unit tests with coverage and assert coverage threshold.
Thus, it looked more as a separate project, that is why I created a new repository.

TODO:
- add action to run unit tests with coverage and assert the quality gateway,
- write detailed documentation with screenshots,
- - verify content of comments in more cases of failing and passing checks.

Note: a similar project to scan Python code is going to be implemented in my other repository - [veripy](https://github.com/nsavelyeva/veripy).
