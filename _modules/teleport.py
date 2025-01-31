# -*- coding: utf-8 -*-
'''
:maintainer:    Erik Kristensen <erik@erikkristensen.com>
:maturity:      new
:depends:       teleport
:platform:      all

Interact with Gravitational Teleport
'''
import re
import yaml
import time
import logging
import os

import salt.crypt
import salt.exceptions

log = logging.getLogger(__name__)

def __virtual__():
    '''
    Only load if tctl exists on the system
    '''
    if salt.utils.path.which('tctl') is None:
        return (False, 'The tctl execution module cannot be loaded: tctl unavailable.')
    else:
        return True
        
def version(failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Get Teleport Version

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.version
    '''
    command = "tctl version"
    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)
    if cmd_result['retcode'] == 0:
        return cmd_result['stdout']
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result

def nodes_add(roles="node", ttl="2m", failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Add Teleport Node

    roles
        The teleport roles to be assigned when the node token is generated

    ttl
        The time to live for the node token

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.nodes_add
    
    .. code-block:: bash
    
        salt '*' teleport.nodes_add roles="node,auth,proxy" ttl="20m"
    '''
    log.debug('teleport - tctl nodes add --roles={0} --ttl={1}'.format(roles, ttl))

    command = "tctl nodes add --roles={0} --ttl={1}".format(roles, ttl)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {}

        if debug:
            result['debug'] = cmd_result

        token_regex  = re.compile(r'^The invite token: ([0-9a-f]{32})\.?$')
        expire_regex = re.compile(r'^  - This invitation token will expire in ([0-9]+) (.*)$')
        cmd_regex    = re.compile(r'^> (.*)$')
        auth_regex   = re.compile(r'.*--auth-server\=(.*)$')
        
        for line in cmd_result['stdout'].splitlines():
            token_match  = token_regex.match(line)
            expire_match = expire_regex.match(line)
            cmd_match    = cmd_regex.match(line)
            auth_match   = auth_regex.match(line)

            if token_match:
                result['token'] = token_match.group(1)
            if expire_match:
                result['expires'] = '{0} {1}'.format(expire_match.group(1), expire_match.group(2))
                time_to_add = 0
                if expire_match.group(2) == 'minutes':
                    time_to_add = int(expire_match.group(1)) * 60
                elif expire_match.group(2) == 'hours':
                    time_to_add = int(expire_match.group(1)) * 60 * 60
                result['expires_at'] = int(time.time()) + time_to_add
            if cmd_match:
                result['command'] = cmd_match.group(1)
            if auth_match:
                result['auth_server'] = auth_match.group(1)

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result

def nodes_list(failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    List Teleport Nodes

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.nodes_list
    '''
    log.debug("teleport - tctl nodes ls")

    command = "tctl nodes ls"

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {'nodes': []}

        if debug:
            result['debug'] = cmd_result

        node_regex = re.compile('^([A-Za-z\.0-9]+)\s*([a-f0-9\-]*)\s*([0-9\.\:]*)\s*([a-z\=,]*)$')
            
        for line in cmd_result['stdout'].splitlines():
            parts = line.split('\t')
            match = node_regex.match(line)
            if match:
                result['nodes'].append({
                    'node_name': match.group(1),
                    'node_id': match.group(2),
                    'address': match.group(3),
                    'labels': match.group(4).split(',')
                })

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result


def tokens_list(failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    List Teleport Tokens

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.tokens_list
    '''
    log.debug("teleport - tctl tokens ls")

    command = "tctl tokens ls"

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {'tokens': []}

        if debug:
            result['debug'] = cmd_result

        node_regex = re.compile('^([0-9a-f]{32})\s*([A-Za-z]*)\s*([0-9]{2}\ [A-Za-z]{3}\ [0-9]{2}\ [0-9\:]{5}\ .*)$')
            
        for line in cmd_result['stdout'].splitlines():
            match = node_regex.match(line)
            if match:
                result['tokens'].append({
                    'token': match.group(1),
                    'role': match.group(2).split(','),
                    'expiry': match.group(3)
                })

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result

def clusters_add(labels="", ttl="2m", failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    return tokens_add(labels=labels, type="trusted_cluster", ttl=ttl, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def databases_add(labels="", ttl="2m", failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    return tokens_add(labels=labels, type="db", ttl=ttl, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def tokens_add(type, labels="", ttl="2m", failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Add Teleport tokens

    labels
        The teleport labels to be assigned when the token is generated

    ttl
        The time to live for the token

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.tokens_add type="db"
    
    .. code-block:: bash
    
        salt '*' teleport.tokens_add labels="env=test" ttl="20m" type="db"
    '''
    log.debug('tctl tokens add --type={0} --labels=\"{1}\" --ttl={2}'.format(type, labels, ttl))

    command = "tctl tokens add --type={0} --labels=\"{1}\" --ttl={2}".format(type, labels, ttl)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {}

        if debug:
            result['debug'] = cmd_result

        token_regex  = re.compile(r'^The [\S]* ?invite token: ([0-9a-f]{32})\.?$')
        expire_regex = re.compile(r'^This token will expire in ([0-9]+) (\w*)\.?$')
        cmd_regex    = re.compile(r'> ([a-z0-9\s\-\\\=\:\.]*)\n')
        auth_regex   = re.compile(r'.*--auth-server\=([a-z0-9\.\:]*) \\$')
        
        cmd_match    = cmd_regex.match(cmd_result['stdout'])
        if cmd_match:
            result['command'] = cmd_match.group(1)

        for line in cmd_result['stdout'].splitlines():
            token_match  = token_regex.match(line)
            expire_match = expire_regex.match(line)
            auth_match   = auth_regex.match(line)

            if token_match:
                result['token'] = token_match.group(1)
            if expire_match:
                result['expires'] = '{0} {1}'.format(expire_match.group(1), expire_match.group(2))
                time_to_add = 0
                if expire_match.group(2) == 'minutes':
                    time_to_add = int(expire_match.group(1)) * 60
                elif expire_match.group(2) == 'hours':
                    time_to_add = int(expire_match.group(1)) * 60 * 60
                result['expires_at'] = int(time.time()) + time_to_add
            if auth_match:
                result['auth_server'] = auth_match.group(1)

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result

def tokens_rm(token, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Remove Teleport Token

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.tokens_rm s0me-t0ken
    '''
    log.debug('tctl tokens rm {0}'.format(token))

    command = "tctl tokens rm {0}".format(token)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {
            'login': token,
            'result': True
        }

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        cmd_result['result'] = False
        return cmd_result

def users_add(login, local_logins=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Add Teleport User

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.users_add ekristen

    .. code-block:: bash
    
        salt '*' teleport.users_add ekristen local_logins="ekristen,erik"
    '''
    log.debug("tctl users add {0} {1}".format(login, local_logins))

    command = "tctl users add {0} {1}".format(login, local_logins)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {
            'login': login,
            'result': True
        }

        if local_logins != None:
            result['local_logins'] = local_logins

        if debug:
            result['debug'] = cmd_result

        expire_regex = re.compile(r'^Signup token has been created and is valid for (.*). Share this')
        url_regex    = re.compile(r'^https://(.*)$')
        
        for line in cmd_result['stdout'].splitlines():
            expire_match = expire_regex.match(line)
            url_match    = url_regex.match(line)
            if expire_match:
                result['expires'] = expire_match.group(1)
            if url_match:
                result['url'] = "https://{0}".format(url_match.group(1))
        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        cmd_result['result'] = False
        return cmd_result

def users_del(login, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Delete Teleport User

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.users_del ekristen
    '''
    log.debug("tctl users del {0}".format(login))
    command = "tctl users del {0}".format(login)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {
            'login': login,
            'result': True
        }

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        cmd_result['result'] = False
        return cmd_result

def users_list(failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    List Teleport Users

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.users_list
    '''
    log.debug("teleport - tctl users ls")

    command = "tctl users ls"

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/root",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {'users': []}

        if debug:
            result['debug'] = cmd_result

        user_regex = re.compile('^([\w]*)\s([a-z]*)$')
            
        for line in cmd_result['stdout'].splitlines():
            parts = line.split('\t')
            match = user_regex.match(line)
            if match:
                result['users'].append({
                    'user': match.group(1),
                    'allowed_logins': match.group(2).split(',')
                })

        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result
    

def users_exists(login):
    '''
    Checks if Teleport User Exists

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.users_exists ekristen
    '''
    existing_users = users_list()['users']
    for entry in existing_users:
        if entry['user'] == login:
            return True
    return False


def node_authentication_token(tgt='*', roles='node', ttl='2m', tgt_type='glob'):
    '''
    Get Teleport Node Authentication Token

    Designed to be called from within an sls file to populate
    the teleport configuration file
    '''
    path_teleport_dir = '/var/lib/teleport'
    path_auth_token = '/var/lib/teleport/auth_token'
    path_node_key = '/var/lib/teleport/node.key'

    authenticated = True

    if not os.path.exists(path_teleport_dir):
      os.makedirs(path_teleport_dir)

    if __salt__['file.file_exists'](path_auth_token) == True:
        try:
            with salt.utils.flopen(path_auth_token, 'r+') as stream:
                authData = yaml.load(stream)
                if authData['expires_at'] < int(time.time()):
                    authenticated = False
        except Exception as e:
            log.error(e)

    if __salt__['file.file_exists'](path_node_key) == False:
        authenticated = False
    else:
        authenticated = True

    if authenticated == False:
        args = ['roles={0}'.format(roles), 'ttl={0}'.format(ttl)]
        authentication_token = __salt__['publish.publish'](tgt, 'teleport.nodes_add', arg=args, tgt_type=tgt_type).values().pop()

        log.debug('authentication_token: {0}'.format(authentication_token))

        with salt.utils.flopen(path_auth_token, 'w+') as stream:
            yaml.dump(authentication_token, stream, default_flow_style=False)

        return authentication_token['token']
    else:
        with salt.utils.flopen(path_auth_token, 'r+') as stream:
            return yaml.load(stream)['token']

def sign_db(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport Database certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_db hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_db hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='db', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign_mongodb(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport MongoDB certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_mongodb hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_mongodb hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='mongodb', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign_cockroachdb(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport CockroachDB certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_cockroachdb hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_cockroachdb hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='cockroachdb', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign_redis(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport Redis certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_redis hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_redis hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='redis', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign_openssh(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport OpenSSH certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_openssh hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_openssh hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='openssh', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign_tls(hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport TLS certificates

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign_tls hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign_tls hosts="localhost,127.0.0.1" ttl="180d" user="jenkins"
    '''
    return sign(format='tls', hosts=hosts, ttl=ttl, user=user, failhard=failhard, ignore_retcode=ignore_retcode, redirect_stderr=redirect_stderr, debug=debug, kwargs=kwargs)

def sign(format, hosts, ttl="2190h", user=None, failhard=True, ignore_retcode=False, redirect_stderr=False, debug=False, **kwargs):
    '''
    Create teleport certificates

    format
        The certificate format

    hosts
        Applicable hosts for the certificate

    ttl
        The time to live for the token

    user
        Applicable user for the certificate

    CLI Example:

    .. code-block:: bash

        salt '*' teleport.sign format="db" hosts="localhost,127.0.0.1"
    
    .. code-block:: bash
    
        salt '*' teleport.sign format="db" hosts="localhost,127.0.0.1" ttl="2190h" user="jenkins"
    '''
    out = "salt-" + hosts.split(',')[0]

    if user != None:
        command = 'tctl auth sign --out={0} --format={1} --host={2} --user={3} --ttl={4} --overwrite'.format(out, format, hosts, user, ttl)
    else:
        command = 'tctl auth sign --out={0} --format={1} --host={2} --ttl={3} --overwrite'.format(out, format, hosts, ttl)

    if debug:
        command += " --debug"

    log.debug(command)

    cmd_result = __salt__['cmd.run_all'](
        command,
        cwd="/tmp",
        runas="root",
        python_shell=False,
        ignore_retcode=ignore_retcode,
        redirect_stderr=redirect_stderr,
        **kwargs)

    if cmd_result['retcode'] == 0:
        result = {}

        if debug:
            result['debug'] = cmd_result

        extensions = {
            "key": ".key",
            "cas": ".cas",
            "crt": ".crt",
            "private_key": "",
            "public_key": "-cert.pub"
        }
        for name,ext in extensions.items():
            cmd_result = __salt__['cmd.run_all']("cat {0}{1}".format(out, ext), cwd="/tmp", runas="root", python_shell=False, ignore_retcode=True)
            if cmd_result['retcode'] == 0:
                result[name] = cmd_result['stdout']
            else:
                result[name] = None
        
        return result
    else:
        if failhard:
            msg = "Command '{0}' failed".format(command)
            err = cmd_result['stdout' if redirect_stderr else 'stderr']
            if err:
                msg += ': {0}'.format(err)
            raise salt.exceptions.CommandExecutionError(msg)
        return cmd_result