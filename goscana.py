#!/usr/bin/python3

import os, sys, subprocess
import json
import urllib.request, urllib.error


class Comment:
    def __init__(self, token, tag):
        self.token = token
        self.tag = f'GOSCANA_{tag}'
        self.handler = f'<!-- {self.tag} -->'
        self.base_url = self.get_base_url()
        self.pr = self.base_url.split('/')[-2]
        self.headers = {'Accept': 'application/vnd.github.v3+json',
                        'Authorization': f'token {self.token}'}

    def get_base_url(self):
        path = os.getenv('GITHUB_EVENT_PATH')  # /github/workflow/event.json
        with open(path) as json_file:
            payload = json.load(json_file)
        pulls_url = payload['pull_request']['_links']['self']['href']
        if not pulls_url:
            sys.exit('Cannot get "pulls_url" from $GITHUB_EVENT_PATH payload')
        pulls_url += '/reviews'
        print(f'Set base URL to {pulls_url}')
        return pulls_url  # f'https://api.github.com/repos/{owner}/{repo}/pulls/{self.pr}/reviews'

    def send(self, req, operation):
        try:
            with urllib.request.urlopen(req) as resp:
                status, content = resp.getcode(), resp.read().decode('utf-8')
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            msg = f'Cannot {operation} comment for the pr {self.pr} due to error: {err}'
            print(msg)
            return False, msg
        return True, content

    def find(self):
        num = 0
        req = urllib.request.Request(self.base_url, method='GET', headers=self.headers)
        ok, content = self.send(req, 'find')
        if ok:
            data = json.loads(content)
            for item in data:
                if f'{item["pull_request_url"]}/' in self.base_url and item.get('body', '').startswith(self.handler):
                    num = item['id']
        if num == 0:
            print(f'No comment sent by {self.tag} already exist')
        else:
            print(f'A comment sent by {self.tag} already exists, its id is: {num}')
        return num

    def create(self, body):
        data = {'body': f'{self.handler}\n{body}', 'event': 'COMMENT'}
        data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(self.base_url, method='POST', data=data, headers=self.headers)
        ok, content = self.send(req, 'create')
        if ok:
            print(f'Successfully created comment')
        else:
            print(f'Failed to create comment due to error\n{content}')
        return ok, content

    def update(self, body, num):
        data = {'body': f'{self.handler}\n{body}'}
        data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(f'{self.base_url}/{num}', method='PUT', data=data, headers=self.headers)
        ok, content = self.send(req, 'update')
        if ok:
            print(f'Successfully updated comment #{num}')
        else:
            print(f'Failed to update comment #{num} due to error\n{content}')
        return ok, content


class Scanner:
    def __init__(self):
        self.name = ''
        self.command = ''
        self.gomod()

    def gomod(self):
        command = 'go mod init'
        if not os.path.isfile('go.mod'):
            cmd, ret, out = self.execute(command, exit_on_failure=True)
            if ret != 0:
                return cmd, ret, out
        command = 'go mod download'
        cmd, ret, out = self.execute(command, exit_on_failure=True)
        return cmd, ret, out

    def execute(self, cmd='', print_output=True, exit_on_failure=False):
        if not cmd:
            cmd = self.command
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as err:
            if exit_on_failure:
                sys.exit(f'Command "{cmd}" failed with error: {err}')
            return cmd, 1, err
        out = (result.stdout + result.stderr).strip()
        ret = 2 if result.stderr.strip() else result.returncode
        if print_output:
            print(out)
        if ret != 0:
            msg = f'Command "{cmd}" failed, captured output is:\n{out}'
            print(msg)
            if exit_on_failure:
                sys.exit(msg)
        return cmd, ret, out

    def scan(self):
        return self.execute()

    def output_success(self, content=''):
        return content or f'## {self.name} Success!'

    def output_failure(self, content, wrap):
        if wrap:
            content = f"\n```\n{content}\n```"
        return f"## ⚠ {self.name} Failure\n\n{content}\n\n"

    def prepare_comment(self, code, output, wrap=False):
        if code:
            return self.output_failure(output, wrap)
        return self.output_success()


class Errcheck(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'errcheck'
        self.command = f'errcheck {options} {path} | grep -v defer $*'  # always ignore defer command


class Fmt(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'gofmt'
        self.command = f'gofmt -l -s {path} $*'

    def prepare_content(self, output):
        result = ''
        if output:
            for name in output.split('\n'):
                cmd, code, diff = self.execute("""gofmt -d -e "%s" | sed -n '/@@.*/,//{/@@.*/d;p}'""" % name.strip())
                result += f"\n<details><summary><code>{name}</code></summary>\n\n```diff\n{diff}\n```\n\n</details>\n"
        return result


class Imports(Scanner):
    def __init__(self, path='.', options=''):
        super().__init__()
        self.name = 'goimports'
        path = path or '.'
        self.command = f'goimports -l {path} $*'

    def prepare_content(self, output):
        result = ''
        if output:
            for name in output.split('\n'):
                cmd, code, diff = self.execute("""goimports -d -e "%s" | sed -n '/@@.*/,//{/@@.*/d;p}'""" % name.strip())
                result += f"\n<details><summary><code>{name}</code></summary>\n\n```diff\n{diff}\n```\n\n</details>\n"
        return result


class Golint(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'golint'
        self.command = f'golint -set_exit_status {path} $*'

    def prepare_content(self, output):
        result = ''
        if output:
            cmd1, ret1, out1 = self.execute("""echo "%s" | awk 'END{print}'""" % output)
            cmd2, ret2, out2 = self.execute("""echo "%s" | sed -e '$d'""" % output)
            result = f"\n{out1}\n<details><summary>Show Detail</summary>\n\n```\n{out2}\n```\n\n</details>\n"
        return result


class Gosec(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'gosec'
        self.command = f'gosec -out result.txt {options} {path}'

    def prepare_content(self, output):
        result = ''
        if output:
            cmd1, ret1, out1 = self.execute('tail -n 6 result.txt')
            cmd2, ret2, out2 = self.execute('cat result.txt')
            result = f"{out1}\n<details><summary>Show Detail</summary>\n\n```\n{out2}\n```\n\n" + \
                     "[Code Reference](https://github.com/securego/gosec#available-rules)\n\n</details>\n"
        return result


class Shadow(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'shadow'
        self.command = f'go vet -vettool=/go/bin/shadow {options} {path} $*'


class Staticcheck(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'staticcheck'
        self.command = f'staticcheck {options} {path} $*'

    def prepare_comment(self, code, output, wrap=True):
        result = super().prepare_comment(code, output, wrap)
        if code:
            result += '[Checks Document](https://staticcheck.io/docs/checks)'
        return result


class Govet(Scanner):
    def __init__(self, path='./...', options='', covgate=0):
        super().__init__()
        self.name = 'govet'
        self.command = f'staticcheck ${options} {path} $*'

    def prepare_comment(self, code, output, wrap=True):
        return super().prepare_comment(code, output, wrap)


if __name__ == '__main__':
    errors = []

    comment = update = True
    try:
        scan, path, options, covgate, comment, update, token = sys.argv[1:]
    except IndexError:
        sys.exit('Error: insufficient number of arguments provided: %s, but need 6' % (len(sys.argv)-1))

    if scan == "errcheck":
        scanner = Errcheck()
    elif scan == "gofmt":
        scanner = Fmt()
    elif scan == "imports":
        scanner = Imports()
    elif scan == "golint":
        scanner = Golint()
    elif scan == "gosec":
        scanner = Gosec()
    elif scan == "shadow":
        scanner = Shadow()
    elif scan == "staticcheck":
        scanner = Staticcheck()
    elif scan == "govet":
        scanner = Govet()

    command, code, output = scanner.scan()
    if code != 0:
        errors.append(f'Command "{command}" failed, captured output is:\n{output}')

    if comment:
        body = scanner.prepare_comment(code, output)  # always non-empty
        comm = Comment(token, scanner.name.upper())
        num = comm.find()

        if update and num != 0:
            ok, content = comm.update(body, num)
        else:
            ok, content = comm.create(body)
        if not ok:
            errors.append(content)

    sys.exit('\n'.join(errors) or None)
